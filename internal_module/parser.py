"""
Parser module for vacancy data processing.
Contains functions for loading, parsing and filtering vacancy data.
"""
import json
import os
from typing import List, Dict, Optional, Any
import numpy as np


# Data file path
DATA_FILE = os.path.join(os.path.dirname(__file__), "../final_folder/vacancies_20260125_144856.txt")

# Predefined role mapping
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

# Experience mapping (approximate years for sorting/charting)
EXPERIENCE_MAP = {
    "noExperience": 0,
    "between1And3": 2,
    "between3And6": 4.5,
    "moreThan6": 8
}


def load_data(file_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load vacancy data from a JSON file.
    
    Args:
        file_path: Optional path to the data file. Uses default if not provided.
        
    Returns:
        List of vacancy items.
    """
    target_file = file_path or DATA_FILE
    
    if not os.path.exists(target_file):
        # Try absolute path as fallback
        if os.path.exists("/workspace/final_folder/vacancies_20260125_144856.txt"):
            with open("/workspace/final_folder/vacancies_20260125_144856.txt", "r", encoding="utf-8") as f:
                return json.load(f).get("items", [])
        return []
    
    with open(target_file, "r", encoding="utf-8") as f:
        return json.load(f).get("items", [])


def process_salary(item: Dict[str, Any]) -> Optional[Dict[str, float]]:
    """
    Extract and normalize salary to monthly rubles.
    
    Args:
        item: Vacancy item dictionary.
        
    Returns:
        Dictionary with 'from', 'to', 'avg' salary values, or None if invalid.
    """
    salary = item.get("salary")
    if not salary:
        return None
    
    if salary.get("currency") != "RUR":
        # Simple skip for non-RUR currencies as conversion rates are not provided
        return None

    s_from = salary.get("from")
    s_to = salary.get("to")
    
    if s_from is None and s_to is None:
        return None
    
    # Calculate initial values
    val_from = s_from if s_from is not None else s_to
    val_to = s_to if s_to is not None else s_from
    
    # Check multiplier (Hourly/Shift)
    # First check salary range
    salary_range = item.get("salary_range")
    multiplier = 1.0
    
    # Heuristic detection based on API structure or values
    # If explicit mode is present in salary range
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


def filter_vacancies_by_role(vacancies: List[Dict[str, Any]], 
                              role_ids: set) -> List[Dict[str, Any]]:
    """
    Filter vacancies by professional role IDs.
    
    Args:
        vacancies: List of vacancy items.
        role_ids: Set of role IDs to filter by.
        
    Returns:
        List of vacancies matching the role IDs.
    """
    filtered = []
    for v in vacancies:
        v_roles = v.get("professional_roles", [])
        v_role_ids = {r.get("id") for r in v_roles}
        
        if role_ids.intersection(v_role_ids):
            filtered.append(v)
    
    return filtered


def calculate_salary_median(vacancies: List[Dict[str, Any]]) -> Optional[float]:
    """
    Calculate median salary from a list of vacancies.
    
    Args:
        vacancies: List of vacancy items.
        
    Returns:
        Median salary value or None if no valid salaries found.
    """
    salaries = []
    for v in vacancies:
        salary_info = process_salary(v)
        if salary_info:
            salaries.append(salary_info["avg"])
    
    if not salaries:
        return None
    
    return float(np.median(salaries))


def filter_high_salary_outliers(vacancies: List[Dict[str, Any]], 
                                 multiplier: float = 1,
                                 return_stats: bool = False) -> Any:
    """
    Filter out vacancies with salaries that are higher than multiplier times the median.
    
    This function removes outlier vacancies where the average salary exceeds
    the median salary multiplied by the given multiplier (default 3x).
    
    Args:
        vacancies: List of vacancy items.
        multiplier: Salary threshold multiplier relative to median (default 3).
        return_stats: If True, returns tuple (filtered_vacancies, stats_dict).
        
    Returns:
        If return_stats=False: List of vacancies with salaries within acceptable range.
        If return_stats=True: Tuple of (filtered_vacancies, stats_dict) where stats_dict
            contains 'total_before', 'total_after', 'filtered_count', 'median', 'threshold'.
    """
    # First, collect all valid salaries to calculate median
    salaries_with_vacancies = []
    vacancies_without_salary = []
    
    for v in vacancies:
        salary_info = process_salary(v)
        if salary_info:
            salaries_with_vacancies.append((v, salary_info["avg"]))
        else:
            # Keep vacancies without salary info
            vacancies_without_salary.append(v)
    
    if not salaries_with_vacancies:
        if return_stats:
            return vacancies_without_salary, {
                "total_before": len(vacancies_without_salary),
                "total_after": len(vacancies_without_salary),
                "filtered_count": 0,
                "median": None,
                "threshold": None
            }
        return vacancies_without_salary
    
    # Calculate median
    salary_values = [s for _, s in salaries_with_vacancies]
    median_salary = float(np.median(salary_values))
    threshold = median_salary * multiplier
    
    # Filter out high outliers
    filtered = []
    filtered_out_count = 0
    for v, salary in salaries_with_vacancies:
        if salary <= threshold:
            filtered.append(v)
        else:
            filtered_out_count += 1
    
    # Include vacancies without salary info
    filtered.extend(vacancies_without_salary)
    
    if return_stats:
        total_before = len(salaries_with_vacancies) + len(vacancies_without_salary)
        return filtered, {
            "total_before": total_before,
            "total_after": len(filtered),
            "filtered_count": filtered_out_count,
            "median": median_salary,
            "threshold": threshold
        }
    
    return filtered


def parse_vacancies_for_role(vacancies: List[Dict[str, Any]], 
                              role_ids: set,
                              filter_outliers: bool = True,
                              outlier_multiplier: float = 1) -> Dict[str, Any]:
    """
    Parse and process vacancies for a specific role with optional outlier filtering.
    
    Args:
        vacancies: List of all vacancy items.
        role_ids: Set of role IDs to filter by.
        filter_outliers: Whether to filter out high salary outliers.
        outlier_multiplier: Multiplier for outlier threshold (default 3x median).
        
    Returns:
        Dictionary containing processed vacancy data and statistics.
        Includes 'filter_stats' with counts before/after filtering.
    """
    # Filter by role
    role_vacancies = filter_vacancies_by_role(vacancies, role_ids)
    
    # Track filtering statistics
    filter_stats = {
        "total_before_filter": len(role_vacancies),
        "filtered_count": 0,
        "median_salary": None,
        "threshold_salary": None
    }
    
    # Optionally filter high salary outliers
    if filter_outliers:
        role_vacancies, outlier_stats = filter_high_salary_outliers(
            role_vacancies, outlier_multiplier, return_stats=True
        )
        filter_stats["filtered_count"] = outlier_stats["filtered_count"]
        filter_stats["median_salary"] = outlier_stats["median"]
        filter_stats["threshold_salary"] = outlier_stats["threshold"]
    
    # Process salaries and experience
    pulkovo_salaries = []
    market_salaries = []
    bubble_data = []
    salary_values = []
    experience_values = []
    processed_vacancies = []
    
    for v in role_vacancies:
        salary_info = process_salary(v)
        if not salary_info:
            continue
            
        avg_salary = salary_info["avg"]
        
        # Check employer
        employer_id = v.get("employer", {}).get("id")
        if employer_id == "666661":
            pulkovo_salaries.append(avg_salary)
        else:
            market_salaries.append(avg_salary)
            
        # Experience
        exp_obj = v.get("experience", {})
        exp_id = exp_obj.get("id", "noExperience")
        exp_name = exp_obj.get("name", "Нет опыта")
        exp_numeric = EXPERIENCE_MAP.get(exp_id, 0)
        
        processed_vacancies.append(v)
        salary_values.append(avg_salary)
        experience_values.append(exp_name)
        
        bubble_data.append({
            "id": v.get("id"),
            "salary": avg_salary,
            "experience": exp_numeric,
            "experience_label": exp_name,
            "title": v.get("name")
        })
    
    return {
        "vacancies": processed_vacancies,
        "pulkovo_salaries": pulkovo_salaries,
        "market_salaries": market_salaries,
        "bubble_data": bubble_data,
        "salary_values": salary_values,
        "experience_values": experience_values,
        "filter_stats": filter_stats
    }
