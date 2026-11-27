from abc import ABC, abstractmethod
from typing import List, Dict, Any, Callable, Awaitable, Tuple


class BaseSourceAdapter(ABC):
    """Abstract base class for all pluggable business lead data sources."""

    def __init__(self, name: str):
        self.name = name

    def capabilities(self) -> Dict[str, bool]:
        """Declares which Smart Lead Filter fields this source adapter supports."""
        return {
            "has_website": True,
            "mobile": True,
            "email": False,
            "rating": True,
            "reviews": True,
            "verified": False,
            "social_only": False,
            "exclude_chains": True,
        }

    @abstractmethod
    async def collect(
        self,
        city: str,
        category: str,
        max_scrolls: int,
        on_listing_collected: Callable[[Dict[str, Any]], Awaitable[None]],
        on_progress_update: Callable[[str, str], Awaitable[None]],
        check_pause_cancel: Callable[[], Awaitable[Tuple[bool, bool]]],
        wait_for_resume: Callable[[], Awaitable[None]],
        state: str = "Odisha",
    ) -> List[Dict[str, Any]]:
        """Executes search and returns collected raw listing dictionaries."""
        pass

    @abstractmethod
    async def close(self):
        """Releases network, browser or thread resources."""
        pass
