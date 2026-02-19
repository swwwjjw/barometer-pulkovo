# Docker Setup Guide

This document explains how to build and run the application using Docker.

## Project Structure

```
.
├── external_module/          # Data fetching service
│   ├── Dockerfile
│   ├── external_main.py
│   └── external_requirements.txt
│
└── internal_module/          # Web application service
    ├── Dockerfile
    ├── internal_main.py
    ├── parser.py
    ├── b1_data.json
    ├── internal_requirements.txt
    └── frontend/             # React frontend
        ├── dist/             # Built frontend (created by npm run build)
        └── ...
```

## External Module (Data Fetcher)

### Purpose
Fetches vacancy data from hh.ru API every 12 hours and saves it to a shared data directory.

### Building

```bash
cd external_module
docker build -t external_module:latest .
```

### Running

```bash
docker run -d --name external_module \
  -v /mnt/bi_sandbox/barometer_vacancies:/app/data \
  external_module:latest
```

**Volume Mounts:**
- `/app/data` - Directory where vacancy data will be saved

**Configuration:**
- Edit `external_main.py` to modify:
  - `INTERVAL_HOURS`: How often to fetch data (default: 12 hours)
  - `KEYWORDS`: List of job search keywords
  - `AREA`: Region ID for hh.ru API (default: 2 for St. Petersburg)

### Stopping

```bash
docker stop external_module
docker rm external_module
```

## Internal Module (Web Application)

### Purpose
Serves the web application with data visualization and analytics.

### Building

**Important:** Build the frontend first!

```bash
# Step 1: Build the frontend
cd internal_module/frontend
npm install
npm run build

# Step 2: Build the Docker image
cd ..  # Back to internal_module directory
docker build -t internal_module:latest .
```

### Running

```bash
docker run -d --name internal_module \
  -v /mnt/allshare_fileserver/barometer_vacancies:/app/data \
  -v vacancies_folder:/app/work \
  -p 8000:8000 \
  internal_module:latest
```

**Volume Mounts:**
- `/app/data` - Shared directory where external_module writes data
- `/app/work` - Working directory for processed vacancy data

**Port Mappings:**
- `8000:8000` - Web application port

**Accessing the Application:**
- Open browser to: `http://localhost:8000`
- API documentation: `http://localhost:8000/docs`

### Stopping

```bash
docker stop internal_module
docker rm internal_module
```

## Data Flow

```
┌─────────────────────┐
│  external_module    │
│  (Data Fetcher)     │
│                     │
│  Fetches from HH.ru │
└──────────┬──────────┘
           │
           │ Writes to /app/data/
           │ vacancies_current.txt
           ↓
    ┌─────────────┐
    │  Shared     │
    │  Volume     │
    └──────┬──────┘
           │
           │ Reads from /app/data/
           ↓
┌──────────────────────┐
│  internal_module     │
│  (Web App)           │
│                      │
│  - Processes data    │
│  - Serves frontend   │
│  - Provides API      │
└──────────────────────┘
```

## Directory Paths Inside Containers

### External Module Container
- Working directory: `/app`
- Data output: `/app/data/vacancies_current.txt`
- Script location: `/app/external_main.py`

### Internal Module Container
- Working directory: `/app`
- Module location: `/app/internal_module/`
- Frontend files: `/app/internal_module/frontend/dist/`
- Data input: `/app/data/vacancies_current.txt`
- Working files: `/app/work/vacancies_current.txt`
- B1 data: `/app/internal_module/b1_data.json`

## Troubleshooting

### Frontend not building
```bash
cd internal_module/frontend
npm install
npm run build
```

### Port 8000 already in use
```bash
# Use a different port
docker run -d --name internal_module \
  -v /mnt/allshare_fileserver/barometer_vacancies:/app/data \
  -v vacancies_folder:/app/work \
  -p 8080:8000 \
  internal_module:latest
```

### Data not updating
1. Check external_module logs: `docker logs external_module`
2. Verify volume mounts are correct
3. Ensure both containers use the same shared directory

### Container logs
```bash
# External module logs
docker logs -f external_module

# Internal module logs
docker logs -f internal_module
```

## Development vs Production

### Development
For development, you don't need Docker. Run services directly:

```bash
# Terminal 1: External module
cd external_module
pip install -r external_requirements.txt
python external_main.py

# Terminal 2: Internal module backend
cd internal_module
pip install -r internal_requirements.txt
uvicorn internal_module.internal_main:app --reload

# Terminal 3: Frontend dev server
cd internal_module/frontend
npm install
npm run dev
```

### Production
Use Docker as described above for production deployments.

## Mobile Responsive Design

The web application is fully responsive and optimized for mobile devices:
- ✓ Responsive layouts for all screen sizes (360px+)
- ✓ Touch-friendly controls
- ✓ Optimized charts for mobile viewing
- ✓ Scrollable tables on small screens
- ✓ Progressive Web App (PWA) support

## Notes

1. **Volume Persistence**: Named volumes (`vacancies_folder`) persist data between container restarts
2. **Network**: If running both containers, they can share data via mounted volumes
3. **Updates**: To update the application, rebuild the image and restart the container
4. **Logs**: Both containers log to stdout, accessible via `docker logs`
