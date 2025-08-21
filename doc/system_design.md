# YouTubeライブチャットコレクター システム設計書

## 1. システム概要

### 1.1 目的
YouTubeでライブ配信をしているVTuberのライブ配信コメントをリアルタイムで取得・保存するWebアプリケーションシステム

### 1.2 主要機能
- 監視対象YouTubeチャンネルの管理
- 監視対象チャンネル一覧表示
- 現在監視中のライブ配信一覧表示
- 監視を終えたライブ配信一覧表示
- 収集したコメントデータの表示

### 1.3 技術要件
- システム運用コストを最小に抑制（月額$2-3目標）
- 極力無料枠のサービスを使用
- 耐障害性は不要だが、コメント収集処理の停止を回避
- TerraformとAnsibleを使用したIaC
- pytchatライブラリを使用したコメント収集
- WebアプリケーションへのIP制限
- YouTube Data APIクォータを無料枠範囲内で運用

## 2. システム全体アーキテクチャ

### 2.1 全体構成図

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Browser   │◄──►│   S3 Web    │    │ API Gateway │
└─────────────┘    └─────────────┘    └──────┬──────┘
                                              │
                   ┌──────────────────────────┼──────────────────────────┐
                   │                          │                          │
           ┌───────▼──┐              ┌────────▼────────┐        ┌────────▼────────┐
           │   API    │              │  RSS Monitor    │        │ Status Checker  │
           │ Handler  │              │    Lambda       │        │     Lambda      │
           └────┬─────┘              └─────────────────┘        └─────────────────┘
                │                             │                          │
                │                    ┌────────▼────────┐                 │
                │                    │   EventBridge   │◄────────────────┘
                │                    │   (Scheduler)   │
                │                    └─────────────────┘
                │                             │
                │                    ┌────────▼────────┐
                │                    │   SQS Queue     │
                │                    └─────────────────┘
                │                             │
                │                    ┌────────▼────────┐
                │                    │ ECS Task        │
                │                    │ Launcher        │
                │                    │ Lambda          │
                │                    └─────────────────┘
                │                             │
                │                    ┌────────▼────────┐
                │                    │ ECS Fargate     │
                │                    │ (Public Subnet) │
                │                    │ Comment         │
                │                    │ Collector       │
                │                    └─────────────────┘
                │                             │
                └─────────────────────────────┼─────────────────────────────┐
                                              │                             │
                                    ┌─────────▼─────────┐                   │
                                    │    DynamoDB       │◄──────────────────┘
                                    │  - Channels       │
                                    │  - LiveStreams    │
                                    │  - Comments       │
                                    │  - TaskStatus     │
                                    └───────────────────┘
```

### 2.2 ネットワーク構成図

```
┌─────────────────────────────────────────────────────────────────┐
│                        VPC (10.0.0.0/16)                       │
│                                                                 │
│  ┌─────────────────────┐    ┌─────────────────────┐            │
│  │  Public Subnet A    │    │  Public Subnet B    │            │
│  │   (10.0.1.0/24)     │    │   (10.0.2.0/24)     │            │
│  │                     │    │                     │            │
│  │  ┌───────────────┐  │    │  ┌───────────────┐  │            │
│  │  │ ECS Fargate   │  │    │  │ ECS Fargate   │  │            │
│  │  │ Task          │  │    │  │ Task          │  │            │
│  │  │ (Public IP)   │  │    │  │ (Public IP)   │  │            │
│  │  └───────────────┘  │    │  └───────────────┘  │            │
│  └─────────────────────┘    └─────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │ Internet        │
                    │ Gateway         │
                    └─────────────────┘
                             │
                    ┌────────▼────────┐
                    │   Internet      │
                    │ - YouTube APIs  │
                    │ - AWS APIs      │
                    └─────────────────┘
