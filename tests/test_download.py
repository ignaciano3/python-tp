import logging
import random
import string
import threading
from pathlib import Path

import pytest


from src.lib.Server import Server
from src.lib.utils.constants import BUFSIZE, DEFAULT_PORT, LOCALHOST
from src.lib.Client import Client
from src.lib.utils.enums import Protocol
from src.lib.utils.types import ADDR


@pytest.fixture
def storages(tmp_path) -> tuple[Path, Path]:
    client_storage = tmp_path / "client_storage"
    client_storage.mkdir()

    server_storage = tmp_path / "server_storage"
    server_storage.mkdir()

    return (client_storage, server_storage)


def start_client(
    file_path: str, server_addr: ADDR, client_num: str | int = "", start_now=True
):
    client = Client(
        "download",
        file_path,
        server_addr[0],
        server_addr[1],
        protocol=Protocol.STOP_WAIT,
        logging_level=logging.ERROR,
    )
    client_thread = threading.Thread(
        target=client.start, name=f"ClientThread-{client_num}"
    )
    if start_now:
        client_thread.start()
    return client, client_thread


def start_server(server_addr, server_storage):
    server = Server(
        host=server_addr[0],
        port=server_addr[1],
        protocol=Protocol.STOP_WAIT,
        server_storage=str(server_storage),
        logging_level=logging.ERROR,
    )
    server_thread = threading.Thread(target=server.start, name="ServerThread")
    server_thread.start()
    return server, server_thread


def test_download_xs(storages):
    client_storage, server_storage = storages

    xs_file = server_storage / "xs.bin"
    xs_file.write_text("HELLO WORLD", encoding="utf-8")

    server_addr = (LOCALHOST, DEFAULT_PORT + 12)
    # Start the server
    server, server_thread = start_server(server_addr, server_storage)

    # Start the client
    downloaded_file = client_storage / "xs.bin"
    client, client_thread = start_client(str(downloaded_file), server_addr)

    client_thread.join(timeout=1)
    server.stop()
    server_thread.join(timeout=1)

    assert len(list(client_storage.iterdir())) == 1  # Chequeo que haya un archivo
    assert downloaded_file.exists(follow_symlinks=False)
    assert downloaded_file.read_text(encoding="utf-8") == "HELLO WORLD"

    server.stop()
    server_thread.join()

    assert server_thread.is_alive() is False


def test_download_md(storages):
    client_storage, server_storage = storages

    md_file = server_storage / "md.bin"
    text = generate_random_text(BUFSIZE * 3)
    md_file.write_text(text, encoding="utf-8")

    server_addr = (LOCALHOST, DEFAULT_PORT + 105)
    # Start the server
    server, server_thread = start_server(server_addr, server_storage)

    # Start the client
    downloaded_file = client_storage / "md.bin"
    client, client_thread = start_client(str(downloaded_file), server_addr)

    client_thread.join(timeout=5)
    server.stop()
    server_thread.join(timeout=5)

    assert len(list(client_storage.iterdir())) == 1  # Chequeo que haya un archivo
    assert downloaded_file.exists(follow_symlinks=False)
    assert downloaded_file.read_text(encoding="utf-8") == text

    assert server_thread.is_alive() is False


def test_download_lg(storages):
    client_storage, server_storage = storages

    lg_file = server_storage / "lg.bin"
    text = generate_random_text(BUFSIZE * 30)
    lg_file.write_text(text, encoding="utf-8")

    server_addr = (LOCALHOST, DEFAULT_PORT + 1)
    # Start the server
    server, server_thread = start_server(server_addr, server_storage)

    # Start the client
    downloaded_file = client_storage / "lg.bin"
    client, client_thread = start_client(str(downloaded_file), server_addr)

    client_thread.join(timeout=20)
    server.stop()
    server_thread.join(timeout=20)

    assert len(list(client_storage.iterdir())) == 1  # Chequeo que haya un archivo
    assert downloaded_file.exists(follow_symlinks=False)
    assert downloaded_file.read_text(encoding="utf-8") == text

    assert server_thread.is_alive() is False


