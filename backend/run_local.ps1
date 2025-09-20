# run_local.ps1

./venv/Scripts/python.exe -c "from app.database import init_db; init_db()"
.\venv\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000
