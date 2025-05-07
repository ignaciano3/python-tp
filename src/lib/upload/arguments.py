from argparse import ArgumentParser

from lib.utils.constants import CLIENT_STORAGE, DEFAULT_PORT, LOCALHOST
from lib.utils.enums import Protocol

"""
usage : upload [ - h ] [ - v | -q ] [ - H ADDR ] [ - p PORT ] [ - s FILEPATH ] [ - n FILENAME ] [ - r protocol ]
<command description>
optional arguments :
-h , -- help show this help message and exit
-v , -- verbose increase output verbosity
-q , -- quiet decrease output verbosity
-H , -- host server IP address
-p , -- port server port
-s , -- src source file path
-n , -- name file name
-r , -- protocol error recovery protocol

"""

parser = ArgumentParser(
    description="Upload a file to a server using a specified protocol."
)

group = parser.add_mutually_exclusive_group(required=False)
group.add_argument("-v", "--verbose", default=False, help="increase output verbosity")
group.add_argument("-q", "--quiet", default=False, help="decrease output verbosity")
parser.add_argument(
    "-H", "--host", action="store_true", help="server IP address", default=LOCALHOST
)
parser.add_argument(
    "-p", "--port", action="store_true", help="server port", default=DEFAULT_PORT
)

parser.add_argument("-s", "--src", help="source file path", default=CLIENT_STORAGE)
parser.add_argument("-n", "--name", help="file name", default="hello.txt")
parser.add_argument(
    "-r",
    "--protocol",
    help="error recovery protocol",
    type=int,
    default=Protocol.STOP_WAIT.value,
)
