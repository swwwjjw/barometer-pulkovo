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
MAX_PAGES = 20
# Параметры запроса к hh.ru
AREA = 2
PER_PAGE = 99  # Если указать 100, то будет 400 Bad request, 
              # т.к. API hh.ru поддерживает возврат до 2000 значений
PROFESSIONAL_ROLE = [[31, 52], [156, 150, 10], [165, 96], [63], 
                     [81], [128, 86], [70], [15, 24, 64], [111, 173, 44, 46], 
                     [130], [89], [89], [64], [114], [131, 81, 52], [90, 120], 
                     [111, 144], [90, 120, 95]]

app = FastAPI()

def save_vacancies_to_file(data: list):
    # Сохраняет полученные данные в .txt файл в /final_folder
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"vacancies_{timestamp}.txt"
    filepath = os.path.join(OUTPUT_FOLDER, filename)
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            # Преобразуем данные в JSON Lines формат с разделителями
            for i, block in enumerate(data):
                if i > 0:
                    f.write("---\n")  # Разделитель между блоками
                
                for item in block["items"]:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")
        
        print(f"[{datetime.now()}] Данные сохранены в {filepath}.")
        print(f"[{datetime.now()}] Всего блоков: {len(data)}, вакансий: {sum(len(block['items']) for block in data)}")
    except Exception as e:
        print(f"[{datetime.now()}] Ошибка сохранения данных: {e}.")

async def fetch_vacancies():
    # Получает данные с API hh.ru
    print(f"[{datetime.now()}] Получение данных из {API_URL}...")
    
    all_blocks = []  # Список блоков данных (каждый блок - для одной группы ролей)

    async with httpx.AsyncClient() as client:
        for vacancy_roles in PROFESSIONAL_ROLE:
            print(f"[{datetime.now()}] Обработка ролей: {vacancy_roles}")
            
            block_items = []  # Вакансии для текущего блока (одной группы ролей)
            
            for page in range(0, MAX_PAGES):
                try:
                    params = [
                        ("area", AREA),
                        ("per_page", PER_PAGE),
                        ("page", page)
                    ]
                    for role_id in vacancy_roles:
                        params.append(("professional_role", role_id))

                    await asyncio.sleep(30)

                    response = await client.get(API_URL, params=params)
                    response.raise_for_status()
                    data = response.json()

                    items = data.get("items", [])
                    block_items.extend(items)
                    
                    # Если получено меньше вакансий, чем PER_PAGE, значит это последняя страница
                    if len(items) < PER_PAGE:
                        print(f"[{datetime.now()}] Получено {len(items)} вакансий на странице {page}. Завершение пагинации.")
                        break
                        
                except httpx.HTTPError as e:
                    print(f"[{datetime.now()}] Ошибка HTTP: {e}.")
                    break
                except Exception as e:
                    print(f"[{datetime.now()}] Ошибка получения данных: {e}.")
                    break
            
            # Добавляем блок с метаданными
            if block_items:
                all_blocks.append({
                    "roles": vacancy_roles,
                    "items": block_items,
                    "count": len(block_items)
                })
                print(f"[{datetime.now()}] Собрано {len(block_items)} вакансий для ролей {vacancy_roles}")
            else:
                print(f"[{datetime.now()}] Не найдено вакансий для ролей {vacancy_roles}")

    if all_blocks:
        save_vacancies_to_file(all_blocks)
    else:
        print(f"[{datetime.now()}] Данные не были получены.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Запускает получение вакансий каждые INTERVAL_HOURS часов
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        fetch_vacancies,
        trigger=IntervalTrigger(hours=INTERVAL_HOURS),
        id="fetch_vacancies_job",
        name="Fetch vacancies every 12 hours",
        replace_existing=True,
    )
    scheduler.start()
    print(f"[{datetime.now()}] Менеджер запущен. Данные собираются каждые {INTERVAL_HOURS} часов.")

    asyncio.create_task(fetch_vacancies())
    
    yield
    
    scheduler.shutdown()
    print(f"[{datetime.now()}] Менеджер остановлен.")

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "Приложение работает."}

@app.get("/status")
async def status():
    return {
        "status": "running",
        "next_run": "every 12 hours",
        "output_folder": OUTPUT_FOLDER,
        "professional_roles_blocks": len(PROFESSIONAL_ROLE)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=1000, reload=True)