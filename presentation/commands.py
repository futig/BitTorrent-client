# import asyncio
from application.controller.downloader import Downloader
from domain.torrent import TorrentFile
from application.utils.config_parser import get_downloader_config, get_distributer_config


def download(path):
    torrent = TorrentFile(path)
    session = Downloader(torrent, get_downloader_config())
    # await session.start()
    
    
def distribute(path):
    pass
