from abc import ABC, abstractmethod


class IDownloader(ABC):
    @abstractmethod
    async def download(self):
        pass
    

