import logging

from lib.server.arguments import parser
from lib.Server import Server
from lib.utils.enums import Protocol


def start_server(
    host: str, port: int, storage_path: str, protocol: Protocol, logging_level: int
):
    server = Server(host, port, protocol, storage_path, logging_level)
    server.start()


if __name__ == "__main__":
    # read host and port from command line arguments
    args = parser.parse_args()

    host, port, storage, protocol = args.host, args.port, args.storage, args.protocol

    if protocol == "selective_repeat":
        protocol = Protocol.SELECTIVE_REPEAT
    else:
        protocol = Protocol.STOP_WAIT

    if args.verbose:
        logging_level = logging.DEBUG
    elif args.quiet:
        logging_level = logging.ERROR
    else:
        logging_level = logging.INFO

    # start server
    start_server(host, port, storage, protocol, logging_level)
