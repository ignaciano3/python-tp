from lib.packages.DataPackage import DataPackage
from lib.packages.AckPackage import AckPackage
from lib.utils.Socket import Socket
from lib.utils.types import ADDR
from lib.utils.constants import BUFSIZE


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

    def send_next_packet(self, package: bytes, sequence_number: int) -> None:
        data_package = DataPackage(package, sequence_number)
        self.socket.sendto(data_package, self.server_addr)
        self.pending_ack[sequence_number] = False  # Aún no se ha recibido ACK

    def wait_for_ack(self):
        # Recibe ACKs y maneja la ventana deslizante
        ack, _ = self.socket.recv()
        ack_package = AckPackage.from_bytes(ack)
        ack_sequence = ack_package.sequence_number

        if ack_sequence in self.pending_ack:
            self.pending_ack[ack_sequence] = True  # Marcar como ACK recibido

        # Si el ACK es para el primer paquete de la ventana, deslizamos la ventana
        while self.pending_ack.get(self.window_start, False):
            self.window_start += 1
            self.window_end += 1
            if self.window_end < self.sequence_number:
                self.send(
                    b""
                )  ########################################chequear que este bien

    def send(self, data: bytes) -> None:
        if self.window_end < self.window_start + self.window_size:
            # Si hay espacio en la ventana, envía el siguiente paquete
            self.send_next_packet(data, self.sequence_number)
            self.sequence_number += 1

    def receive(self) -> bytes:
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

    def start_sending(self, file_path: str):
        with open(file_path, "rb") as file:
            while True:
                data = file.read(BUFSIZE - 50)
                if not data:
                    break  # Fin del archivo
                # Enviar el paquete si hay espacio en la ventana
                self.send(data)
