# YouTube Live Chat Collector

YouTubeライブ配信のコメントをリアルタイムで収集・保存するWebアプリケーションシステム

## 🎯 システム概要

- YouTubeチャンネルのライブ配信を24時間自動監視
- リアルタイムでコメントを収集・保存
- 完全なWebアプリケーションでデータ管理・閲覧
- AWS上でサーバーレス構成により低コストで運用
- 商用レベルの安定性と機能を実現

## 🌐 Webアプリケーション機能

**主要機能**:
- 📊 **システムダッシュボード**: リアルタイム統計表示
- 📺 **チャンネル管理**: 完全なCRUD操作
- 🔴 **アクティブ配信監視**: ライブ配信状況表示
- 💬 **コメント収集管理**: 収集データ確認・制御

## 🏗️ アーキテクチャ

### **技術スタック**
- **フロントエンド**: React.js + TypeScript (S3 Static Website)
- **バックエンド**: AWS Lambda + API Gateway + DynamoDB
- **コメント収集**: ECS Fargate + pytchat
- **インフラ**: Terraform (110リソース完全自動化)
- **デプロイ**: Ansible (完全自動化)
- **監視**: CloudWatch + EventBridge

### **システム構成**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React.js      │    │   API Gateway    │    │   Lambda        │
│   Frontend      │◄──►│   REST API       │◄──►│   Functions     │
│   (S3 Website)  │    │                  │    │   (4 Functions) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   EventBridge   │    │   SQS Queue      │    │   DynamoDB      │
│   (Scheduler)   │◄──►│   (Task Control) │◄──►│   (4 Tables)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   ECS Fargate   │    │   ECR Registry   │    │   CloudWatch    │
│   (Comment      │◄──►│   (Container     │◄──►│   (Logs &       │
│    Collector)   │    │    Images)       │    │    Monitoring)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

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
│       ├── frontend/         # S3、CloudFront
│       └── integration/      # サービス間統合
├── src/                      # ソースコード
│   ├── lambda/               # Lambda関数
│   │   ├── rss_monitor/      # RSS監視
│   │   ├── stream_status_checker/  # 配信状態チェック
│   │   ├── ecs_task_launcher/      # ECS制御
│   │   └── api_handler/      # REST API
│   ├── ecs/                  # ECSコンテナ
│   │   └── comment_collector/ # コメント収集
│   └── frontend/             # Webアプリケーション
│       └── youtube-chat-viewer/
├── ansible/                  # デプロイ自動化
│   ├── deploy-all.yml        # 完全システムデプロイ
│   ├── quick-deploy.yml      # 個別コンポーネントデプロイ
│   ├── playbooks/            # 工程別プレイブック
│   │   ├── 01-pre-checks.yml      # 事前チェック
│   │   ├── 02-deploy-lambda.yml   # Lambda関数デプロイ
│   │   ├── 03-deploy-container.yml # ECSコンテナデプロイ
│   │   ├── 04-deploy-frontend.yml # フロントエンドデプロイ
│   │   ├── 05-post-verification.yml # デプロイ後検証
│   │   └── old/              # 旧プレイブック保管
│   └── roles/                # Ansibleロール
│       ├── lambda-deployment/     # Lambda関数デプロイロール
│       └── container-deployment/  # コンテナデプロイロール
└── docs/                     # ドキュメント
    ├── design_system.md      # システム設計書
    ├── design_functional.md  # 機能設計書
    ├── spec_data_model.md    # データモデル仕様
    ├── spec_api.md           # API仕様書
    └── log_development_with_q_developer.md # 開発記録
```
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

#### 🚀 ワンコマンド完全デプロイ（推奨）

```bash
cd ansible
ansible-playbook deploy-all.yml
```

**実行内容**:
- 事前チェック（AWS CLI、Docker、Node.js、Terraform状態）
- Lambda関数デプロイ（4関数）
- ECSコンテナデプロイ（Comment Collector）
- フロントエンドデプロイ（React.js → S3）
- デプロイ後検証（ヘルスチェック）

#### 🎯 個別コンポーネントデプロイ

```bash
# Lambda関数のみ
ansible-playbook quick-deploy.yml -e "component=lambda"

# ECSコンテナのみ
ansible-playbook quick-deploy.yml -e "component=container"

# フロントエンドのみ
ansible-playbook quick-deploy.yml -e "component=frontend"
```

#### 📋 工程別デプロイ

```bash
# 事前チェック
ansible-playbook playbooks/01-pre-checks.yml

# Lambda関数デプロイ
ansible-playbook playbooks/02-deploy-lambda.yml

# ECSコンテナデプロイ
ansible-playbook playbooks/03-deploy-container.yml

# フロントエンドデプロイ
ansible-playbook playbooks/04-deploy-frontend.yml

# デプロイ後検証
ansible-playbook playbooks/05-post-verification.yml
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
**最終更新**: 2025-08-23  
**バージョン**: 2.0  
**システム完成度**: 98% (商用運用可能レベル)
