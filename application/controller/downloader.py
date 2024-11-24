import asyncio

import domain.exceptions as exc

from application.interfaces.idownloader import IDownloader
from application.controller.tracker import Tracker
from application.controller.peer_connection import PeerConnection
from application.utils.peer_id_generator import generate_peer_id
from domain.torrent import TorrentFile



class Downloader(IDownloader):
    def __init__(self, torrent: TorrentFile, config: dict):
        self.torrent = torrent
        self.peer_id = generate_peer_id()
        
        self.downloaded_pieces = set()
        
        # self.piece_length = self.torrent.piece_length
        # self.total_length = self.torrent.total_length
        # self.file_data = bytearray(self.total_length)
        
        try:
            self.port = config["port"]
            self.debug = config["debug"]
            self.max_connections = config["max_connections"]
            self.allow_multiple_requests = config["allow_multiple_requests"]
        except KeyError as e:
            raise exc.ConfigFieldException(e) from None
        if self._debug:
            print("Downloader was initialized successfully", end="\n")


    async def download(self):
        tracker = Tracker(self.port, self.torrent, self.peer_id)
        peers = await tracker.get_peers()
        if not peers:
            raise exc.NoPeersException()
        if self._debug:
            print(f"Got {len(peers)} peers", end="\n")
        await self.connect_to_peers(peers)
        if self._debug:
            await self.monitor_download()
        await self.save_file()


    async def connect_to_peers(self, peers):
        connections_count = min(len(peers), self.max_connections)
        cons = [PeerConnection(peers[i]) for i in range(connections_count)]
        await asyncio.gather(con.connect() for con in cons)


    async def monitor_download(self):
        total_pieces = len(self.torrent.pieces)
        while len(self.downloaded_pieces) < self.total_pieces:
            await asyncio.sleep(1)
            print(f"Загружено {len(self.downloaded_pieces)}/{total_pieces} кусков.")
        print("Скачивание завершено.")