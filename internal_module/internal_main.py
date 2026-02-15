import os
import json
from typing import List, Dict, Optional, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import pandas as pd
import numpy as np

# Импорт модуля парсера
from internal_module.parser import (
    load_data,
    process_salary,
    filter_salary_outliers,
    parse_vacancies_for_group,
    get_group_list,
    EXPERIENCE_MAP
)

app = FastAPI()

# Загрузка данных B1
B1_DATA = []
b1_data_path = os.path.join(os.path.dirname(__file__), "b1_data.json")
if os.path.exists(b1_data_path):
    with open(b1_data_path, 'r', encoding='utf-8') as f:
        B1_DATA = json.load(f)
    print(f"Загружено блоков B1: {len(B1_DATA)}")
else:
    print(f"Файл с данными B1 не найден: {b1_data_path}")

# Включение CORS для разработки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Обслуживание статических файлов для React приложения
# Примечание: фронтенд должен быть собран в 'frontend/dist'
frontend_path = os.path.join(os.path.dirname(__file__), "frontend/dist")

VACANCY_DATA = {}

@app.on_event("startup")
def startup_event():
    global VACANCY_DATA
    VACANCY_DATA = load_data()
    metadata = VACANCY_DATA.get("metadata", {})
    total = metadata.get("total_vacancies", 0)
    total_groups = metadata.get("total_groups", 0)
    print(f"Загружено {total} вакансий в {total_groups} группах")

@app.get("/api/groups")
def get_groups():
    """Получить список всех групп вакансий с метаданными."""
    return get_group_list(VACANCY_DATA)

@app.get("/api/stats/{group_id}")
def get_stats(group_id: str, filter_outliers: bool = True):
    """Получить статистику для конкретной группы вакансий."""
    groups = VACANCY_DATA.get("groups", {})
    
    if group_id not in groups:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    
    group_data = groups[group_id]
    group_vacancies = group_data.get("vacancies", [])
    group_keywords = group_data.get("keywords", "")
    
    # Использование модуля парсера для обработки вакансий с фильтрацией выбросов
    parsed_data = parse_vacancies_for_group(
        group_vacancies, 
        filter_outliers=filter_outliers
    )
    
    salary_values = parsed_data["salary_values"]
    pulkovo_salaries = parsed_data["pulkovo_salaries"]
    market_salaries = parsed_data["market_salaries"]
    bubble_data = parsed_data["bubble_data"]
    experience_values = parsed_data["experience_values"]
    employment_values = parsed_data["employment_values"]
    schedule_values = parsed_data["schedule_values"]
    filter_stats = parsed_data["filter_stats"]

    if not salary_values:
        return {"error": "Нет данных для этой группы"}
        
    # Агрегация данных для пузырькового графика - группировка по зарплате, опыту и работодателю
    bubble_df = pd.DataFrame(bubble_data)
    if not bubble_df.empty:
        # Группировка по зарплате, опыту и работодателю, подсчет вхождений
        bubble_agg = bubble_df.groupby(['salary', 'experience', 'experience_label', 'employer']).size().reset_index(name='count')
        # Масштабирование счетчика для размера пузырька при необходимости
        bubble_data_agg = bubble_agg.to_dict(orient='records')
    else:
        bubble_data_agg = []

    # Метрики
    metrics = {
        "min": float(np.min(salary_values)),
        "max": float(np.max(salary_values)),
        "avg": float(np.mean(salary_values)),
        "median": float(np.median(salary_values)),
        "count": len(salary_values)
    }
    
    # Пулково vs Рынок
    pulkovo_avg = float(np.mean(pulkovo_salaries)) if pulkovo_salaries else 0
    market_avg = float(np.mean(market_salaries)) if market_salaries else 0
    
    comparison = {
        "pulkovo": pulkovo_avg,
        "market": market_avg
    }

    # Распределения
    # Гистограмма зарплат (простые интервалы)
    hist, bin_edges = np.histogram(salary_values, bins=8)
    salary_dist = []
    for i in range(len(hist)):
        salary_dist.append({
            "range": f"{int(bin_edges[i])} - {int(bin_edges[i+1])}",
            "count": int(hist[i])
        })
        
    # Распределение по опыту
    exp_series = pd.Series(experience_values)
    exp_counts = exp_series.value_counts().to_dict()
    experience_dist = [{"name": k, "value": v} for k, v in exp_counts.items()]
    
    # Распределение по типу занятости
    emp_series = pd.Series(employment_values)
    emp_counts = emp_series.value_counts().to_dict()
    employment_dist = [{"name": k, "count": v} for k, v in emp_counts.items()]
    
    # Распределение по графику работы
    sched_series = pd.Series(schedule_values)
    sched_counts = sched_series.value_counts().to_dict()
    schedule_dist = [{"name": k, "count": v} for k, v in sched_counts.items()]
    
    return {
        "group_id": group_id,
        "keywords": group_keywords,
        "metrics": metrics,
        "comparison": comparison,
        "bubble_data": bubble_data_agg,
        "salary_dist": salary_dist,
        "experience_dist": experience_dist,
        "employment_dist": employment_dist,
        "schedule_dist": schedule_dist,
        "outliers_filtered": filter_outliers,
        "filter_stats": {
            "total_before_filter": filter_stats["total_before_filter"],
            "filtered_out_count": filter_stats["filtered_count"],
            "total_after_filter": len(salary_values),
            "median_salary_for_filter": filter_stats["median_salary"],
            "threshold_salary": filter_stats["threshold_salary"]
        }
    }

