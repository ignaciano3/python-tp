import logging
import random
import string
import threading
import time
from pathlib import Path

import pytest

from src.lib.Client import Client
from src.lib.Server import Server
from src.lib.utils.constants import BUFSIZE, DEFAULT_PORT, LOCALHOST
from src.lib.utils.enums import Protocol
from src.lib.utils.types import ADDR


@pytest.fixture
def storages(tmp_path) -> tuple[Path, Path]:
    client_storage = tmp_path / "client_storage"
    client_storage.mkdir()

    server_storage = tmp_path / "server_storage"
    server_storage.mkdir()

    return (client_storage, server_storage)


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


def start_client(
    file_path: str, server_addr: ADDR, client_num: str | int = "", start_now=True
):
    client = Client(
        "upload",
        file_path,
        server_addr[0],
        server_addr[1],
        protocol=Protocol.SELECTIVE_REPEAT,
        logging_level=logging.ERROR,
    )
    client_thread = threading.Thread(
        target=client.start, name=f"ClientThread-{client_num}"
    )
    if start_now:
        client_thread.start()
    return client, client_thread


def test_upload_xs(storages):
    client_storage, server_storage = storages

    xs_file = client_storage / "xs.bin"
    xs_file.write_text("HELLO WORLD", encoding="utf-8")

    server_addr = (LOCALHOST, DEFAULT_PORT + 14)
    # Start the server
    server, server_thread = start_server(server_addr, server_storage)

    assert server_thread.is_alive()

    # Start the client
    _, client_thread = start_client(str(xs_file), server_addr)

    client_thread.join(timeout=3)
    server.stop()
    server_thread.join(timeout=1)

    uploaded_file = server_storage / "xs.bin"

    assert len(list(server_storage.iterdir())) == 1  # Chequeo que haya un archivo
    assert uploaded_file.exists(follow_symlinks=False)
    assert uploaded_file.read_text(encoding="utf-8") == "HELLO WORLD"

    server.stop()
    server_thread.join()

    assert server_thread.is_alive() is False


def test_upload_md(storages):
    client_storage, server_storage = storages

    md_file = client_storage / "md.bin"
    text = generate_random_text(BUFSIZE * 3)
    md_file.write_text(text, encoding="utf-8")

    server_addr = (LOCALHOST, DEFAULT_PORT + 105)

    # Start the server
    server, server_thread = start_server(server_addr, server_storage)

    assert server_thread.is_alive()

    # Start the client
    # Start the client
    _, client_thread = start_client(str(md_file), server_addr)

    client_thread.join(timeout=5)
    server.stop()
    server_thread.join(timeout=5)

    uploaded_file = server_storage / "md.bin"

    assert len(list(server_storage.iterdir())) == 1  # Chequeo que haya un archivo
    assert uploaded_file.exists(follow_symlinks=False)
    assert uploaded_file.read_text(encoding="utf-8") == text

    assert server_thread.is_alive() is False


def test_upload_lg(storages):
    client_storage, server_storage = storages

    lg_file = client_storage / "lg.bin"
    text = generate_random_text(BUFSIZE * 30)
    lg_file.write_text(text, encoding="utf-8")

    server_addr = (LOCALHOST, DEFAULT_PORT + 2)
    # Start the server
    server, server_thread = start_server(server_addr, server_storage)

    assert server_thread.is_alive()

    # Start the client
    _, client_thread = start_client(str(lg_file), server_addr)

    client_thread.join(timeout=2)
    server.stop()
    server_thread.join(timeout=2)

    uploaded_file = server_storage / "lg.bin"

    assert len(list(server_storage.iterdir())) == 1  # Chequeo que haya un archivo
    assert uploaded_file.exists(follow_symlinks=False)
    assert uploaded_file.read_text(encoding="utf-8") == text

    assert server_thread.is_alive() is False


