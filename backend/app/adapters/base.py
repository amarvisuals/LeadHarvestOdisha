from abc import ABC, abstractmethod
from typing import List, Dict, Any, Callable, Awaitable, Optional, Tuple

class BaseSourceAdapter(ABC):
    """Abstract base class for all pluggable business lead data sources."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def collect(
        self,
        city: str,
        category: str,
        max_scrolls: int,
        on_listing_collected: Callable[[Dict[str, Any]], Awaitable[None]],
        on_progress_update: Callable[[str, str], Awaitable[None]],
        check_pause_cancel: Callable[[], Awaitable[Tuple[bool, bool]]], # returns (is_paused, is_cancelled)
        wait_for_resume: Callable[[], Awaitable[None]]
    ) -> List[Dict[str, Any]]:
        """
        Executes search and returns collected raw listing dictionaries.
        """
        pass

    @abstractmethod
    async def close(self):
        """Releases network, browser or thread resources."""
        pass
