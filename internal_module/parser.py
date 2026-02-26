import json
import os
from typing import List, Dict, Optional, Any
import numpy as np
import shutil

# Определяем пути
BASE_DIR = os.path.dirname(__file__)
LOCAL_FILE = os.path.join(BASE_DIR, "hh_data", "vacancies_current.txt")
SHARE_FILE = "/mnt/allshare_fileserver/barometer_vacancies/vacancies_current.txt"
# DATA_FILE = "hh_data/vacancies_current.txt"

def resolve_data_file() -> Optional[str]:
    """Определить доступный файл данных и обновить локальную копию при необходимости."""
    os.makedirs(os.path.dirname(LOCAL_FILE), exist_ok=True)

    if os.path.exists(SHARE_FILE):
        try:
            if os.path.exists(LOCAL_FILE):
                os.remove(LOCAL_FILE)  # удаляем старую локальную копию
            shutil.move(SHARE_FILE, LOCAL_FILE)  # перемещаем новый файл в папку скрипта
            print(f"Новый файл данных скопирован из {SHARE_FILE} в {LOCAL_FILE}")
            return LOCAL_FILE
        except OSError as exc:
            print(f"Не удалось обновить локальный файл из шары: {exc}")

    # Нового файла нет — используем существующий локальный
    if os.path.exists(LOCAL_FILE):
        print(f"Используется существующий локальный файл: {LOCAL_FILE}")
        return LOCAL_FILE

    print(
        f"Файл с данными не найден ни в общей папке ({SHARE_FILE}), "
        f"ни локально ({LOCAL_FILE}). Запуск без данных вакансий."
    )
    return None

# Маппинг опыта (примерные годы для сортировки/построения графиков)
EXPERIENCE_MAP = {
    "noExperience": 0,
    "between1And3": 2,
    "between3And6": 4.5,
    "moreThan6": 8
}

