# YouTube Comment Collector Docker Image
FROM python:3.9-slim

# 作業ディレクトリ設定
WORKDIR /app

# システムパッケージの更新とインストール
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係をコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY main.py .

# 非rootユーザーを作成
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# ヘルスチェック設定
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# アプリケーション実行
CMD ["python", "main.py"]
