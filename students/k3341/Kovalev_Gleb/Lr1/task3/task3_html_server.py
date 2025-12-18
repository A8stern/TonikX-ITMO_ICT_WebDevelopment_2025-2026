import socket
import sys

def load_index_html(filename="index.html"):
    try:
        with open(filename, "rb") as f:
            return f.read()
    except FileNotFoundError:
        return None

def build_http_response(status_code, body, content_type="text/html; charset=utf-8"):
    status_map = {
        200: "OK",
        404: "Not Found",
        500: "Internal Server Error",
    }

    reason = status_map.get(status_code, "OK")
    status_line = f"HTTP/1.1 {status_code} {reason}\r\n"

    headers = (
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(body)}\r\n"
        "Connection: close\r\n"
        "\r\n"
    )

    return status_line.encode("utf-8") + headers.encode("utf-8") + body

def parse_request_path(request_text):
    try:
        first_line = request_text.split("\r\n")[0]
        parts = first_line.split(" ")
        if len(parts) >= 2:
            return parts[1]
    except Exception:
        pass
    return "/"

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    host = "localhost"
    port = 8080

    try:
        server_socket.bind((host, port))
        server_socket.listen(1)
        print(f"HTTP Server запущен на {host}:{port}")

        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Подключен клиент: {client_address}")

            try:
                request_data = client_socket.recv(4096).decode("utf-8", errors="replace")
                print(f"Получен запрос:\n{request_data}")

                path = parse_request_path(request_data)

                if path == "/" or path == "/index.html":
                    html = load_index_html("index.html")

                    if html is None:
                        body = b"<h1>404 Not Found</h1><p>index.html not found</p>"
                        response = build_http_response(404, body)
                    else:
                        response = build_http_response(200, html)

                else:
                    body = b"<h1>404 Not Found</h1><p>Only / or /index.html supported</p>"
                    response = build_http_response(404, body)

                client_socket.send(response)

            except Exception as e:
                error_msg = f"Ошибка обработки клиента: {str(e)}"
                print(error_msg)

                body = f"<h1>500 Server Error</h1><pre>{error_msg}</pre>".encode("utf-8")
                response = build_http_response(500, body)
                client_socket.send(response)

            finally:
                client_socket.close()
                print(f"Соединение с {client_address} закрыто")

    except Exception as e:
        print(f"Ошибка: {e}")
        sys.exit(1)

    finally:
        server_socket.close()


if __name__ == "__main__":
    main()