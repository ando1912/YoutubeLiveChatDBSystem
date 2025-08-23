# YouTube Live Chat Collector - Ansible デプロイ管理

このディレクトリには、YouTube Live Chat Collectorシステムの自動デプロイ用Ansibleプレイブックが含まれています。

## 📁 ファイル構成

```
ansible/
├── deploy-all.yml              # メイン一括デプロイ
├── quick-deploy.yml            # 個別コンポーネント迅速デプロイ
├── playbooks/                  # 各工程別プレイブック
│   ├── 01-pre-checks.yml       # 事前チェック
│   ├── 02-deploy-lambda.yml    # Lambda関数デプロイ
│   ├── 03-deploy-container.yml # ECSコンテナデプロイ
│   ├── 04-deploy-frontend.yml  # フロントエンドデプロイ
│   └── 05-post-verification.yml # デプロイ後検証
├── roles/                      # Ansibleロール
│   ├── lambda-deployment/      # Lambda関数デプロイロール
│   └── container-deployment/   # コンテナデプロイロール
├── inventory                   # インベントリファイル
├── ansible.cfg                 # Ansible設定
└── README.md                   # このファイル
```

## 🚀 使用方法

### 1. 完全システムデプロイ（推奨）

全コンポーネントを順次デプロイします：

```bash
# メインディレクトリから実行
cd /home/ando-pvt/github/250820_YoutubeLiveChatCollector/ansible
ansible-playbook deploy-all.yml
```

**実行内容**:
- Phase 1: 事前チェック（AWS CLI、Docker、Node.js、Terraform状態）
- Phase 2: Lambda関数デプロイ（4関数）
- Phase 3: ECSコンテナデプロイ（Comment Collector）
- Phase 4: フロントエンドデプロイ（React.js → S3）
- Phase 5: デプロイ後検証（ヘルスチェック）

### 2. 個別コンポーネントデプロイ

特定のコンポーネントのみをデプロイします：

```bash
# Lambda関数のみ
ansible-playbook quick-deploy.yml -e "component=lambda"

# ECSコンテナのみ
ansible-playbook quick-deploy.yml -e "component=container"

# フロントエンドのみ
ansible-playbook quick-deploy.yml -e "component=frontend"

# 全コンポーネント（deploy-all.ymlと同等）
ansible-playbook quick-deploy.yml -e "component=all"
```

### 3. 各工程の個別実行

各工程を個別に実行することも可能です：

```bash
# 事前チェックのみ
ansible-playbook playbooks/01-pre-checks.yml

# Lambda関数デプロイのみ
ansible-playbook playbooks/02-deploy-lambda.yml

# ECSコンテナデプロイのみ
ansible-playbook playbooks/03-deploy-container.yml

# フロントエンドデプロイのみ
ansible-playbook playbooks/04-deploy-frontend.yml

# デプロイ後検証のみ
ansible-playbook playbooks/05-post-verification.yml
```

## 📋 前提条件

### 必要なツール

- **AWS CLI**: 設定済み（`aws configure`）
- **Docker**: 起動済み（ECSコンテナデプロイ用）
- **Node.js & npm**: インストール済み（フロントエンドビルド用）
- **Ansible**: インストール済み

### インフラストラクチャ

Terraformインフラが事前にデプロイされている必要があります：

```bash
cd terraform/environments/dev
terraform init
terraform plan
terraform apply
```

## 🔧 設定

### 環境変数

各プレイブックで使用される主要な変数：

```yaml
env_name: "dev"                    # 環境名
aws_region: "ap-northeast-1"       # AWSリージョン
aws_account_id: "209547544773"     # AWSアカウントID
```

### デプロイ制御フラグ

`deploy-all.yml`では、各コンポーネントのデプロイを制御できます：

```yaml
deploy_lambda: true      # Lambda関数デプロイ
deploy_container: true   # ECSコンテナデプロイ
deploy_frontend: true    # フロントエンドデプロイ
```

## 📊 デプロイ対象コンポーネント

### Lambda関数（4個）

1. **RSS Monitor Lambda**
   - YouTube RSSフィード監視
   - 5分間隔実行
   - 新規配信検出

2. **Stream Status Checker Lambda**
   - 配信状態チェック
   - 5分間隔実行
   - YouTube Data API使用

3. **ECS Task Launcher Lambda**
   - ECSタスク制御
   - SQS駆動実行
   - コメント収集開始・停止

4. **API Handler Lambda**
   - REST API処理
   - フロントエンド連携
   - CRUD操作

### ECSコンテナ

- **Comment Collector**
  - pytchatライブラリ使用
  - リアルタイムコメント収集
  - DynamoDB保存

### フロントエンド

- **React.js アプリケーション**
  - TypeScript実装
  - S3 Static Website
  - API Gateway連携

## 🔍 トラブルシューティング

### よくある問題

1. **Docker daemon not running**
   ```bash
   # Linux
   sudo systemctl start docker
   
   # WSL2
   # Docker Desktopを起動
   ```

2. **AWS credentials not configured**
   ```bash
   aws configure
   # または環境変数設定
   export AWS_ACCESS_KEY_ID=your_key
   export AWS_SECRET_ACCESS_KEY=your_secret
   ```

3. **Terraform infrastructure not deployed**
   ```bash
   cd terraform/environments/dev
   terraform apply
   ```

4. **Node.js dependencies missing**
   ```bash
   cd src/frontend/youtube-chat-viewer
   npm install
   ```

### ログ確認

デプロイ後のログ確認方法：

```bash
# Lambda関数ログ
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/dev-"

# ECSタスクログ
aws logs describe-log-groups --log-group-name-prefix "/ecs/dev-"

# API Gateway ログ
aws logs describe-log-groups --log-group-name-prefix "API-Gateway-Execution-Logs"
```

## 📈 デプロイ後の確認

### システムヘルスチェック

デプロイ完了後、以下を確認してください：

1. **フロントエンドアクセス**
   - ブラウザでフロントエンドURLにアクセス
   - ダッシュボードが正常表示されることを確認

2. **API動作確認**
   ```bash
   # チャンネル一覧取得
   curl -H "x-api-key: YOUR_API_KEY" "https://YOUR_API_GATEWAY_URL/dev/channels"
   ```

3. **Lambda関数確認**
   ```bash
   # Lambda関数一覧
   aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `dev-`)].FunctionName'
   ```

4. **DynamoDBテーブル確認**
   ```bash
   # テーブル一覧
   aws dynamodb list-tables --query 'TableNames[?starts_with(@, `dev-`)]'
   ```

## 🎯 次のステップ

デプロイ完了後：

1. **チャンネル追加**: フロントエンドからYouTubeチャンネルを追加
2. **監視開始**: チャンネル監視を開始
3. **ログ監視**: CloudWatch Logsでシステム動作を確認
4. **データ確認**: DynamoDBでコメント収集状況を確認

## 📞 サポート

問題が発生した場合：

1. **事前チェック実行**: `ansible-playbook playbooks/01-pre-checks.yml`
2. **検証レポート確認**: `ansible-playbook playbooks/05-post-verification.yml`
3. **ログ確認**: CloudWatch Logsでエラー詳細を確認
4. **個別デプロイ**: 問題のあるコンポーネントのみ再デプロイ

---

**作成日**: 2025-08-23  
**バージョン**: 1.0  
**対象システム**: YouTube Live Chat Collector  
**対象環境**: dev (開発環境)
