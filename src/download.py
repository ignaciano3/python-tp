import logging
from lib.Client import Client
from lib.download.arguments import parser
from lib.utils.enums import Protocol
import time


def download(
    file_path: str, host: str, port: int, protocol: Protocol, logging_level
) -> None:
    ##### TIMER PARA CUANTO TARDA LA CONSULTA DEL CLIENTE #####

    start_time = time.time()

    client = Client("download", file_path, host, port, protocol, logging_level)
    client.start()

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Tiempo total de ejecución: {elapsed_time:.4f} segundos")


if __name__ == "__main__":
    args = parser.parse_args()
    host: str = args.host
    port: int = args.port
    protocol: Protocol = Protocol(args.protocol)
    destination: str = args.dst
    file_name: str = args.name
    file_path: str = destination + "/" + file_name

    if args.verbose:
        logging_level = logging.DEBUG
    elif args.quiet:
        logging_level = logging.ERROR
    else:
        logging_level = logging.INFO

    download(file_path, host, port, protocol, logging_level)
