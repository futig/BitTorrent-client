import asyncio
import random
import aiohttp
import hashlib
import struct
from typing import List, Tuple
from domain.torrent import TorrentFile
from domain.peer import Peer
import socket

class Downloader:
    def __init__(self, torrent: TorrentFile, config: dict):
        self.torrent = torrent
        self.config = config
        self.peers: List[Peer] = []
        self.session = aiohttp.ClientSession()
        self.info_hash = self.torrent.get_info_hash()
        self.peer_id = self._generate_peer_id()
        self.port = self.config.get('port', 6881)
        self.downloaded_pieces = set()
        self.total_pieces = len(self.torrent.pieces)
        self.piece_length = self.torrent.piece_length
        self.total_length = self.torrent.total_length
        self.file_data = bytearray(self.total_length)
        self.lock = asyncio.Lock()

    def _generate_peer_id(self) -> str:
        """Генерирует уникальный peer_id."""
        return '-PC0001-' + ''.join([str(random.randint(0, 9)) for _ in range(12)])

    async def get_peers_from_tracker(self):
        """Получает список пиров от трекера."""
        params = {
            'info_hash': bytes.fromhex(self.info_hash),
            'peer_id': self.peer_id.encode('utf-8'),
            'port': self.port,
            'uploaded': 0,
            'downloaded': 0,
            'left': self.total_length,
            'compact': 1
        }
        announce_url = self.torrent.announce
        async with self.session.get(announce_url, params=params) as response:
            if response.status != 200:
                print(f"Ошибка при обращении к трекеру: {response.status}")
                return
            content = await response.read()
            return self._parse_tracker_response(content)

    def _parse_tracker_response(self, data: bytes) -> List[Tuple[str, int]]:
        """Парсит ответ трекера и возвращает список пиров."""
        import bencodepy
        try:
            decoded = bencodepy.decode(data)
            peers = decoded.get(b'peers', [])
            if isinstance(peers, list):
                # Non-compact format
                peer_list = []
                for peer in peers:
                    ip = peer[b'ip'].decode('utf-8')
                    port = peer[b'port']
                    peer_list.append((ip, port))
                return peer_list
            else:
                # Compact format
                peer_list = []
                for i in range(0, len(peers), 6):
                    ip = socket.inet_ntoa(peers[i:i+4])
                    port = struct.unpack('!H', peers[i+4:i+6])[0]
                    peer_list.append((ip, port))
                return peer_list
        except Exception as e:
            print(f"Ошибка при разборе ответа трекера: {e}")
            return []

    async def connect_to_peers(self, peers: List[Tuple[str, int]]):
        """Устанавливает соединения с пирами."""
        tasks = []
        for ip, port in peers:
            peer = Peer(ip, port, self)
            self.peers.append(peer)
            tasks.append(peer.connect())
            if len(tasks) >= self.config.get('max_connections', 50):
                break  # Ограничиваем количество одновременных подключений
        await asyncio.gather(*tasks)

    async def download(self):
        """Основной метод для запуска процесса скачивания."""
        peers = await self.get_peers_from_tracker()
        if not peers:
            print("Не удалось получить список пиров от трекера.")
            return
        print(f"Получено {len(peers)} пиров от трекера.")
        await self.connect_to_peers(peers)
        await self.monitor_download()

    async def monitor_download(self):
        """Мониторит процесс скачивания."""
        while len(self.downloaded_pieces) < self.total_pieces:
            await asyncio.sleep(1)
            print(f"Загружено {len(self.downloaded_pieces)}/{self.total_pieces} кусков.")
        print("Скачивание завершено.")
        await self.save_file()
        await self.session.close()

    async def save_file(self):
        """Сохраняет скачанные данные в файл."""
        if self.torrent.multi_file:
            for file_info in self.torrent.files:
                path = file_info['path']
                length = file_info['length']
                data = self.file_data[:length]
                with open(path, 'wb') as f:
                    f.write(data)
                self.file_data = self.file_data[length:]
        else:
            with open(self.torrent.name, 'wb') as f:
                f.write(self.file_data)
        print(f"Файл сохранён как {self.torrent.name}")

    async def add_piece(self, index: int, data: bytes):
        """Добавляет загруженный кусок данных."""
        async with self.lock:
            if index not in self.downloaded_pieces:
                start = index * self.piece_length
                end = start + len(data)
                self.file_data[start:end] = data
                self.downloaded_pieces.add(index)
                print(f"Кусок {index} добавлен. Всего загружено {len(self.downloaded_pieces)}/{self.total_pieces}")

    def validate_piece(self, index: int, data: bytes) -> bool:
        """Проверяет целостность куска данных."""
        hash_func = hashlib.sha1()
        hash_func.update(data)
        return hash_func.digest() == self.torrent.pieces[index]

