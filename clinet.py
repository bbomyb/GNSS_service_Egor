import socket
import struct
import sys
import os


def recv_exactly(sock, n):
    """Читает ровно n байт из сокета. Блокирует, пока не получит все."""
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise RuntimeError("Сервер закрыл соединение")
        buf += chunk
    return buf


def send_rinex(host: str, port: int, rover_path: str, base_path: str):
    for path in [rover_path, base_path]:
        if not os.path.isfile(path):
            print(f"Ошибка: файл не найден — {path}")
            return

    # Читаем файлы
    with open(rover_path, 'rb') as f:
        rover_data = f.read()
    rover_name = os.path.basename(rover_path)

    with open(base_path, 'rb') as f:
        base_data = f.read()
    base_name = os.path.basename(base_path)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))

          # Отправка файла базы
        s.sendall(struct.pack('>I', len(base_name)))
        s.sendall(base_name.encode('utf-8'))
        s.sendall(struct.pack('>Q', len(base_data)))
        s.sendall(base_data)

        # Отправка файла ровера
        s.sendall(struct.pack('>I', len(rover_name)))
        s.sendall(rover_name.encode('utf-8'))
        s.sendall(struct.pack('>Q', len(rover_data)))
        s.sendall(rover_data)

        #Приём ответа
        prefix = recv_exactly(s, 4)

        if prefix == b"OK::":
            size_bytes = recv_exactly(s, 8)
            result_size = struct.unpack('>Q', size_bytes)[0]
            result = recv_exactly(s, result_size)
            print("\n=== Результат обработки ===")
            print(result.decode('utf-8'))

        elif prefix.startswith(b"ERR"):
            rest = s.recv(1024)
            full_error = (prefix + rest).decode('utf-8', errors='replace')
            print("Сервер вернул ошибку:", full_error)

        else:
            print("Некорректный ответ от сервера:", repr(prefix))


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Использование: python client.py <путь_к_роверу.obs> <путь_к_базе.obs>")
        sys.exit(1)
    send_rinex('localhost', 9999, sys.argv[1], sys.argv[2])
