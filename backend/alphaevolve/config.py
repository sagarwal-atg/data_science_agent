"""Centralised runtime configuration using Pydantic BaseSettings.

Environment variables (defaults in brackets):

OPENAI_API_KEY    – Required for evolution step (no default)
OPENAI_MODEL      – Chat model name ["gpt-5.1"]
MAX_COMPLETION_TOKENS        – Token cap for LLM replies [4096]
LOCAL_MODEL_NAME  – HuggingFace model name [None]
LOCAL_MODEL_PATH  – Path to local model [None]
LOCAL_SERVER_URL  – OpenAI-compatible server base URL [None]

SQLITE_DB         – Path to SQLite file ["~/.alphaevolve/programs.db"]
"""

from pathlib import Path
from typing import Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str = Field("", env="OPENAI_API_KEY")
    openai_model: str = Field("gpt-5.1", env="OPENAI_MODEL")
    max_completion_tokens: int = Field(4096, env="MAX_COMPLETION_TOKENS")
    llm_backend: str = Field("openai", env="LLM_BACKEND")
    # Local backend options
    local_model_name: Optional[str] = Field(None, env="LOCAL_MODEL_NAME")
    local_model_path: Optional[str] = Field(None, env="LOCAL_MODEL_PATH")
    local_server_url: Optional[str] = Field(None, env="LOCAL_SERVER_URL")

    # Storage
    sqlite_db: str = Field("~/.alphaevolve/programs.db", env="SQLITE_DB")
    prompt_population_size: int = Field(50, env="PROMPT_POPULATION_SIZE")
    prompt_mutation_rate: float = Field(0.3, env="PROMPT_MUTATION_RATE")
    prompt_iterations: int = Field(5, env="PROMPT_ITERATIONS")
    prompt_sqlite_db: str = Field("~/.alphaevolve/prompts.db", env="PROMPT_SQLITE_DB")

    # ------------------------------------------------------------------
    # Evolutionary parameters
    # ------------------------------------------------------------------
    population_size: int = Field(1000, env="POPULATION_SIZE")
    archive_size: int = Field(100, env="ARCHIVE_SIZE")
    num_islands: int = Field(5, env="NUM_ISLANDS")

    # Selection parameters
    elite_selection_ratio: float = Field(0.1, env="ELITE_SELECTION_RATIO")
    exploration_ratio: float = Field(0.2, env="EXPLORATION_RATIO")
    exploitation_ratio: float = Field(0.7, env="EXPLOITATION_RATIO")
    diversity_metric: str = Field("edit_distance", env="DIVERSITY_METRIC")

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields from .env


DEFAULT_CONFIG_FILE = Path(__file__).with_name("default_config.yaml")
if DEFAULT_CONFIG_FILE.exists():
    with DEFAULT_CONFIG_FILE.open("r") as f:
        yaml_defaults = yaml.safe_load(f) or {}
else:
    yaml_defaults = {}


settings = Settings(**yaml_defaults)
