"""
Parser module for vacancy data processing.
Contains functions for loading, parsing and filtering vacancy data.
"""
import json
import os
from typing import List, Dict, Optional, Any
import numpy as np


# Data file path - use latest available file
DATA_FILE = os.path.join(os.path.dirname(__file__), "../final_folder/vacancies_20260209_145339.txt")

# Experience mapping (approximate years for sorting/charting)
EXPERIENCE_MAP = {
    "noExperience": 0,
    "between1And3": 2,
    "between3And6": 4.5,
    "moreThan6": 8
}


def load_data(file_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load vacancy data from a JSON file.
    Supports both old format ({"items": [...]}) and new format ({"groups": {...}}).
    
    Args:
        file_path: Optional path to the data file. Uses default if not provided.
        
    Returns:
        Dictionary with 'metadata' and 'groups' keys (new format) or 
        legacy format converted to groups structure.
    """
    target_file = file_path or DATA_FILE
    
    if not os.path.exists(target_file):
        # Try absolute path as fallback for newest file
        fallback_paths = [
            "/workspace/final_folder/vacancies_20260209_145339.txt",
            "/workspace/final_folder/vacancies_20260207_144420.txt",
            "/workspace/final_folder/vacancies_20260125_144856.txt"
        ]
        for fallback in fallback_paths:
            if os.path.exists(fallback):
                target_file = fallback
                break
        else:
            return {"metadata": {}, "groups": {}}
    
    with open(target_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Check for new format (with groups)
    if "groups" in data:
        return data
    
    # Old format (with items) - convert to groups structure
    return {
        "metadata": {"total_vacancies": len(data.get("items", []))},
        "groups": {"all_vacancies": {"keywords": "all", "vacancies": data.get("items", [])}}
    }


def get_group_list(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract list of groups with their metadata.
    
    Args:
        data: The full JSON data with groups structure.
        
    Returns:
        List of group dictionaries with name, keywords, and vacancy count.
    """
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

def filter_salary_outliers(vacancies: List[Dict[str, Any]], 
                           high_multiplier: float = 3,
                           low_divisor: float = 5,
                           return_stats: bool = False) -> Any:
    """
    Filter out vacancies with salaries that are too high or too low compared to median.
    
    This function removes outlier vacancies where the average salary exceeds
    the median salary multiplied by high_multiplier (default 3x) OR is below
    the median salary divided by low_divisor (default median/3).
    
    Args:
        vacancies: List of vacancy items.
        high_multiplier: Upper threshold multiplier relative to median (default 3).
        low_divisor: Lower threshold divisor relative to median (default 3).
        return_stats: If True, returns tuple (filtered_vacancies, stats_dict).
        
    Returns:
        If return_stats=False: List of vacancies with salaries within acceptable range.
        If return_stats=True: Tuple of (filtered_vacancies, stats_dict) where stats_dict
            contains filtering statistics for both high and low outliers.
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
                "filtered_high_count": 0,
                "filtered_low_count": 0,
                "filtered_total_count": 0,
                "median": None,
                "high_threshold": None,
                "low_threshold": None
            }
        return vacancies_without_salary
    
    # Calculate median and thresholds
    salary_values = [s for _, s in salaries_with_vacancies]
    median_salary = float(np.median(salary_values))
    high_threshold = median_salary * high_multiplier
    low_threshold = median_salary / low_divisor
    
    # Filter out high and low outliers
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
    
    # Include vacancies without salary info
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
    """
    Parse and process vacancies for a specific group with optional outlier filtering.
    
    Args:
        vacancies: List of vacancy items from a group.
        filter_outliers: Whether to filter out high salary outliers.
        
    Returns:
        Dictionary containing processed vacancy data and statistics.
        Includes 'filter_stats' with counts before/after filtering.
    """
    # Track filtering statistics
    filter_stats = {
        "total_before_filter": len(vacancies),
        "filtered_count": 0,
        "median_salary": None,
        "threshold_salary": None
    }
    
    # Optionally filter salary outliers (both high and low)
    if filter_outliers:
        vacancies, outlier_stats = filter_salary_outliers(
            vacancies, return_stats=True
        )
        filter_stats["filtered_count"] = outlier_stats["filtered_total_count"]
        filter_stats["median_salary"] = outlier_stats["median"]
        filter_stats["threshold_salary"] = outlier_stats["high_threshold"]
    
    # Process salaries and experience
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
        
        # Employment type
        employment_obj = v.get("employment", {})
        employment_name = employment_obj.get("name", "Не указано")
        employment_values.append(employment_name)
        
        # Schedule type
        schedule_obj = v.get("schedule", {})
        schedule_name = schedule_obj.get("name", "Не указано")
        schedule_values.append(schedule_name)
        
        processed_vacancies.append(v)
        salary_values.append(avg_salary)
        experience_values.append(exp_name)
        
        # Get employer information
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
