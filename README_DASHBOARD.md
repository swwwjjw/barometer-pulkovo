# Job Market Dashboard Module

This module provides a visualization dashboard for job posting data collected from HH.ru.

## Components

1.  **Backend (`main.py`, `dashboard_service.py`)**:
    *   FastAPI application that collects data from HH.ru (scheduled every 12 hours).
    *   Provides API endpoints for the dashboard (`/api/dashboard/...`).
    *   Parses JSON data from `final_folder`.
    *   Calculates statistics (Salary vs Rating, Pulkovo comparison, distributions).

2.  **Frontend (`static/index.html`)**:
    *   React application (Single Page App).
    *   Uses Recharts for visualization.
    *   Displays:
        *   Job Title Dropdown.
        *   Key Metrics (Min, Max, Avg, Median Salary).
        *   Bubble Chart (Salary vs Employer Rating).
        *   Bar Chart (Pulkovo vs Market).
        *   Salary Distribution.
        *   Work Experience Distribution.

## How to Run

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2.  Run the application:
    ```bash
    python main.py
    ```

3.  Open the dashboard in your browser:
    *   http://localhost:1000/

## Data

*   The application looks for the latest `.txt` file in `final_folder`.
*   A sample file `vacancies_sample.txt` is provided for testing.
*   The system automatically fetches new data every 12 hours.

## Features

*   **Salary Conversion**: Hourly and shift-based salaries are estimated and converted to monthly values.
*   **Employer Rating**: Simulated for demonstration (as it's not directly available in standard API response).
*   **Filtering**: Data is filtered by the selected job title using the predefined Professional Role IDs.
