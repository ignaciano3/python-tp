from io import BufferedReader, BufferedWriter
from lib.utils.types import ADDR
from lib.utils.Socket import Socket
from lib.protocols.selective_repeat import SelectiveRepeatProtocol
from lib.utils.logger import create_logger
import logging


class StopAndWaitProtocol:
    def __init__(
        self, socket: Socket, server_addr: ADDR, logging_level=logging.DEBUG
    ) -> None:
        self.socket = socket
        self.server_addr = server_addr
        self.sequence_number = 0
        self.tries = 0
        self.logger = create_logger(
            "selective_repeat", "[STOP AND WAIT]", logging_level
        )

    def send(self, file: BufferedReader) -> None:
        SelectiveRepeatProtocol(
            self.socket, self.server_addr, 1, True, self.logger
        ).send(file)

    def receive(self, file: BufferedWriter) -> None:
        SelectiveRepeatProtocol(
            self.socket, self.server_addr, 1, True, self.logger
        ).receive(file)
