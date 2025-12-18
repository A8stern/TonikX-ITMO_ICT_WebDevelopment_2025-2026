import socket
import sys
import math

def pythagorean_theorem(a, b):
    try:
        a, b = float(a), float(b)
        if a <= 0 or b <= 0:
            return "Ошибка: катеты должны быть положительными числами"
        c = math.sqrt(a ** 2 + b ** 2)
        return f"Гипотенуза: {c:.2f}"
    except ValueError:
        return "Ошибка: введите корректные числа"

def process_request(data):
    try:
        parts = data.strip().split(',')

        if len(parts) != 2:
            return "Ошибка: для теоремы Пифагора нужно 2 параметра (катеты)"
        return pythagorean_theorem(parts[0], parts[1])

    except Exception as e:
        return f"Ошибка обработки запроса: {str(e)}"

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    host = 'localhost'
    port = 12346

    try:
        server_socket.bind((host, port))
        server_socket.listen(1)
        print(f"TCP Server запущен на {host}:{port}")

        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Подключен клиент: {client_address}")

            try:
                data = client_socket.recv(1024).decode('utf-8')
                print(f"Получен запрос: {data}")

                result = process_request(data)
                print(f"Результат: {result}")

                client_socket.send(result.encode('utf-8'))

            except Exception as e:
                error_msg = f"Ошибка обработки клиента: {str(e)}"
                print(error_msg)
                client_socket.send(error_msg.encode('utf-8'))

            finally:
                client_socket.close()
                print(f"Соединение с {client_address} закрыто")

    except Exception as e:
        print(f"Ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()