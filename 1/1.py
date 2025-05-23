import tkinter as tk
from tkinter import filedialog, messagebox
import chardet


class EncodingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Кодирование информации")
        self.root.geometry("800x600")

        # Выбор кодировки
        self.encoding_var = tk.StringVar(value="Windows-1251")
        self.encodings = ["Windows-1251", "KOI8-R", "ISO-8859-5", "CP866"]

        # Создание интерфейса
        self.create_widgets()

    def create_widgets(self):
        # Фрейм для выбора кодировки
        encoding_frame = tk.LabelFrame(self.root, text="Выбор кодировки", padx=5, pady=5)
        encoding_frame.pack(fill=tk.X, padx=5, pady=5)

        for i, encoding in enumerate(self.encodings):
            rb = tk.Radiobutton(encoding_frame, text=encoding, variable=self.encoding_var,
                                value=encoding, command=self.update_encoding)
            rb.grid(row=0, column=i, padx=5, pady=5)

        # Фрейм для ввода текста
        input_frame = tk.LabelFrame(self.root, text="Исходный текст", padx=5, pady=5)
        input_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.input_text = tk.Text(input_frame, height=10)
        self.input_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Фрейм для кнопок
        button_frame = tk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        self.encode_btn = tk.Button(button_frame, text="Закодировать", command=self.encode_text)
        self.encode_btn.pack(side=tk.LEFT, padx=5)

        self.decode_btn = tk.Button(button_frame, text="Декодировать", command=self.decode_text)
        self.decode_btn.pack(side=tk.LEFT, padx=5)

        # Фрейм для вывода результата
        output_frame = tk.LabelFrame(self.root, text="Результат", padx=5, pady=5)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.output_text = tk.Text(output_frame, height=10)
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Фрейм для кнопок сохранения
        save_frame = tk.Frame(self.root)
        save_frame.pack(fill=tk.X, padx=5, pady=5)

        self.save_bin_btn = tk.Button(save_frame, text="Сохранить в бинарный файл", command=self.save_binary)
        self.save_bin_btn.pack(side=tk.LEFT, padx=5)

        self.save_txt_btn = tk.Button(save_frame, text="Сохранить в текстовый файл", command=self.save_text)
        self.save_txt_btn.pack(side=tk.LEFT, padx=5)

        self.load_btn = tk.Button(save_frame, text="Загрузить файл", command=self.load_file)
        self.load_btn.pack(side=tk.LEFT, padx=5)

    def update_encoding(self):
        pass

    def encode_text(self):
        text = self.input_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Ошибка", "Введите текст для кодирования")
            return

        encoding = self.encoding_var.get()
        try:
            # Кодируем текст в выбранную кодировку
            encoded_bytes = text.encode(encoding, errors='replace')

            # Отображаем байты в виде чисел, разделенных пробелами
            byte_values = ' '.join([str(b) for b in encoded_bytes])
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, byte_values)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка кодирования: {str(e)}")

    def decode_text(self):
        text = self.output_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Ошибка", "Введите закодированный текст для декодирования")
            return

        encoding = self.encoding_var.get()
        try:
            # Обрабатываем два формата ввода:
            # 1. Последовательность чисел (209 208 197...)
            # 2. Строка байтов (b'\xd1\xd0\xc5...')

            if text.startswith("b'") or text.startswith('b"'):
                # Это строковое представление байтов
                import ast
                byte_data = ast.literal_eval(text)
            else:
                # Это последовательность чисел
                byte_list = [int(b) for b in text.split()]
                byte_data = bytes(byte_list)

            # Декодируем текст из выбранной кодировки
            decoded_text = byte_data.decode(encoding, errors='replace')
            self.input_text.delete("1.0", tk.END)
            self.input_text.insert(tk.END, decoded_text)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка декодирования: {str(e)}")

    def save_binary(self):
        text = self.output_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Ошибка", "Нет данных для сохранения")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".bin",
            filetypes=[("Бинарные файлы", "*.bin"), ("Все файлы", "*.*")]
        )

        if not file_path:
            return

        try:
            # Обрабатываем два формата ввода, как в decode_text
            if text.startswith("b'") or text.startswith('b"'):
                import ast
                byte_data = ast.literal_eval(text)
            else:
                byte_list = [int(b) for b in text.split()]
                byte_data = bytes(byte_list)

            with open(file_path, 'wb') as f:
                f.write(byte_data)
            messagebox.showinfo("Успех", "Файл успешно сохранен")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка сохранения: {str(e)}")

    def save_text(self):
        text = self.output_text.get("1.0", tk.END)
        if not text.strip():
            messagebox.showwarning("Ошибка", "Нет данных для сохранения")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )

        if not file_path:
            return

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text)
            messagebox.showinfo("Успех", "Файл успешно сохранен")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка сохранения: {str(e)}")

    def load_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Текстовые файлы", "*.txt"), ("Бинарные файлы", "*.bin"), ("Все файлы", "*.*")]
        )

        if not file_path:
            return

        try:
            # Пытаемся определить кодировку для текстовых файлов
            if file_path.endswith('.bin'):
                # Бинарный файл - читаем как есть
                with open(file_path, 'rb') as f:
                    content = f.read()

                # Отображаем байты в виде чисел
                byte_values = ' '.join([str(b) for b in content])
                self.output_text.delete("1.0", tk.END)
                self.output_text.insert(tk.END, byte_values)
            else:
                # Текстовый файл - пытаемся определить кодировку
                with open(file_path, 'rb') as f:
                    raw_data = f.read()
                    result = chardet.detect(raw_data)
                    encoding = result['encoding'] if result['confidence'] > 0.7 else 'utf-8'

                with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                    content = f.read()

                self.input_text.delete("1.0", tk.END)
                self.input_text.insert(tk.END, content)

            messagebox.showinfo("Успех", "Файл успешно загружен")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки файла: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = EncodingApp(root)
    root.mainloop()