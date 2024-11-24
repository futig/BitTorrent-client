import socket
import struct
import bencodepy
import aiohttp
import urllib.parse as url

from application.interfaces.itracker import ITracker

class Tracker(ITracker):
    def __init__(self, port, torrent, peer_id):
        self.port = port
        self.torrent = torrent
        self.peer_id = peer_id
        self.session = aiohttp.ClientSession()
    
    
    async def get_peers(self):
        url = self.torrent.announce + '?' + self._get_url_params()
        async with self.http_client.get(url) as response:
            if response.status != 200:
                raise ConnectionError(f"Ошибка при обращении к трекеру: {response.status}")
            data = await response.read()
            return self._parse_tracker_response(data)


    def _parse_response(self, data: bytes):
        decoded = bencodepy.decode(data)
        peers = decoded[b"peers"]
        peer_list = []
        if isinstance(peers, list):
            # Non-compact format
            for peer in peers:
                ip = peer[b"ip"].decode("utf-8")
                port = peer[b"port"]
                peer_list.append((ip, port))
        else:
            # Compact format
            for i in range(0, len(peers), 6):
                ip = socket.inet_ntoa(peers[i : i + 4])
                port = struct.unpack("!H", peers[i + 4 : i + 6])[0]
                peer_list.append((ip, port))
        return peer_list
        
    def _get_url_params(self):
        params = {
            "info_hash": bytes.fromhex(self.torrent.get_info_hash()),
            "peer_id": self.peer_id.encode("utf-8"),
            "port": self.port,
            "uploaded": 0,
            "downloaded": 0,
            "left": self.torrent.total_length,
            "compact": 1,
        }
        return url.urlencode(params)
            