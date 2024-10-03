import os

import requests
import streamlit as st


def setup_config() -> None:
    """
    Настраивает параметры страницы Streamlit и изменяет стиль страницы.

    Эта функция задает заголовок страницы, иконку, макет, а также скрывает
    некоторые элементы интерфейса Streamlit, такие как главное меню и футер.
    """
    # Настройка страницы
    st.set_page_config(
        page_title="Сервис по поиску дубликатов записей спортсменов",
        page_icon="⛸️",
        layout="wide",
    )

    st.markdown(
        """
        <style>
            .reportview-container {
                margin-top: -2em;
            }
            #MainMenu {visibility: hidden;}
            .stDeployButton {display:none;}
            footer {visibility: hidden;}
            #stDecoration {display:none;}
        </style>
        """,
        unsafe_allow_html=True,
    )


class StreamlitService:
    def __init__(self, api_url: str):
        self.api_url = api_url
        self.auth_disabled = (
            os.getenv("DISABLE_AUTH", "false").lower() == "true"
        )  # Проверяем, отключена ли авторизация
        # Используем st.session_state для хранения токена и флага авторизации
        if "token" not in st.session_state:
            st.session_state["token"] = None
        if "authenticated" not in st.session_state:
            if self.auth_disabled:
                st.session_state["authenticated"] = True
            else:
                st.session_state["authenticated"] = False

    def login(self):
        if self.auth_disabled:
            st.session_state["authenticated"] = (
                True  # Автоматическая авторизация, если отключена
            )
            return

        st.title("Авторизация")

        # Форма для ввода логина и пароля
        username = st.text_input("Введите логин")
        password = st.text_input("Введите пароль", type="password")

        if st.button("Войти"):
            if username and password:
                response = self.get_token(username, password)
                if response:
                    st.session_state["authenticated"] = True
                    st.rerun()  # Перезагрузка интерфейса для отображения следующего шага
                else:
                    st.error("Ошибка авторизации, проверьте логин и пароль.")
            else:
                st.error("Введите логин и пароль.")

    def get_token(self, username, password):
        data = {"username": username, "password": password}
        response = requests.post(f"{self.api_url}/auth/token", data=data)
        if response.status_code == 200:
            st.session_state["token"] = response.json()["access_token"]
            return True
        return False

    def get_school_matches(self, school_name):
        if st.session_state["token"] or self.auth_disabled:
            headers = (
                {"Authorization": f"Bearer {st.session_state['token']}"}
                if st.session_state["token"]
                else {}
            )
            response = requests.post(
                f"{self.api_url}/data/get_school_matches",
                json={"school_name": school_name},
                headers=headers,
            )
            if response.status_code == 200:
                return response.json()
            else:
                st.error("Не удалось получить данные.")
        else:
            st.warning("Сначала необходимо авторизоваться.")
        return None

    def reload_resources(self):
        if st.session_state["token"] or self.auth_disabled:
            headers = (
                {"Authorization": f"Bearer {st.session_state['token']}"}
                if st.session_state["token"]
                else {}
            )
            response = requests.post(
                f"{self.api_url}/data/reload_resources/",
                headers=headers,
            )
            if response.status_code == 200:
                return True
            else:
                st.error("Не удалось обновить данные.")
        else:
            st.warning("Сначала необходимо авторизоваться.")
        return None

    def run(self):
        setup_config()
        # Если есть токен в session_state или пользователь авторизован, показываем анализ
        if st.session_state["authenticated"]:
            st.title("🔍 Сервис анализа данных платформы МойЧемпион.РФ ⛸️")
            tab1, tab2 = st.tabs(["Школы", "Другие виды анализа"])

            with tab1:
                school_name = st.text_input("Введите название школы")

                if st.button("Распознать название"):
                    if school_name:
                        # Отправка POST-запроса к API для распознавания наименования школы
                        matches = self.get_school_matches(school_name)
                        if matches:
                            st.write(matches)
                    else:
                        # Вывод сообщения, если не введено название школы
                        st.write("Пожалуйста, введите название школы")

                if st.button("Обновить данные сервиса"):
                    if self.reload_resources():
                        st.success("Данные обновлены.")

            with tab2:
                st.info("В разработке")

        else:
            self.login()


if __name__ == "__main__":
    streamlit_service = StreamlitService(api_url=os.getenv("API_URL"))
    streamlit_service.run()
