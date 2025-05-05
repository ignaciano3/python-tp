from lib.Client import Client
from lib.utils.constants import CLIENT_STORAGE


def upload(file_path: str, host: str, port: int = 8080) -> None:
    client = Client("upload", file_path, host, port)
    client.start()


if __name__ == "__main__":
    upload(CLIENT_STORAGE + "/xs.bin", "localhost", 8080)
