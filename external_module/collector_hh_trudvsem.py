import asyncio
import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Настройки для работы с файловой системой
OUTPUT_FOLDER = "/mnt/bi_sandbox/barometer_vacancies"
# OUTPUT_FOLDER = "/mnt/allshare_fileserver/barometer_vacancies"
CURRENT_FILE = "vacancies_current.txt"

# Настройки для работы с API hh.ru
HH_API_URL = "https://api.hh.ru/vacancies"
HH_MAX_PAGES = 20
HH_AREA = 2
HH_PER_PAGE = 99

# Настройки для работы с API "Работа России"
TRUDVSEM_API_URL = "http://opendata.trudvsem.ru/api/v1/vacancies"
TRUDVSEM_MAX_PAGES = 20
TRUDVSEM_PER_PAGE = 100

# Общие настройки
INTERVAL_HOURS = 12
REQUEST_DELAY_SECONDS = 1
HTTP_TIMEOUT_SECONDS = 30

KEYWORDS = [
    "грузчик нагрузки",
    "аналитик данных SQL",
    "ml engineer",
    "машинист катка",
    "руководитель склада OR NAME:(инженер склада)",
    "фельдшер помощь",
    "обслуживание воздушных судов",
    "уборщик самолетов",
    "осмотр медицинской",
    "системный виртуализация",
    "склад комплектовщик",
    "кинолог",
    "инженер холодильного",
    "гбр охрана",
    "бариста выпечка",
    "отчетность пекарня",
    "закупки булочная",
    "управляющий кафе",
    "товаровед кладовщик",
    "тракторист снег",
    "регистрация пассажиров",
    "обслуживание в бизнес-залах",
    "официант сервировка",
    "машинист фреза",
    "aналитик 1С: ERP",
    "программист 1С ЗУП",
]


def save_vacancies_to_file(grouped_data: Dict[str, Any]) -> None:
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
    except Exception as exc:
        print(f"[{datetime.now()}] Ошибка сохранения данных: {exc}.")
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def _experience_bucket(experience_years: Any) -> Dict[str, str]:
    """Преобразует числовой стаж Trudvsem к классификатору HH."""
    try:
        years = int(experience_years)
    except (TypeError, ValueError):
        years = 0

    if years <= 0:
        return {"id": "noExperience", "name": "Нет опыта"}
    if years <= 3:
        return {"id": "between1And3", "name": "От 1 года до 3 лет"}
    if years <= 6:
        return {"id": "between3And6", "name": "От 3 до 6 лет"}
    return {"id": "moreThan6", "name": "Более 6 лет"}