@app.get("/api/overall-stats")
def get_overall_stats(filter_outliers: bool = True):
    """Получить статистику для ВСЕХ вакансий в txt файле."""
    groups = VACANCY_DATA.get("groups", {})
    if not groups:
        return {"error": "Нет загруженных вакансий"}
    
    # Объединение всех вакансий из всех групп
    all_vacancies = []
    for group_data in groups.values():
        all_vacancies.extend(group_data.get("vacancies", []))
    
    # Применение фильтрации выбросов зарплат при включенной опции
    vacancies_to_process = all_vacancies
    filter_stats = {
        "total_before_filter": len(all_vacancies),
        "filtered_high_count": 0,
        "filtered_low_count": 0,
        "filtered_total_count": 0,
        "median_salary": None,
        "high_threshold": None,
        "low_threshold": None
    }
    
    if filter_outliers:
        vacancies_to_process, outlier_stats = filter_salary_outliers(
            all_vacancies, 
            return_stats=True,
            high_multiplier=10
        )
        filter_stats["filtered_high_count"] = outlier_stats["filtered_high_count"]
        filter_stats["filtered_low_count"] = outlier_stats["filtered_low_count"]
        filter_stats["filtered_total_count"] = outlier_stats["filtered_total_count"]
        filter_stats["median_salary"] = outlier_stats["median"]
        filter_stats["high_threshold"] = outlier_stats["high_threshold"]
        filter_stats["low_threshold"] = outlier_stats["low_threshold"]
    
    salary_values = []
    experience_values = []
    employment_values = []
    schedule_values = []
    
    for v in vacancies_to_process:
        salary_info = process_salary(v)
        if salary_info:
            salary_values.append(salary_info["avg"])
        
        # Опыт
        exp_obj = v.get("experience", {})
        exp_name = exp_obj.get("name", "Не указано")
        experience_values.append(exp_name)
        
        # Тип занятости
        employment_obj = v.get("employment", {})
        employment_name = employment_obj.get("name", "Не указано")
        employment_values.append(employment_name)
        
        # График работы
        schedule_obj = v.get("schedule", {})
        schedule_name = schedule_obj.get("name", "Не указано")
        schedule_values.append(schedule_name)
    
    # Общее количество вакансий
    total_count = len(vacancies_to_process)
    
    # Метрики зарплат (только для вакансий с указанной зарплатой после фильтрации)
    metrics = {}
    if salary_values:
        metrics = {
            "min": float(np.min(salary_values)),
            "max": float(np.max(salary_values)),
            "avg": float(np.mean(salary_values)),
            "median": float(np.median(salary_values)),
            "with_salary_count": len(salary_values)
        }
    
    # Распределение по опыту
    exp_series = pd.Series(experience_values)
    exp_counts = exp_series.value_counts().to_dict()
    experience_dist = [{"name": k, "value": v} for k, v in exp_counts.items()]
    
    # Распределение по типу занятости
    emp_series = pd.Series(employment_values)
    emp_counts = emp_series.value_counts().to_dict()
    employment_dist = [{"name": k, "count": v} for k, v in emp_counts.items()]
    
    # Распределение по графику работы
    sched_series = pd.Series(schedule_values)
    sched_counts = sched_series.value_counts().to_dict()
    schedule_dist = [{"name": k, "count": v} for k, v in sched_counts.items()]
    
    return {
        "total_count": total_count,
        "metrics": metrics,
        "experience_dist": experience_dist,
        "employment_dist": employment_dist,
        "schedule_dist": schedule_dist,
        "outliers_filtered": filter_outliers,
        "filter_stats": filter_stats
    }

@app.get("/api/b1/blocks")
def get_b1_blocks():
    """Получить все блоки B1 с их статистикой"""
    return [{
        "name": block["name"],
        "stats": {
            "avg": block["stats"]["avg_monthly_salary"],
            "median": block["stats"]["median_monthly_salary"],
            "min": block["stats"]["min_monthly_salary"],
            "max": block["stats"]["max_monthly_salary"]
        },
        "positions_count": len(block["positions"])
    } for block in B1_DATA]

@app.get("/api/b1/blocks/{block_index}")
def get_b1_block_details(block_index: int):
    """Получить детальную информацию о конкретном блоке B1, включая все позиции"""
    if block_index < 0 or block_index >= len(B1_DATA):
        raise HTTPException(status_code=404, detail="Блок не найден")
    
    block = B1_DATA[block_index]
    
    # Преобразование данных в формат, ожидаемый фронтендом
    return {
        "name": block["name"],
        "stats": {
            "avg": block["stats"]["avg_monthly_salary"],
            "median": block["stats"]["median_monthly_salary"],
            "min": block["stats"]["min_monthly_salary"],
            "max": block["stats"]["max_monthly_salary"]
        },
        "positions": [{
            "name": position["name"],
            "salary": position["monthly_salary"]["median"]
        } for position in block["positions"]]
    }

@app.get("/dashboard")
async def dashboard():
    """Отображение основного дашборда"""
    if os.path.exists(os.path.join(frontend_path, "index.html")):
        return FileResponse(os.path.join(frontend_path, "index.html"))
    return {"error": "Фронтенд не найден"}

@app.get("/b1")
async def b1_page():
    """Отдельный эндпоинт для обзора зарплат B1"""
    if os.path.exists(os.path.join(frontend_path, "index.html")):
        return FileResponse(os.path.join(frontend_path, "index.html"))
    return {"error": "Фронтенд не найден"}

if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")
else:
    print("Сборка фронтенда не найдена. Выполните 'npm run build' в папке frontend.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("internal_main:app", host="0.0.0.0", port=7777, reload=True)