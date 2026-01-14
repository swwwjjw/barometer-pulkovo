# HH Vacancies Fetcher

This service fetches vacancies from HeadHunter API for Saint Petersburg (area=2) and saves them to the `final_folder`.

## Prerequisites

- Python 3.8+
- pip

## Installation

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the App

You can start the application using Python:

```bash
python main.py
```

Or directly with uvicorn:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Features

- **Automatic Fetching**: The app is configured to fetch vacancies immediately on startup and then every 12 hours.
- **API Endpoint**: There is a health check endpoint at `http://localhost:8000/`.
- **Storage**: Fetched data is saved as JSON files in the `final_folder`.
