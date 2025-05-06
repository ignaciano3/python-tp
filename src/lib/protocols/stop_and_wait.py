from lib.packages.AckPackage import AckPackage
from lib.utils.types import ADDR
from lib.utils.Socket import Socket
from lib.packages.Package import Package


class StopAndWaitProtocol:
    def __init__(self, socket: Socket, server_addr: ADDR):
        self.socket = socket
        self.server_addr = server_addr
        self.sequence_number = 0
        self.tries = 0

    def send(self, package: Package) -> None:
        # Envía el paquete al servidor
        self.socket.sendto(package, self.server_addr)

        # Espera la confirmación (ACK)
        ack, _ = self.socket.recv()

        # Procesa el ACK recibido
        ack_package = AckPackage.from_bytes(ack)

        if self.tries >= 5:
            print("Número máximo de reintentos alcanzado. Abortando.")
            raise Exception("Número máximo de reintentos alcanzado. Abortando.")
        # Si el número de secuencia no coincide, vuelve a enviar el paquete
        if ack_package.sequence_number != self.sequence_number:
            self.tries += 1
            self.send(package)  # Retransmite si el número de secuencia no coincide
        else:
            self.tries = 0
            self.sequence_number ^= 1

    def receive(self) -> Package:
        # Recibe el paquete del servidor
        package, _ = self.socket.recv()

        # Envía un ACK al servidor
        ack_package = AckPackage(self.sequence_number)
        self.socket.sendto(ack_package, self.server_addr)

        # Procesa el paquete recibido
        return Package.from_bytes(package)
