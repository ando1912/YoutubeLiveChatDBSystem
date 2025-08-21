# YouTube Live Chat Collector

YouTubeライブ配信のコメントをリアルタイムで収集・保存するWebアプリケーションシステム

## システム概要

- YouTubeチャンネルのライブ配信を自動監視
- リアルタイムでコメントを収集・保存
- Webインターフェースでデータを閲覧
- AWS上でサーバーレス構成により低コストで運用

## アーキテクチャ

- **フロントエンド**: React.js (S3 Static Website)
- **バックエンド**: AWS Lambda + API Gateway
- **コメント収集**: ECS Fargate + pytchat
- **データベース**: DynamoDB
- **インフラ**: Terraform
- **デプロイ**: Ansible

## ディレクトリ構成

```
├── terraform/                 # インフラ定義
│   ├── environments/
│   │   └── dev/               # 開発環境設定
│   └── modules/               # Terraformモジュール
│       ├── networking/        # VPC、サブネット
│       ├── storage/           # DynamoDB
│       ├── compute/           # Lambda、ECS
│       ├── messaging/         # SQS、EventBridge
│       ├── api/              # API Gateway
│       └── frontend/         # S3、CloudFront
├── src/                      # ソースコード
│   ├── lambda/               # Lambda関数
│   │   ├── rss_monitor/      # RSS監視
│   │   ├── stream_status_checker/  # 配信状態チェック
│   │   ├── ecs_task_launcher/      # ECS制御
│   │   └── api_handler/      # REST API
│   ├── ecs/                  # ECSコンテナ
│   │   └── comment_collector/ # コメント収集
│   └── frontend/             # Webアプリケーション
│       └── react-app/
├── ansible/                  # デプロイ自動化
│   ├── playbooks/
│   └── roles/
└── docs/                     # ドキュメント
    ├── system_design.md      # システム設計書
    ├── functional_design.md  # 機能設計書
    └── data_model_and_api.md # データモデル・API仕様
```

## セットアップ手順

### 1. 前提条件

- AWS CLI設定済み
- Terraform >= 1.0
- Ansible >= 2.9
- Docker
- Node.js >= 16

### 2. 環境設定

```bash
# リポジトリクローン
git clone <repository-url>
cd 250820_YoutubeLiveChatCollector

# Terraform変数設定
cp terraform/environments/dev/terraform.tfvars.example terraform/environments/dev/terraform.tfvars
# terraform.tfvarsを編集してYouTube API Keyなどを設定
```

### 3. インフラ構築

```bash
cd terraform/environments/dev
terraform init
terraform plan
terraform apply
```

### 4. アプリケーションデプロイ

```bash
# Lambda関数デプロイ
cd ../../../ansible
ansible-playbook playbooks/deploy-lambda.yml

# ECSコンテナビルド・デプロイ
cd ../src/ecs/comment_collector
docker build -t comment-collector .
# ECRにプッシュ（詳細は後述）

# フロントエンドビルド・デプロイ
cd ../../frontend/react-app
npm install
npm run build
# S3にデプロイ（詳細は後述）
```

## 使用方法

1. Webアプリケーションにアクセス
2. 監視したいYouTubeチャンネルを追加
3. ライブ配信が開始されると自動的にコメント収集開始
4. 収集されたコメントをWebで確認

## 設定

### YouTube Data API

1. Google Cloud Consoleでプロジェクト作成
2. YouTube Data API v3を有効化
3. APIキーを取得
4. `terraform.tfvars`に設定

### IP制限

本番環境では`allowed_ip_addresses`を適切に設定してください。

## 監視・運用

- CloudWatch Logsでログ確認
- DynamoDBでデータ確認
- コスト監視（月額$2-3想定）

## トラブルシューティング

### よくある問題

1. **YouTube API制限**
   - 1日10,000 units制限
   - 制限超過時は翌日まで待機

2. **ECS Task起動失敗**
   - CloudWatch Logsでエラー確認
   - セキュリティグループ設定確認

3. **Lambda関数エラー**
   - CloudWatch Logsでエラー詳細確認
   - IAM権限設定確認

## 開発

### ローカル開発環境

```bash
# フロントエンド開発サーバー起動
cd src/frontend/react-app
npm start

# Lambda関数のローカルテスト
cd src/lambda/rss_monitor
python -m pytest tests/
```

### デプロイ

各コンポーネントのデプロイ手順は`docs/deployment_guide.md`を参照

## ライセンス

MIT License

## 貢献

プルリクエストやイシューの報告を歓迎します。

---

**作成日**: 2025-08-21  
**バージョン**: 1.0
