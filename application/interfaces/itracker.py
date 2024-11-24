from abc import ABC, abstractmethod


class ITracker(ABC):
    @abstractmethod
    async def get_peers(self):
        pass

    @abstractmethod
    def _parse_response(self, data: bytes):
        pass
