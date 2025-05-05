from lib.Client import Client
from lib.utils.constants import CLIENT_STORAGE


def download(file_path: str, host: str, port: int = 8080) -> None:
    client = Client("download", file_path, host, port)
    client.start()


if __name__ == "__main__":
    download(CLIENT_STORAGE + "/xs.bin", "localhost", 8080)
