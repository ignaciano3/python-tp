from argparse import ArgumentParser

from lib.utils.constants import CLIENT_STORAGE, DEFAULT_PORT, LOCALHOST
from lib.utils.enums import Protocol

"""
python download -h
usage : download [ - h ] [ - v | -q ] [ - H ADDR ] [ - p PORT ] [ - d FILEPATH ] [ - n FILENAME ] [ - r protocol ]
< command description >
optional arguments :
-h , -- help show this help message and exit
-v , -- verbose increase output verbosity
-q , -- quiet decrease output verbosity
-H , -- host server IP address
-p , -- port server port
-d , -- dst destination file path
-n , -- name file name
-r , -- protocol error recovery protocol
"""

parser = ArgumentParser(
    description="Start a Download Client to receive files using a specified protocol."
)
group = parser.add_mutually_exclusive_group(required=False)
group.add_argument(
    "-v", "--verbose", action="store_true", help="increase output verbosity"
)
group.add_argument(
    "-q", "--quiet", action="store_true", help="decrease output verbosity"
)
parser.add_argument(
    "-H", "--host", action="store_true", help="server IP address", default=LOCALHOST
)
parser.add_argument(
    "-p", "--port", action="store_true", help="server port", default=DEFAULT_PORT
)
parser.add_argument(
    "-d", "--dst", help="destination file path", default=CLIENT_STORAGE + "/hello.txt"
)
parser.add_argument("-n", "--name", action="store_true", help="file name")
parser.add_argument(
    "-r",
    "--protocol",
    action="store_true",
    help="error recovery protocol",
    default=Protocol.STOP_WAIT,
)
