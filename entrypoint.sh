#!/bin/bash

# Удаление базы данных (если нужно)
rm -f blander.db

# Запуск FastAPI и Streamlit с обработкой сигналов
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 &
PID1=$!

streamlit run frontend/streamlit_app.py --server.port=8501 --server.address=0.0.0.0 &
PID2=$!

# Ожидание завершения процессов
wait $PID1 $PID2