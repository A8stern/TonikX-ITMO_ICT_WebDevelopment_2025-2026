import socket

def get_pythagorean_params():
    try:
        a = float(input("Введите длину первого катета: "))
        b = float(input("Введите длину второго катета: "))
        return f"{a},{b}"
    except ValueError:
        print("Ошибка: введите корректные числа")
        return None

def send_request(server_host, server_port, request):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        client_socket.connect((server_host, server_port))

        client_socket.send(request.encode('utf-8'))
        print(f"Отправлен запрос: {request}")

        response = client_socket.recv(1024).decode('utf-8')
        print(f"Результат: {response}")

        return response

    except ConnectionRefusedError:
        print("Ошибка: не удалось подключиться к серверу. Убедитесь, что сервер запущен.")
        return None
    except Exception as e:
        print(f"Ошибка соединения: {e}")
        return None
    finally:
        client_socket.close()

def main():
    server_host = 'localhost'
    server_port = 12346

    while True:
        request = get_pythagorean_params()

        if request is None:
            print("Попробуйте еще раз с корректными данными.")
            continue

        send_request(server_host, server_port, request)

        continue_choice = input("\nХотите выполнить еще одну операцию? (y/n): ").strip().lower()
        if continue_choice != 'y':
            print("До свидания!")
            break

if __name__ == "__main__":
    main()