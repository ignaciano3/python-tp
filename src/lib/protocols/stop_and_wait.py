from lib.packages.AckPackage import AckPackage
from lib.utils.types import ADDR
from lib.utils.Socket import Socket
from lib.packages.DataPackage import DataPackage


class StopAndWaitProtocol:
    def __init__(self, socket: Socket, server_addr: ADDR):
        self.socket = socket
        self.server_addr = server_addr
        self.sequence_number = 0

    def send(self, data: bytes) -> None:
        # Crea un paquete de datos con el número de secuencia
        data_package = DataPackage(data, self.sequence_number)

        # Envía el paquete al servidor
        self.socket.sendto(data_package, self.server_addr)

        # Espera la confirmación (ACK)
        ack, _ = self.socket.recv()

        # Procesa el ACK recibido
        ack_package = AckPackage.from_bytes(ack)

        # Si el número de secuencia no coincide, vuelve a enviar el paquete
        if ack_package.sequence_number != self.sequence_number:
            self.send(data)  # Retransmite si el número de secuencia no coincide
        else:
            self.sequence_number ^= 1
