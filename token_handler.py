import uvicorn
import webbrowser
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import httpx

app = FastAPI()

# Глобальные переменные для обмена данными между потоками
auth_code = None
state = "my_unique_state_123"  # Для защиты от CSRF

@app.get("/")
async def auth():
    # Автоматически перенаправляем на HH
    auth_url = f"https://hh.ru/oauth/authorize?response_type=code&client_id=MI85K2MSM4M9BKE1D7TBBMI358QU9OQJ3ILI2CBJB81SI0K7HL2J6BO3H3TCM4OR&state={state}&redirect_uri=http://localhost:1000/callback"
    return HTMLResponse(f"""
        <html>
            <script>window.location.href = "{auth_url}"</script>
            <body>Перенаправление на авторизацию HH...</body>
        </html>
    """)

@app.get("/callback")
async def callback(request: Request):
    global auth_code
    code = request.query_params.get("code")
    received_state = request.query_params.get("state")
    
    # Проверяем state для безопасности
    if received_state != state:
        return HTMLResponse("Ошибка: неверный state параметр", status_code=400)
    
    if code:
        auth_code = code
        return HTMLResponse("""
            <h2>Авторизация успешна!</h2>
            <p>Вы можете закрыть это окно и вернуться в приложение.</p>
        """)
    return HTMLResponse("Ошибка: код не получен", status_code=400)

async def get_tokens():
    """Получаем токены с помощью httpx"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://hh.ru/oauth/token",
            data={
                'grant_type': 'authorization_code',
                'client_id': 'MI85K2MSM4M9BKE1D7TBBMI358QU9OQJ3ILI2CBJB81SI0K7HL2J6BO3H3TCM4OR',
                'client_secret': 'V0IHK8VT0KGU14BDV742ITMGS65ISHUEUO0V8TV09R63NFU4294A25SUNKFLAQR1',
                'code': auth_code,
                'redirect_uri': 'http://localhost:1000/callback'
            }
        )
        return response.json()

async def main():
    # Запускаем сервер в фоне
    config = uvicorn.Config(app, host="127.0.0.1", port=1000, log_level="error")
    server = uvicorn.Server(config)
    
    # Открываем браузер
    webbrowser.open('http://localhost:1000')
    
    print("Открыта страница авторизации HH...")
    print("Ожидаем, пока вы авторизуетесь...")
    
    # Ждем получения кода
    while auth_code is None:
        await asyncio.sleep(1)
    
    # Получаем токены
    tokens = await get_tokens()
    
    # Останавливаем сервер
    server.should_exit = True
    
    return tokens

if __name__ == "__main__":
    tokens = asyncio.run(main())
    print("Токены получены:", tokens)