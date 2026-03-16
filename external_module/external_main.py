import os
import json
import asyncio
from datetime import datetime
import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Настройки для работы с файловой системой
OUTPUT_FOLDER = "/mnt/bi_sandbox/barometer_vacancies"
# OUTPUT_FOLDER = "/mnt/allshare_fileserver/barometer_vacancies"
CURRENT_FILE = "vacancies_current.txt"

# Настройки для работы с API
API_URL = "https://api.hh.ru/vacancies"
INTERVAL_HOURS = 12
MAX_PAGES = 20
AREA = 2
PER_PAGE = 99
KEYWORDS = [
    'грузчик нагрузки',
    'аналитик данных SQL',
    'ml engineer',
    'машинист катка',
    'руководитель склада OR NAME:(инженер склада)',
    'фельдшер помощь',
    'обслуживание воздушных судов',
    'уборщик самолетов',
    'осмотр медицинской',
    'системный виртуализация',
    'склад комплектовщик',
    'кинолог',
    'инженер холодильного',
    'гбр охрана',
    'бариста выпечка',
    'отчетность пекарня',
    'закупки булочная',
    'управляющий кафе',
    'товаровед кладовщик',
    'тракторист снег',
    'регистрация пассажиров',
    'обслуживание в бизнес-залах',
    'официант сервировка',
    'машинист фреза',
    'aналитик 1С: ERP',
    'программист 1С ЗУП'
]

def save_vacancies_to_file(grouped_data: dict):
    """Сохраняет сгруппированные данные в файл vacancies_current.txt атомарно."""
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    final_path = os.path.join(OUTPUT_FOLDER, CURRENT_FILE)
    tmp_path = final_path + ".tmp"

    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(grouped_data, f, ensure_ascii=False, indent=4)
        os.replace(tmp_path, final_path)  # Атомарная замена (POSIX, Windows)
        print(f"[{datetime.now()}] Данные сохранены в {final_path}.")
    except Exception as e:
        print(f"[{datetime.now()}] Ошибка сохранения данных: {e}.")
        # Если что-то пошло не так, пытаемся удалить временный файл
        try:
            os.remove(tmp_path)
        except OSError:
            pass

async def fetch_vacancies():
    """Получает данные с API hh.ru, группирует по ролям и сохраняет."""
    print(f"[{datetime.now()}] Запуск сбора данных из {API_URL}...")

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

                    # Задержка между запросами для снижения нагрузки на API
                    await asyncio.sleep(5)

                    response = await client.get(API_URL, params=params)
                    response.raise_for_status()
                    data = response.json()

                    items = data.get("items", [])
                    group_items.extend(items)

                    # Если страница неполная – достигли конца
                    if len(items) < PER_PAGE:
                        break

                except httpx.HTTPError as e:
                    print(f"[{datetime.now()}] HTTP ошибка в группе {group_name}, страница {page}: {e}.")
                    break
                except Exception as e:
                    print(f"[{datetime.now()}] Неизвестная ошибка в группе {group_name}, страница {page}: {e}.")
                    break

            grouped_data[group_name] = {
                "keywords": vacancy_keywords,
                "vacancies": group_items,
                "count": len(group_items)
            }
            total_count += len(group_items)
            print(f"[{datetime.now()}] Группа {group_name} обработана, найдено {len(group_items)} вакансий.")

    if grouped_data:
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

async def main():
    """Главная асинхронная функция: запуск планировщика и бесконечный цикл."""
    scheduler = AsyncIOScheduler()

    # Добавляем задачу с интервалом
    scheduler.add_job(
        fetch_vacancies,
        trigger=IntervalTrigger(hours=INTERVAL_HOURS),
        id="fetch_vacancies_job",
        name=f"Fetch vacancies every {INTERVAL_HOURS} hours",
        replace_existing=True,
    )

    # Запускаем планировщик
    scheduler.start()
    print(f"[{datetime.now()}] Планировщик запущен. Сбор данных каждые {INTERVAL_HOURS} часов.")

    # Выполняем первый сбор сразу при старте
    asyncio.create_task(fetch_vacancies())

    # Бесконечное ожидание (планировщик работает в фоновом режиме)
    try:
        while True:
            await asyncio.sleep(3600)  # Просыпаемся раз в час, чтобы не блокировать сигналы
    except KeyboardInterrupt:
        print(f"[{datetime.now()}] Получен сигнал остановки, завершаем работу...")
        scheduler.shutdown()

if __name__ == "__main__":
    asyncio.run(main())