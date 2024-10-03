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
