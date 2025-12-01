"""Async evolution controller.

High‑level loop:
1. Choose a *parent* strategy (elite or random) from `ProgramStore`.
2. Build prompt, call OpenAI → JSON diff/full code.
3. Apply patch ⇒ child code.
4. Evaluate back‑test KPIs.
5. Insert child into store (which updates MAP‑Elites grid).
"""

import asyncio
import inspect
import json
import logging
import random
import textwrap
from collections.abc import Sequence
from pathlib import Path
from typing import Optional, Union

from alphaevolve.config import settings
from alphaevolve.evaluator.backtest import evaluate
from alphaevolve.evolution.patching import apply_patch
from alphaevolve.evolution.prompt_ga import PromptGenome
from alphaevolve.llm_engine import client as llm_client
from alphaevolve.llm_engine import prompts
from alphaevolve.store.sqlite import ProgramStore
from alphaevolve.strategies.base import BaseLoggingStrategy
from examples import config as example_config

logger = logging.getLogger(__name__)


class Controller:
    def __init__(
        self,
        store: ProgramStore,
        *,
        initial_program_paths: Optional[Sequence[Union[str, Path]]] = None,
        metric: Optional[str] = None,
        max_concurrency: int = 4,
        prompt: Optional[PromptGenome] = None,
    ):
        self.store = store
        self.sem = asyncio.Semaphore(max_concurrency)
        self.initial_program_paths = [Path(p) for p in initial_program_paths or []]
        self.prompt = prompt or PromptGenome(prompts.SYSTEM_MSG, prompts.USER_TEMPLATE)
        self.metric = metric or example_config.HOF_METRIC
        self._ensure_seed_population()

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------
    def _ensure_seed_population(self):
        """If DB empty, insert seed strategies w/out metrics (lazy eval)."""
        if self.store._count() > 0:
            return  # already seeded

        paths = self.initial_program_paths
        if not paths:
            paths = [
                Path("examples/sma_momentum.py"),
                Path("examples/vol_adj_momentum.py"),
            ]

        for i, path in enumerate(paths):
            try:
                code = Path(path).read_text()
            except Exception as e:
                logger.error(f"Failed to read seed program {path}: {e}")
                continue
            self.store.insert(
                textwrap.dedent(code),
                metrics=None,
                parent_id=None,
                island=i % settings.num_islands,
            )
        logger.info("Seed strategies inserted into store.")

    def _select_parent(self, parent_id: Optional[str]):
        if parent_id:
            return self.store.get(parent_id)
        r = random.random()
        if r < settings.elite_selection_ratio:
            elites = self.store.top_k(k=settings.archive_size, metric=self.metric)
            return random.choice(elites) if elites else self.store.sample()
        r -= settings.elite_selection_ratio
        if r < settings.exploitation_ratio:
            best = self.store.top_k(k=1, metric=self.metric)
            return best[0] if best else self.store.sample()
        r -= settings.exploitation_ratio
        if r < settings.exploration_ratio:
            island = random.randrange(settings.num_islands)
            return self.store.sample(island=island)
        return self.store.sample()

    async def _spawn(self, parent_id: Optional[str], *, prompt: Optional[PromptGenome] = None):
        """Generate, evaluate & store one child strategy."""
        prompt = prompt or self.prompt
        async with self.sem:
            # 1) Select parent
            parent = self._select_parent(parent_id)
            if parent is None:
                logger.warning("No parent found; skipping spawn.")
                return

            # 2) Build prompt & call OpenAI
            messages = prompts.build(parent, self.store, metric=self.metric, prompt=prompt)
            try:
                msg = await llm_client.chat(messages)
            except Exception as e:
                logger.error(f"OpenAI call failed: {e}")
                return

            # 3) Apply patch
            try:
                diff_json = json.loads(msg.content)
            except json.JSONDecodeError as e:
                logger.error(f"Model did not return valid JSON: {e}\n{msg.content[:500]}")
                return

            child_strategy = apply_patch(parent["code"], diff_json)

            if "class BaseLoggingStrategy" not in child_strategy:
                imports = "from collections import deque\nimport backtrader as bt"
                base_cls = inspect.getsource(BaseLoggingStrategy)
                child_code = textwrap.dedent(imports + "\n\n" + base_cls + "\n\n" + child_strategy)
            else:
                child_code = textwrap.dedent(child_strategy)

            # 4) Evaluate
            try:
                kpis = await evaluate(child_code)
            except Exception as e:
                logger.error(f"Evaluation failed: {e}")
                return

            # 5) Persist
            self.store.insert(
                child_code,
                kpis,
                parent_id=parent["id"],
                island=parent.get("island", 0),
            )
            logger.info("Child stored (%s %.2f)", self.metric, kpis.get(self.metric, 0))

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    async def run_forever(self):
        """Continuous evolution loop (no termination)."""
        while True:
            await self._spawn(None, prompt=self.prompt)
            # Optional: back‑off to be polite to API limits when concurrency=1
            await asyncio.sleep(0.01)

    async def run(self, iterations: int) -> None:
        """Run the evolution loop for a fixed number of iterations."""
        for _ in range(iterations):
            await self._spawn(None, prompt=self.prompt)
            await asyncio.sleep(0.01)
