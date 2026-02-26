# internal_module Docker setup

This repository includes Docker configuration for running `internal_module` with FastAPI + built frontend.

## Requirements

- Docker
- Docker Compose (plugin: `docker compose`)
- Host directory `/mnt/allshare_fileserver/barometer_vacancies` available on the machine

The folder `/mnt/allshare_fileserver/barometer_vacancies` is mounted into the container at the same path.

## Build image

From the repository root:

```bash
docker compose build internal_module
```

## Start container

```bash
docker compose up -d internal_module
```

The app will be available at:

- http://localhost:8083

## Build + start in one command

```bash
docker compose up -d --build internal_module
```

## Stop container

```bash
docker compose down
```
