import json
import os
from typing import List, Dict, Optional, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import pandas as pd
import numpy as np

app = FastAPI()

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_FILE = os.path.join(os.path.dirname(__file__), "../final_folder/vacancies_20260125_144856.txt")

# Predefined Roles Mapping
ROLES_CONFIG = [
    {"name": "Грузчик на склад", "ids": [31, 52]},
    {"name": "Аналитик данных", "ids": [156, 150, 10]},
    {"name": "ML инженер", "ids": [165, 96]},
    {"name": "Машинист катка", "ids": [63]},
    {"name": "Инженер склада", "ids": [81]},
    {"name": "Машинист фрезы", "ids": [128, 86]},
    {"name": "Агент по регистрации пассажиров (ПО)", "ids": [70]},
    {"name": "Фельдшер / фельдшер скорой медицинской помощи", "ids": [15, 24, 64]},
    {"name": "Специалист по обслуживанию ВС", "ids": [111, 173, 44, 46]},
    {"name": "Мойщик-уборщик", "ids": [130]},
    {"name": "Агент по сервису", "ids": [89]},
    {"name": "Агент по сервису в Бизнес-зал", "ids": [89]},
    {"name": "Медицинская сестра/медицинский брат", "ids": [64]},
    {"name": "Системный инженер", "ids": [114]},
    {"name": "Инспектор Перронного Контроля", "ids": [131, 81, 52]},
    {"name": "Кинолог", "ids": [90, 120]},
    {"name": "Инженер холодильных установок", "ids": [111, 144]},
    {"name": "Инспектор Группы Быстрого Реагирования", "ids": [90, 120, 95]}
]

# Experience Mapping (approximate years for sorting/plotting)
EXPERIENCE_MAP = {
    "noExperience": 0,
    "between1And3": 2,
    "between3And6": 4.5,
    "moreThan6": 8
}

def load_data():
    if not os.path.exists(DATA_FILE):
        # Fallback to absolute path if needed or just return empty
        if os.path.exists("/workspace/final_folder/vacancies_20260125_144856.txt"):
             with open("/workspace/final_folder/vacancies_20260125_144856.txt", "r", encoding="utf-8") as f:
                return json.load(f).get("items", [])
        return []
    
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f).get("items", [])

VACANCIES = []

def process_salary(item):
    """
    Extracts and normalizes salary to monthly RUR.
    Returns (min_salary, max_salary, avg_salary) or None if invalid.
    """
    salary = item.get("salary")
    if not salary:
        return None
    
    if salary.get("currency") != "RUR":
        # Simple skip for non-RUR for now as no conversion rates provided
        return None

    s_from = salary.get("from")
    s_to = salary.get("to")
    
    if s_from is None and s_to is None:
        return None
    
    # Calculate initial values
    val_from = s_from if s_from is not None else s_to
    val_to = s_to if s_to is not None else s_from
    
    # Check for multiplier (Hourly/Shift)
    # Check salary_range first
    salary_range = item.get("salary_range")
    multiplier = 1.0
    
    # Heuristic detection based on API structure or values
    # If explicit mode is present in salary_range
    if salary_range and salary_range.get("mode"):
        mode_id = salary_range["mode"].get("id")
        if mode_id == "SHIFT":
            multiplier = 15 # 15 shifts/month assumption
        elif mode_id == "HOURLY": # Not sure if this is the exact ID, but logical
            multiplier = 165 # 165 hours/month
    
    # Fallback heuristic if mode not found but values are very low
    # Monthly salary usually > 10000. 
    # If avg < 1000, likely hourly. If < 10000 and > 1000, likely shift?
    # But let's stick to explicit data or safe defaults.
    # The example data showed 'mode': {'id': 'SHIFT', ...} in salary_range
    
    return {
        "from": val_from * multiplier,
        "to": val_to * multiplier,
        "avg": ((val_from + val_to) / 2) * multiplier
    }

@app.on_event("startup")
def startup_event():
    global VACANCIES
    VACANCIES = load_data()
    print(f"Loaded {len(VACANCIES)} vacancies")

