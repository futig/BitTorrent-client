from abc import ABC, abstractmethod


class IFileManager(ABC):
    @abstractmethod
    async def save_file(self):
        pass

    @abstractmethod
    async def add_piece(self, index: int, data: bytes):
       pass
