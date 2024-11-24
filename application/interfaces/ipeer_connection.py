from abc import ABC, abstractmethod


class IPeerConnection(ABC):
    @abstractmethod
    async def connect(self):
        pass
