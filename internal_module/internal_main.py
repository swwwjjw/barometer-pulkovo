import os
from typing import List, Dict, Optional, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import pandas as pd
import numpy as np

# Import parser module
from internal_module.parser import (
    load_data,
    process_salary,
    filter_high_salary_outliers,
    parse_vacancies_for_role,
    ROLES_CONFIG,
    EXPERIENCE_MAP
)

app = FastAPI()

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files for React app
# Note: frontend is expected to be built in 'frontend/dist'
frontend_path = os.path.join(os.path.dirname(__file__), "frontend/dist")

VACANCIES = []

@app.on_event("startup")
def startup_event():
    global VACANCIES
    VACANCIES = load_data()
    print(f"Loaded {len(VACANCIES)} vacancies")

@app.get("/api/roles")
def get_roles():
    return ROLES_CONFIG

@app.get("/api/stats/{role_index}")
def get_stats(role_index: int, filter_outliers: bool = True):
    """
    Get statistics for a specific role.
    
    Args:
        role_index: Index of the role in ROLES_CONFIG.
        filter_outliers: Whether to filter vacancies with salaries 3x higher than median.
    """
    if role_index < 0 or role_index >= len(ROLES_CONFIG):
        raise HTTPException(status_code=404, detail="Role not found")
    
    role_config = ROLES_CONFIG[role_index]
    target_ids = set(map(str, role_config["ids"]))  # IDs in data are likely strings
    
    # Use parser module to process vacancies with outlier filtering
    parsed_data = parse_vacancies_for_role(
        VACANCIES, 
        target_ids, 
        filter_outliers=filter_outliers,
        outlier_multiplier=3
    )
    
    salary_values = parsed_data["salary_values"]
    pulkovo_salaries = parsed_data["pulkovo_salaries"]
    market_salaries = parsed_data["market_salaries"]
    bubble_data = parsed_data["bubble_data"]
    experience_values = parsed_data["experience_values"]
    filter_stats = parsed_data["filter_stats"]

    if not salary_values:
        return {"error": "No data found for this role"}
        
    # Aggregate bubble chart data
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
    # Salary histogram (simple bins)
    hist, bin_edges = np.histogram(salary_values, bins=8)
    salary_dist = []
    for i in range(len(hist)):
        salary_dist.append({
            "range": f"{int(bin_edges[i])} - {int(bin_edges[i+1])}",
            "count": int(hist[i])
        })
        
    # Experience distribution
    exp_series = pd.Series(experience_values)
    exp_counts = exp_series.value_counts().to_dict()
    experience_dist = [{"name": k, "value": v} for k, v in exp_counts.items()]
    
    return {
        "role": role_config["name"],
        "metrics": metrics,
        "comparison": comparison,
        "bubble_data": bubble_data_agg,
        "salary_dist": salary_dist,
        "experience_dist": experience_dist,
        "outliers_filtered": filter_outliers,
        "filter_stats": {
            "total_before_filter": filter_stats["total_before_filter"],
            "filtered_out_count": filter_stats["filtered_count"],
            "total_after_filter": len(salary_values),
            "median_salary_for_filter": filter_stats["median_salary"],
            "threshold_salary": filter_stats["threshold_salary"]
        }
    }

@app.get("/dashboard")
async def dashboard():
    if os.path.exists(os.path.join(frontend_path, "index.html")):
        return FileResponse(os.path.join(frontend_path, "index.html"))
    return {"error": "Frontend not found"}

if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")
else:
    print("Frontend build not found. Run 'npm run build' in frontend directory.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("internal_main:app", host="0.0.0.0", port=7777, reload=True)
