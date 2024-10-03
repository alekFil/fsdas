FROM python:3.12-slim-bullseye

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Указываем порты, которые нужно открыть
EXPOSE 5013
EXPOSE 8513

# Команда для запуска FastAPI и Streamlit одновременно
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 5013 & streamlit run app/frontend/streamlit_app.py --server.port 8513 --server.headless true"]
