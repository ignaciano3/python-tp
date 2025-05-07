from io import BufferedReader, BufferedWriter
from lib.packages.AckPackage import AckPackage
from lib.utils.types import ADDR
from lib.utils.Socket import Socket
from lib.packages.Package import Package
from lib.utils.enums import PackageType
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
        finished = False

        while not finished:
            package, _ = self.socket.recv()
            finished = self._receive_aux(package, file)

    def _receive_aux(self, package: Package, file: BufferedWriter) -> bool:
        if package.type == PackageType.FIN or package.data is None:
            file.flush()
            return True

        if not package.valid:
            ack_package = AckPackage(self.sequence_number, False)
            self.socket.sendto(ack_package, self.server_addr)
            return False

        if package.type != PackageType.DATA:
            raise Exception("El paquete recibido no es un DataPackage.")

        # 4. Sino, es un DataPackage
        file.write(package.data)

        # 5. ACK por cada paquete
        ack_package = AckPackage(self.sequence_number)  # type: ignore
        self.socket.sendto(ack_package, self.server_addr)
        self.sequence_number ^= 1  # TODO: Implement a better sequence number handling

        return False
