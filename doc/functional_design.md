# 機能別設計詳細

## 1. チャンネル監視機能

### 1.1 機能概要
- 登録されたYouTubeチャンネルのRSSフィードを定期監視
- 新しいライブ配信の検出
- 配信情報のデータベース登録

### 1.2 アーキテクチャ図

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   EventBridge   │────►│ RSS Monitor     │────►│ YouTube RSS     │
│   (5分間隔)      │     │ Lambda          │     │ Feed API        │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   DynamoDB      │
                        │  LiveStreams    │
                        │  (新配信登録)    │
                        └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   SQS Queue     │
                        │ (Task Control)  │
                        └─────────────────┘
```

### 1.3 処理フロー
1. EventBridge (5分間隔) → rss-monitor-lambda実行
2. DynamoDB Channelsテーブルから監視対象チャンネル取得
3. 各チャンネルのRSSフィードをHTTP GET
4. フィード内容を解析し、新しいライブ配信URLを検出
5. 新配信をDynamoDB LiveStreamsテーブルに登録 (status: upcoming)
6. SQS task-control-queueにTask起動メッセージ送信

### 1.4 使用リソース
- **Lambda**: rss-monitor-lambda (128MB, 5分timeout)
- **EventBridge**: rss-monitor-schedule (rate(5 minutes))
- **DynamoDB**: Channels, LiveStreams
- **SQS**: task-control-queue

### 1.5 RSS フィード解析仕様
- **URL形式**: `https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}`
- **検出対象**: `<entry>`要素内の`<link href="...watch?v=VIDEO_ID">`
- **ライブ判定**: タイトルに「ライブ」「配信」等のキーワード含有
- **重複チェック**: DynamoDB LiveStreamsテーブルでvideo_id存在確認

## 2. 配信開始監視機能

### 2.1 機能概要
- YouTube Data APIを使用した配信状態の監視
- 配信開始・終了の検出
- ECS Task起動・停止の制御

### 2.2 アーキテクチャ図

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   EventBridge   │────►│ Stream Status   │────►│ YouTube Data    │
│   (1分間隔)      │     │ Checker Lambda  │     │ API v3          │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   DynamoDB      │
                        │  LiveStreams    │
                        │  (状態更新)      │
                        └─────────────────┘
                                 │
                        ┌────────▼────────┐
                        │  配信開始検出    │
                        └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   SQS Queue     │
                        │ (Task Control)  │
                        └─────────────────┘
```

### 2.3 処理フロー
1. EventBridge (1分間隔) → stream-status-checker-lambda実行
2. DynamoDB LiveStreamsから監視対象配信取得 (status: upcoming, live)
3. YouTube Data API v3 videos.listで配信状態確認
4. 配信状態をDynamoDBに更新 (upcoming → live → ended)
5. 状態変化検出時の処理:
   - ライブ開始: SQSにTask起動メッセージ
   - ライブ終了: SQSにTask停止メッセージ

### 2.4 使用リソース
- **Lambda**: stream-status-checker-lambda (256MB, 1分timeout)
- **EventBridge**: stream-status-schedule (rate(1 minute))
- **DynamoDB**: LiveStreams
- **SQS**: task-control-queue
- **外部API**: YouTube Data API v3

### 2.5 YouTube Data API仕様
- **エンドポイント**: `https://www.googleapis.com/youtube/v3/videos`
- **パラメータ**: `part=liveStreamingDetails&id={VIDEO_ID}`
- **レスポンス解析**: `liveStreamingDetails.actualStartTime`の有無で判定
- **クォータ消費**: 1 unit per request

## 3. ECS Task制御機能

### 3.1 機能概要
- SQSメッセージに基づくECS Fargateタスクの起動・停止
- タスク実行状態の管理
- エラーハンドリングと再試行

### 3.2 アーキテクチャ図

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   SQS Queue     │────►│ ECS Task        │────►│   ECS Fargate   │
│ (Task Control)  │     │ Launcher Lambda │     │   Cluster       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                 │                        │
                                 ▼                        ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │   DynamoDB      │     │ Comment         │
                        │  TaskStatus     │     │ Collector       │
                        │  (Task状態管理)  │     │ Container       │
                        └─────────────────┘     └─────────────────┘
```

### 3.3 処理フロー

#### Task起動フロー
1. SQSメッセージ受信 (action: start, video_id: xxx)
2. 既存Task状態確認 (DynamoDB TaskStatus)
3. ECS RunTask API呼び出し
4. Task ARNをDynamoDB TaskStatusに記録
5. Task起動確認とエラーハンドリング

#### Task停止フロー
1. SQSメッセージ受信 (action: stop, video_id: xxx)
2. DynamoDB TaskStatusからTask ARN取得
3. ECS StopTask API呼び出し
4. TaskStatus更新 (stopped_at記録)

### 3.4 使用リソース
- **Lambda**: ecs-task-launcher-lambda (256MB, 30秒timeout)
- **SQS**: task-control-queue (trigger)
- **ECS**: Fargate Cluster, Task Definition
- **DynamoDB**: TaskStatus
- **IAM**: ECS操作権限

### 3.5 SQSメッセージ形式
```json
{
  "action": "start|stop",
  "video_id": "VIDEO_ID",
  "channel_id": "CHANNEL_ID",
  "timestamp": "2025-08-21T07:00:00Z"
}
```

## 4. コメント収集機能

### 4.1 機能概要
- ECS Fargateでの長時間実行コメント収集
- pytchatライブラリによるリアルタイムコメント取得
- DynamoDBへのコメントデータ保存

### 4.2 アーキテクチャ図

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ ECS Fargate     │────►│    pytchat      │────►│ YouTube Live    │
│ Task            │     │   Library       │     │ Chat API        │
│ (Public Subnet) │     └─────────────────┘     └─────────────────┘
└─────────────────┘              │
         │                       │
         │              ┌────────▼────────┐
         │              │ リアルタイム     │
         │              │ コメント取得     │
         │              └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│   DynamoDB      │     │   DynamoDB      │
│  TaskStatus     │     │   Comments      │
│  (実行状態)      │     │  (コメント保存)  │
└─────────────────┘     └─────────────────┘
```

