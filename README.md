external:
source /venv/bin/activate
python3 external_main.py


internal:
source /venv/bin/activate
cd frontend
npm ci
npm run build
cd ..
python3 internal_main.py