def test_concurrent_upload(storages):
    client_storage, server_storage = storages

    FILE_AMOUNT = 5
    files: list[Path] = []

    for i in range(FILE_AMOUNT):
        file = client_storage / f"{i}.bin"
        text = generate_random_text(BUFSIZE) * 5
        file.write_text(text, encoding="utf-8")
        files.append(file)

    server_addr = (LOCALHOST, DEFAULT_PORT + 22)
    # Start the server
    server, server_thread = start_server(server_addr, server_storage)

    # Start the clients
    client_threads: list[threading.Thread] = []

    for file in files:
        # Start the client
        _, client_thread = start_client(
            str(file), server_addr, file.name, start_now=False
        )
        client_threads.append(client_thread)

    assert server_thread.is_alive()

    for client_thread in client_threads:
        client_thread.start()

    for client_thread in client_threads:
        assert server_thread.is_alive() is True
        client_thread.join(5)

    for client_thread in client_threads:
        assert client_thread.is_alive() is False
    server.stop()
    server_thread.join(timeout=5)

    assert (
        len(list(server_storage.iterdir())) == FILE_AMOUNT
    )  # Chequeo que esten los archivos
    for i in range(FILE_AMOUNT):
        uploaded_file = server_storage / f"{i}.bin"
        assert uploaded_file.exists(follow_symlinks=False)
        assert uploaded_file.read_text(encoding="utf-8") == files[i].read_text(
            encoding="utf-8"
        )


def test_upload_xxl(storages):
    client_storage, server_storage = storages

    xxl_file = client_storage / "xxl.bin"
    # el tp pide que el archivo sea de 5MB, pero por si acaso le pongo 10MB
    text = generate_random_text(512) * 2 * 1024 * 10  # 10 MB
    xxl_file.write_text(text, encoding="utf-8")

    server_addr = (LOCALHOST, DEFAULT_PORT + 4)

    # record the time
    start_time = time.time()

    # Start the server
    server, server_thread = start_server(server_addr, server_storage)

    assert server_thread.is_alive()

    # Start the client
    _, client_thread = start_client(str(xxl_file), server_addr)

    uploaded_file = server_storage / "xxl.bin"

    client_thread.join(timeout=60 * 2)  # 2 minutes
    server.stop()
    server_thread.join(timeout=2)

    # check that the time is less than 2 minutes
    elapsed_time = time.time() - start_time
    assert elapsed_time < 120

    assert len(list(server_storage.iterdir())) == 1  # Chequeo que haya un archivo
    assert uploaded_file.exists(follow_symlinks=False)
    assert uploaded_file.read_text(encoding="utf-8") == text

    assert server_thread.is_alive() is False


def test_upload_xl(storages):
    client_storage, server_storage = storages

    xl_file = client_storage / "xl.bin"
    text = generate_random_text(BUFSIZE * 1024)
    xl_file.write_text(text, encoding="utf-8")

    server_addr = (LOCALHOST, DEFAULT_PORT + 5)
    # Start the server
    server, server_thread = start_server(server_addr, server_storage)

    assert server_thread.is_alive()

    # Start the client
    _, client_thread = start_client(str(xl_file), server_addr)

    uploaded_file = server_storage / "xl.bin"

    client_thread.join(timeout=5)
    server.stop()
    server_thread.join(timeout=10)

    assert len(list(server_storage.iterdir())) == 1  # Chequeo que haya un archivo
    assert uploaded_file.exists(follow_symlinks=False)
    assert uploaded_file.read_text(encoding="utf-8") == text

    assert server_thread.is_alive() is False


def test_concurrent_upload_xl(storages):
    client_storage, server_storage = storages

    FILE_AMOUNT = 40
    files: list[Path] = []

    for i in range(FILE_AMOUNT):
        file = client_storage / f"{i}.bin"
        text = generate_random_text(500) * BUFSIZE
        file.write_text(text, encoding="utf-8")
        files.append(file)

    server_addr = (LOCALHOST, DEFAULT_PORT + 21)
    # Start the server
    server, server_thread = start_server(server_addr, server_storage)

    # Start the clients
    client_threads = []

    for file in files:
        # Start the client
        _, client_thread = start_client(
            str(file), server_addr, file.name, start_now=False
        )
        client_threads.append(client_thread)

    assert server_thread.is_alive()

    for client_thread in client_threads:
        client_thread.start()

    for client_thread in client_threads:
        client_thread.join(10)

    for client_thread in client_threads:
        assert client_thread.is_alive() is False
    server.stop()
    server_thread.join(timeout=5)

    assert (
        len(list(server_storage.iterdir())) == FILE_AMOUNT
    )  # Chequeo que esten los archivos
    for i in range(FILE_AMOUNT):
        uploaded_file = server_storage / f"{i}.bin"
        assert uploaded_file.exists(follow_symlinks=False)
        assert uploaded_file.read_text(encoding="utf-8") == files[i].read_text(
            encoding="utf-8"
        )


def generate_random_text(length):
    return "".join(
        random.choice(string.ascii_letters + string.digits) for _ in range(length)
    )
