from dataclasses import dataclass
from io import BufferedReader, BufferedWriter
from lib.utils.Socket import Socket
from lib.utils.types import ADDR
from lib.utils.constants import BUFSIZE
from lib.packages.DataPackage import DataPackage
from lib.packages.AckPackage import AckPackage

@dataclass
class WindowItem:
    sequence_number: int
    data: bytes
    acked: bool = False


class Window:
    def __init__(self, start: int, end: int):
        self.start = start  # Número de secuencia del primer paquete en la ventana
        self.end = end  # Número de secuencia del último paquete en la ventana
        self.acks: list[WindowItem] = []  # ACKs recibidos en la ventana

class SelectiveRepeatProtocol:
    def __init__(self, socket: Socket, server_addr: ADDR, window_size: int = 5):
        self.socket = socket
        self.server_addr = server_addr
        self.window = Window(0, window_size - 1)
        self.sequence_number = 0

    def send(self, file: BufferedReader) -> None:
        while True:
            data = file.read(BUFSIZE - 8)
            if not data:
                break  # Fin del archivo
            
            while self.window.end - self.window.start + 1 >= 5:
                data_package = DataPackage(data, self.sequence_number)
                self._send_aux(data_package)

    def _send_aux(self, package: DataPackage) -> None:
        # Envía el paquete al servidor
        self.socket.sendto(package, self.server_addr)

        # Espera la confirmación (ACK)
        ack = None
        try:
            self.socket.settimeout(10)  # Timeout de 1 segundo
            ack, _ = self.socket.recv()
        except TimeoutError:
            print("Timeout alcanzado. Reintentando...")
            self._send_aux(package)
        except Exception as e:
            print(f"Error al recibir el ACK: {e}")
            self._send_aux(package)

        if not isinstance(ack, AckPackage):
            return

        # Si el número de secuencia no coincide, vuelve a enviar el paquete
        if ack.sequence_number != self.sequence_number:
            self._send_aux(package)
        else:
            # Agrega el número de secuencia al conjunto de recibidos
            self.window.acks.append(WindowItem(ack.sequence_number, ack.data, True))

            # Si el número de secuencia coincide, actualiza la ventana
            if ack.sequence_number == self.window.start:
                self.window.start += 1
                self.window.acks.pop(ack.sequence_number)

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