```

## 3. 使用AWSリソース詳細

### 3.1 コンピューティング

#### Lambda Functions
| 関数名 | Runtime | Memory | Timeout | 同時実行数 | Trigger |
|--------|---------|--------|---------|-----------|---------|
| rss-monitor-lambda | Python 3.9 | 128MB | 5分 | 1 | EventBridge |
| stream-status-checker-lambda | Python 3.9 | 256MB | 1分 | 1 | EventBridge |
| ecs-task-launcher-lambda | Python 3.9 | 256MB | 30秒 | 10 | SQS |
| api-handler-lambda | Python 3.9 | 256MB | 30秒 | 100 | API Gateway |

#### ECS Fargate
| 項目 | 設定値 | 備考 |
|------|--------|------|
| Cluster名 | youtube-comment-collector | |
| Task Definition | comment-collector:1 | |
| CPU | 256 (0.25 vCPU) | |
| Memory | 512MB | |
| Network Mode | awsvpc | |
| Launch Type | FARGATE | |
| Platform Version | LATEST | |
| Assign Public IP | ENABLED | |

### 3.2 ストレージ

#### DynamoDB Tables
| テーブル名 | 課金モード | 暗号化 | GSI | 想定サイズ |
|------------|-----------|--------|-----|-----------|
| Channels | On-Demand | AWS Managed | なし | ~1KB × 50件 |
| LiveStreams | On-Demand | AWS Managed | channel_id-index | ~2KB × 1000件 |
| Comments | On-Demand | AWS Managed | video_id-timestamp-index | ~500B × 100万件 |
| TaskStatus | On-Demand | AWS Managed | なし | ~300B × 100件 |

#### S3 Buckets
| バケット名 | 用途 | 暗号化 | バージョニング |
|-----------|------|--------|---------------|
| frontend-assets-bucket | 静的サイト | AES-256 | 無効 |
| terraform-state-bucket | Terraform状態 | AES-256 | 有効 |

#### ECR Repository
| リポジトリ名 | 用途 | ライフサイクル |
|-------------|------|---------------|
| comment-collector | ECSコンテナ | 最新5イメージ保持 |

### 3.3 ネットワーキング

#### VPC構成
| リソース | 設定値 | 備考 |
|----------|--------|------|
| VPC CIDR | 10.0.0.0/16 | |
| Public Subnet A | 10.0.1.0/24 (ap-northeast-1a) | |
| Public Subnet B | 10.0.2.0/24 (ap-northeast-1c) | |
| Internet Gateway | 1個 | |
| Route Table | Public用1個 | |

#### Security Groups
| 名前 | 用途 | Inbound | Outbound |
|------|------|---------|----------|
| ecs-comment-collector-sg | ECS Task | なし | HTTPS/HTTP → 0.0.0.0/0 |
| lambda-sg | Lambda関数 | なし | HTTPS → 0.0.0.0/0 |

#### API Gateway
| 項目 | 設定値 |
|------|--------|
| Type | Regional REST API |
| Authentication | API Key |
| Throttling | 1000 req/sec |
| CORS | 有効 |

### 3.4 メッセージング・スケジューリング

#### SQS Queues
| キュー名 | タイプ | 可視性タイムアウト | DLQ |
|----------|--------|------------------|-----|
| task-control-queue | Standard | 30秒 | 有効 |
| task-control-dlq | Standard | - | - |

#### EventBridge Rules
| ルール名 | スケジュール | ターゲット |
|----------|-------------|-----------|
| rss-monitor-schedule | rate(5 minutes) | rss-monitor-lambda |
| stream-status-schedule | rate(1 minute) | stream-status-checker-lambda |

## 4. コスト設計

### 4.1 月額コスト見積もり

#### 前提条件
- 監視チャンネル数: 10チャンネル
- 月間ライブ配信数: 30配信
- 平均配信時間: 2時間
- 月間コメント数: 10万件

#### 詳細コスト
```
ECS Fargate:
- 稼働時間: 30配信 × 2時間 = 60時間/月
- CPU: 0.25 vCPU × 60時間 × $0.04048 = $0.61
- Memory: 0.5GB × 60時間 × $0.004445 = $0.13
- 小計: $0.74

Lambda:
- 実行時間・リクエスト数: 無料枠内
- 小計: $0

DynamoDB:
- ストレージ: ~5GB (無料枠25GB内)
- 読み書き: 無料枠内
- 小計: $0

