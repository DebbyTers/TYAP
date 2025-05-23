import socket
import os
from datetime import datetime
import threading

CONFIG_FILE = 'tcp_config.txt'
DEFAULT_IP = '127.0.0.1'
DEFAULT_PORT = 5005
BUFFER_SIZE = 1024


def decode_text(binary_str):
    """Декодирование бинарной строки с поддержкой русского и английского алфавитов"""
    binary_list = binary_str.split()
    decoded = []
    for code in binary_list:
        if len(code) != 8:
            decoded.append(' ')
            continue

        prefix = code[0]
        char_code = int(code[1:], 2)

        if code == '00000000':
            decoded.append(' ')
        elif prefix == '0':  # Английская строчная
            decoded.append(chr(char_code + ord('a')))
        elif prefix == '1':  # Английская заглавная
            decoded.append(chr(char_code + ord('A')).upper())
        elif prefix == '2':  # Русская строчная
            if code == '21100101':  # Специальный код для 'ё'
                decoded.append('ё')
            else:
                decoded.append(chr(char_code + ord('а')))
        elif prefix == '3':  # Русская заглавная
            if code == '31100101':  # Специальный код для 'Ё'
                decoded.append('Ё')
            else:
                decoded.append(chr(char_code + ord('А')).upper())
        else:
            decoded.append(' ')
    return ''.join(decoded)


def handle_client(conn, addr, server_file):
    """Обработка подключения клиента"""
    try:
        with conn:
            print(f"Подключен клиент: {addr}")
            while True:
                data = conn.recv(BUFFER_SIZE)
                if not data:
                    break

                binary_data = data.decode('utf-8')
                decoded_text = decode_text(binary_data)

                print(f"\nСообщение от {addr}:")
                print(f"Двоичные данные: {binary_data}")
                print(f"Декодированный текст: {decoded_text}")

                # Запись в файл сервера
                timestamp = datetime.now().strftime("%d%m.%Y_%H-%M-%S")
                with open(server_file, 'a', encoding='utf-8') as f:
                    f.write(f"{timestamp} {addr}: {binary_data}\n")
    finally:
        print(f"Клиент отключен: {addr}")


def read_config():
    """Чтение конфигурационного файла"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            ip = lines[0].strip() if len(lines) > 0 else DEFAULT_IP
            port = int(lines[1].strip()) if len(lines) > 1 else DEFAULT_PORT
            return ip, port
    except (FileNotFoundError, ValueError):
        return DEFAULT_IP, DEFAULT_PORT


def main():
    """Основная функция сервера"""
    ip, port = read_config()

    # Создание файла для логов сервера
    server_file = datetime.now().strftime("%d%m.%Y_%H-%M-%S") + "_server.txt"
    with open(server_file, 'w', encoding='utf-8') as f:
        f.write(f"Сервер запущен {datetime.now()}\n")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((ip, port))
        s.listen()
        print(f"Сервер запущен на {ip}:{port}")

        try:
            while True:
                conn, addr = s.accept()
                client_thread = threading.Thread(
                    target=handle_client,
                    args=(conn, addr, server_file)
                )
                client_thread.start()
        except KeyboardInterrupt:
            print("\nСервер остановлен")


if __name__ == "__main__":
    main()