"""
python start - server -h
usage : start - server [ - h ] [ - v | -q ] [ - H ADDR ] [ - p PORT ] [ - s DIRPATH ] [ - r protocol ]
< command description >
optional arguments :
-h , -- help show this help message and exit
-v , -- verbose increase output verbosity
-q , -- quiet decrease output verbosity
-H , -- host service IP address
-p , -- port service port
-s , -- storage storage dir path
-r , -- protocol error recovery protocol
"""

from argparse import ArgumentParser
from lib.utils.enums import Protocol

from lib.utils.constants import DEFAULT_PORT, LOCALHOST, SERVER_STORAGE

parser = ArgumentParser(
    description="Start a server to receive files using a specified protocol."
)
group = parser.add_mutually_exclusive_group(required=False)
group.add_argument("-v", "--verbose", default=False, help="increase output verbosity")
group.add_argument("-q", "--quiet", default=False, help="decrease output verbosity")
parser.add_argument(
    "-H", "--host", type=str, default=LOCALHOST, help="service IP address"
)
parser.add_argument(
    "-p",
    "--port",
    type=int,
    default=DEFAULT_PORT,
    help="service port",
)
parser.add_argument(
    "-s",
    "--storage",
    type=str,
    default=SERVER_STORAGE,
    help="storage dir path",
)
parser.add_argument(
    "-r",
    "--protocol",
    default=Protocol.STOP_WAIT,
    type=int,
    help="error recovery protocol",
)
