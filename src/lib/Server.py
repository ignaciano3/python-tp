import logging
from lib.utils.logger import create_logger
from lib.utils.Socket import Socket
from lib.server.ServerRequestHandler import ServerRequestHandler
from lib.utils.constants import SERVER_STORAGE
from lib.utils.enums import Protocol


class Server:
    def __init__(
        self,
        host: str,
        port: int = 8080,
        protocol: Protocol = Protocol.STOP_WAIT,
        server_storage=SERVER_STORAGE,
        logging_level=logging.DEBUG,
    ) -> None:
        self.host = host
        self.port = port
        self.running = False
        self.socket = Socket(logging_level)
        self.logging_level = logging_level
        self.logger = create_logger("server", "[SERVER]", logging_level)
        self.server_storage = server_storage
        self.protocol = protocol

    def bind_socket(self) -> None:
        try:
            self.socket.bind(self.host, self.port)
        except OSError as e:
            self.logger.error(f"Error binding socket: {e}")
            raise

    def start(self) -> None:
        self.running = True
        self.bind_socket()
        self.logger.info(f"Server started on {self.host}:{self.port}")
        self.logger.info(f"Protocol: {self.protocol.name}")
        self.logger.info(f"Server storage: {self.server_storage}")

        request_handler = ServerRequestHandler(
            self.server_storage, self.socket, self.logging_level
        )

        while self.running:
            try:
                request = self.socket.recv()
                request_handler.handle_request(request)
            except KeyboardInterrupt:
                self.logger.info(
                    "Interrupción del teclado recibida. Cerrando el servidor."
                )
                self.stop()
                break
            except OSError as e:
                if not self.running:
                    break
                self.logger.error(f"Error receiving data: {e}")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")

    def stop(self) -> None:
        self.socket.close()
        self.running = False
        self.logger.info("Server stopped")
