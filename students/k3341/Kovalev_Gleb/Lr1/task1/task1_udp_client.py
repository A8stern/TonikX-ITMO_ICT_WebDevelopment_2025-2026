import socket
import sys

def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    server_host = 'localhost'
    server_port = 12345

    try:
        message = "Hello, server"

        client_socket.sendto(message.encode('utf-8'), (server_host, server_port))
        print(f"Отправлено сообщение серверу: {message}")

        response, server_address = client_socket.recvfrom(1024)
        response_message = response.decode('utf-8')

        print(f"Получен ответ от сервера {server_address}: {response_message}")

    except Exception as e:
        print(f"Ошибка клиента: {e}")
        sys.exit(1)

    finally:
        client_socket.close()
        print("Клиент завершил работу")

if __name__ == "__main__":
    main()