from presentation.commands import distribute, download
import asyncio

if __name__ == "__main__":
    path = "E:\\Learning\\Fiit\\PythonTasks\\BitTorrent-client\\test_data\\green_day.torrent"
    asyncio.run(download(path))
    