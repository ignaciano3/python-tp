from io import BufferedWriter
from lib.packages.AckPackage import AckPackage
from lib.utils.types import ADDR
from lib.utils.Socket import Socket
from lib.packages.Package import Package
from lib.utils.enums import PackageType


class StopAndWaitProtocol:
    def __init__(self, socket: Socket, server_addr: ADDR):
        self.socket = socket
        self.server_addr = server_addr
        self.sequence_number = 0
        self.tries = 0

    def send(self, package: Package) -> None:
        if self.tries >= 5:
            print("Número máximo de reintentos alcanzado. Abortando.")
            raise Exception("Número máximo de reintentos alcanzado. Abortando.")

        # Envía el paquete al servidor
        self.socket.sendto(package, self.server_addr)

        # Espera la confirmación (ACK)
        try:
            self.socket.settimeout(10)  # Timeout de 1 segundo
            ack, _ = self.socket.recv()
        except TimeoutError:
            print("Timeout alcanzado. Reintentando...")
            self.tries += 1
            self.send(package)
        except Exception as e:
            print(f"Error al recibir el ACK: {e}")
            self.tries += 1
            self.send(package)

        if not isinstance(ack, AckPackage):
            return

        # Si el número de secuencia no coincide, vuelve a enviar el paquete
        if  ack.sequence_number != self.sequence_number:
            self.tries += 1
            self.send(package)  # Retransmite si el número de secuencia no coincide
        else:
            self.tries = 0
            self.sequence_number ^= 1

    def receive(self, package: Package, file: BufferedWriter) -> bool:
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
