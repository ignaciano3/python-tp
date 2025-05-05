from lib.utils.logger import create_logger
from lib.utils.Socket import Socket
from lib.server.ServerRequestHandler import ServerRequestHandler
from lib.utils.constants import SERVER_STORAGE


class Server:
    def __init__(
        self, host: str, port: int = 8080, server_storage=SERVER_STORAGE
    ) -> None:
        self.host = host
        self.port = port
        self.running = False
        self.socket = Socket()
        self.logger = create_logger("server", "[SERVER]")
        self.server_storage = server_storage

    def start(self) -> None:
        self.running = True
        self.socket.bind(self.host, self.port)
        self.logger.info(f"Server started on {self.host}:{self.port}")

        request_handler = ServerRequestHandler(self.server_storage, self.socket)

        while True:
            request = self.socket.recv()
            request_handler.handle_request(request)

    def stop(self) -> None:
        self.socket.close()
        self.running = False
        self.logger.info("Server stopped")
