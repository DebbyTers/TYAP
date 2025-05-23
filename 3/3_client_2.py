import socket
import os
from datetime import datetime

CONFIG_FILE = 'tcp_config.txt'
DEFAULT_IP = '127.0.0.1'
DEFAULT_PORT = 5005


def encode_text(text):
    """Кодирование текста с поддержкой русского и английского алфавитов"""
    encoded = []
    for char in text:
        # Пробел
        if char == ' ':
            encoded.append('00000000')
        # Английские строчные буквы (a-z)
        elif 'a' <= char <= 'z':
            encoded.append(f'0{ord(char) - ord("a"):07b}')
        # Английские заглавные буквы (A-Z)
        elif 'A' <= char <= 'Z':
            encoded.append(f'1{ord(char) - ord("A"):07b}')
        # Русские строчные буквы (а-я)
        elif 'а' <= char <= 'я':
            encoded.append(f'2{ord(char) - ord("а"):07b}')
        # Русские заглавные буквы (А-Я)
        elif 'А' <= char <= 'Я':
            encoded.append(f'3{ord(char) - ord("А"):07b}')
        # Буква 'ё' и 'Ё'
        elif char == 'ё':
            encoded.append('21100101')  # Код для 'ё'
        elif char == 'Ё':
            encoded.append('31100101')  # Код для 'Ё'
        # Все остальные символы кодируем как пробел
        else:
            encoded.append('00000000')
    return ' '.join(encoded)


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
    """Основная функция клиента"""
    ip, port = read_config()

    # Создание файла для логов клиента
    client_file = datetime.now().strftime("%d%m.%Y_%H-%M-%S") + "_client.txt"

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((ip, port))
            print(f"Подключено к серверу {ip}:{port}")

            while True:
                text = input("Введите текст для отправки (или 'exit' для выхода): ")
                if text.lower() == 'exit':
                    break

                binary_data = encode_text(text)
                print(f"Закодированный текст: {binary_data}")

                s.sendall(binary_data.encode('utf-8'))
                print(f"Отправлено {len(binary_data)} байт")

                # Запись в файл клиента
                with open(client_file, 'a', encoding='utf-8') as f:
                    f.write(f"{datetime.now()}: {binary_data}\n")

        except ConnectionRefusedError:
            print("Не удалось подключиться к серверу")
        except KeyboardInterrupt:
            print("\nКлиент остановлен")


if __name__ == "__main__":
    main()