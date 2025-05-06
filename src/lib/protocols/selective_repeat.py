from io import BufferedReader, BufferedWriter
from lib.utils.Socket import Socket
from lib.utils.types import ADDR


class SelectiveRepeatProtocol:
    def __init__(self, socket: Socket, server_addr: ADDR, window_size: int = 5):
        self.socket = socket
        self.server_addr = server_addr
        self.window_size = window_size
        self.received_packets = set()  # Para los ACKs recibidos
        self.pending_ack = {}  # Paquetes que estamos esperando ACK
        self.window_start = 0  # El inicio de la ventana de envío
        self.window_end = 0  # El final de la ventana de envío
        self.sequence_number = 0  # El número de secuencia para los paquetes

    def send(self, file: BufferedReader) -> None:
        pass

    def receive(self, file: BufferedWriter):
        pass

    """
    def receivee(self) -> bytes:
        data, _ = self.socket.recv()

        # Extrae el número de secuencia del paquete
        ack_package = AckPackage.from_bytes(data)
        sequence_number = ack_package.sequence_number

        # Agrega el número de secuencia al conjunto de recibidos
        self.received_packets.add(sequence_number)

        # Enviar un ACK con el número de secuencia
        ack = AckPackage(sequence_number)
        self.socket.sendto(ack, self.server_addr)

        return data
        """
