from io import BufferedReader, BufferedWriter
from lib.packages.AckPackage import AckPackage
from lib.utils.types import ADDR
from lib.utils.Socket import Socket
from lib.packages.Package import Package
from lib.utils.enums import PackageType
from lib.packages.DataPackage import DataPackage
from lib.utils.constants import BUFSIZE


class StopAndWaitProtocol:
    def __init__(self, socket: Socket, server_addr: ADDR):
        self.socket = socket
        self.server_addr = server_addr
        self.sequence_number = 0
        self.tries = 0

    def send(self, file: BufferedReader) -> None:
        while True:
            data = file.read(BUFSIZE - 8)
            if not data:
                break  # Fin del archivo

            data_package = DataPackage(data, self.sequence_number)
            self._send_aux(data_package)

    def _send_aux(self, package: Package) -> None:
        if self.tries >= 5:
            print("Número máximo de reintentos alcanzado. Abortando.")
            raise Exception("Número máximo de reintentos alcanzado. Abortando.")

        # Envía el paquete al servidor
        self.socket.sendto(package, self.server_addr)

        # Espera la confirmación (ACK)
        ack = None
        try:
            self.socket.settimeout(10)  # Timeout de 1 segundo
            ack, _ = self.socket.recv()
        except TimeoutError:
            print("Timeout alcanzado. Reintentando...")
            self.tries += 1
            self._send_aux(package)
        except Exception as e:
            print(f"Error al recibir el ACK: {e}")
            self.tries += 1
            self._send_aux(package)

        if not isinstance(ack, AckPackage):
            return

        # Si el número de secuencia no coincide, vuelve a enviar el paquete
        if ack.sequence_number != self.sequence_number:
            self.tries += 1
            self._send_aux(package)  # Retransmite si el número de secuencia no coincide
        else:
            self.tries = 0
            self.sequence_number ^= 1

    def receive(self, file: BufferedWriter) -> None:
        finished = False

        while not finished:
            package, _ = self.socket.recv()

            finished = self._receive_aux(package, file)

    def _receive_aux(self, package: Package, file: BufferedWriter) -> bool:           
        # 3. Recibe el paquete del socket
        if package.type == PackageType.FIN or package.data is None:
            file.flush()
            return True

        if package.type != PackageType.DATA:
            raise Exception("El paquete recibido no es un DataPackage.")

        # 4. Sino, es un DataPackage
        file.write(package.data)

        # 5. ACK por cada paquete
        ack_package = AckPackage(self.sequence_number)  # type: ignore
        self.socket.sendto(ack_package, self.server_addr)
        self.sequence_number ^= 1  # TODO: Implement a better sequence number handling

        return False