def _to_number(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    value_str = str(value).strip()
    if not value_str:
        return None

    cleaned = value_str.replace(" ", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _salary_from_text(salary_text: Any) -> Optional[float]:
    """Резервный парсинг зарплаты из строки вида 'от 40000'."""
    if not salary_text:
        return None

    numbers = re.findall(r"\d+(?:[.,]\d+)?", str(salary_text))
    if not numbers:
        return None

    parsed = [_to_number(num) for num in numbers]
    parsed = [num for num in parsed if num is not None]
    if not parsed:
        return None

    if len(parsed) == 1:
        return parsed[0]

    return sum(parsed) / len(parsed)


def normalize_trudvsem_vacancy(vacancy: Dict[str, Any]) -> Dict[str, Any]:
    """
    Приводит объект вакансии Trudvsem к форме, совместимой с HH-парсером.
    """
    company_data = vacancy.get("company") or {}
    company_name = company_data.get("name", "Не указано")
    company_id = (
        company_data.get("companycode")
        or company_data.get("inn")
        or company_data.get("ogrn")
        or company_name
    )

    salary_min = _to_number(vacancy.get("salary_min"))
    salary_max = _to_number(vacancy.get("salary_max"))
    if salary_min is None and salary_max is None:
        parsed_salary = _salary_from_text(vacancy.get("salary"))
        salary_min = parsed_salary
        salary_max = parsed_salary
    elif salary_min is None:
        salary_min = salary_max
    elif salary_max is None:
        salary_max = salary_min

    currency_raw = vacancy.get("currency")
    currency_value = str(currency_raw or "").lower()
    salary_currency = "RUR" if "руб" in currency_value else str(currency_raw or "")
    salary_object = None
    if salary_min is not None or salary_max is not None:
        salary_object = {
            "from": salary_min,
            "to": salary_max,
            "currency": salary_currency,
        }

    requirement = vacancy.get("requirement") or {}
    experience_data = _experience_bucket(requirement.get("experience"))

    region_data = vacancy.get("region")
    if isinstance(region_data, dict):
        area_name = region_data.get("name", "Не указано")
    else:
        area_name = str(region_data) if region_data else "Не указано"

    vacancy_id = vacancy.get("id") or vacancy.get("vac_url") or f"trudvsem-{company_id}"

    return {
        "id": f"trudvsem-{vacancy_id}",
        "name": vacancy.get("job-name", "Без названия"),
        "salary": salary_object,
        "employer": {
            "id": str(company_id),
            "name": company_name,
        },
        "experience": experience_data,
        "employment": {"name": vacancy.get("employment", "Не указано")},
        "schedule": {"name": vacancy.get("schedule", "Не указано")},
        "area": {"name": area_name},
        "source": {"id": "trudvsem", "name": "Работа России"},
        "published_at": vacancy.get("creation-date"),
        "alternate_url": vacancy.get("vac_url"),
        "snippet": {
            "requirement": vacancy.get("requirements") or "",
            "responsibility": vacancy.get("duty") or "",
        },
    }


async def fetch_hh_for_keyword(client: httpx.AsyncClient, vacancy_keywords: str) -> List[Dict[str, Any]]:
    """Получает вакансии HH для одной группы ключевых слов."""
    items: List[Dict[str, Any]] = []

    for page in range(HH_MAX_PAGES):
        params = [
            ("area", HH_AREA),
            ("per_page", HH_PER_PAGE),
            ("page", page),
            ("text", vacancy_keywords),
        ]

        try:
            await asyncio.sleep(REQUEST_DELAY_SECONDS)
            response = await client.get(HH_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            page_items = data.get("items", [])
            items.extend(page_items)

            if len(page_items) < HH_PER_PAGE:
                break
        except httpx.HTTPError as exc:
            print(f"[{datetime.now()}] HH HTTP ошибка, ключевые слова '{vacancy_keywords}', страница {page}: {exc}.")
            break
        except Exception as exc:
            print(f"[{datetime.now()}] HH неизвестная ошибка, ключевые слова '{vacancy_keywords}', страница {page}: {exc}.")
            break

    return items


async def fetch_trudvsem_for_keyword(client: httpx.AsyncClient, vacancy_keywords: str) -> List[Dict[str, Any]]:
    """Получает вакансии Trudvsem для одной группы ключевых слов."""
    items: List[Dict[str, Any]] = []

    for page in range(TRUDVSEM_MAX_PAGES):
        offset = page * TRUDVSEM_PER_PAGE
        params = {
            "text": vacancy_keywords,
            "limit": TRUDVSEM_PER_PAGE,
            "offset": offset,
        }

        try:
            await asyncio.sleep(REQUEST_DELAY_SECONDS)
            response = await client.get(TRUDVSEM_API_URL, params=params)
            response.raise_for_status()
            data = response.json()

            status = str(data.get("status"))
            if status != "200":
                error_message = data.get("meta", {}).get("error", "неизвестная ошибка API")
                print(
                    f"[{datetime.now()}] Trudvsem API вернул статус {status} "
                    f"для ключевых слов '{vacancy_keywords}', page={page}: {error_message}"
                )
                break

            raw_items = data.get("results", {}).get("vacancies", [])
            if not isinstance(raw_items, list):
                print(
                    f"[{datetime.now()}] Trudvsem: неожиданный формат 'results.vacancies' "
                    f"для ключевых слов '{vacancy_keywords}', page={page}."
                )
                break

            normalized_page_items = []
            for wrapped_vacancy in raw_items:
                vacancy = wrapped_vacancy.get("vacancy", {})
                if isinstance(vacancy, dict):
                    normalized_page_items.append(normalize_trudvsem_vacancy(vacancy))

            items.extend(normalized_page_items)

            if len(raw_items) < TRUDVSEM_PER_PAGE:
                break
        except httpx.HTTPError as exc:
            print(
                f"[{datetime.now()}] Trudvsem HTTP ошибка, ключевые слова '{vacancy_keywords}', "
                f"страница {page}: {exc}."
            )
            break
        except Exception as exc:
            print(
                f"[{datetime.now()}] Trudvsem неизвестная ошибка, ключевые слова '{vacancy_keywords}', "
                f"страница {page}: {exc}."
            )
            break

    return items


def merge_and_deduplicate_vacancies(*vacancy_lists: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Объединяет вакансии и убирает дубликаты по id."""
    merged: Dict[str, Dict[str, Any]] = {}
    for vacancies in vacancy_lists:
        for vacancy in vacancies:
            vacancy_id = str(vacancy.get("id"))
            if vacancy_id not in merged:
                merged[vacancy_id] = vacancy
    return list(merged.values())


async def fetch_vacancies() -> None:
    """Получает данные с HH и Trudvsem, группирует по ролям и сохраняет."""
    print(f"[{datetime.now()}] Запуск сбора данных из HH и Trudvsem...")

    grouped_data: Dict[str, Dict[str, Any]] = {}
    total_count = 0
    source_totals = {"hh": 0, "trudvsem": 0}

    timeout = httpx.Timeout(HTTP_TIMEOUT_SECONDS)
    async with httpx.AsyncClient(timeout=timeout) as client:
        for group_index, vacancy_keywords in enumerate(KEYWORDS):
            group_name = f"group_{group_index + 1}_keywords_{vacancy_keywords.replace(' ', '_')}"
            print(f"[{datetime.now()}] Обработка группы {group_name}...")

            hh_items = await fetch_hh_for_keyword(client, vacancy_keywords)
            trudvsem_items = await fetch_trudvsem_for_keyword(client, vacancy_keywords)
            merged_items = merge_and_deduplicate_vacancies(hh_items, trudvsem_items)

            grouped_data[group_name] = {
                "keywords": vacancy_keywords,
                "vacancies": merged_items,
                "count": len(merged_items),
                "source_counts": {
                    "hh": len(hh_items),
                    "trudvsem": len(trudvsem_items),
                },
            }

            source_totals["hh"] += len(hh_items)
            source_totals["trudvsem"] += len(trudvsem_items)
            total_count += len(merged_items)

            print(
                f"[{datetime.now()}] Группа {group_name} обработана: "
                f"HH={len(hh_items)}, Trudvsem={len(trudvsem_items)}, "
                f"после дедупликации={len(merged_items)}."
            )

    if grouped_data:
        result_data = {
            "metadata": {
                "fetched_at": datetime.now().isoformat(),
                "total_vacancies": total_count,
                "total_groups": len(grouped_data),
                "sources": source_totals,
            },
            "groups": grouped_data,
        }
        save_vacancies_to_file(result_data)
    else:
        print(f"[{datetime.now()}] Данные не были получены.")


async def main() -> None:
    """Главная асинхронная функция: запуск планировщика и бесконечный цикл."""
    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        fetch_vacancies,
        trigger=IntervalTrigger(hours=INTERVAL_HOURS),
        id="fetch_vacancies_job",
        name=f"Fetch HH + Trudvsem vacancies every {INTERVAL_HOURS} hours",
        replace_existing=True,
    )

    scheduler.start()
    print(f"[{datetime.now()}] Планировщик запущен. Сбор данных каждые {INTERVAL_HOURS} часов.")

    asyncio.create_task(fetch_vacancies())

    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        print(f"[{datetime.now()}] Получен сигнал остановки, завершаем работу...")
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