def load_data() -> Dict[str, Any]:
    """Загрузить данные вакансий из JSON файла."""
    target_file = resolve_data_file()
    if not target_file:
        return {"metadata": {"total_vacancies": 0, "total_groups": 0}, "groups": {}}
    
    with open(target_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Проверка на новый формат (с группами)
    if "groups" in data:
        data.setdefault("metadata", {})
        data["metadata"].setdefault("total_vacancies", sum(
            len(group.get("vacancies", [])) for group in data.get("groups", {}).values()
        ))
        data["metadata"].setdefault("total_groups", len(data.get("groups", {})))
        return data
    
    # Старый формат (с элементами) - преобразование в структуру groups
    items = data.get("items", [])
    return {
        "metadata": {"total_vacancies": len(items), "total_groups": 1},
        "groups": {"all_vacancies": {"keywords": "all", "vacancies": items}}
    }


def get_group_list(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Извлечь список групп с их метаданными."""
    groups = data.get("groups", {})
    group_list = []
    
    for group_id, group_data in groups.items():
        keywords = group_data.get("keywords", "")
        vacancy_count = len(group_data.get("vacancies", []))
        group_list.append({
            "id": group_id,
            "keywords": keywords,
            "vacancy_count": vacancy_count
        })
    
    return group_list


def process_salary(item: Dict[str, Any]) -> Optional[Dict[str, float]]:
    """Извлечь и нормализовать зарплату до месячных рублей."""
    salary = item.get("salary")
    if not salary:
        return None
    
    if salary.get("currency") != "RUR":
        # Простой пропуск для валют, отличных от RUR, так как курсы конверсии не предоставлены
        return None

    s_from = salary.get("from")
    s_to = salary.get("to")
    
    if s_from is None and s_to is None:
        return None
    
    # Расчет начальных значений
    val_from = s_from if s_from is not None else s_to
    val_to = s_to if s_to is not None else s_from
    
    # Проверка множителя (Почасовая/Сменная)
    # Сначала проверка диапазона зарплаты
    salary_range = item.get("salary_range")
    multiplier = 1.0
    
    # Эвристическое определение на основе структуры API или значений
    # Если явный режим присутствует в диапазоне зарплаты
    if salary_range and salary_range.get("mode"):
        mode_id = salary_range["mode"].get("id")
        if mode_id == "SHIFT":
            multiplier = 20
        elif mode_id == "HOUR":
            multiplier = 156
    
    return {
        "from": val_from * multiplier,
        "to": val_to * multiplier,
        "avg": ((val_from + val_to) / 2) * multiplier
    }

def calculate_salary_median(vacancies: List[Dict[str, Any]]) -> Optional[float]:
    """Рассчитать медианную зарплату из списка вакансий."""
    salaries = []
    for v in vacancies:
        salary_info = process_salary(v)
        if salary_info:
            salaries.append(salary_info["avg"])
    
    if not salaries:
        return None
    
    return float(np.median(salaries))

def filter_salary_outliers(vacancies: List[Dict[str, Any]], 
                           high_multiplier: float = 3,
                           low_divisor: float = 5,
                           return_stats: bool = False) -> Any:
    """Отфильтровать вакансии с зарплатами, которые слишком высокие или низкие по сравнению с медианой."""
    # Сначала собрать все валидные зарплаты для расчета медианы
    salaries_with_vacancies = []
    vacancies_without_salary = []
    
    for v in vacancies:
        salary_info = process_salary(v)
        if salary_info:
            salaries_with_vacancies.append((v, salary_info["avg"]))
        else:
            # Сохранить вакансии без информации о зарплате
            vacancies_without_salary.append(v)
    
    if not salaries_with_vacancies:
        if return_stats:
            return vacancies_without_salary, {
                "total_before": len(vacancies_without_salary),
                "total_after": len(vacancies_without_salary),
                "filtered_high_count": 0,
                "filtered_low_count": 0,
                "filtered_total_count": 0,
                "median": None,
                "high_threshold": None,
                "low_threshold": None
            }
        return vacancies_without_salary
    
    # Расчет медианы и порогов
    salary_values = [s for _, s in salaries_with_vacancies]
    median_salary = float(np.median(salary_values))
    high_threshold = median_salary * high_multiplier
    low_threshold = median_salary / low_divisor
    
    # Фильтрация высоких и низких выбросов
    filtered = []
    filtered_high_count = 0
    filtered_low_count = 0
    for v, salary in salaries_with_vacancies:
        if salary > high_threshold:
            filtered_high_count += 1
        elif salary < low_threshold:
            filtered_low_count += 1
        else:
            filtered.append(v)
    
    # Включить вакансии без информации о зарплате
    filtered.extend(vacancies_without_salary)
    
    if return_stats:
        total_before = len(salaries_with_vacancies) + len(vacancies_without_salary)
        return filtered, {
            "total_before": total_before,
            "total_after": len(filtered),
            "filtered_high_count": filtered_high_count,
            "filtered_low_count": filtered_low_count,
            "filtered_total_count": filtered_high_count + filtered_low_count,
            "median": median_salary,
            "high_threshold": high_threshold,
            "low_threshold": low_threshold
        }
    
    return filtered


def parse_vacancies_for_group(vacancies: List[Dict[str, Any]], 
                               filter_outliers: bool = True) -> Dict[str, Any]:
    """Парсить и обработать вакансии для конкретной группы с опциональной фильтрацией выбросов."""
    # Отслеживание статистики фильтрации
    filter_stats = {
        "total_before_filter": len(vacancies),
        "filtered_count": 0,
        "median_salary": None,
        "threshold_salary": None
    }
    
    # Опционально фильтровать выбросы зарплат (как высокие, так и низкие)
    if filter_outliers:
        vacancies, outlier_stats = filter_salary_outliers(
            vacancies, return_stats=True
        )
        filter_stats["filtered_count"] = outlier_stats["filtered_total_count"]
        filter_stats["median_salary"] = outlier_stats["median"]
        filter_stats["threshold_salary"] = outlier_stats["high_threshold"]
    
    # Обработка зарплат и опыта
    pulkovo_salaries = []
    market_salaries = []
    bubble_data = []
    salary_values = []
    experience_values = []
    employment_values = []
    schedule_values = []
    processed_vacancies = []
    
    for v in vacancies:
        salary_info = process_salary(v)
        if not salary_info:
            continue
            
        avg_salary = salary_info["avg"]
        
        # Проверка работодателя
        employer_id = v.get("employer", {}).get("id")
        if employer_id == "666661":
            pulkovo_salaries.append(avg_salary)
        else:
            market_salaries.append(avg_salary)
            
        # Опыт
        exp_obj = v.get("experience", {})
        exp_id = exp_obj.get("id", "noExperience")
        exp_name = exp_obj.get("name", "Нет опыта")
        exp_numeric = EXPERIENCE_MAP.get(exp_id, 0)
        
        # Тип занятости
        employment_obj = v.get("employment", {})
        employment_name = employment_obj.get("name", "Не указано")
        employment_values.append(employment_name)
        
        # Тип графика
        schedule_obj = v.get("schedule", {})
        schedule_name = schedule_obj.get("name", "Не указано")
        schedule_values.append(schedule_name)
        
        processed_vacancies.append(v)
        salary_values.append(avg_salary)
        experience_values.append(exp_name)
        
        # Получение информации о работодателе
        employer_obj = v.get("employer", {})
        employer_name = employer_obj.get("name", "Не указано")
        
        bubble_data.append({
            "id": v.get("id"),
            "salary": avg_salary,
            "experience": exp_numeric,
            "experience_label": exp_name,
            "title": v.get("name"),
            "employer": employer_name
        })
    
    return {
        "vacancies": processed_vacancies,
        "pulkovo_salaries": pulkovo_salaries,
        "market_salaries": market_salaries,
        "bubble_data": bubble_data,
        "salary_values": salary_values,
        "experience_values": experience_values,
        "employment_values": employment_values,
        "schedule_values": schedule_values,
        "filter_stats": filter_stats
    }
