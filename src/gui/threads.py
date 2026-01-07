"""
Background thread management for GUI operations
"""

from __future__ import annotations
import threading
import queue
from typing import Callable, Any, Optional
from dataclasses import dataclass


@dataclass
class TaskResult:
    """Result from a background task"""

    success: bool
    data: Any = None
    error: Optional[str] = None


class BackgroundTaskManager:
    """Manages background tasks for the GUI to prevent freezing"""

    def __init__(self, root):
        self.root = root
        self.result_queue = queue.Queue()
        self.active_threads = []

    def run_task(
        self,
        task_func: Callable,
        on_complete: Callable[[TaskResult], None],
        *args,
        **kwargs,
    ):
        """
        Run a task in background thread and call on_complete when done.

        Args:
            task_func: Function to run in background
            on_complete: Callback function to handle result (called in main thread)
            *args, **kwargs: Arguments to pass to task_func
        """

        def worker():
            try:
                result = task_func(*args, **kwargs)
                task_result = TaskResult(success=True, data=result)
            except Exception as e:
                task_result = TaskResult(success=False, error=str(e))

            # Put result in queue
            self.result_queue.put((on_complete, task_result))

            # Schedule UI update in main thread
            self.root.after(10, self._process_results)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        self.active_threads.append(thread)

    def _process_results(self):
        """Process results from background threads (runs in main thread)"""
        try:
            while True:
                callback, result = self.result_queue.get_nowait()
                callback(result)
        except queue.Empty:
            pass

    def cleanup_finished_threads(self):
        """Remove finished threads from active list"""
        self.active_threads = [t for t in self.active_threads if t.is_alive()]
