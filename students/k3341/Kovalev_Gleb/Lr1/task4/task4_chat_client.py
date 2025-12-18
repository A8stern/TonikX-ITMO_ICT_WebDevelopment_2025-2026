import socket
import threading
import sys

HOST = "127.0.0.1"
PORT = 12347
BUFFER_SIZE = 1024

def receive_messages(sock: socket.socket):
    try:
        while True:
            data = sock.recv(BUFFER_SIZE)
            if not data:
                print("\n[Клиент] Соединение закрыто сервером.")
                break
            print(data.decode("utf-8", errors="replace"), end="")
    except Exception:
        pass

def recv_once(sock: socket.socket) -> str:
    data = sock.recv(BUFFER_SIZE)
    return data.decode("utf-8", errors="replace") if data else ""

def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client_socket.connect((HOST, PORT))

        prompt = recv_once(client_socket)
        if prompt:
            print(prompt, end="")
        username = input().strip()
        if username == "":
            username = "guest"
        client_socket.sendall((username + "\n").encode("utf-8"))

        t = threading.Thread(target=receive_messages, args=(client_socket,), daemon=True)
        t.start()

        while True:
            msg = input()
            client_socket.sendall((msg + "\n").encode("utf-8"))

            if msg.strip().lower() == "/quit":
                break

    except Exception as e:
        print(f"Ошибка: {e}")
        sys.exit(1)

    finally:
        try:
            client_socket.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()