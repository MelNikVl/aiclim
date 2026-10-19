FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /service
COPY pyproject.toml ./
COPY constraints.txt ./
COPY app ./app
RUN pip install --no-cache-dir -c constraints.txt . && useradd --create-home appuser
USER appuser
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --no-access-log"]
