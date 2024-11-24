import bencodepy
import os
import hashlib

from domain.file import File

class TorrentFile:
    def __init__(self, file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Торрент-файл не найден: {file_path}")
        
        self.file_path = file_path
        self.info = None
        self.announce = None
        self.multi_file = None
        self.piece_length = None
        self.pieces = None
        self.files = None
        self.name = None
        self.total_length = None
        
        try:
            self._decode_torrent_file()
        except Exception as e:
            raise ValueError(f"Ошибка декодирования торрент-файла: {e}")


    def _decode_torrent_file(self):
        with open(self.file_path, 'rb') as f:
            decoded = bencodepy.decode(f.read())
            
        self.info = decoded[b'info']
        self.announce = decoded[b'announce']
        self.multi_file = b'files' in self.info
        self.piece_length = self.info[b'piece length']
        self.pieces = self.info[b'pieces']
        self.name = self.info[b'name'].decode('utf-8')
        
        self.files = self._get_files()
        self.total_length = sum(file.length for file in self.files)
        

    def _get_files(self):
        if self.multi_file:
            files = self.info[b'files']
            file_list = []
            for file in files:
                length = file[b'length']
                path = b'/'.join(file[b'path']).decode('utf-8')
                file_list.append(File(path, length))
            return file_list
        else:
            length = self.info.get(b'length')
            name = self.info.get(b'name', b'').decode('utf-8')
            return [File(name, length)]


    def get_info_hash(self) -> str:
        """
        Вычисляет info_hash, необходимый для взаимодействия с трекером и пиринговой сетью.
        Info_hash — это SHA1 хеш от байтового представления секции 'info'.
        """
        info_encoded = bencodepy.encode(self.info)
        return hashlib.sha1(info_encoded).hexdigest()

