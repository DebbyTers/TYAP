import socket
import os
from datetime import datetime
import atexit

# Конфигурация
CONFIG_FILE = '../udp_config.txt'
DEFAULT_IP = '127.0.0.1'
DEFAULT_PORT = 5005
BUFFER_SIZE = 1024
created_files = []


# Регистрируем функцию очистки при выходе
def cleanup():
    """Удаление всех созданных файлов при завершении программы"""
    for filepath in created_files:
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"Удалён файл: {filepath}")
        except Exception as e:
            print(f"Ошибка при удалении файла {filepath}: {e}")


atexit.register(cleanup)


def encode_text(text):
    """Улучшенное кодирование текста с поддержкой русского и английского алфавитов"""
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


def save_to_file(binary_data, is_receiver=False):
    """Сохранение данных в файл с добавлением файла в список для последующего удаления"""
    timestamp = datetime.now().strftime("%Y_%H-%M-%S")
    prefix = "receive" if is_receiver else "send"
    filename = f"{prefix}_{timestamp}.bit"

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(binary_data)

    created_files.append(filename)
    print(f"Сохранено в файл: {filename}")


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


def sender():
    """Режим отправителя"""
    ip, port = read_config()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        while True:
            text = input("Введите текст для отправки (или 'exit' для выхода): ")
            if text.lower() == 'exit':
                break

            binary_data = encode_text(text)
            print(f"Закодированный текст: {binary_data}")

            sock.sendto(binary_data.encode('utf-8'), (ip, port))
            print(f"Отправлено {len(binary_data)} байт на {ip}:{port}")

            save_to_file(binary_data)
    finally:
        sock.close()


def receiver():
    """Режим получателя"""
    ip, port = read_config()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((ip, port))
    print(f"Ожидание сообщений на {ip}:{port}")

    try:
        while True:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            binary_data = data.decode('utf-8')
            print(f"\nПолучено {len(binary_data)} байт от {addr}")
            print(f"Двоичные данные: {binary_data}")

            decoded_text = decode_text(binary_data)
            print(f"Декодированный текст: {decoded_text}")

            save_to_file(binary_data, is_receiver=True)
    finally:
        sock.close()


def main():
    """Основная функция"""
    print("1. Отправитель")
    print("2. Получатель")
    choice = input("Выберите режим: ")

    if choice == '1':
        sender()
    elif choice == '2':
        receiver()
    else:
        print("Неверный выбор")


if __name__ == "__main__":
    main()