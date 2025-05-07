from typing import Literal
from lib.Client import Client
import logging
from lib.utils.enums import Protocol
from lib.upload.arguments import parser
import time


def upload(file_path: str, host: str, port: int, protocol: Protocol, logging_level):
    start_time = time.time()

    client = Client("upload", file_path, host, port, protocol, logging_level)
    client.start()

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Tiempo total de ejecución: {elapsed_time:.4f} segundos")


if __name__ == "__main__":
    args = parser.parse_args()
    host: str = args.host
    port: int = args.port
    protocol: Literal[0, 1] = args.protocol
    file_name: str = args.name
    file_source: str = args.src
    file_path: str = file_source + "/" + file_name

    if args.verbose:
        logging_level = logging.DEBUG
    elif args.quiet:
        logging_level = logging.ERROR
    else:
        logging_level = logging.INFO

    upload(file_path, host, port, Protocol(protocol), logging_level)
