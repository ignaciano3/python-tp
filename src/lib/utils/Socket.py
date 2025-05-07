import logging
import random
import socket

from lib.utils.constants import BUFSIZE
from lib.utils.logger import create_logger
from lib.packages.Package import Package
from lib.packages.FactoryPackage import FactoryPackage
from lib.utils.package_error import PackageErr, ChecksumErr


class Socket:
    def __init__(self, logging_level=logging.DEBUG) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.logger = create_logger("socket", "[SOCKET]", logging_level)

    def bind(self, host: str, port: int) -> None:
        self.logger.debug(f"Binding socket to {host}:{port}")
        self.socket.bind((host, port))

    def sendto(self, package: Package, addr: tuple[str, int]) -> None:
        self.logger.debug(f"Sending data to {addr}")
        self.socket.sendto(package.to_bytes(), addr)

    def recv(self, bufsize=BUFSIZE) -> tuple[Package, tuple[str, int]]:
        self.logger.debug(f"Receiving data with buffer size {bufsize}")
        try:
            received = self.socket.recvfrom(bufsize)
            
            package_raw = received[0]
            package = FactoryPackage.recover_package(package_raw)

            return (package, received[1])
        except (PackageErr, ChecksumErr, TimeoutError) as e:
            self.logger.error(f"Error en el paquete recibido: {e}")
            raise e
        except ConnectionResetError:
            self.logger.error("La otra parte cerró la conexión")
            raise
        except Exception as e:
            self.logger.exception("Excepción inesperada en recv:")
            raise e

    def close(self) -> None:
        self.logger.debug("Closing socket")
        self.socket.close()

    def settimeout(self, timeout: int) -> None:
        self.logger.debug(f"Setting socket timeout to {timeout} seconds")
        self.socket.settimeout(timeout)
