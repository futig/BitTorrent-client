# domain/torrent_file.py
import bencodepy
import os
from typing import List, Dict, Any
import hashlib


class TorrentFile:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.meta_info = self._decode_torrent_file()
        self.announce = self._get_announce()
        self.info = self._get_info()
        self.multi_file = self._is_multi_file()
        self.piece_length = self._get_piece_length()
        self.pieces = self._get_pieces()
        self.files = self._get_files()
        self.name = self._get_name()
        self.total_length = self._get_total_length()

    def _decode_torrent_file(self) -> Dict[str, Any]:
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Торрент-файл не найден: {self.file_path}")
        
        with open(self.file_path, 'rb') as f:
            try:
                decoded = bencodepy.decode(f.read())
                return decoded
            except bencodepy.BencodeDecodeError as e:
                raise ValueError(f"Ошибка декодирования торрент-файла: {e}")

    def _get_announce(self) -> str:
        return self.meta_info.get(b'announce', b'').decode('utf-8')

    def _get_info(self) -> Dict[str, Any]:
        info = self.meta_info.get(b'info')
        if not info:
            raise ValueError("Отсутствует секция 'info' в торрент-файле.")
        return info

    def _get_piece_length(self) -> int:
        piece_length = self.info.get(b'piece length')
        if not piece_length:
            raise ValueError("Отсутствует поле 'piece length' в секции 'info'.")
        return piece_length

    def _get_pieces(self) -> List[bytes]:
        pieces = self.info.get(b'pieces')
        if not pieces:
            raise ValueError("Отсутствует поле 'pieces' в секции 'info'.")
        # Каждый хеш куска имеет длину 20 байт
        if len(pieces) % 20 != 0:
            raise ValueError("Некорректная длина поля 'pieces'.")
        return [pieces[i:i + 20] for i in range(0, len(pieces), 20)]

    def _is_multi_file(self) -> bool:
        return b'files' in self.info

    def _get_files(self) -> List[Dict[str, Any]]:
        if self.multi_file:
            files = self.info.get(b'files', [])
            file_list = []
            for file in files:
                length = file.get(b'length')
                path = b'/'.join(file.get(b'path', [])).decode('utf-8')
                file_list.append({'length': length, 'path': path})
            return file_list
        else:
            length = self.info.get(b'length')
            name = self.info.get(b'name', b'').decode('utf-8')
            return [{'length': length, 'path': name}]

    def _get_name(self) -> str:
        name = self.info.get(b'name')
        if not name:
            raise ValueError("Отсутствует поле 'name' в секции 'info'.")
        return name.decode('utf-8')

    def _get_total_length(self) -> int:
        if self.multi_file:
            return sum(file['length'] for file in self.files)
        else:
            return self.files[0]['length']

    def get_info_hash(self) -> str:
        """
        Вычисляет info_hash, необходимый для взаимодействия с трекером и пиринговой сетью.
        Info_hash — это SHA1 хеш от байтового представления секции 'info'.
        """
        info_encoded = bencodepy.encode(self.info)
        return hashlib.sha1(info_encoded).hexdigest()

    def __str__(self):
        return (
            f"TorrentFile(\n"
            f"  announce='{self.announce}',\n"
            f"  name='{self.name}',\n"
            f"  piece length={self.piece_length},\n"
            f"  pieces={len(self.pieces)},\n"
            f"  files={self.files},\n"
            f"  total length={self.total_length},\n"
            f"  multi file={self.multi_file}\n"
            f")"
        )
