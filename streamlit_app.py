import streamlit as st
import requests
import os
from datetime import datetime

from api.lesson_load import load_lessons

# Конфигурация
API_URL = "http://localhost:8000"
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")
os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'


def main():
    st.set_page_config(page_title="BLANDER", layout="wide")

    # Управление сессией
    if 'token' not in st.session_state:
        show_auth()
    else:
        show_main_interface()


def show_auth():
    """Форма авторизации/регистрации"""
    tab1, tab2 = st.tabs(["Вход", "Регистрация"])

    with tab1:
        with st.form("login"):
            email = st.text_input("Email")
            password = st.text_input("Пароль", type="password")
            if st.form_submit_button("Войти"):
                response = requests.post(
                    f"{API_URL}/auth/login",
                    json={"email": email, "password": password}
                )
                if response.status_code == 200:
                    st.session_state.token = response.json()["access_token"]
                    st.rerun()
                else:
                    st.error("Ошибка авторизации")

    with tab2:
        with st.form("register"):
            email = st.text_input("Email (регистрация)")
            password = st.text_input("Пароль (регистрация)", type="password")
            if st.form_submit_button("Зарегистрироваться"):
                response = requests.post(
                    f"{API_URL}/auth/register",
                    json={"email": email, "password": password}
                )
                if response.status_code == 200:
                    st.success("Регистрация успешна! Войдите в систему")
                else:
                    st.error("Ошибка авторизации")
                    st.error(response.json().get("detail"))


def show_main_interface():
    """Основной интерфейс после авторизации"""
    headers = {"Authorization": f"Bearer {st.session_state.token}"}

    # Навигация
    menu = ["Уроки", "Анализатор", "Подписка", "Выход"]
    choice = st.sidebar.selectbox("Меню", menu)

    if choice == "Уроки":
        show_lessons(headers)
    elif choice == "Анализатор":
        show_analyzer(headers)
    elif choice == "Подписка":
        show_subscription(headers)
    elif choice == "Выход":
        del st.session_state.token
        st.rerun()


def show_lessons(headers):
    """Список уроков"""
    st.header("📚 Уроки деловой переписки")
    # lessons = requests.get(f"{API_URL}/lessons", headers=headers).json()
    lessons = load_lessons()
    # tab = st.tabs(["Уроки"])

    for lesson in lessons:
        with st.expander(f"Урок {lesson['id']}: {lesson['title']}"):
        # with tab:
            st.markdown(f"**Описание:** {lesson['description']}")

            st.markdown(f"**Задание:** {lesson['exercise']['task']}")

            st.markdown("### Советы")
            for idx, point in enumerate(lesson["theory"], 1):
                st.markdown(f"{idx}. {point}")

            st.markdown("### Практика")
            answer = st.text_area("Ваш ответ", key=f"lesson_{lesson['id']}", height=150)

            if st.button("Проверить", key=f"btn_{lesson['id']}"):
                # Анализ ошибок
                text = f"текст ученика: {answer}, эталон: {lesson['exercise']['example_input']}"
                analysis  = requests.post(
                    f"{API_URL}/analyze",
                    json={"text": text},
                    headers=headers
                )
                responce = analysis.json()

                # Обратная связь
                st.markdown(f"Ваша оценка: {responce['score']} / 10 ")
                st.markdown(f"\n **Грамматические ошибки:** {responce['grammar_errors']}")
                st.markdown(f"\n **Стилистические ошибки:** {responce['style_issues']}")
                st.markdown(f"\n **Улучшенная версия:** {responce['improved_text']}")
                st.markdown(f"\n **Рекомендации:** {responce['feedback']}")

                #Добавить прогресс


def show_analyzer(headers):
    """Анализатор текста"""
    st.header("🔍 Анализ письма")
    text = st.text_area("Введите текст письма:", height=300)
    st.markdown(text)

    if st.button("Проанализировать"):
        response = requests.post(
            f"{API_URL}/analyze",
            json={"text": text},
            headers=headers
        )
        if response.status_code == 200:
            result = response.json()
            st.subheader("Результаты анализа")
            st.write(f"Оценка: {result['score']}/100")
            st.subheader("Рекомендации:")
            for feedback in result["feedback"]:
                st.write(f"- {feedback}")
            st.write(f"Улучшенный текст: {result['improved_text']}", height=200)
        else:
            st.markdown(response.json())
            st.error("Ошибка анализа")


def show_subscription(headers):
    """Управление подпиской"""
    st.header("💳 Подписка")
    user_info = requests.get(f"{API_URL}/user", headers=headers).json()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Текущий статус")
        st.write(f"Тариф: {user_info['subscription'].capitalize()}")
        st.write(f"Дата регистрации: {user_info['created_at'][:10]}")

    with col2:
        st.subheader("Сменить тариф")
        plan = st.selectbox("Выберите тариф", ["Base", "Premium"])
        if st.button("Оформить подписку"):
            response = requests.post(
                f"{API_URL}/billing/create-session",
                json={"text": plan},
                headers=headers
            )
            if response.status_code == 200:
                payment_url = response.json()['session_id']
                st.markdown(f"""
                <div style="
                    border: 2px solid #3498db;
                    border-radius: 10px;
                    padding: 20px;
                    text-align: center;
                    margin: 20px 0;
                ">
                    <h3 style="color: #2c3e50;">Подписка</h3>
                    <a href="{payment_url}" target="_blank">
                        <button style="
                            background: #3498db;
                            color: white;
                            padding: 12px 30px;
                            border: none;
                            border-radius: 25px;
                            font-size: 16px;
                            cursor: pointer;
                        ">Активировать подписку →</button>
                    </a>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error("Ошибка при создании платежа")


if __name__ == "__main__":
    main()