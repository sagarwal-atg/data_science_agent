"""Progress tracking for long-running operations."""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class ProgressUpdate(BaseModel):
    """A progress update message."""
    step: int
    total_steps: int
    step_name: str
    step_description: str
    progress_percent: float  # 0-100
    sub_step: Optional[str] = None
    timestamp: str


class ProgressTracker:
    """
    Tracks progress of long-running operations.
    
    Used to send real-time updates to the frontend via SSE.
    """
    
    def __init__(self, task_id: str, total_steps: int = 4):
        self.task_id = task_id
        self.total_steps = total_steps
        self.current_step = 0
        self.current_step_name = ""
        self.current_step_description = ""
        self.sub_step = None
        self.progress_percent = 0.0
        self.updates: asyncio.Queue[ProgressUpdate] = asyncio.Queue()
        self.is_complete = False
        self.error: Optional[str] = None
    
    async def start_step(self, step: int, name: str, description: str):
        """Start a new major step."""
        self.current_step = step
        self.current_step_name = name
        self.current_step_description = description
        self.sub_step = None
        # Progress is based on step number
        self.progress_percent = ((step - 1) / self.total_steps) * 100
        await self._send_update()
    
    async def update_sub_step(self, sub_step: str, progress_within_step: float = 0):
        """Update the current sub-step within a major step."""
        self.sub_step = sub_step
        # Add sub-step progress to the overall progress
        step_contribution = (1 / self.total_steps) * 100
        self.progress_percent = ((self.current_step - 1) / self.total_steps) * 100 + (progress_within_step / 100) * step_contribution
        await self._send_update()
    
    async def complete_step(self, step: int):
        """Mark a step as complete."""
        self.progress_percent = (step / self.total_steps) * 100
        self.sub_step = "Complete"
        await self._send_update()
    
    async def complete(self):
        """Mark the entire operation as complete."""
        self.is_complete = True
        self.progress_percent = 100
        self.current_step = self.total_steps
        self.sub_step = "Analysis complete!"
        await self._send_update()
    
    async def set_error(self, error: str):
        """Set an error state."""
        self.error = error
        self.sub_step = f"Error: {error}"
        await self._send_update()
    
    async def _send_update(self):
        """Send a progress update to the queue."""
        update = ProgressUpdate(
            step=self.current_step,
            total_steps=self.total_steps,
            step_name=self.current_step_name,
            step_description=self.current_step_description,
            progress_percent=min(100, self.progress_percent),
            sub_step=self.sub_step,
            timestamp=datetime.now().isoformat(),
        )
        await self.updates.put(update)
        # Small delay to allow event to be sent before continuing
        await asyncio.sleep(0.05)
    
    async def get_updates(self):
        """Generator that yields progress updates."""
        while True:
            try:
                # Use a short timeout to check for updates frequently
                update = await asyncio.wait_for(self.updates.get(), timeout=1.0)
                yield update
                
                # Check if we're done after yielding
                if self.is_complete or self.error is not None:
                    # Drain any remaining updates in the queue
                    while not self.updates.empty():
                        try:
                            remaining = self.updates.get_nowait()
                            yield remaining
                        except asyncio.QueueEmpty:
                            break
                    break
                    
            except asyncio.TimeoutError:
                # Check if analysis is complete
                if self.is_complete or self.error is not None:
                    # Drain any remaining updates
                    while not self.updates.empty():
                        try:
                            remaining = self.updates.get_nowait()
                            yield remaining
                        except asyncio.QueueEmpty:
                            break
                    break
                    
                # Send a heartbeat to keep connection alive
                yield ProgressUpdate(
                    step=self.current_step,
                    total_steps=self.total_steps,
                    step_name=self.current_step_name or "Processing",
                    step_description=self.current_step_description or "Working...",
                    progress_percent=self.progress_percent,
                    sub_step=self.sub_step or "Processing...",
                    timestamp=datetime.now().isoformat(),
                )


# Global storage for active progress trackers
_active_trackers: Dict[str, ProgressTracker] = {}


def create_tracker(task_id: str, total_steps: int = 4) -> ProgressTracker:
    """Create a new progress tracker."""
    tracker = ProgressTracker(task_id, total_steps)
    _active_trackers[task_id] = tracker
    return tracker


def get_tracker(task_id: str) -> Optional[ProgressTracker]:
    """Get an existing progress tracker."""
    return _active_trackers.get(task_id)


def remove_tracker(task_id: str):
    """Remove a progress tracker."""
    _active_trackers.pop(task_id, None)

