import socket
import threading
import json
import mysql.connector

# Настройки подключения к базе данных
db_connection = mysql.connector.connect(
    host="f1.aurorix.net",  # IP вашего MySQL сервера
    user="u69898_aPM7nxNveE",  # Имя пользователя
    password="vV!85o!PjSZ.iFSShQVzbSaG",  # Пароль
    database="s69898_main"  # Имя базы данных
)
cursor = db_connection.cursor()

# Функция для создания таблицы, если она не существует
def create_tables():
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS servers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            host VARCHAR(255) NOT NULL,
            port INT NOT NULL
        );
        """)
        db_connection.commit()
        print("Таблицы успешно созданы или уже существуют.")
    except mysql.connector.Error as err:
        print(f"Ошибка при создании таблиц: {err}")

# Хранилище серверов
server_list = [
    {"name": "Резервный сервер 1", "host": "18.184.231.68", "port": 58264}
]

# Блокировка для потокобезопасности
lock = threading.Lock()

# Функция для регистрации пользователя
def register_user(username, password):
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    if cursor.fetchone():
        return False  # Пользователь уже существует
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
    db_connection.commit()
    return True

# Функция для входа пользователя
def login_user(username, password):
    cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
    if cursor.fetchone():
        return True
    return False

# Функция для получения списка серверов
def handle_client(client_socket):
    try:
        request = client_socket.recv(4096).decode('utf-8')
        data = json.loads(request)

        if data["action"] == "get_servers":
            with lock:
                response = {"status": "success", "servers": server_list}
            client_socket.sendall(json.dumps(response).encode('utf-8'))

        elif data["action"] == "register":
            username = data["username"]
            password = data["password"]
            success = register_user(username, password)
            if success:
                response = {"status": "success", "message": "Регистрация успешна!"}
            else:
                response = {"status": "error", "message": "Пользователь уже существует!"}
            client_socket.sendall(json.dumps(response).encode('utf-8'))

        elif data["action"] == "login":
            username = data["username"]
            password = data["password"]
            success = login_user(username, password)
            if success:
                response = {"status": "success", "message": "Вход успешен!"}
            else:
                response = {"status": "error", "message": "Неверный логин или пароль"}
            client_socket.sendall(json.dumps(response).encode('utf-8'))

    except Exception as e:
        print(f"Ошибка обработки клиента: {e}")
        client_socket.sendall(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
    finally:
        client_socket.close()

def start_server():
    """Запускает сервер."""
    create_tables()  # Создаем таблицы при запуске
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 28468))
    server.listen(5)
    print("Основной сервер запущен. Ожидание клиентов...")

    while True:
        client_socket, addr = server.accept()
        print(f"Подключен клиент: {addr}")
        client_thread = threading.Thread(target=handle_client, args=(client_socket,))
        client_thread.start()

if __name__ == "__main__":
    start_server()
