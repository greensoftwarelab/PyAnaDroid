from abc import ABC, abstractmethod


class AbstractWorkLoad(ABC):
    """Defines a interface to store and consume work units representing tests to be performed over apps."""
    def __init__(self):
        super().__init__()

    @abstractmethod
    def add_unit(self, wunit):
        """Adds a work unit to the workload.
        Args:
            wunit: work unit.
        """
        pass

    @abstractmethod
    def consume(self):
        """Consume work unit."""
        pass

    @abstractmethod
    def flush(self):
        """Flush work units and clean workload."""
        pass