import os
import aiofiles
from domain.torrent import TorrentFile
import domain.exceptions as exc
from application.interfaces.ifile_manager import IFileManager


class FileManager(IFileManager):
    def __init__(self, download_path, torrent):
        self.download_path = download_path
        self.torrent = torrent

    async def create_empty_files(self):
        for file in self.torrent.files:
            file_path = os.path.join(self.download_path, file.path)
            directory = os.path.dirname(file_path)
            try:
                os.makedirs(directory, exist_ok=True)
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.seek(file.length - 1)
                    await f.write(b'\0')
            except Exception:
                raise exc.DirectoriesCreationException()

    async def add_piece(self, piece_index, piece_data):
        piece_start = piece_index * self.torrent.piece_length
        piece_end = min(piece_start + len(piece_data), self.torrent.size)

        current_pos = piece_start
        for file in self.torrent.files:
            file_path = os.path.join(self.download_path, file.path)
            file_start = sum(f.length for f in self.torrent.files[:self.torrent.files.index(file)])
            file_end = file_start + file.length

            if current_pos >= file_end:
                continue
            if current_pos < file_start:
                current_pos = file_start

            async with aiofiles.open(file_path, 'r+b') as f:
                await f.seek(current_pos - file_start)
                bytes_to_write = min(piece_end - current_pos, file_end - current_pos)
                await f.write(piece_data[current_pos - piece_start:current_pos - piece_start + bytes_to_write])

            current_pos += bytes_to_write
            if current_pos >= piece_end:
                break
