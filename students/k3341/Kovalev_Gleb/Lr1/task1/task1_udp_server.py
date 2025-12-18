import socket
import sys

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    host = 'localhost'
    port = 12345

    try:
        server_socket.bind((host, port))
        print(f"UDP Server запущен на {host}:{port}")
        print("Ожидание сообщений от клиента...")

        data, client_address = server_socket.recvfrom(1024)
        message = data.decode('utf-8')

        print(f"Получено сообщение от {client_address}: {message}")

        response = "Hello, client"
        server_socket.sendto(response.encode('utf-8'), client_address)
        print(f"Отправлен ответ клиенту: {response}")

    except Exception as e:
        print(f"Ошибка сервера: {e}")
        sys.exit(1)

    finally:
        server_socket.close()
        print("Сервер завершил работу")

if __name__ == "__main__":
    main()