@app.get("/api/roles")
def get_roles():
    return ROLES_CONFIG

@app.get("/api/stats/{role_index}")
def get_stats(role_index: int):
    if role_index < 0 or role_index >= len(ROLES_CONFIG):
        raise HTTPException(status_code=404, detail="Role not found")
    
    role_config = ROLES_CONFIG[role_index]
    target_ids = set(map(str, role_config["ids"])) # IDs in data are likely strings
    
    # Filter vacancies
    # professional_roles is a list of objects {id, name}
    relevant_vacancies = []
    pulkovo_salaries = []
    market_salaries = [] # All salaries for this role
    
    bubble_data = []
    salary_values = []
    experience_values = []
    
    for v in VACANCIES:
        # Check roles
        v_roles = v.get("professional_roles", [])
        v_role_ids = {r.get("id") for r in v_roles}
        
        # If intersection of target_ids and v_role_ids is not empty
        if not target_ids.intersection(v_role_ids):
            continue
            
        salary_info = process_salary(v)
        if not salary_info:
            continue
            
        avg_salary = salary_info["avg"]
        
        # Employer check
        employer_id = v.get("employer", {}).get("id")
        if employer_id == "666661":
            pulkovo_salaries.append(avg_salary)
        else:
            market_salaries.append(avg_salary) # Should this include Pulkovo? "Pulkovo vs Market". Usually exclusive.
            
        # Experience
        exp_obj = v.get("experience", {})
        exp_id = exp_obj.get("id", "noExperience")
        exp_name = exp_obj.get("name", "Нет опыта")
        exp_numeric = EXPERIENCE_MAP.get(exp_id, 0)
        
        relevant_vacancies.append(v)
        salary_values.append(avg_salary)
        experience_values.append(exp_name)
        
        bubble_data.append({
            "id": v.get("id"),
            "salary": avg_salary,
            "experience": exp_numeric,
            "experience_label": exp_name,
            "title": v.get("name")
        })

    if not salary_values:
        return {"error": "No data found for this role"}
        
    # Aggregate bubble data
    bubble_df = pd.DataFrame(bubble_data)
    if not bubble_df.empty:
        # Group by salary and experience, count
        bubble_agg = bubble_df.groupby(['salary', 'experience', 'experience_label']).size().reset_index(name='count')
        # Scale count for bubble size if needed, or just pass count
        bubble_data_agg = bubble_agg.to_dict(orient='records')
    else:
        bubble_data_agg = []

    # Metrics
    metrics = {
        "min": float(np.min(salary_values)),
        "max": float(np.max(salary_values)),
        "avg": float(np.mean(salary_values)),
        "median": float(np.median(salary_values)),
        "count": len(salary_values)
    }
    
    # Pulkovo vs Market
    pulkovo_avg = float(np.mean(pulkovo_salaries)) if pulkovo_salaries else 0
    market_avg = float(np.mean(market_salaries)) if market_salaries else 0
    
    comparison = {
        "pulkovo": pulkovo_avg,
        "market": market_avg
    }
    
    # Distributions
    # Salary Hist (simple bins)
    hist, bin_edges = np.histogram(salary_values, bins=10)
    salary_dist = []
    for i in range(len(hist)):
        salary_dist.append({
            "range": f"{int(bin_edges[i])} - {int(bin_edges[i+1])}",
            "count": int(hist[i])
        })
        
    # Experience Dist
    exp_series = pd.Series(experience_values)
    exp_counts = exp_series.value_counts().to_dict()
    experience_dist = [{"name": k, "value": v} for k, v in exp_counts.items()]
    
    return {
        "role": role_config["name"],
        "metrics": metrics,
        "comparison": comparison,
        "bubble_data": bubble_data_agg,
        "salary_dist": salary_dist,
        "experience_dist": experience_dist
    }

# Serve React App static files
# Note: This expects the frontend to be built into 'frontend/dist'
frontend_path = os.path.join(os.path.dirname(__file__), "frontend/dist")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")
else:
    print("Frontend build not found. Run 'npm run build' in frontend directory.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("internal_main:app", host="0.0.0.0", port=8000, reload=True)
