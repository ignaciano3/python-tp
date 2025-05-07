import logging
import threading
from lib.utils.constants import LOCALHOST
from lib.utils.enums import Protocol
from lib.Server import Server
from lib.Client import Client


def main():
    server = Server(
        host=LOCALHOST,
        port=12345,
        protocol=Protocol.STOP_WAIT,
        server_storage="src/lib/server_storage",
        logging_level=logging.INFO,
    )
    server_thread = threading.Thread(target=server.start, name="ServerThread")
    server_thread.start()

    print("Server started.")
    client_threads: list[threading.Thread] = []
    for i in range(40):
        file_path = f"src/lib/client_storage/{(i % 5) + 1}.txt"
        client = Client(
            "upload",
            file_path,
            LOCALHOST,
            12345,
            protocol=Protocol.SELECTIVE_REPEAT,
            logging_level=logging.INFO,
        )
        client_thread = threading.Thread(target=client.start, name=f"ClientThread-{i}")
        client_threads.append(client_thread)

    for client_thread in client_threads:
        client_thread.start()

    for client_thread in client_threads:
        client_thread.join(timeout=5)

    print("All clients finished.")

    server.stop()
    server_thread.join(timeout=1)
    print("Server stopped.")


if __name__ == "__main__":
    main()