API Gateway:
- リクエスト数: ~1000/月 (無料枠100万内)
- 小計: $0

S3:
- ストレージ: ~100MB
- リクエスト: ~1000/月
- 小計: $1

その他:
- CloudWatch Logs: 無料枠内
- EventBridge: 無料枠内
- SQS: 無料枠内

月額総計: $1.74 ≈ $2
```

### 4.2 スケーリング時のコスト
- チャンネル数2倍: +$0.74 (ECS稼働時間増)
- コメント数10倍: +$5-10 (DynamoDB課金開始)

## 5. セキュリティ設計

### 5.1 ネットワークセキュリティ
- ECS TaskはPublic Subnetに配置するが、Security Groupでインバウンド通信を完全遮断
- アウトバウンド通信のみHTTPS/HTTPを許可
- API GatewayでAPI Key認証を実装

### 5.2 IAM権限設計

#### 最小権限の原則
各リソースに必要最小限の権限のみ付与

#### Lambda実行ロール
- CloudWatch Logs書き込み権限
- DynamoDB読み書き権限（テーブル別）
- SQS送受信権限
- ECS Task操作権限（ecs-task-launcher-lambdaのみ）

#### ECS Task権限
- DynamoDB読み書き権限（Comments, TaskStatus）
- CloudWatch Logs書き込み権限

### 5.3 データ暗号化
- DynamoDB: AWS Managed Key
- S3: AES-256
- Lambda環境変数: AWS KMS
- ECS Task環境変数: AWS KMS

## 6. 運用設計

### 6.1 監視・アラート
- CloudWatch Logsでの集約ログ管理
- Lambda関数エラー率監視
- ECS Task実行失敗監視
- DynamoDB スロットリング監視
- YouTube API クォータ使用量監視

### 6.2 バックアップ・復旧
- DynamoDB: Point-in-time Recovery無効（コスト考慮）
- 重要データの手動エクスポート機能
- Terraform状態ファイルのS3バックアップ

### 6.3 ログ管理
- CloudWatch Logsでの統合ログ管理
- ログ保持期間: 7日間
- 重要エラーのアラート設定

## 7. 開発・デプロイメント設計

### 7.1 ディレクトリ構成
```
youtube-live-chat-collector/
├── terraform/
│   ├── environments/
│   │   └── dev/
│   │       ├── main.tf
│   │       ├── variables.tf
│   │       └── terraform.tfvars
│   └── modules/
│       ├── networking/
│       ├── compute/
│       ├── storage/
│       └── api/
├── src/
│   ├── lambda/
│   │   ├── rss_monitor/
│   │   ├── stream_status_checker/
│   │   ├── ecs_task_launcher/
│   │   └── api_handler/
│   ├── ecs/
│   │   └── comment_collector/
│   └── frontend/
│       └── react-app/
├── ansible/
│   ├── playbooks/
│   └── roles/
└── docs/
    ├── system_design.md
    └── deployment_guide.md
```

### 7.2 デプロイメント手順
1. Terraformでインフラ構築
2. ECRリポジトリ作成・イメージプッシュ
3. Lambda関数デプロイ
4. フロントエンドビルド・S3デプロイ
5. 動作確認・テスト

### 7.3 CI/CD設計（将来拡張）
- GitHub Actionsでの自動デプロイ
- Terraformプラン・アプライの自動化
- コンテナイメージの自動ビルド・プッシュ

## 8. 制限事項・考慮点

### 8.1 技術的制限
- Lambda最大実行時間: 15分
- ECS Fargate最小課金単位: 1分
- DynamoDB項目サイズ: 400KB
- YouTube Data API: 10,000 units/日

### 8.2 運用上の考慮点
- YouTube API制限による機能停止リスク
- ECS Task起動時間（30秒-1分程度）
- ネットワーク障害時の復旧手順
- コメント取得の遅延可能性

### 8.3 拡張可能性
- リアルタイム統計表示機能
- コメント分析・感情分析機能
- 複数リージョン展開
- 高可用性構成への移行
- WebSocket APIでのリアルタイム更新

---

**作成日**: 2025-08-21  
**バージョン**: 1.0  
**作成者**: Amazon Q Developer
