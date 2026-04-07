from ftplib import FTP, error_perm
import os


def connect_ftp():
    host = input("FTP host: ").strip()
    port = int(input("FTP port: ").strip())
    username = input("Username: ").strip()
    password = input("Password: ").strip()

    ftp = FTP()
    ftp.connect(host, port, timeout=10)
    ftp.login(username, password)

    print(f"\nподключение к {host}:{port}")
    print(f"Текущая директория на сервере: {ftp.pwd()}\n")
    return ftp


def list_files(ftp: FTP):
    print("\nСписок файлов и директорий на сервере:\n")
    try:
        ftp.retrlines("LIST")
    except Exception as e:
        print(f"Ошибка: {e}")
    print()


def upload_file(ftp: FTP):
    local_path = input("Введите путь к локальному файлу для загрузки: ").strip()

    if not os.path.isfile(local_path):
        print("файл не найден\n")
        return

    remote_name = input("Введите имя файла на сервере : ").strip()
    if not remote_name:
        remote_name = os.path.basename(local_path)

    try:
        with open(local_path, "rb") as file:
            ftp.storbinary(f"STOR {remote_name}", file)
        print(f"Файл '{local_path}' загружен как '{remote_name}'.\n")
    except Exception as e:
        print(f"Ошибка: {e}\n")


def download_file(ftp: FTP):
    remote_name = input("Введите имя файла на сервере для скачивания: ").strip()
    local_path = input("Введите путь для сохранения файла локально: ").strip()

    try:
        with open(local_path, "wb") as file:
            ftp.retrbinary(f"RETR {remote_name}", file.write)
        print(f"Файл '{remote_name}' скачан в '{local_path}'.\n")
    except Exception as e:
        print(f"Ошибка: {e}\n")


def main():
    ftp = None

    try:
        ftp = connect_ftp()

        while True:
            print("Действия:")
            print("1 - Получать список всех директорий и файлов сервера и выводить его на консоль")
            print("2 - Загружать новый файл на сервер")
            print("3 - Загружать файл с сервера и сохранять его локально")
            print("4 - Выход")

            choice = input("Действие: ").strip()

            if choice == "1":
                list_files(ftp)
            elif choice == "2":
                upload_file(ftp)
            elif choice == "3":
                download_file(ftp)
            elif choice == "4":
                print("Выход")
                break

    except Exception as e:
        print(f"Ошибка: {e}")

    finally:
        if ftp is not None:
            try:
                ftp.quit()
            except Exception:
                pass


if __name__ == "__main__":
    main()
