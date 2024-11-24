# import asyncio
from application.controller.downloader import Downloader
from domain.torrent import TorrentFile
from application.utils.config_parser import get_downloader_config, get_distributer_config


async def download(path):
    downloader = Downloader(path, get_downloader_config())
    await downloader.download()
    
    
def distribute(path):
    pass
