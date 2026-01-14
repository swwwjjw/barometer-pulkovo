import os
import json
import asyncio
from datetime import datetime
from fastapi import FastAPI
import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from contextlib import asynccontextmanager

# Configuration
API_URL = "https://api.hh.ru/vacancies"
OUTPUT_FOLDER = "final_folder"
INTERVAL_HOURS = 12

app = FastAPI()

def save_vacancies_to_file(data: dict):
    """Saves the fetched data to a .txt file in the final_folder."""
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"vacancies_{timestamp}.txt"
    filepath = os.path.join(OUTPUT_FOLDER, filename)
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"[{datetime.now()}] Data successfully saved to {filepath}")
    except Exception as e:
        print(f"[{datetime.now()}] Error saving data: {e}")

async def fetch_vacancies():
    """Fetches vacancies from the HH API."""
    print(f"[{datetime.now()}] Fetching data from {API_URL}...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(API_URL, params={"area": 2})
            response.raise_for_status()
            data = response.json()
            save_vacancies_to_file(data)
        except httpx.HTTPError as e:
            print(f"[{datetime.now()}] HTTP Error: {e}")
        except Exception as e:
            print(f"[{datetime.now()}] Unexpected Error: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize scheduler
    scheduler = AsyncIOScheduler()
    # Run once immediately on startup for demonstration/testing or wait for interval?
    # The prompt says "automatically access... once a day (12 hours)".
    # Usually it's good to run it once on startup or schedule it.
    # I'll schedule it to run every 12 hours.
    scheduler.add_job(
        fetch_vacancies,
        trigger=IntervalTrigger(hours=INTERVAL_HOURS),
        id="fetch_vacancies_job",
        name="Fetch vacancies every 12 hours",
        replace_existing=True,
    )
    scheduler.start()
    print(f"[{datetime.now()}] Scheduler started. Job scheduled every {INTERVAL_HOURS} hours.")
    
    # Run fetch immediately so we don't wait 12 hours to see if it works
    asyncio.create_task(fetch_vacancies())
    
    yield
    
    # Shutdown
    scheduler.shutdown()
    print(f"[{datetime.now()}] Scheduler shut down.")

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "HH Vacancies Fetcher Service is running."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=1000, reload=True)
