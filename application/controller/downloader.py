import random
import bencodepy
import hashlib

import struct

import asyncio
import aiohttp
import socket

from application.interfaces.idownloader import IDownloader
from application.controller.tracker import Tracker
from application.utils.peer_id_generator import generate_peer_id
from domain.torrent import TorrentFile

# from domain.peer import Peer




class Downloader(IDownloader):
    def __init__(self, torrent: TorrentFile, config: dict):
        self.torrent = torrent
        self.config = config
        self.peer_id = generate_peer_id()
        
        # self.peers: list[Peer] = []
        
        self.session = aiohttp.ClientSession()
        
        self.port = self.config["port"]
        self.downloaded_pieces = set()
        self.total_pieces = len(self.torrent.pieces)
        self.piece_length = self.torrent.piece_length
        self.total_length = self.torrent.total_length
        self.file_data = bytearray(self.total_length)
        self.lock = asyncio.Lock()

    async def download(self):
        tracker = Tracker(self.port, self.torrent, self.peer_id)
        peers = await tracker.get_peers()
        if not peers:
            raise ValueError("Не удалось получить список пиров от трекера.")
        print(f"Получено {len(peers)} пиров от трекера.")
        # await self.connect_to_peers(peers)
        # await self.monitor_download()



    # async def connect_to_peers(self, peers: list[(str, int)]):
    #     """Устанавливает соединения с пирами."""
    #     tasks = []
    #     for ip, port in peers:
    #         peer = Peer(ip, port, self)
    #         self.peers.append(peer)
    #         tasks.append(peer.connect())
    #         if len(tasks) >= self.config.get("max_connections", 50):
    #             break  # Ограничиваем количество одновременных подключений
    #     await asyncio.gather(*tasks)

    # async def monitor_download(self):
    #     """Мониторит процесс скачивания."""
    #     while len(self.downloaded_pieces) < self.total_pieces:
    #         await asyncio.sleep(1)
    #         print(
    #             f"Загружено {len(self.downloaded_pieces)}/{self.total_pieces} кусков."
    #         )
    #     print("Скачивание завершено.")
    #     await self.save_file()
    #     await self.session.close()

    # async def save_file(self):
    #     """Сохраняет скачанные данные в файл."""
    #     if self.torrent.multi_file:
    #         for file_info in self.torrent.files:
    #             path = file_info["path"]
    #             length = file_info["length"]
    #             data = self.file_data[:length]
    #             with open(path, "wb") as f:
    #                 f.write(data)
    #             self.file_data = self.file_data[length:]
    #     else:
    #         with open(self.torrent.name, "wb") as f:
    #             f.write(self.file_data)
    #     print(f"Файл сохранён как {self.torrent.name}")

    # async def add_piece(self, index: int, data: bytes):
    #     """Добавляет загруженный кусок данных."""
    #     async with self.lock:
    #         if index not in self.downloaded_pieces:
    #             start = index * self.piece_length
    #             end = start + len(data)
    #             self.file_data[start:end] = data
    #             self.downloaded_pieces.add(index)
    #             print(
    #                 f"Кусок {index} добавлен. Всего загружено {len(self.downloaded_pieces)}/{self.total_pieces}"
    #             )

    # def validate_piece(self, index: int, data: bytes) -> bool:
    #     """Проверяет целостность куска данных."""
    #     hash_func = hashlib.sha1()
    #     hash_func.update(data)
    #     return hash_func.digest() == self.torrent.pieces[index]
