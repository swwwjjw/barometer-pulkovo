"""
Явное имя модуля парсера для удобной отладки.

Основная реализация пока остается в parser.py для обратной совместимости.
"""

from parser import (  # noqa: F401
    calculate_salary_median,
    filter_salary_outliers,
    get_group_list,
    load_data,
    parse_vacancies_for_group,
    process_salary,
)
