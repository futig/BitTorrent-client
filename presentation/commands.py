import asyncio
from application.downloader import Downloader
from domain.torrent import TorrentFile
from application.config_parser import get_downloader_config, get_distributer_config


async def download(path):
    torrent = TorrentFile(path)
    downloader = Downloader(torrent, get_downloader_config())
    await downloader.download()
    
    
def distribute(path):
    pass
