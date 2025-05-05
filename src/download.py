from lib.Client import Client


def download(file_name: str, host: str, port: int = 8080) -> None:
    client = Client("download", file_name, host, port)
    client.start()


if __name__ == "__main__":
    download("xs.bin", "localhost", 8080)