def test_concurrent_download(storages):
    client_storage, server_storage = storages

    FILE_AMOUNT = 5
    files: list[tuple[Path, Path]] = []

    for i in range(FILE_AMOUNT):
        file = server_storage / f"{i}.bin"
        file_client = client_storage / f"{i}.bin"

        text = generate_random_text(BUFSIZE * 5)
        file.write_text(text, encoding="utf-8")
        files.append((file, file_client))

    server_addr = (LOCALHOST, DEFAULT_PORT + 35)
    # Start the server
    server, server_thread = start_server(server_addr, server_storage)

    # Start the clients
    client_threads = []

    for file in files:
        client, client_thread = start_client(
            str(file[1]), server_addr, file[0].name, False
        )
        client_threads.append(client_thread)

    for client_thread in client_threads:
        client_thread.start()
        client_thread.join(timeout=20)

    server.stop()
    server_thread.join(timeout=20)

    assert (
        len(list(client_storage.iterdir())) == FILE_AMOUNT
    )  # Chequeo que esten los archivos
    for i in range(FILE_AMOUNT):
        downloaded_file = client_storage / f"{i}.bin"
        assert downloaded_file.exists(follow_symlinks=False)
        downloaded_text = downloaded_file.read_text(encoding="utf-8")
        server_text = files[i][0].read_text(encoding="utf-8")
        assert downloaded_text == server_text


def test_download_xl(storages):
    client_storage, server_storage = storages

    md_file = server_storage / "xl.bin"
    text = generate_random_text(BUFSIZE * 1024)
    md_file.write_text(text, encoding="utf-8")

    server_addr = (LOCALHOST, DEFAULT_PORT + 1)
    # Start the server
    server, server_thread = start_server(server_addr, server_storage)

    # Start the client
    downloaded_file = client_storage / "xl.bin"
    client, client_thread = start_client(str(downloaded_file), server_addr)

    client_thread.join(timeout=20)
    server.stop()
    server_thread.join(timeout=20)

    assert len(list(client_storage.iterdir())) == 1  # Chequeo que haya un archivo
    assert downloaded_file.exists(follow_symlinks=False)
    assert downloaded_file.read_text(encoding="utf-8") == text

    assert server_thread.is_alive() is False


def test_concurrent_download_xl(storages):
    client_storage, server_storage = storages

    FILE_AMOUNT = 20
    files: list[tuple[Path, Path]] = []

    for i in range(FILE_AMOUNT):
        file = server_storage / f"{i}.bin"
        file_client = client_storage / f"{i}.bin"

        text = generate_random_text(BUFSIZE) * 1024
        file.write_text(text, encoding="utf-8")
        files.append((file, file_client))

    server_addr = (LOCALHOST, DEFAULT_PORT + 35)
    # Start the server
    server, server_thread = start_server(server_addr, server_storage)

    # Start the clients
    client_threads = []

    for file in files:
        client, client_thread = start_client(
            str(file[1]), server_addr, file[0].name, False
        )
        client_threads.append(client_thread)

    for client_thread in client_threads:
        client_thread.start()
        client_thread.join(timeout=20)

    server.stop()
    server_thread.join(timeout=20)

    assert (
        len(list(client_storage.iterdir())) == FILE_AMOUNT
    )  # Chequeo que esten los archivos
    for i in range(FILE_AMOUNT):
        downloaded_file = client_storage / f"{i}.bin"
        assert downloaded_file.exists(follow_symlinks=False)
        downloaded_text = downloaded_file.read_text(encoding="utf-8")
        server_text = files[i][0].read_text(encoding="utf-8")
        assert downloaded_text == server_text

def generate_random_text(length):
    return "".join(
        random.choice(string.ascii_letters + string.digits) for _ in range(length)
    )
