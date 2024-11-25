import asyncio
import struct
import hashlib
import bitstring

from application.interfaces.ipeer_connection import IPeerConnection
from domain.message_types import MessageTypes


class PeerConnection(IPeerConnection):
    def __init__(self, peer, torrent, peer_id, file_manager, debug, max_requests):
        self._ip = peer.ip
        self._port = peer.port
        self._peer_id = peer_id
        self._torrent = torrent
        self._file_manager = file_manager
        self._debug = debug
        self._requestsLimit = max(1, max_requests)

        self._reader = None
        self._writer = None
        self._choked = True
        self._available_pieces = bitstring.BitArray(length=self._torrent.pieces_count)
        self._requested_pieces = set()
        self._downloaded_pieces = set()
        self._in_progress_pieces = {}

    async def connect(self):
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self._ip, self._port), timeout=5
            )
            await self._handshake()
            await self._listen()
            self._writer.close()
            await self._writer.wait_closed()
            if self._debug:
                print("Connection closed")
        except Exception as e:
            if self._debug:
                print(f"Не удалось подключиться к пиру {self._ip}:{self._port} - {e}")


    async def _handshake(self):
        pstr = b"BitTorrent protocol"
        pstrlen = chr(19).encode()
        reserved = b"\x00" * 8
        info_hash = bytes.fromhex(self._torrent.info_hash)
        peer_id = self._peer_id.encode("utf-8")
        handshake = b"".join([pstrlen, pstr, reserved, info_hash, peer_id])
        self._writer.write(handshake)
        await self._writer.drain()

        response = await self._reader.readexactly(len(handshake))
        if not response:
            if self._debug:
                print("Failed to receive handshake")
            return

        if self._debug:
            print(f"Handshake с {self._ip}:{self._port} успешен.")

    async def _listen(self):
        while len(self._downloaded_pieces) < self._torrent.pieces_count:
            try:
                length_prefix = await self._reader.readexactly(4)
                if not length_prefix:
                    if self._debug:
                        print(f"Соединение с {self._ip}:{self._port} закрыто.")
                    break

                (length,) = struct.unpack("!I", length_prefix)
                if length == 0:
                    if self._debug:
                        print(f"Keep alive {self._ip}:{self._port}")
                    break

                message = await self._reader.readexactly(length)
                await self._handle_message(message[0], message[1:])
            except asyncio.IncompleteReadError:
                if self._debug:
                    print(f"Соединение с {self._ip}:{self._port} прервано.")
                break
            except Exception as e:
                if self._debug:
                    print(f"Ошибка при получении данных от {self._ip}:{self._port} - {e}")
                break

    async def _handle_message(self, msg_id, payload):
        if msg_id == MessageTypes.CHOKE:
            self._choked = True
            if self._debug:
                print(f"Пир {self._ip}:{self._port} заблокировал вас.")

        elif msg_id == MessageTypes.UNCHOKE:
            self._choked = False
            if self._debug:
                print(f"Пир {self._ip}:{self._port} разблокировал вас.")
            await self._request_pieces()

        elif msg_id == MessageTypes.HAVE:
            index = struct.unpack("!I", payload)[0]
            self._available_pieces[index] = True
            if self._debug:
                print(f"Пир {self._ip}:{self._port} имеет кусок {index}.")
            await self._request_pieces()

        elif msg_id == MessageTypes.BITFIELD:
            self._available_pieces = bitstring.BitArray(
                bytes=payload, length=self._torrent.pieces_count
            )
            if self._debug:
                print(f"Пир {self._ip}:{self._port} прислал bitfield.")
            self._writer.write(b"\0\0\0\1\2")
            await self._writer.drain()

        elif msg_id == MessageTypes.PIECE:
            await self._handle_piece(payload)

    async def _request_pieces(self):
        if self._choked or len(self._requested_pieces) >= self._requestsLimit:
            return
        # Ограничиваем количество одновременных запросов
        for i in range(self._torrent.pieces_count):
            if (
                self._available_pieces[i]
                and i not in self._requested_pieces
                and i not in self._downloaded_pieces
            ):
                await self._request_piece(i)
                self._requested_pieces.add(i)
                if len(self._requested_pieces) >= self._requestsLimit:
                    break

    async def _request_piece(self, piece_index):
        piece_length = self._torrent.piece_length
        if piece_index == self._torrent.pieces_count - 1:
            piece_length = self._torrent.size % self._torrent.piece_length

        self._in_progress_pieces[piece_index] = {}
        block = 2**14
        for offset in range(0, piece_length, block):
            length = min(block, piece_length - offset)
            request = await self.generate_request(length, offset, piece_index)
            self._writer.write(request)
            await self._writer.drain()

    async def generate_request(self, length, offset, piece_index):
        return (
            (13).to_bytes(4, byteorder="big")
            + bytes([6])
            + piece_index.to_bytes(4, byteorder="big")
            + offset.to_bytes(4, byteorder="big")
            + length.to_bytes(4, byteorder="big")
        )

    async def _handle_piece(self, payload):
        index = struct.unpack("!I", payload[:4])[0]
        begin = struct.unpack("!I", payload[4:8])[0]
        block = payload[8:]
        if self._debug:
            print(f"Received piece {index}, offset {begin}, length {len(block)}")

        if index not in self._in_progress_pieces:
            self._in_progress_pieces[index] = {}
        self._in_progress_pieces[index][begin] = block

        if (
            sum(len(block) for block in self._in_progress_pieces[index].values())
            >= self._torrent.piece_length
        ):
            complete_piece = b"".join(
                block for _, block in sorted(self._in_progress_pieces[index].items())
            )
            if self._validate_piece(index, complete_piece):
                if self._debug:
                    print(f"Piece {index} downloaded and verified")
                await self._file_manager.add_piece(index, complete_piece)
                self._downloaded_pieces.add(index)
            else:
                if self._debug:
                    print(f"Piece {index} failed verification")
            del self._in_progress_pieces[index]
            self._requested_pieces.remove(index)
            await self._request_pieces()

    def _validate_piece(self, index, data):
        piece_hash = hashlib.sha1(data).digest()
        return piece_hash == self._torrent.get_piece_hash(index)