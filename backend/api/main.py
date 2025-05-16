import json
import os
from json import JSONDecodeError

import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from . import database, auth, schemas
from fastapi.middleware.cors import CORSMiddleware
import requests

import stripe
import ollama
import logging

from .database import get_db

app = FastAPI()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logging.basicConfig(level=logging.DEBUG)


# Регистрация пользователя
@app.post("/auth/register")
async def register(
        user: schemas.UserCreate,
        db: Session = Depends(get_db)
):
    existing_user = db.query(database.User).filter_by(email=user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = database.User(
        email=user.email,
        password_hash=auth.get_password_hash(user.password)
    )
    db.add(new_user)
    db.commit()
    return {
        "id": new_user.id,
        "email": new_user.email,
        "message": "User created successfully"
    }


# Авторизация
@app.post("/auth/login")
async def login(
        created_user: schemas.UserCreate,
        db: Session = Depends(get_db)
):
    user = db.query(database.User).filter_by(email=created_user.email).first()
    if not user or not auth.verify_password(created_user.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"access_token": auth.create_access_token({"sub": user.email})}

# Авторизация
@app.get("/user")
async def user(
        db: Session = Depends(get_db)
):
    user = db.query(database.User).filter_by().first()
    # Добавить обработку ошибок
    return user

# Анализ текста (требует авторизации)
@app.post("/analyze")
async def analyze_text(
        text: schemas.TextRequest,
        user: schemas.UserCreate = Depends(auth.get_current_user),
        db: Session = Depends(get_db)
):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "mistral:7b-instruct-q4_K_M",
                "prompt": f"""
                Отвечай на русском языке
                Ты эксперт по деловой переписке. Проанализируй письмо:
                {text}

                Формат ответа (JSON):
                {{
                    "score": 0-10,
                    "feedback": ["...", "..."],
                    "grammar_errors": ["...", "..."],
                    "style_issues": ["...", "..."],
                    "improved_text": "..."
                }}
                """,
                "format": "json",
                "stream": False,
                "options": {"temperature": 0.3}
            },
        )

        if response.status_code == 200:
            # Очистка ответа от не-JSON
            raw_response = response.json()["response"]
            cleaned_response = raw_response.strip().replace('```json', '').replace('```', '')

            try:
                return json.loads(cleaned_response)
            except JSONDecodeError:
                # Восстановление некорректного JSON
                return json.loads(cleaned_response + '"}')
        return {"error": f"API Error: {response.status_code}"}

    except Exception as e:
        return {"error": str(e)}

# Платежи через Stripe
@app.post("/billing/create-session")
async def create_payment_session(
        plan: schemas.TextRequest,
        # user: schemas.UserCreate = Depends(auth.get_current_user),
        db: Session = Depends(get_db),
):
    try:
        #Вынести потом апи в .env
        stripe.api_key = "sk_test_51RM9PPQRdTZh3F2HIfV66v1uVHrD2wEypVhLjGwZ48IoTfC7Hz2cuqYKeRrqgcyp0QLBhdTjcXJcyo1FNmabPnDz006a5a3iOK"
        if plan == "Base":
            price = "price_1ROzHzQRdTZh3F2H0ZFxQip7"
        else:
            price = "price_1ROzHbQRdTZh3F2HWIkDt1xO"
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": price,
                "quantity": 1,
            }],
            mode="subscription",
            success_url="http://localhost:8501/success",
            # customer=user.stripe_id
        )
        return {"session_id": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000)