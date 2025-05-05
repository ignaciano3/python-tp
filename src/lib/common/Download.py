from lib.utils.Socket import Socket
from lib.utils.types import ADDR


class Download:
    def __init__(self, file_path: str, socket: Socket, server_addr: ADDR) -> None:
        self.file_path = file_path
        self.socket = socket
        self.server_addr = server_addr

    def start(self) -> None:
        self.socket.sendto(b"download", self.server_addr)
        