### 4.3 処理フロー
1. ECS Fargate Task起動
2. 環境変数からvideo_id取得
3. pytchat.create()でライブチャット接続
4. 無限ループでコメント取得:
   - chat.get()でコメント取得
   - DynamoDB Commentsテーブルに保存
   - 配信終了検出まで継続
5. 配信終了時、Task自動終了

### 4.4 使用リソース
- **ECS Fargate**: comment-collector Task (0.25vCPU, 512MB)
- **ECR**: comment-collector コンテナイメージ
- **DynamoDB**: Comments, TaskStatus
- **VPC**: Public Subnets
- **外部API**: YouTube Live Chat (pytchat経由)

### 4.5 pytchat設定
- **接続方式**: `pytchat.create(video_id=VIDEO_ID)`
- **取得間隔**: リアルタイム（pytchatライブラリ制御）
- **エラーハンドリング**: 接続断時の自動再接続
- **終了条件**: `chat.is_alive()`がFalseになるまで

## 5. Webアプリケーション機能

### 5.1 機能概要
- チャンネル管理UI
- 配信一覧表示
- コメントデータ表示
- REST API提供

### 5.2 アーキテクチャ図

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Browser      │────►│   S3 Static     │     │  API Gateway    │
│                 │     │   Website       │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                                                │
         └────────────────────────────────────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │ API Handler     │
                        │ Lambda          │
                        └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   DynamoDB      │
                        │ - Channels      │
                        │ - LiveStreams   │
                        │ - Comments      │
                        └─────────────────┘
```

### 5.3 API エンドポイント設計

| Method | Endpoint | 機能 | 説明 |
|--------|----------|------|------|
| GET | /channels | チャンネル一覧取得 | 登録済みチャンネル一覧 |
| POST | /channels | チャンネル追加 | 新規チャンネル登録 |
| GET | /streams | 配信一覧取得 | 全配信または状態別 |
| GET | /streams/{video_id}/comments | コメント一覧取得 | 特定配信のコメント |

### 5.4 使用リソース
- **S3**: frontend-assets-bucket (静的サイトホスティング)
- **API Gateway**: Regional REST API
- **Lambda**: api-handler-lambda (256MB, 30秒timeout)
- **DynamoDB**: 全テーブル (読み取り専用)

### 5.5 フロントエンド仕様
- **フレームワーク**: React.js
- **状態管理**: React Hooks
- **UIライブラリ**: Material-UI または Bootstrap
- **ビルドツール**: Create React App
- **デプロイ**: S3 Static Website Hosting

## 6. データモデル設計

### 6.1 Channels テーブル
| 項目 | 型 | キー | 説明 |
|------|----|----|------|
| channel_id | String | PK | YouTubeチャンネルID |
| channel_name | String | - | チャンネル名 |
| rss_url | String | - | RSSフィードURL |
| is_active | Boolean | - | 監視有効フラグ |
| created_at | String | - | 作成日時 (ISO8601) |
| updated_at | String | - | 更新日時 (ISO8601) |

### 6.2 LiveStreams テーブル
| 項目 | 型 | キー | 説明 |
|------|----|----|------|
| video_id | String | PK | YouTube動画ID |
| channel_id | String | GSI-PK | チャンネルID |
| title | String | - | 配信タイトル |
| status | String | - | 配信状態 (upcoming/live/ended) |
| scheduled_start_time | String | - | 予定開始時刻 |
| actual_start_time | String | - | 実際の開始時刻 |
| actual_end_time | String | - | 実際の終了時刻 |
| created_at | String | - | 作成日時 |
| updated_at | String | - | 更新日時 |

### 6.3 Comments テーブル
| 項目 | 型 | キー | 説明 |
|------|----|----|------|
| comment_id | String | PK | コメントID (UUID) |
| video_id | String | SK | 動画ID |
| author_name | String | - | 投稿者名 |
| message | String | - | コメント内容 |
| timestamp | String | - | 投稿時刻 (ISO8601) |
| superchat_amount | Number | - | スーパーチャット金額 |
| created_at | String | - | 取得日時 |

**GSI**: video_id-timestamp-index (video_id, timestamp)

### 6.4 TaskStatus テーブル
| 項目 | 型 | キー | 説明 |
|------|----|----|------|
| video_id | String | PK | 動画ID |
| task_arn | String | - | ECS TaskのARN |
| status | String | - | Task状態 (RUNNING/STOPPED) |
| started_at | String | - | 開始時刻 |
| stopped_at | String | - | 停止時刻 |

## 7. エラーハンドリング設計

### 7.1 Lambda関数エラーハンドリング
- **リトライ設定**: 3回まで自動リトライ
- **Dead Letter Queue**: 失敗メッセージをDLQに送信
- **CloudWatch Alarms**: エラー率5%超過でアラート

### 7.2 ECS Taskエラーハンドリング
- **Task失敗時**: 自動的に新しいTaskを起動
- **ネットワークエラー**: pytchatの自動再接続機能を利用
- **DynamoDB書き込みエラー**: 指数バックオフでリトライ

### 7.3 YouTube API制限対応
- **クォータ超過**: 処理をスキップしてログ出力
- **レート制限**: 指数バックオフでリトライ
- **API障害**: 一時的なスキップとアラート

---

**作成日**: 2025-08-21  
**バージョン**: 1.0  
**作成者**: Amazon Q Developer
