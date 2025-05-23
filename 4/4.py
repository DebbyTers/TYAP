import socket
import pickle
import os
from datetime import datetime
import struct


class UDPMessage:
    """Класс для работы с сообщениями"""

    def __init__(self, is_check=False, message=""):
        self.isCheck = is_check
        self.message = message.encode('utf-8')
        self.length = len(self.message)

    def pack(self):
        """Упаковка сообщения в байты"""
        # Формат: ? (булев), I (целое), s (байты)
        return struct.pack(f'?I{self.length}s', self.isCheck, self.length, self.message)

    @classmethod
    def unpack(cls, data):
        """Распаковка сообщения из байтов"""
        # Сначала читаем isCheck и length
        is_check, length = struct.unpack('?I', data[:5])
        # Затем читаем сообщение
        message = struct.unpack(f'{length}s', data[5:5 + length])[0]
        return cls(is_check, message.decode('utf-8'))


def save_to_file(data, is_receiver=False):
    """Сохранение данных в файл"""
    timestamp = datetime.now().strftime("%d%m.%Y_%H-%M-%S")
    prefix = "receive" if is_receiver else "send"
    filename = f"{prefix}_{timestamp}.txt"

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(data)

    print(f"Сохранено в файл: {filename}")


def encode_text(text):
    """Кодирование текста"""
    encoded = []
    for char in text:
        if char == ' ':
            encoded.append('00000')
        elif char.isupper():
            encoded.append(f'1{ord(char.lower()) - ord("a"):04b}')
        elif char.islower():
            encoded.append(f'0{ord(char) - ord("a"):04b}')
        else:
            encoded.append('00000')
    return ' '.join(encoded)


def decode_text(binary_str):
    """Декодирование текста"""
    binary_list = binary_str.split()
    decoded = []
    for code in binary_list:
        if code == '00000':
            decoded.append(' ')
        elif len(code) == 5:
            case_bit = code[0]
            char_code = int(code[1:], 2)
            if 0 <= char_code <= 25:
                char = chr(char_code + ord('a'))
                if case_bit == '1':
                    char = char.upper()
                decoded.append(char)
            else:
                decoded.append(' ')
        else:
            decoded.append(' ')
    return ''.join(decoded)


def sender(sock, ip, port):
    """Функция отправителя"""
    while True:
        print("\n1. Отправить обычное сообщение")
        print("2. Отправить сообщение для проверки")
        print("3. Выход")
        choice = input("Выберите действие: ")

        if choice == '3':
            break

        text = input("Введите текст сообщения: ")

        if choice == '1':
            msg = UDPMessage(False, text)
        elif choice == '2':
            msg = UDPMessage(True, text)
        else:
            print("Неверный выбор")
            continue

        # Отправка сообщения
        sock.sendto(msg.pack(), (ip, port))
        print(f"Отправлено сообщение ({'проверка' if msg.isCheck else 'обычное'}): {text}")

        # Сохранение отправленного сообщения
        save_to_file(text)

        # Если это сообщение для проверки, ждем ответ
        if msg.isCheck:
            data, _ = sock.recvfrom(1024)
            response = UDPMessage.unpack(data)
            print(f"Получен ответ: {response.message}")


def receiver(sock, ip, port):
    """Функция получателя"""
    sock.bind((ip, port))
    print(f"Ожидание сообщений на {ip}:{port}")

    while True:
        data, addr = sock.recvfrom(1024)
        try:
            msg = UDPMessage.unpack(data)

            if msg.isCheck:
                # Отправляем ответ на проверочное сообщение
                response = UDPMessage(False, "Проверка пройдена")
                sock.sendto(response.pack(), addr)
                print(f"Получен запрос проверки от {addr}, отправлен ответ")
            else:
                # Проверка длины сообщения
                if msg.length != len(msg.message):
                    print("Сообщение повреждено")
                    save_to_file(f"Поврежденное сообщение: {msg.message}", True)
                else:
                    # Декодирование и вывод сообщения
                    binary_data = encode_text(msg.message)
                    decoded_text = decode_text(binary_data)

                    print(f"\nПолучено сообщение от {addr}:")
                    print(f"Двоичные данные: {binary_data}")
                    print(f"Декодированный текст: {decoded_text}")

                    save_to_file(msg.message, True)
        except Exception as e:
            print(f"Ошибка обработки сообщения: {e}")


def read_config():
    """Чтение конфигурационного файла"""
    try:
        with open('udp_config.txt', 'r') as f:
            lines = f.readlines()
            ip = lines[0].strip() if len(lines) > 0 else '127.0.0.1'
            port = int(lines[1].strip()) if len(lines) > 1 else 5005
            return ip, port
    except (FileNotFoundError, ValueError):
        return '127.0.0.1', 5005


def main():
    """Основная функция"""
    ip, port = read_config()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    print("1. Отправитель")
    print("2. Получатель")
    choice = input("Выберите режим: ")

    if choice == '1':
        sender(sock, ip, port)
    elif choice == '2':
        receiver(sock, ip, port)
    else:
        print("Неверный выбор")

    sock.close()


if __name__ == "__main__":
    main()