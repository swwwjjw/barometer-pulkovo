# External Module - Job Vacancy Fetcher

This module fetches job vacancies from hh.ru API every 12 hours and saves them to a local file.

## Features

- Asynchronous data fetching from hh.ru API
- Scheduled execution every 12 hours using APScheduler
- Automatic grouping of vacancies by keywords
- Atomic file writes to prevent data corruption
- Runs first fetch immediately on startup

## Docker Build and Run

### Build the Docker image

```bash
cd external_module
docker build -t external-module:latest .
```

### Run the container

```bash
docker run -d \
  --name external-module \
  -v /path/to/output:/mnt/bi_sandbox/barometer_vacancies \
  external-module:latest
```

**Note:** Replace `/path/to/output` with the actual path where you want to store the vacancy data.

### Run with docker-compose (from workspace root)

You can also add this service to your docker-compose.yml:

```yaml
services:
  external-module:
    build:
      context: ./external_module
      dockerfile: Dockerfile
    volumes:
      - ./data/vacancies:/mnt/bi_sandbox/barometer_vacancies
    restart: always
```

Then run:

```bash
docker-compose up -d external-module
```

## Configuration

You can modify the following parameters in `external_main.py`:

- `INTERVAL_HOURS`: Frequency of data fetching (default: 12 hours)
- `MAX_PAGES`: Maximum pages to fetch per keyword (default: 20)
- `AREA`: Geographic area ID (default: 2 for Saint Petersburg)
- `PER_PAGE`: Results per page (default: 99)
- `KEYWORDS`: List of search keywords for vacancies

## Output

The module saves data to `/mnt/bi_sandbox/barometer_vacancies/vacancies_current.txt` in JSON format with the following structure:

```json
{
  "metadata": {
    "fetched_at": "2026-02-17T15:00:00",
    "total_vacancies": 1500,
    "total_groups": 20
  },
  "groups": {
    "group_1_keywords_...": {
      "keywords": "keyword phrase",
      "vacancies": [...],
      "count": 75
    }
  }
}
```

## Dependencies

- Python 3.10
- httpx - Async HTTP client
- apscheduler - Task scheduling library
