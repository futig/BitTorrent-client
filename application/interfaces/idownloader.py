from abc import ABC, abstractmethod


class IDownloader(ABC):
    @staticmethod
    @abstractmethod
    def _generate_peer_id() -> str:
        pass

    # @abstractmethod
    # async def connect_to_peers(self, peers: list[(str, int)]):
    #     pass

    @abstractmethod
    async def download(self):
        pass
    
    # @abstractmethod
    # async def monitor_download(self):
    #     pass

    # @abstractmethod
    # async def save_file(self):
    #     pass

    # @abstractmethod
    # async def add_piece(self, index: int, data: bytes):
    #    pass


