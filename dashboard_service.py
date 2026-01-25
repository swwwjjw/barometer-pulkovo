import os
import json
import glob
from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import statistics

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

DATA_FOLDER = "final_folder"
PULKOVO_EMPLOYER_ID = "666661"

# Mapping from prompt
JOB_TITLES_MAP = {
    "Грузчик на склад": [31, 52],
    "Аналитик данных": [156, 150, 10],
    "ML инженер": [165, 96],
    "Машинист катка": [63],
    "Инженер склада": [81],
    "Машинист фрезы": [128, 86],
    "Агент по регистрации пассажиров (ПО)": [70],
    "Фельдшер / фельдшер скорой медицинской помощи": [15, 24, 64],
    "Специалист по обслуживанию ВС": [111, 173, 44, 46],
    "Мойщик-уборщик": [130],
    "Агент по сервису": [89],
    "Агент по сервису в Бизнес-зал": [89],
    "Медицинская сестра/медицинский брат": [64],
    "Системный инженер": [114],
    "Инспектор Перронного Контроля": [131, 81, 52],
    "Кинолог": [90, 120],
    "Инженер холодильных установок": [111, 144],
    "Инспектор Группы Быстрого Реагирования": [90, 120, 95]
}

class SalaryStats(BaseModel):
    min: float
    max: float
    avg: float
    median: float

class DashboardData(BaseModel):
    job_title: str
    salary_stats: SalaryStats
    pulkovo_salary: Optional[float]
    market_salary_avg: float
    salary_rating_data: List[Dict] # {salary, rating, employer_name}
    salary_distribution: List[Dict] # {range, count}
    experience_distribution: List[Dict] # {experience, count}

def get_latest_file():
    files = glob.glob(os.path.join(DATA_FOLDER, "*.txt"))
    if not files:
        return None
    return max(files, key=os.path.getctime)

def load_data():
    filepath = get_latest_file()
    if not filepath:
        return []
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("items", [])
    except Exception as e:
        print(f"Error loading data: {e}")
        return []

def calculate_monthly_salary(item):
    """
    Extracts and converts salary to monthly.
    Heuristic: If salary is very low (< 1000), assume hourly and multiply by 160 (standard hours).
    If it's medium low (< 5000), assume per shift and multiply by 15 (standard shifts).
    This is a rough heuristic as API doesn't strictly provide this field in 'items'.
    """
    salary = item.get("salary")
    if not salary:
        return None
    
    # Use 'to' if available, else 'from'. If both, use average.
    s_from = salary.get("from")
    s_to = salary.get("to")
    
    if s_from is None and s_to is None:
        return None
    
    if s_from is not None and s_to is not None:
        val = (s_from + s_to) / 2
    elif s_from is not None:
        val = s_from
    else:
        val = s_to
        
    if salary.get("currency") != "RUR":
        # Simplified: ignore non-RUR or assume 1:1 for this exercise if not specified
        # In real app, we'd need exchange rates.
        pass

    # Conversion heuristics
    if val < 1000: # Hourly
        return val * 168 # Standard monthly hours
    elif val < 10000: # Per shift (daily)
        return val * 20 # Standard working days
    
    return val

def get_employer_rating(item):
    # Mock rating as it's not standard in HH items
    # Hash employer ID to get a consistent pseudo-random rating between 3.0 and 5.0
    emp_id = item.get("employer", {}).get("id", "0")
    try:
        seed = int(emp_id)
    except:
        seed = hash(emp_id)
    
    import random
    r = random.Random(seed)
    return round(3.0 + r.random() * 2.0, 1)

@router.get("/titles")
def get_titles():
    return list(JOB_TITLES_MAP.keys())

@router.get("/stats/{job_title}")
def get_stats(job_title: str):
    if job_title not in JOB_TITLES_MAP:
        raise HTTPException(status_code=404, detail="Job title not found")
        
    target_roles = set(JOB_TITLES_MAP[job_title])
    all_items = load_data()
    
    filtered_items = []
    for item in all_items:
        # Check if item matches any of the target roles
        # Item roles are in item['professional_roles'] list of dicts with 'id'
        item_roles = {int(r['id']) for r in item.get('professional_roles', [])}
        if not item_roles.isdisjoint(target_roles):
            filtered_items.append(item)
            
    if not filtered_items:
        return {
            "job_title": job_title,
            "salary_stats": {"min": 0, "max": 0, "avg": 0, "median": 0},
            "pulkovo_salary": None,
            "market_salary_avg": 0,
            "salary_rating_data": [],
            "salary_distribution": [],
            "experience_distribution": []
        }

    salaries = []
    salary_rating_points = []
    pulkovo_salaries = []
    experience_counts = {}

    for item in filtered_items:
        monthly_salary = calculate_monthly_salary(item)
        if monthly_salary:
            salaries.append(monthly_salary)
            rating = get_employer_rating(item)
            emp_name = item.get("employer", {}).get("name", "Unknown")
            salary_rating_points.append({
                "salary": monthly_salary,
                "rating": rating,
                "employer": emp_name,
                "vacancy": item.get("name")
            })
            
            if item.get("employer", {}).get("id") == PULKOVO_EMPLOYER_ID:
                pulkovo_salaries.append(monthly_salary)
        
        exp_name = item.get("experience", {}).get("name", "Не указано")
        experience_counts[exp_name] = experience_counts.get(exp_name, 0) + 1

    if not salaries:
         return {
            "job_title": job_title,
            "salary_stats": {"min": 0, "max": 0, "avg": 0, "median": 0},
            "pulkovo_salary": None,
            "market_salary_avg": 0,
            "salary_rating_data": [],
            "salary_distribution": [],
            "experience_distribution": [{"name": k, "value": v} for k, v in experience_counts.items()]
        }

    # Stats
    min_sal = min(salaries)
    max_sal = max(salaries)
    avg_sal = statistics.mean(salaries)
    median_sal = statistics.median(salaries)
    
    pulkovo_avg = statistics.mean(pulkovo_salaries) if pulkovo_salaries else None
    
    # Distribution buckets
    bucket_count = 10
    if max_sal == min_sal:
        step = 10000
    else:
        step = (max_sal - min_sal) / bucket_count
        
    buckets = {}
    for s in salaries:
        bucket_index = int((s - min_sal) / step) if step > 0 else 0
        if bucket_index >= bucket_count:
            bucket_index = bucket_count - 1
        
        range_start = int(min_sal + bucket_index * step)
        range_end = int(min_sal + (bucket_index + 1) * step)
        label = f"{range_start}-{range_end}"
        buckets[label] = buckets.get(label, 0) + 1
        
    salary_dist = [{"range": k, "count": v} for k, v in buckets.items()]
    # Sort by range start (parsing label)
    salary_dist.sort(key=lambda x: int(x["range"].split("-")[0]))

    exp_dist = [{"name": k, "value": v} for k, v in experience_counts.items()]

    return {
        "job_title": job_title,
        "salary_stats": {
            "min": round(min_sal, 2),
            "max": round(max_sal, 2),
            "avg": round(avg_sal, 2),
            "median": round(median_sal, 2)
        },
        "pulkovo_salary": round(pulkovo_avg, 2) if pulkovo_avg else None,
        "market_salary_avg": round(avg_sal, 2),
        "salary_rating_data": salary_rating_points,
        "salary_distribution": salary_dist,
        "experience_distribution": exp_dist
    }
