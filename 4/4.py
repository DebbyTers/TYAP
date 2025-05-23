import socket
import json
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QWidget, QTextEdit, QPushButton, QLabel, QComboBox,
                             QMessageBox)
from PyQt5.QtCore import QThread, pyqtSignal


class UDPMessage:
    def __init__(self, is_check=False, message=b""):
        self.IsCheck = is_check
        self.Message = message
        self.Length = len(message)

    def to_bytes(self):
        """Сериализация сообщения в байты"""
        data = {
            'IsCheck': self.IsCheck,
            'Length': self.Length,
            'Message': self.Message.decode('utf-8') if not self.IsCheck else ''
        }
        return json.dumps(data).encode('utf-8')

    @staticmethod
    def from_bytes(data):
        """Десериализация сообщения из байтов"""
        try:
            decoded = json.loads(data.decode('utf-8'))
            msg = UDPMessage()
            msg.IsCheck = decoded['IsCheck']
            msg.Length = decoded['Length']
            msg.Message = decoded['Message'].encode('utf-8') if not msg.IsCheck else b""
            return msg
        except:
            return None


class UDPThread(QThread):
    message_received = pyqtSignal(UDPMessage)
    error_occurred = pyqtSignal(str)

    def __init__(self, ip, port):
        super().__init__()
        self.ip = ip
        self.port = port
        self.running = True

    def run(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.ip, self.port))

        while self.running:
            try:
                data, addr = self.sock.recvfrom(4096)
                msg = UDPMessage.from_bytes(data)
                if msg:
                    self.message_received.emit(msg)
                else:
                    self.error_occurred.emit("Невозможно декодировать сообщение")
            except Exception as e:
                self.error_occurred.emit(f"Ошибка приема: {str(e)}")

    def stop(self):
        self.running = False
        if hasattr(self, 'sock'):
            self.sock.close()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UDP Protocol v4")
        self.setGeometry(100, 100, 800, 600)

        # Загрузка конфигурации
        self.load_config()

        # Инициализация UI
        self.init_ui()

        # UDP соединение
        self.udp_thread = UDPThread(self.config['ip'], self.config['port'])
        self.udp_thread.message_received.connect(self.handle_message)
        self.udp_thread.error_occurred.connect(self.show_error)
        self.udp_thread.start()

    def load_config(self):
        """Загрузка конфигурации из файла"""
        try:
            with open('config.json', 'r') as f:
                self.config = json.load(f)
        except:
            # Конфиг по умолчанию
            self.config = {
                'ip': '127.0.0.1',
                'port': 12345
            }
            with open('config.json', 'w') as f:
                json.dump(self.config, f)

    def init_ui(self):
        main_widget = QWidget()
        layout = QVBoxLayout()

        # Меню выбора функций
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Отправить сообщение", "Проверить соединение"])
        layout.addWidget(self.mode_combo)

        # Поле ввода сообщения
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Введите сообщение...")
        layout.addWidget(self.input_text)

        # Кнопки
        btn_layout = QHBoxLayout()
        self.send_btn = QPushButton("Отправить")
        self.send_btn.clicked.connect(self.send_message)
        btn_layout.addWidget(self.send_btn)

        self.clear_btn = QPushButton("Очистить")
        self.clear_btn.clicked.connect(self.clear_fields)
        btn_layout.addWidget(self.clear_btn)
        layout.addLayout(btn_layout)

        # Вывод информации
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(QLabel("Полученные сообщения:"))
        layout.addWidget(self.output_text)

        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

    def send_message(self):
        """Отправка сообщения"""
        try:
            mode = self.mode_combo.currentIndex()
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            if mode == 0:  # Обычное сообщение
                text = self.input_text.toPlainText()
                if not text:
                    QMessageBox.warning(self, "Ошибка", "Введите сообщение")
                    return

                msg = UDPMessage(is_check=False, message=text.encode('utf-8'))
                sock.sendto(msg.to_bytes(), (self.config['ip'], self.config['port']))

                # Логирование отправки
                self.log_message(f"Отправлено: {text}")

            elif mode == 1:  # Проверка соединения
                msg = UDPMessage(is_check=True)
                sock.sendto(msg.to_bytes(), (self.config['ip'], self.config['port']))
                self.log_message("Отправлен запрос проверки соединения")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка отправки: {str(e)}")
        finally:
            sock.close()

    def handle_message(self, msg):
        """Обработка входящего сообщения"""
        if msg.IsCheck:
            # Отправляем ответ на проверку соединения
            try:
                response = UDPMessage(is_check=False, message="Проблем не обнаружено".encode('utf-8'))
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(response.to_bytes(), (self.config['ip'], self.config['port']))
                sock.close()
                self.log_message("Отправлен ответ на проверку соединения")
            except Exception as e:
                self.show_error(f"Ошибка отправки ответа: {str(e)}")
        else:
            # Проверяем длину сообщения
            if msg.Length == len(msg.Message):
                text = msg.Message.decode('utf-8')
                self.output_text.append(f"Получено: {text}")
                self.log_message(f"Получено: {text}")

                # Сохранение в файл
                self.save_to_file(text)
            else:
                self.output_text.append("Сообщение повреждено!")
                self.log_message("Ошибка: получено поврежденное сообщение")

    def log_message(self, message):
        """Логирование в консоль"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def save_to_file(self, message):
        """Сохранение сообщения в файл"""
        filename = datetime.now().strftime("%d.%m.%Y_%H-%M-%S.txt")
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(message)
            self.log_message(f"Сообщение сохранено в {filename}")
        except Exception as e:
            self.show_error(f"Ошибка сохранения файла: {str(e)}")

    def show_error(self, error):
        """Отображение ошибки"""
        QMessageBox.critical(self, "Ошибка", error)
        self.log_message(f"Ошибка: {error}")

    def clear_fields(self):
        """Очистка полей ввода"""
        self.input_text.clear()

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        self.udp_thread.stop()
        self.udp_thread.wait()
        event.accept()


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()