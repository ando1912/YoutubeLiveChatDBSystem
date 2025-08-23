# AWS アーキテクチャ構成図 説明書

## 概要

この文書は、YouTube Live Chat Collectorシステムのaws_architecture_diagram.drawioファイルの構成図について詳細に説明します。

## 構成図の使用方法

### draw.ioでの開き方
1. [draw.io](https://app.diagrams.net/) にアクセス
2. 「Open Existing Diagram」を選択
3. `aws_architecture_diagram.drawio` ファイルを選択
4. 図が表示されます

### 編集方法
- 各コンポーネントをクリックして選択・編集可能
- 右側のプロパティパネルで色やテキストを変更
- 新しいコンポーネントは左側のライブラリから追加

## アーキテクチャ構成要素

### 1. ネットワーク層

#### AWS Cloud / Region
- **リージョン**: ap-northeast-1 (東京)
- **可用性**: Multi-AZ構成

#### VPC (Virtual Private Cloud)
- **CIDR**: 10.0.0.0/16
- **構成**: パブリックサブネットのみ
- **コスト最適化**: NAT Gateway不使用

#### サブネット構成
```
Public Subnet A: 10.0.1.0/24 (ap-northeast-1a)
Public Subnet B: 10.0.2.0/24 (ap-northeast-1c)
```

#### Internet Gateway
- パブリックサブネットからインターネットへの接続
- ECS TasksとLambda関数のアウトバウンド通信

### 2. コンピューティング層

#### Lambda Functions
1. **RSS Monitor Lambda**
   - **トリガー**: EventBridge (5分間隔)
   - **機能**: YouTubeチャンネルのRSSフィード監視
   - **接続先**: YouTube RSS Feed API, DynamoDB, SQS

2. **Status Checker Lambda**
   - **トリガー**: EventBridge (1分間隔)
   - **機能**: YouTube Data APIでライブ配信状態確認
   - **接続先**: YouTube Data API v3, DynamoDB, SQS, Parameter Store

3. **ECS Launcher Lambda**
   - **トリガー**: SQS Queue
   - **機能**: ECS Fargateタスクの起動・停止制御
   - **接続先**: ECS Fargate Tasks, DynamoDB

4. **API Handler Lambda**
   - **トリガー**: API Gateway
   - **機能**: REST APIエンドポイントの処理
   - **接続先**: DynamoDB

#### ECS Fargate Tasks
- **配置**: Public Subnet A & B
- **機能**: pytchatライブラリでのコメント収集
- **実行時間**: 配信終了まで継続実行
- **接続先**: YouTube Live Chat API, DynamoDB, CloudWatch Logs

### 3. ストレージ層

#### DynamoDB
- **テーブル**: Channels, LiveStreams, Comments, TaskStatus
- **課金**: Pay-per-request (オンデマンド)
- **暗号化**: AWS Managed Key

#### S3 Bucket
- **用途**: React フロントエンドの静的サイトホスティング
- **アクセス**: パブリック読み取り許可
- **接続**: ユーザーからHTTPS接続

#### Parameter Store
- **用途**: YouTube API Keyの安全な保存
- **暗号化**: KMS暗号化 (SecureString)
- **コスト**: 無料 (Standard Parameters)

#### ECR Repository
- **用途**: ECS Fargateコンテナイメージの保存
- **ライフサイクル**: 最新5イメージのみ保持

### 4. メッセージング・イベント層

#### EventBridge
- **RSS Monitor**: 5分間隔でスケジュール実行
- **Status Checker**: 1分間隔でスケジュール実行
- **コスト**: 無料枠内

#### SQS Queue
- **用途**: ECS Task制御メッセージの配信
- **タイプ**: Standard Queue
- **Dead Letter Queue**: 3回リトライ後にDLQ送信

### 5. API・フロントエンド層

#### API Gateway
- **タイプ**: Regional REST API
- **認証**: API Key
- **エンドポイント**: /channels, /streams, /comments
- **CORS**: 有効

#### フロントエンド
- **技術**: React.js
- **ホスティング**: S3 Static Website
- **アクセス**: ユーザーから直接HTTPS接続

### 6. 監視・ログ層

#### CloudWatch Logs
- **対象**: 全Lambda関数、ECS Tasks
- **保持期間**: 7日間
- **コスト**: 無料枠内

### 7. 外部サービス連携

#### YouTube APIs
1. **YouTube RSS Feed**
   - RSS Monitor Lambdaからアクセス
   - 新しいライブ配信の検出

2. **YouTube Data API v3**
   - Status Checker Lambdaからアクセス
   - ライブ配信状態の確認
   - APIキーはParameter Storeから取得

3. **YouTube Live Chat API**
   - ECS Fargate Tasksからpytchat経由でアクセス
   - リアルタイムコメント取得

## データフロー

### 1. チャンネル監視フロー
```
EventBridge (5分) → RSS Monitor Lambda → YouTube RSS API
                                      ↓
                              DynamoDB (LiveStreams) → SQS Queue
```

### 2. 配信開始監視フロー
```
EventBridge (1分) → Status Checker Lambda → YouTube Data API v3
                                          ↓
                                  DynamoDB (LiveStreams) → SQS Queue
```

### 3. コメント収集フロー
```
SQS Queue → ECS Launcher Lambda → ECS Fargate Tasks
                                        ↓
                              YouTube Live Chat API → DynamoDB (Comments)
```

### 4. Web UI フロー
```
User → S3 (Frontend) → API Gateway → API Handler Lambda → DynamoDB
```

## セキュリティ設計

### ネットワークセキュリティ
- **ECS Tasks**: Public Subnetだが、Security Groupでインバウンド完全遮断
- **Lambda**: VPC内配置不要（マネージドサービス）
- **API Gateway**: API Key認証

### データ暗号化
- **DynamoDB**: AWS Managed Key
- **Parameter Store**: KMS暗号化
- **S3**: AES-256暗号化

### IAM権限
- **最小権限の原則**: 各サービスに必要最小限の権限のみ付与
- **ロール分離**: Lambda実行ロール、ECS Taskロール、ECS Task実行ロールを分離

## コスト最適化ポイント

### 1. ネットワークコスト削減
- **NAT Gateway削除**: 月額$32削減
- **パブリックサブネット使用**: 直接インターネット接続

### 2. 無料枠活用
- **Lambda**: 100万リクエスト/月
- **DynamoDB**: 25GB + 読み書き容量
- **API Gateway**: 100万リクエスト/月
- **Parameter Store**: Standard Parameters

### 3. リソース最適化
- **ECS Fargate**: 最小CPU/メモリ構成 (0.25vCPU, 512MB)
- **CloudWatch Logs**: 7日間保持
- **ECR**: ライフサイクルポリシーで古いイメージ削除

## 運用監視

### メトリクス監視
- **Lambda**: エラー率、実行時間、同時実行数
- **ECS**: Task実行状況、CPU/メモリ使用率
- **DynamoDB**: 読み書きスロットリング
- **API Gateway**: レスポンス時間、エラー率

### ログ管理
- **集約**: CloudWatch Logs
- **検索**: CloudWatch Insights
- **アラート**: CloudWatch Alarms

## 拡張性考慮

### スケールアウト対応
- **Lambda**: 自動スケール (同時実行数制限内)
- **ECS Fargate**: 必要に応じてTask数増加
- **DynamoDB**: オンデマンド課金で自動スケール
- **API Gateway**: 自動スケール

### 将来拡張ポイント
- **CloudFront**: フロントエンドのCDN配信
- **ElastiCache**: DynamoDBキャッシュ層
- **Kinesis**: 大量データストリーミング処理
- **Step Functions**: 複雑なワークフロー管理

## 図の凡例

### 線の種類
- **オレンジ実線**: トリガー・起動関係
- **青実線**: データフロー
- **黒実線**: 外部API接続
- **緑破線**: ログ・監視関係

### 色分け
- **オレンジ**: コンピューティングサービス (Lambda, ECS)
- **紫**: データベースサービス (DynamoDB)
- **ピンク**: API・メッセージングサービス
- **緑**: ストレージ・管理サービス
- **グレー**: 外部サービス・ユーザー

---

**作成日**: 2025-08-21  
**対象システム**: YouTube Live Chat Collector  
**図ファイル**: aws_architecture_diagram.drawio
