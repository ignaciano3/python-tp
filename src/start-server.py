from lib.Server import Server

def start_server(host: str, port: int = 8080) -> None:
    server = Server(host, port)
    server.start()

if __name__ == "__main__":
    start_server("localhost", 8080)