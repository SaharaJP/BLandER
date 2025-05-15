#!/bin/bash

rm -f blander.db

# run FastAPI backend
uvicorn api.main:app --host 0.0.0.0 --port 8000 &

# run frontend
streamlit run streamlit_app.py --server.port=8501 --server.address=0.0.0.0