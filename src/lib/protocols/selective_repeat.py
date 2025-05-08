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
from threading import Thread, Event
from typing import Optional
import heapq

from lib.packages.NackPackage import NackPackage
from lib.utils.package_error import ChecksumErr, PackageErr


@dataclass
class WindowItem:
    sequence_number: int
    data: bytes
    acked: bool = False
    retries_left: int = 4  # una menos que max_retries
    timer_thread: Optional[Thread] = None  ### NUEVO TIMER
    stop_event: Optional[Event] = None  ### NUEVO TIMER

    def __lt__(self, other):  # para que funcione con heapq
        return self.sequence_number < other.sequence_number


class Window:
    def __init__(self, size: int = 5):
        self.size = size  # Número de secuencia del primer paquete en la ventana
        self.items: list[WindowItem] = []  # ACKs recibidos en la ventana

    def length(self) -> int:
        return len(self.items)

    def add_item(self, item: WindowItem):
        heapq.heappush(self.items, item)

    def remove_first_sent(self):
        if self.items:
            return heapq.heappop(self.items)  # saca el de menor sequence_number
        else:
            raise Exception("No hay paquetes en la ventana para eliminar.")


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
        item = WindowItem(package.sequence_number, package.data)
        self.window.add_item(item)
        self.last_sequence_number = self.obtener_proximo_seq_number(
            self.last_sequence_number
        )

        self._start_timer_for_item(item)  ### NUEVO TIMER

    def _receive_ack(self) -> None:
        if self.tries >= self.max_tries:
            self.logger.error("Número máximo de reintentos alcanzado. Abortando.")
            raise Exception("Número máximo de reintentos alcanzado. Abortando.")
        # Espera la confirmación (ACK)
        self.socket.settimeout(10)  # Timeout de 1 segundo
        try:
            ack, _ = self.socket.recv()
            if isinstance(ack, NackPackage):
                raise TimeoutError

        except TimeoutError:
            self.logger.debug("Timeout esperando ACK")

            # Es probable que el paquete se haya perdido, por lo tanto lo reenviamos
            data_package = DataPackage(
                self.window.items[0].data, self.first_sequence_number
            )
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

        self.logger.debug(
            f"Recibiendo ACK: {ack.sequence_number}  - ({self.first_sequence_number} {self.last_sequence_number})"
        )

        item = self.get_item(ack.sequence_number)
        if item.stop_event:  ### NUEVO TIMER
            item.stop_event.set()

        if ack.sequence_number != self.first_sequence_number:
            self.logger.debug(
                f"ACK no coincide: {ack.sequence_number} != {self.first_sequence_number}"
            )
        else:
            first_package = self.window.items[0]
            if first_package.sequence_number < ack.sequence_number:
                self.logger.warning(
                    f"El servidor mando un paquete con seq_number {first_package.sequence_number} que no esta en la ventana"
                )
                # raise ValueError("El primer paquete no coincide con el ACK recibido")
                return

            self.window.items.remove(first_package)
            self.first_sequence_number = self.obtener_proximo_seq_number(
                self.first_sequence_number
            )

            if not self.from_stop_and_wait and self.window.length() > 0:
                self._actualizar_window()

    def _actualizar_window(self) -> None:
        if self.window.length() == 0:
            self.logger.warning("No hay paquetes en la ventana para actualizar.")
            return

        first_package = self.window.items[0]

        if first_package.acked:
            # caso en que llego en desorden algun paquete
            self.window.items.remove(first_package)
            self.logger.warning(
                f"Remuevo el paquete rezagado con seq_number {first_package.sequence_number} con ack true en la ventana"
            )
            self.first_sequence_number += 1
            self._actualizar_window()

    # ---------------------------- RECEIVE ---------------------------- #

    def receive(self, file: BufferedWriter) -> None:
        finished = False

        while not finished:
            finished, seq_number = self._receive_data(file)
            self._send_ack(seq_number)

    def _receive_data(self, file: BufferedWriter, retries=0) -> tuple[bool, int]:
        if retries >= self.max_tries:
            self.logger.error("Número máximo de reintentos alcanzado. Abortando.")
            raise Exception("Número máximo de reintentos alcanzado. Abortando.")

        package = None
        try:
            package, _ = self.socket.recv()
        except (PackageErr, ChecksumErr, TimeoutError):
            self.logger.error("Timeout esperando paquete")
            self.tries += 1
            self._send_nack(self.first_sequence_number)
            self._receive_data(file, retries + 1)
        except Exception as e:
            self.logger.error(f"Error inesperado al recibir el paquete: {e}")
            self.tries += 1
            raise

        if package is None:
            return (False, 0)

        if package.type == PackageType.FIN or package.data is None:
            file.flush()
            return (True, package.sequence_number)

        if not package.valid:
            ack_package = NackPackage(package.sequence_number)
            self.socket.sendto(ack_package, self.server_addr)

            return self._receive_data(file, retries + 1)

        if package.type != PackageType.DATA:
            raise Exception("El paquete recibido no es un DataPackage.")

        file.write(package.data)
        return (False, package.sequence_number)

    def _send_ack(self, seq_number: int) -> None:
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
        for item in self.window.items:
            if item.sequence_number == seq_number:
                item.acked = True
                if item.stop_event:  ### NUEVO TIMER
                    item.stop_event.set()  ### NUEVO TIMER
                break
        else:
            self.logger.warning(
                f"ACK recibido por paquete fuera de la ventana: {seq_number}"
            )
            return False

        # Avanzar la ventana si el primero fue ACKed
        while self.window.items and self.window.items[0].acked:
            self.window.remove_first_sent()
            self.first_sequence_number += 1

        return True

    def contains_seq_num(self, seq_num: int) -> bool:
        for item in self.window.items:
            if item.sequence_number == seq_num:
                return True
        return False

    def resend_package(self, seq_num: int) -> bool:
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

    ### NUEVO TIMER
    def _start_timer_for_item(self, item: WindowItem) -> None:
        stop_event = Event()
        item.stop_event = stop_event  # Asignás igualmente si otro código lo necesita

        def timeout_func(local_stop_event=stop_event):  # Capturás el Event localmente
            while not local_stop_event.wait(timeout=3):
                if item.acked:
                    return
                self.logger.debug(
                    f"Timeout para paquete {item.sequence_number}, reenviando."
                )
                item.retries_left -= 1
                data_package = DataPackage(item.data, item.sequence_number)
                self._send_package(data_package)

        thread = Thread(target=timeout_func)
        thread.daemon = True
        thread.start()

        item.timer_thread = thread
