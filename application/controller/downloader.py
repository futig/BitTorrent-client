import asyncio

import domain.exceptions as exc
from application.interfaces.idownloader import IDownloader
from application.controller.tracker import Tracker
from application.controller.file_manager import FileManager
from application.controller.peer_connection import PeerConnection
from application.utils.peer_id_generator import generate_peer_id
from domain.torrent import TorrentFile


class Downloader(IDownloader):
    def __init__(self, path, config):
        self.torrent = TorrentFile(path)
        self.peer_id = generate_peer_id()
        try:
            self.file_manager = FileManager(config["download_path"], self.torrent)
            self.port = int(config["port"])
            self.debug = config["debug"] == "True"
            self.max_connections = int(config["max_connections"])
            self.max_requests = int(config["max_requests"])
        except KeyError as e:
            raise exc.ConfigFieldException(e) from None
        if self.debug:
            print("Downloader was initialized successfully", end="\n")

    async def download(self):
        try:
            await self.file_manager.create_empty_files()
            tracker = Tracker(self.port, self.torrent, self.peer_id)
            peers = await tracker.get_peers()
            if not peers:
                raise exc.NoPeersException()
            if self.debug:
                print(f"Got {len(peers)} peers", end="\n")
            await self.connect_to_peers(peers)
            print("Done!")
        except Exception as e:
            print("Something went wrong")

    async def connect_to_peers(self, peers):
        connections_count = min(len(peers), self.max_connections)
        print(self.debug)
        cons = [
            PeerConnection(
                peers[i],
                self.torrent,
                self.peer_id,
                self.file_manager,
                self.debug,
                self.max_requests,
            )
            for i in range(connections_count)
        ]
        tasks = [con.connect() for con in cons]
        await asyncio.gather(*tasks)

