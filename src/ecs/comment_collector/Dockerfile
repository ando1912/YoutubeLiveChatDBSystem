FROM python:3.9-slim

WORKDIR /app

# システムパッケージの更新
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Pythonの依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# 非rootユーザーで実行
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# アプリケーション実行
CMD ["python", "main.py"]
