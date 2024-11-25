from abc import ABC, abstractmethod


class IFileManager(ABC):
    @abstractmethod
    async def create_empty_files(self):
        pass

    @abstractmethod
    async def add_piece(self, index, data):
       pass
