import socket
import threading
import sys

HOST = "0.0.0.0"
PORT = 12347
BUFFER_SIZE = 1024

clients = {}
clients_lock = threading.Lock()

def broadcast(message: str, exclude_socket=None):
    data = message.encode("utf-8")

    with clients_lock:
        sockets = list(clients.keys())

    for sock in sockets:
        if sock == exclude_socket:
            continue
        try:
            sock.sendall(data)
        except Exception:
            remove_client(sock)

def remove_client(client_socket):
    with clients_lock:
        username = clients.pop(client_socket, None)

    try:
        client_socket.close()
    except Exception:
        pass

    if username:
        broadcast(f"[Сервер] {username} вышел из чата.\n")

def handle_client(client_socket, client_address):
    print(f"Подключен клиент: {client_address}")

    try:
        client_socket.sendall("Введите ник: ".encode("utf-8"))
        username = client_socket.recv(BUFFER_SIZE).decode("utf-8", errors="replace").strip()

        if not username:
            username = f"user_{client_address[1]}"

        with clients_lock:
            clients[client_socket] = username

        client_socket.sendall(f"[Сервер] Привет, {username}! Команда: /quit чтобы выйти.\n".encode("utf-8"))
        broadcast(f"[Сервер] {username} вошел в чат.\n", exclude_socket=client_socket)

        while True:
            data = client_socket.recv(BUFFER_SIZE)
            if not data:
                break

            text = data.decode("utf-8", errors="replace").strip()

            if text == "":
                continue

            if text.lower() == "/quit":
                break

            broadcast(f"{username}: {text}\n", exclude_socket=None)

    except Exception as e:
        print(f"Ошибка клиента {client_address}: {e}")

    finally:
        remove_client(client_socket)
        print(f"Соединение с {client_address} закрыто")

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen(10)
        print(f"TCP Chat Server запущен на {HOST}:{PORT}")

        while True:
            client_socket, client_address = server_socket.accept()

            t = threading.Thread(
                target=handle_client,
                args=(client_socket, client_address),
                daemon=True
            )
            t.start()

    except KeyboardInterrupt:
        print("\nОстановка сервера...")
    except Exception as e:
        print(f"Ошибка: {e}")
        sys.exit(1)
    finally:
        try:
            server_socket.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()