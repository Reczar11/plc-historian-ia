from abc import ABC, abstractmethod


class PLCDataSource(ABC):
    """Common interface for reading PLC tags."""

    @abstractmethod
    def read_tags(self, tag_names: list[str]) -> dict[str, dict]:
        """Read tags and return a mapping of name to reading.

        Each value is ``{"value": ..., "timestamp": iso8601_string, "quality": "good"|"bad"}``.
        """
        ...
