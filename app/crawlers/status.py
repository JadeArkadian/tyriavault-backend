"""
Crawler status tracking module.
Provides a simple way to track and query crawler execution status.
"""
from dataclasses import dataclass
from enum import Enum


class CrawlerStatus(Enum):
    """Status of a crawler."""
    IDLE = "idle"  # Crawler is registered but not started
    RUNNING = "running"  # Crawler is currently executing
    WAITING = "waiting"  # Crawler finished successfully and is waiting for next run
    FAILED = "failed"  # Crawler failed and is waiting to retry


@dataclass
class CrawlerState:
    """Complete state information for a crawler."""
    name: str
    status: CrawlerStatus
    total_runs: int = 0
    total_errors: int = 0

    def to_dict(self) -> dict:
        """Convert state to dictionary for easy serialization."""
        return {
            "name": self.name,
            "status": self.status.value,
            "total_runs": self.total_runs,
            "total_errors": self.total_errors,
        }
