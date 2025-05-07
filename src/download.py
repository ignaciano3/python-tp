import logging
from lib.Client import Client
from lib.download.arguments import parser
from lib.utils.enums import Protocol


def download(
    file_path: str, host: str, port: int, protocol: Protocol, logging_level
) -> None:
    client = Client("download", file_path, host, port, protocol, logging_level)
    client.start()


if __name__ == "__main__":
    args = parser.parse_args()
    host: str = args.host
    port: int = args.port
    protocol: Protocol = args.protocol
    destination: str = args.dst

    if args.verbose:
        logging_level = logging.DEBUG
    elif args.quiet:
        logging_level = logging.ERROR
    else:
        logging_level = logging.INFO

    download(destination, host, port, protocol, logging_level)
