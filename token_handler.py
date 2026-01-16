import requests
from flask import Flask, request
import threading
import webbrowser

app = Flask(__name__)

# Глобальная переменная для хранения кода
auth_code = None

@app.route('/')
def callback():
    global auth_code
    auth_code = request.args.get('code')
    return "Авторизация успешна! Вы можете закрыть это окно."

def run_server():
    app.run(port=1000)

# Запускаем сервер в отдельном потоке
server_thread = threading.Thread(target=run_server)
server_thread.daemon = True
server_thread.start()

# Даем серверу время запуститься
import time
time.sleep(1)

# Формируем ссылку с redirect_uri на localhost
HH_CLIENT_ID = 'MI85K2MSM4M9BKE1D7TBBMI358QU9OQJ3ILI2CBJB81SI0K7HL2J6BO3H3TCM4OR'
redirect_uri = 'http://localhost:1000'
auth_url = f"https://hh.ru/oauth/authorize?response_type=code&client_id=&redirect_uri={redirect_uri}"

# Открываем браузер автоматически
webbrowser.open(auth_url)

# Ждем, пока пользователь авторизуется и мы получим код
print("Ждем авторизации...")
while auth_code is None:
    time.sleep(1)

# Теперь у нас есть auth_code, получаем токен
client_secret = 'V0IHK8VT0KGU14BDV742ITMGS65ISHUEUO0V8TV09R63NFU4294A25SUNKFLAQR1'
url = "https://hh.ru/oauth/token"
body = {
    'grant_type': 'authorization_code',
    'client_id': HH_CLIENT_ID,
    'client_secret': client_secret,
    'code': auth_code,
    'redirect_uri': redirect_uri
}

response = requests.post(url, data=body)
tokens = response.json()

print("Токен получен!")
print(tokens)