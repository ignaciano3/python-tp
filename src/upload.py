from lib.Client import Client


def upload(file_name: str, host: str, port: int = 8080) -> None:
    client = Client("upload", file_name, host, port)
    client.start()


if __name__ == "__main__":
    upload("xs.bin", "localhost", 8080)
