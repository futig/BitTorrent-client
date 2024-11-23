import asyncio
import struct
from typing import Optional
from application.downloader import Downloader

class Peer:
    def __init__(self, ip: str, port: int, downloader: Downloader):
        self.ip = ip
        self.port = port
        self.downloader = downloader
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.interested = False
        self.choked = True
        self.peer_id = None
        self.bitfield = None

    async def connect(self):
        """Устанавливает соединение с пиром и инициирует протокол."""
        try:
            self.reader, self.writer = await asyncio.open_connection(self.ip, self.port)
            await self.handshake()
            await self.listen()
        except Exception as e:
            print(f"Не удалось подключиться к пиру {self.ip}:{self.port} - {e}")

    async def handshake(self):
        """Отправляет handshake сообщение и получает ответ."""
        pstr = b"BitTorrent protocol"
        pstrlen = len(pstr)
        reserved = b'\x00' * 8
        info_hash = bytes.fromhex(self.downloader.info_hash)
        peer_id = self.downloader.peer_id.encode('utf-8')
        handshake = struct.pack(f"!B{pstrlen}s8s20s20s", pstrlen, pstr, reserved, info_hash, peer_id)
        self.writer.write(handshake)
        await self.writer.drain()

        # Читаем handshake от пира
        response = await self.reader.readexactly(68)
        # Можно добавить проверку соответствия info_hash и pstr
        # Для упрощения пропускаем это
        print(f"Handshake с {self.ip}:{self.port} успешен.")

    async def listen(self):
        """Прослушивает сообщения от пира."""
        while True:
            try:
                length_prefix = await self.reader.readexactly(4)
                (length,) = struct.unpack("!I", length_prefix)
                if length == 0:
                    print(f"Соединение с {self.ip}:{self.port} закрыто пиров.")
                    break
                message_id = await self.reader.readexactly(1)
                payload = await self.reader.readexactly(length - 1)
                await self.handle_message(message_id, payload)
            except asyncio.IncompleteReadError:
                print(f"Соединение с {self.ip}:{self.port} прервано.")
                break
            except Exception as e:
                print(f"Ошибка при получении данных от {self.ip}:{self.port} - {e}")
                break

    async def handle_message(self, message_id: bytes, payload: bytes):
        """Обрабатывает полученные сообщения от пира."""
        msg_id = message_id[0]
        if msg_id == 0:
            # choke
            self.choked = True
            print(f"Пир {self.ip}:{self.port} заблокировал вас.")
        elif msg_id == 1:
            # unchoke
            self.choked = False
            print(f"Пир {self.ip}:{self.port} разблокировал вас.")
            asyncio.create_task(self.request_pieces())
        elif msg_id == 4:
            # have
            index = struct.unpack("!I", payload)[0]
            print(f"Пир {self.ip}:{self.port} имеет кусок {index}.")
        elif msg_id == 5:
            # bitfield
            self.bitfield = payload
            print(f"Пир {self.ip}:{self.port} прислал bitfield.")
            asyncio.create_task(self.request_pieces())
        elif msg_id == 7:
            # piece
            index = struct.unpack("!I", payload[:4])[0]
            begin = struct.unpack("!I", payload[4:8])[0]
            block = payload[8:]
            # Предполагаем, что begin == 0 и блок соответствует куску
            if begin == 0:
                if self.downloader.validate_piece(index, block):
                    await self.downloader.add_piece(index, block)
                else:
                    print(f"Кусок {index} от {self.ip}:{self.port} не прошёл проверку.")
        # Можно добавить обработку других типов сообщений

    async def request_pieces(self):
        """Запрашивает куски, которые пир имеет и которые ещё не скачаны."""
        for index in range(self.downloader.total_pieces):
            if index in self.downloader.downloaded_pieces:
                continue
            byte_index = index // 8
            bit_index = index % 8
            if self.bitfield and not (self.bitfield[byte_index] & (1 << (7 - bit_index))):
                continue
            if not self.downloader.config.get('allow_multiple_requests', False):
                # Ограничиваем количество одновременных запросов
                self.downloader.config['allow_multiple_requests'] = True
            if not self.downloader.config.get('allow_multiple_requests', False):
                continue
            await self.send_request(index)
            break  # Запрашиваем по одному куску за раз

    async def send_request(self, index: int):
        """Отправляет запрос на получение куска."""
        if self.choked:
            return
        begin = 0
        length = self.downloader.piece_length
        request = struct.pack("!IbIII", 13, 6, index, begin, length)
        # Протокол BitTorrent не включает message_id=6, который является 'request'
        # Правильный request имеет message_id=6
        request = struct.pack("!I", 13) + struct.pack("!BIII", 6, index, begin, length)
        self.writer.write(request)
        await self.writer.drain()
        print(f"Запрошен кусок {index} у {self.ip}:{self.port}")