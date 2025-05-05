import logging
import os
from lib.utils.Socket import Socket
from lib.utils.types import ADDR
from lib.packages.InitPackage import UploadHeader
from lib.utils.logger import create_logger
from lib.packages.DataPackage import DataPackage
from lib.packages.FinPackage import FinPackage
from lib.utils.constants import BUFSIZE

class Upload:
    def __init__(self, file_path: str, socket: Socket, server_addr: ADDR, logging_level= logging.DEBUG) -> None:
        self.file_path = file_path
        self.socket = socket
        self.server_addr = server_addr
        self.logger = create_logger("client", "[CLIENT]", logging_level)
    
    def start(self) -> None:
        file_name = os.path.basename(self.file_path)

        header = UploadHeader(file_name)
        self.socket.sendto(header, self.server_addr)
        self.socket.recv()
        
        with open(self.file_path, "rb") as file:
            while True:
                data = file.read(BUFSIZE - 50)
                if not data:
                    break
                data_package = DataPackage(data)
                self.socket.sendto(data_package, self.server_addr)
                self.socket.recv()

        fin_package = FinPackage()
        self.socket.sendto(fin_package, self.server_addr)

        self.socket.recv()

        self.socket.close()
        self.logger.info(f"File {file_name} uploaded successfully.")

