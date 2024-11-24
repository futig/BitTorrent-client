from abc import ABC, abstractmethod


class IPeerConnection(ABC):
    @abstractmethod
    def validate_piece(self, index: int, data: bytes) -> bool:
        pass
    
    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def handshake(self):
        pass

    @abstractmethod
    async def listen(self):
        pass

    @abstractmethod
    async def handle_message(self, message_id: bytes, payload: bytes):
        pass

    @abstractmethod
    async def request_pieces(self):
        pass

    @abstractmethod
    async def send_request(self, index: int):
        pass