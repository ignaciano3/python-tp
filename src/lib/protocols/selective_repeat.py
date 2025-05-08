from dataclasses import dataclass
from io import BufferedReader, BufferedWriter
import logging
from lib.utils.Socket import Socket
from lib.utils.types import ADDR
from lib.utils.constants import BUFSIZE
from lib.packages.DataPackage import DataPackage
from lib.packages.AckPackage import AckPackage
from lib.utils.logger import create_logger
from lib.utils.enums import PackageType

from lib.packages.NackPackage import NackPackage
from lib.utils.package_error import ChecksumErr, PackageErr


@dataclass
class WindowItem:
    sequence_number: int
    data: bytes
    acked: bool = False
    retries_left: int = 5  # una menos que max_retries
    # timer_thread: Optional[Thread] = None  ### NUEVO TIMER
    # stop_event: Optional[Event] = None  ### NUEVO TIMER

    def __lt__(self, other):  # para que funcione con heapq
        return self.sequence_number < other.sequence_number

    def __repr__(self):
        return f"WindowItem(seq_num={self.sequence_number}, acked={self.acked}, retries_left={self.retries_left})"

    def __str__(self):
        return f"WindowItem(seq_num={self.sequence_number}, acked={self.acked}, retries_left={self.retries_left})"


class Window:
    def __init__(self, size: int = 5):
        self.size = size  # Número de secuencia del primer paquete en la ventana
        self.items: list[WindowItem] = []  # ACKs recibidos en la ventana

    def length(self) -> int:
        return len(self.items)

    # def add_item(self, item: WindowItem):
    #     heapq.heappush(self.items, item)

    def add_item(self, item: WindowItem):
        for i, existing in enumerate(self.items):
            if item.sequence_number < existing.sequence_number:
                self.items.insert(i, item)
                return
        self.items.append(item)

    def remove_first_sent(self):
        if not self.items:
            raise Exception("No hay paquetes en la ventana para eliminar.")
        self.items.pop(0)

    def see_top(self) -> WindowItem:
        if not self.items:
            raise Exception("No hay paquetes en la ventana para ver.")
        return self.items[0]

    def see_top_seq_num(self) -> int:
        if not self.items:
            raise Exception("No hay paquetes en la ventana para ver.")
        return self.items[0].sequence_number

    def see_last_seq_num(self) -> int:
        if not self.items:
            raise Exception("No hay paquetes en la ventana para ver.")
        return self.items[-1].sequence_number


