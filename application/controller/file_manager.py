import asyncio
from domain.torrent import TorrentFile
from application.interfaces.ifile_manager import IFileManager


class FileManager(IFileManager):
    def __init__(self, download_path, torrent):
        self.download_path = download_path
        self.file_data = bytearray(torrent.total_length)
        self.lock = asyncio.Lock()
        self.piece_length = self.torrent.piece_length
        self.total_length = self.torrent.total_length
        self.file_data = bytearray(self.total_length)
        self.downloaded_pieces = set()
        
        
    async def save_file(self):
        if self.torrent.multi_file:
            for file_info in self.torrent.files:
                path = file_info["path"]
                length = file_info["length"]
                data = self.file_data[:length]
                with open(path, "wb") as f:
                    f.write(data)
                self.file_data = self.file_data[length:]
        else:
            with open(self.torrent.name, "wb") as f:
                f.write(self.file_data)
        print(f"Файл сохранён как {self.torrent.name}")
        

    async def add_piece(self, index: int, data: bytes):
        async with self.lock:
            if index not in self.downloaded_pieces:
                start = index * self.piece_length
                end = start + len(data)
                self.file_data[start:end] = data
                self.downloaded_pieces.add(index)
                print(
                    f"Кусок {index} добавлен. Всего загружено {len(self.downloaded_pieces)}/{self.total_pieces}"
                )