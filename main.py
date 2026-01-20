import os
import json
import asyncio
from datetime import datetime
from fastapi import FastAPI
import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from contextlib import asynccontextmanager

# Настройки
API_URL = "https://api.hh.ru/vacancies"
OUTPUT_FOLDER = "final_folder"
INTERVAL_HOURS = 12
# Параметры запроса к  hh.ru
AREA = 2
PER_PAGE = 2000
PROFESSIONAL_ROLE = [[31, 52], [156, 150, 10], [165, 96], [63], [81], [128, 86], [70], [15, 24, 64], [111, 173, 44, 46], [130], [89], [89], [64], [114], [131, 81, 52], [90, 120], [111, 144], [90, 120, 95]]

app = FastAPI()

def save_vacancies_to_file(data: dict):
    # Сохраняет полученные данные в .txt файл в /final_folder
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"vacancies_{timestamp}.txt"
    filepath = os.path.join(OUTPUT_FOLDER, filename)
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"[{datetime.now()}] Данные сохранены в {filepath}")
    except Exception as e:
        print(f"[{datetime.now()}] Ошибка сохранения данных: {e}")

async def fetch_vacancies():
    # Получает данные с API hh.ru
    print(f"[{datetime.now()}] Получение данных из {API_URL}...")
    
    all_items = []

    async with httpx.AsyncClient() as client:
        for vacancy_roles in PROFESSIONAL_ROLE:
            try:
                params = [
                    ("area", AREA),
                    ("per_page", PER_PAGE),
                ]
                for role_id in vacancy_roles:
                    params.append(("professional_role", role_id))
                response = await client.get(API_URL, params=params)
                response.raise_for_status()
                data = response.json()

                items = data.get("items", [])
                all_items.extend(items)
                    
            except httpx.HTTPError as e:
                print(f"[{datetime.now()}] Ошибка HTTP: {e}")
            except Exception as e:
                print(f"[{datetime.now()}] Ошибка получения данных: {e}")

    if all_items:
        save_vacancies_to_file({"items": all_items, "meta": {"total_fetched": len(all_items)}})
    else:
        print(f"[{datetime.now()}] Данные не были получены")

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        fetch_vacancies,
        trigger=IntervalTrigger(hours=INTERVAL_HOURS),
        id="fetch_vacancies_job",
        name="Fetch vacancies every 12 hours",
        replace_existing=True,
    )
    scheduler.start()
    print(f"[{datetime.now()}] Менеджер запущен. Данные собираются каждые {INTERVAL_HOURS} часов")

    asyncio.create_task(fetch_vacancies())
    
    yield
    
    scheduler.shutdown()
    print(f"[{datetime.now()}] Менеджер остановлен")

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "Приложение работает"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=1000, reload=True)