class SelectiveRepeatProtocol:
    def __init__(
        self,
        socket: Socket,
        server_addr: ADDR,
        window_size: int = 5,
        from_stop_and_wait: bool = False,
        logger: logging.Logger | None = None,
        logging_level: int = logging.DEBUG,
    ) -> None:
        self.from_stop_and_wait = from_stop_and_wait
        self.socket = socket
        self.server_addr = server_addr
        self.window = Window(window_size)

        if logger is None:
            logger = create_logger(
                "selective_repeat", "[SELECTIVE REPEAT]", logging_level
            )
        self.logger = logger

        self.last_sequence_number = 0
        self.first_sequence_number = 0
        self.tries = 0
        self.max_tries = 5

        self.sequence_number = 0

    # ---------------------------- SEND ---------------------------- #

    def get_item(self, seq_number: int) -> WindowItem:
        for item in self.window.items:
            if item.sequence_number == seq_number:
                return item
        raise ValueError(
            f"El paquete con seq_number {seq_number} no se encuentra en la ventana."
        )

    def send(self, file: BufferedReader) -> None:
        finished = False
        while not finished:
            while self.window.length() < self.window.size:
                data = file.read(BUFSIZE - 16)

                if not data:
                    break

                data_package = DataPackage(data, self.last_sequence_number)
                self._send_package(data_package)
                self.agregar_paquete_al_window(data_package)

            if self.window.length() == 0:
                finished = True
                break
            self._receive_ack()

    def _send_package(self, package: DataPackage) -> None:
        self.socket.sendto(package, self.server_addr)
        self.logger.debug(
            f"Enviando paquete: {package.sequence_number}  - ({self.first_sequence_number} {self.last_sequence_number})"
        )

    def obtener_proximo_seq_number(self, seq_number: int) -> int:
        if self.from_stop_and_wait:
            return seq_number ^ 1
        else:
            return seq_number + 1

    def agregar_paquete_al_window(self, package: DataPackage) -> None:
        item = WindowItem(package.sequence_number, package.data, acked=False)
        self.window.add_item(item)
        self.last_sequence_number = self.obtener_proximo_seq_number(
            self.last_sequence_number
        )

        # self._start_timer_for_item(item)  ### NUEVO TIMER

    def _receive_ack(self) -> None:
        if self.tries >= self.max_tries:
            self.logger.error("Número máximo de reintentos alcanzado. Abortando.")
            raise Exception("Número máximo de reintentos alcanzado. Abortando.")
        # Espera la confirmación (ACK)
        self.socket.settimeout(5000)  # Timeout de 1 segundo
        try:
            ack, _ = self.socket.recv()
            if isinstance(ack, NackPackage):
                self.nack_sequence_number = ack.sequence_number
                raise TimeoutError

        except TimeoutError:
            self.logger.debug("Timeout esperando ACK")

            item = self.get_item(self.nack_sequence_number)
            data_package = DataPackage(item.data, self.nack_sequence_number)
            self.logger.warning("RECIBIENDO ACK")
            self.logger.warning(data_package)
            self._send_package(data_package)
            self.tries += 1
            return
        except Exception as e:
            self.logger.error(f"Error inesperado al recibir el ACK: {e}")
            self.tries += 1
            raise

        if not isinstance(ack, AckPackage):
            return
        self.tries = 0

        self.logger.debug(
            f"Recibiendo ACK: {ack.sequence_number}  - ({self.first_sequence_number} {self.last_sequence_number})"
        )

        if not self.from_stop_and_wait:
            if (
                ack.sequence_number > self.last_sequence_number
                or ack.sequence_number < self.first_sequence_number
            ):
                self.logger.error("FUERA DE VENTANA CULOROTO")
                return

        item = self.get_item(ack.sequence_number)
        if not item.acked:
            item.acked = True
        else:
            self.logger.error("FUERA DE VENTANA CULOROTO 2")

        self._actualizar_window()

    def _actualizar_window(self) -> None:
        if self.window.length() == 0:
            self.logger.warning("No hay paquetes en la ventana para actualizar.")
            return

        first_package = self.get_item(self.first_sequence_number)

        if first_package.acked:
            # caso en que llego en desorden algun paquete
            self.window.items.remove(first_package)
            self.logger.warning(
                f"Remuevo el paquete rezagado con seq_number {first_package.sequence_number} con ack true en la ventana"
            )
            self.first_sequence_number = self.obtener_proximo_seq_number(
                self.first_sequence_number
            )
            self._actualizar_window()

    # ---------------------------- RECEIVE ---------------------------- #

    def receive(self, file: BufferedWriter) -> None:
        finished = False

        while not finished:
            finished, seq_number = self._receive_data(file)
            self._send_ack(seq_number)

    def _receive_data(self, file: BufferedWriter, retries=0) -> tuple[bool, int]:
        # if retries >= self.max_tries:
        #     self.logger.error("Número máximo de reintentos alcanzado. Abortando.")
        #     raise Exception("Número máximo de reintentos alcanzado. Abortando.")

        package = None
        try:
            package, _ = self.socket.recv()
        except (PackageErr, ChecksumErr, TimeoutError):
            self.logger.error("Timeout esperando paquete")
            self.tries += 1
            self._send_nack(self.first_sequence_number)
            return self._receive_data(file, retries + 1)
        except Exception as e:
            self.logger.error(f"Error inesperado al recibir el paquete: {e}")
            self.tries += 1
            raise

        if package is None:
            self.logger.error("Paquete recibido es None")
            return (False, 0)

        if package.type == PackageType.FIN or package.data is None:
            self.logger.debug("Paquete FIN recibido")
            file.flush()
            return (True, package.sequence_number)

        if not package.valid:
            ack_package = NackPackage(package.sequence_number)
            self.logger.error(
                f"Checksum inválido, mando Nack con seq_num: {package.sequence_number}"
            )
            self.socket.sendto(ack_package, self.server_addr)

            return self._receive_data(file, retries + 1)

        if package.type != PackageType.DATA:
            raise Exception("El paquete recibido no es un DataPackage.")

        self.logger.debug(
            "Escribí paquete de datos con seq_num: " + str(package.sequence_number)
        )
        file.write(package.data)
        return (False, package.sequence_number)

    def _send_ack(self, seq_number: int) -> None:
        self.logger.debug(f"Enviando ACK: {seq_number}")
        ack_package = AckPackage(seq_number)
        self.socket.sendto(ack_package, self.server_addr)

    def _send_nack(self, seq_number: int) -> None:
        nack_package = NackPackage(seq_number)
        self.socket.sendto(nack_package, self.server_addr)

    # ---------------------------- SERVER ---------------------------- #

    def send_chunk(self, chunk: bytes) -> None:
        data_package = DataPackage(chunk, self.last_sequence_number)

        self._send_package(data_package)
        self.agregar_paquete_al_window(data_package)

    def ack_received(self, seq_number: int) -> bool:
        self.logger.warning("Llego ACK de seq_num: " + str(seq_number))
        try:
            item = self.get_item(seq_number)
            item.acked = True
        except ValueError:
            self.logger.warning(
                f"ACK recibido por paquete fuera de la ventana: {seq_number}"
            )
            return False

        # Avanzar la ventana si el primero fue ACKed
        while self.window.items and self.window.items[0].acked:
            print(f"Estoy actualizando first_se de: {self.first_sequence_number}")
            self.window.remove_first_sent()
            self.first_sequence_number += 1

        return True

    def contains_seq_num(self, seq_num: int) -> bool:
        for item in self.window.items:
            if item.sequence_number == seq_num:
                return True
        return False

    def resend_package(self, seq_num: int) -> bool:
        # self.logger.warning(f"Elementos en la window: {self.window.items}")
        for item in self.window.items:
            if item.sequence_number == seq_num:
                if item.retries_left <= 0:
                    self.logger.error(
                        f"Paquete con seq_num {seq_num} ha alcanzado el número máximo de reintentos."
                    )
                    return False
                item.retries_left -= 1
                data_package = DataPackage(item.data, seq_num)
                self._send_package(data_package)
                self.logger.debug(
                    f"Reenviando paquete: {data_package.sequence_number}  - ({self.first_sequence_number} {self.last_sequence_number})"
                )
                break
        else:
            self.logger.warning(
                f"Paquete con seq_num {seq_num} no encontrado en la ventana"
            )
            return False
        return True
