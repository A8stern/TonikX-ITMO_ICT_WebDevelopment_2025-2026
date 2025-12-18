import socket
import sys
from urllib.parse import parse_qs

HOST = "127.0.0.1"
PORT = 8080
BUFFER_SIZE = 4096
DATA_FILE = "grades.txt"


def load_grades():
    grades = {}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                parts = line.split("|")
                subject = parts[0]
                marks = []

                for m in parts[1:]:
                    try:
                        m = int(m)
                        if 2 <= m <= 5:
                            marks.append(m)
                    except ValueError:
                        pass

                grades[subject] = marks
    except FileNotFoundError:
        pass

    return grades


def save_grades(grades):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        for subject, marks in grades.items():
            line = subject
            for m in marks:
                line += f"|{m}"
            f.write(line + "\n")


def build_html(grades):
    rows = ""

    for subject, marks in grades.items():
        marks_str = ", ".join(map(str, marks)) if marks else "—"
        rows += f"""
        <tr>
            <td>{subject}</td>
            <td>{marks_str}</td>
        </tr>
        """

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Оценки</title>
</head>
<body>
    <h1>Оценки по дисциплинам</h1>

    <table border="1" cellpadding="5">
        <tr>
            <th>Дисциплина</th>
            <th>Оценки</th>
        </tr>
        {rows}
    </table>

    <h2>Добавить оценку</h2>
    <form method="POST" action="/add">
        <label>Дисциплина:</label><br>
        <input type="text" name="subject" required><br><br>
    
        <label>Оценка (2–5):</label><br>
        <input type="number" name="grade" min="2" max="5" required><br><br>
    
        <button type="submit">Добавить оценку</button>
    </form>
</body>
</html>"""


def build_response(body, status="200 OK"):
    headers = (
        f"HTTP/1.1 {status}\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        f"Content-Length: {len(body.encode('utf-8'))}\r\n"
        "Connection: close\r\n"
        "\r\n"
    )
    return headers + body


def handle_request(request: str):
    lines = request.split("\r\n")
    request_line = lines[0]

    try:
        method, path, _ = request_line.split(" ")
    except ValueError:
        return build_response("<h1>400 Bad Request</h1>", "400 Bad Request")

    grades = load_grades()

    if method == "GET" and path == "/":
        html = build_html(grades)
        return build_response(html)

    if method == "POST" and path == "/add":
        body = request.split("\r\n\r\n", 1)[1]
        data = parse_qs(body)

        subject = data.get("subject", [""])[0].strip()
        grade = data.get("grade", [""])[0].strip()

        try:
            grade = int(grade)
            if 2 <= grade <= 5 and subject:
                grades.setdefault(subject, []).append(grade)
                save_grades(grades)
        except ValueError:
            pass

        html = build_html(grades)
        return build_response(html)

    return build_response("<h1>404 Not Found</h1>", "404 Not Found")

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        print(f"HTTP сервер запущен: http://{HOST}:{PORT}")

        while True:
            client_socket, client_address = server_socket.accept()

            try:
                request = client_socket.recv(BUFFER_SIZE).decode("utf-8", errors="replace")
                response = handle_request(request)
                client_socket.sendall(response.encode("utf-8"))
            except Exception as e:
                print(f"Ошибка клиента {client_address}: {e}")
            finally:
                client_socket.close()

    except Exception as e:
        print(f"Ошибка сервера: {e}")
        sys.exit(1)

    finally:
        server_socket.close()


if __name__ == "__main__":
    main()