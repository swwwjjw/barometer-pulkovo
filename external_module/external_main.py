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
OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../final_folder")
INTERVAL_HOURS = 12
MAX_PAGES = 20
# Параметры запроса к hh.ru
AREA = 2
PER_PAGE = 99

# Разделили на отдельные роли для группировки
KEYWORDS = [
    'грузчик нагрузки',
    'аналитик данных SQL',
    'машинное обучение',
    'машинист катка',
    'руководитель склада',
    'фельдшер помощь',
    'обслуживание воздушных судов',
    'мойщик посуды',
    'осмотр медицинской',
    'системный виртуализация',
    'склад комплектовщик',
    'кинолог охранник',
    'инженер холодильного',
    'гбр охрана'
]

app = FastAPI()

def save_vacancies_to_file(grouped_data: dict):
    """Сохраняет сгруппированные данные в .txt файл"""
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"vacancies_{timestamp}.txt"
    filepath = os.path.join(OUTPUT_FOLDER, filename)
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(grouped_data, f, ensure_ascii=False, indent=4)
        print(f"[{datetime.now()}] Данные сохранены в {filepath}.")
    except Exception as e:
        print(f"[{datetime.now()}] Ошибка сохранения данных: {e}.")

async def fetch_vacancies():
    """Получает данные с API hh.ru и группирует по ролям"""
    print(f"[{datetime.now()}] Получение данных из {API_URL}...")
    
    # Словарь для хранения сгруппированных данных
    grouped_data = {}
    total_count = 0
    
    async with httpx.AsyncClient() as client:
        for group_index, vacancy_keywords in enumerate(KEYWORDS):
            group_name = f"group_{group_index+1}_keywords_{vacancy_keywords.replace(' ', '_')}"
            print(f"[{datetime.now()}] Обработка группы {group_name}...")
            
            group_items = []
            
            for page in range(0, MAX_PAGES):
                try:
                    params = [
                        ("area", AREA),
                        ("per_page", PER_PAGE),
                        ("page", page),
                        ("text", vacancy_keywords)
                    ]
                    
                    # Ждем между запросами
                    await asyncio.sleep(5)
                    
                    response = await client.get(API_URL, params=params)
                    response.raise_for_status()
                    data = response.json()
                    
                    items = data.get("items", [])
                    
                    # Добавляем вакансии в группу
                    for item in items:
                        # Добавляем информацию о группе ролей в каждую вакансию
                        item["_group_keywords"] = vacancy_keywords
                        item["_group_name"] = group_name
                    
                    group_items.extend(items)
                    
                    # Если вакансий меньше, чем запрошено, значит страницы закончились
                    if len(items) < PER_PAGE:
                        break
                        
                except httpx.HTTPError as e:
                    print(f"[{datetime.now()}] Ошибка HTTP в группе {group_name}, страница {page}: {e}.")
                    break
                except Exception as e:
                    print(f"[{datetime.now()}] Ошибка получения данных в группе {group_name}, страница {page}: {e}.")
                    break
            
            # Сохраняем группу в общий словарь
            grouped_data[group_name] = {
                "keywords": vacancy_keywords,
                "vacancies": group_items,
                "count": len(group_items)
            }
            
            total_count += len(group_items)
            
            print(f"[{datetime.now()}] Группа {group_name} обработана, найдено {len(group_items)} вакансий.")
    
    if grouped_data:
        # Добавляем общую информацию
        result_data = {
            "metadata": {
                "fetched_at": datetime.now().isoformat(),
                "total_vacancies": total_count,
                "total_groups": len(grouped_data)
            },
            "groups": grouped_data
        }
        
        save_vacancies_to_file(result_data)
    else:
        print(f"[{datetime.now()}] Данные не были получены.")

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
    print(f"[{datetime.now()}] Менеджер запущен. Данные собираются каждые {INTERVAL_HOURS} часов.")

    asyncio.create_task(fetch_vacancies())
    
    yield
    
    scheduler.shutdown()
    print(f"[{datetime.now()}] Менеджер остановлен.")

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "Приложение работает."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("external_main:app", host="0.0.0.0", port=5000, reload=True)