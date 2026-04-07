import io
import tkinter as tk
from ftplib import FTP, error_perm
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


def decode_text(data: bytes) -> str:
    for encoding in ("utf-8", "cp1251", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def connect_to_ftp(host: str, port: int, username: str, password: str) -> FTP:
    ftp = FTP()
    ftp.connect(host, port, timeout=10)
    ftp.login(username, password)
    return ftp


def list_entries(ftp: FTP) -> list[dict]:
    try:
        items = list(ftp.mlsd())
        return [{"name": name, "type": facts.get("type", "file")} for name, facts in items]
    except error_perm:
        return [{"name": name, "type": "file"} for name in ftp.nlst()]


def upload_text_file(ftp: FTP, remote_name: str, content: str) -> None:
    ftp.storbinary(f"STOR {remote_name}", io.BytesIO(content.encode("utf-8")))


def retrieve_file_bytes(ftp: FTP, remote_name: str) -> bytes:
    chunks: list[bytes] = []
    ftp.retrbinary(f"RETR {remote_name}", chunks.append)
    return b"".join(chunks)


def download_remote_file(ftp: FTP, remote_name: str, local_path: str) -> None:
    with open(local_path, "wb") as file:
        ftp.retrbinary(f"RETR {remote_name}", file.write)


class FileEditor(tk.Toplevel):
    def __init__(self, master, title: str, initial_name: str, initial_text: str, on_save):
        super().__init__(master)
        self.title(title)
        self.geometry("700x500")
        self.on_save = on_save

        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        ttk.Label(self, text="Имя файла:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.name_var = tk.StringVar(value=initial_name)
        ttk.Entry(self, textvariable=self.name_var).grid(
            row=0, column=1, padx=10, pady=10, sticky="ew"
        )

        self.text = tk.Text(self, wrap="word")
        self.text.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.text.insert("1.0", initial_text)

        buttons = ttk.Frame(self)
        buttons.grid(row=2, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="e")
        ttk.Button(buttons, text="Сохранить", command=self.save).pack(side="left", padx=5)
        ttk.Button(buttons, text="Отмена", command=self.destroy).pack(side="left")

        self.transient(master)
        self.grab_set()
        self.focus()

    def save(self):
        filename = self.name_var.get().strip()
        if not filename:
            messagebox.showerror("Ошибка", "Укажите имя файла.", parent=self)
            return
        self.on_save(filename, self.text.get("1.0", "end-1c"))
        self.destroy()


class FTPGuiClient(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GUI FTP Client")
        self.geometry("1000x650")

        self.ftp: FTP | None = None
        self.entries: list[dict] = []

        self.host_var = tk.StringVar(value="127.0.0.1")
        self.port_var = tk.StringVar(value="21")
        self.user_var = tk.StringVar(value="TestUser")
        self.password_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Нет подключения")
        self.path_var = tk.StringVar(value="/")

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        connection = ttk.LabelFrame(self, text="Подключение")
        connection.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        for column in range(9):
            connection.columnconfigure(column, weight=1 if column in (1, 3, 5, 7) else 0)

        ttk.Label(connection, text="Хост").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(connection, textvariable=self.host_var).grid(
            row=0, column=1, padx=5, pady=5, sticky="ew"
        )
        ttk.Label(connection, text="Порт").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        ttk.Entry(connection, textvariable=self.port_var, width=8).grid(
            row=0, column=3, padx=5, pady=5, sticky="ew"
        )
        ttk.Label(connection, text="Логин").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        ttk.Entry(connection, textvariable=self.user_var).grid(
            row=0, column=5, padx=5, pady=5, sticky="ew"
        )
        ttk.Label(connection, text="Пароль").grid(row=0, column=6, padx=5, pady=5, sticky="w")
        ttk.Entry(connection, textvariable=self.password_var, show="*").grid(
            row=0, column=7, padx=5, pady=5, sticky="ew"
        )
        ttk.Button(connection, text="Подключиться", command=self.connect).grid(
            row=0, column=8, padx=5, pady=5
        )

        toolbar = ttk.Frame(self)
        toolbar.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        ttk.Label(toolbar, text="Текущая директория:").pack(side="left")
        ttk.Label(toolbar, textvariable=self.path_var).pack(side="left", padx=(5, 20))
        ttk.Button(toolbar, text="Обновить", command=self.refresh_list).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Открыть", command=self.retrieve_file).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Создать", command=self.create_file).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Обновить файл", command=self.update_file).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Удалить", command=self.delete_file).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Скачать", command=self.download_file).pack(side="left", padx=2)

        content = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        content.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="nsew")

        left = ttk.Frame(content)
        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)
        self.files_list = tk.Listbox(left)
        self.files_list.grid(row=0, column=0, sticky="nsew")
        self.files_list.bind("<Double-Button-1>", lambda _event: self.open_selected())
        scrollbar = ttk.Scrollbar(left, orient="vertical", command=self.files_list.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.files_list.configure(yscrollcommand=scrollbar.set)
        content.add(left, weight=1)

        right = ttk.Frame(content)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)
        ttk.Label(right, text="Содержимое файла").grid(row=0, column=0, sticky="w")
        self.preview = tk.Text(right, wrap="word")
        self.preview.grid(row=1, column=0, sticky="nsew")
        content.add(right, weight=2)

        status = ttk.Label(self, textvariable=self.status_var, relief="sunken", anchor="w")
        status.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="ew")

    def set_status(self, text: str):
        self.status_var.set(text)

    def ensure_connection(self) -> FTP:
        if self.ftp is None:
            raise RuntimeError("Сначала подключитесь к серверу.")
        return self.ftp

    def connect(self):
        self.disconnect()
        try:
            ftp = connect_to_ftp(
                self.host_var.get().strip(),
                int(self.port_var.get().strip()),
                self.user_var.get().strip(),
                self.password_var.get(),
            )
            self.ftp = ftp
            self.path_var.set(ftp.pwd())
            self.set_status(f"Подключено к {self.host_var.get().strip()}:{self.port_var.get().strip()}")
            self.refresh_list()
        except Exception as error:
            self.disconnect()
            messagebox.showerror("Ошибка подключения", str(error), parent=self)
            self.set_status("Ошибка подключения")

    def disconnect(self):
        if self.ftp is not None:
            try:
                self.ftp.quit()
            except Exception:
                pass
        self.ftp = None

    def refresh_list(self):
        ftp = self.ensure_connection()
        self.entries.clear()
        self.files_list.delete(0, tk.END)
        self.preview.delete("1.0", tk.END)
        self.entries = list_entries(ftp)
        for entry in self.entries:
            display = f"[DIR] {entry['name']}" if entry["type"] == "dir" else entry["name"]
            self.files_list.insert(tk.END, display)
        self.path_var.set(ftp.pwd())
        self.set_status("Список файлов обновлён")

    def get_selected_entry(self) -> dict:
        selection = self.files_list.curselection()
        if not selection:
            raise RuntimeError("Выберите файл или директорию.")
        return self.entries[selection[0]]

    def retrieve_bytes(self, remote_name: str) -> bytes:
        ftp = self.ensure_connection()
        return retrieve_file_bytes(ftp, remote_name)

    def retrieve_file(self):
        entry = self.get_selected_entry()
        if entry["type"] == "dir":
            messagebox.showinfo("Информация", "Открытие директорий не поддержано.", parent=self)
            return
        try:
            data = self.retrieve_bytes(entry["name"])
            self.preview.delete("1.0", tk.END)
            self.preview.insert("1.0", decode_text(data))
            self.set_status(f"Файл {entry['name']} открыт")
        except Exception as error:
            messagebox.showerror("Ошибка", str(error), parent=self)

    def open_selected(self):
        try:
            entry = self.get_selected_entry()
            if entry["type"] == "dir":
                ftp = self.ensure_connection()
                ftp.cwd(entry["name"])
                self.refresh_list()
                return
            self.retrieve_file()
        except Exception as error:
            messagebox.showerror("Ошибка", str(error), parent=self)

    def save_remote_file(self, filename: str, content: str):
        ftp = self.ensure_connection()
        upload_text_file(ftp, filename, content)
        self.refresh_list()
        self.preview.delete("1.0", tk.END)
        self.preview.insert("1.0", content)
        self.set_status(f"Файл {filename} сохранён")

    def create_file(self):
        FileEditor(self, "Создание файла", "", "", self.save_remote_file)

    def update_file(self):
        try:
            entry = self.get_selected_entry()
            if entry["type"] == "dir":
                messagebox.showinfo("Информация", "Обновление директорий не поддержано.", parent=self)
                return
            content = decode_text(self.retrieve_bytes(entry["name"]))
            FileEditor(self, "Редактирование файла", entry["name"], content, self.save_remote_file)
        except Exception as error:
            messagebox.showerror("Ошибка", str(error), parent=self)

    def delete_file(self):
        try:
            entry = self.get_selected_entry()
            ftp = self.ensure_connection()
            if entry["type"] == "dir":
                ftp.rmd(entry["name"])
            else:
                ftp.delete(entry["name"])
            self.refresh_list()
            self.set_status(f"{entry['name']} удалён")
        except Exception as error:
            messagebox.showerror("Ошибка", str(error), parent=self)

    def download_file(self):
        try:
            entry = self.get_selected_entry()
            if entry["type"] == "dir":
                messagebox.showinfo("Информация", "Скачивание директорий не поддержано.", parent=self)
                return
            target_path = filedialog.asksaveasfilename(
                parent=self, initialfile=Path(entry["name"]).name
            )
            if not target_path:
                return
            download_remote_file(self.ensure_connection(), entry["name"], target_path)
            self.set_status(f"Файл {entry['name']} скачан в {target_path}")
        except Exception as error:
            messagebox.showerror("Ошибка", str(error), parent=self)

    def on_close(self):
        self.disconnect()
        self.destroy()


def main():
    app = FTPGuiClient()
    app.mainloop()


if __name__ == "__main__":
    main()
