# API仕様書

## 1. REST API 仕様

### 1.1 共通仕様

#### ベースURL
```
https://{api-gateway-id}.execute-api.ap-northeast-1.amazonaws.com/dev
```

#### 認証
- **方式**: API Key
- **ヘッダー**: `x-api-key: YOUR_API_KEY`

#### レスポンス形式
```json
{
  "success": true,
  "data": {},
  "error": null,
  "timestamp": "2025-08-21T07:00:00.000Z"
}
```

#### エラーレスポンス
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "Invalid channel_id format"
  },
  "timestamp": "2025-08-21T07:00:00.000Z"
}
```

#### HTTPステータスコード
| コード | 説明 |
|--------|------|
| 200 | 成功 |
| 400 | リクエストエラー |
| 401 | 認証エラー |
| 403 | 権限エラー |
| 404 | リソースが見つからない |
| 500 | 内部サーバーエラー |

### 1.2 チャンネル管理API

#### GET /channels
チャンネル一覧を取得

**リクエスト**
```http
GET /channels
x-api-key: YOUR_API_KEY
```

**クエリパラメータ**
- `active` (optional): `true` | `false` - アクティブなチャンネルのみ取得

**レスポンス**
```json
{
  "success": true,
  "data": {
    "channels": [
      {
        "channel_id": "UCxxxxxxxxxxxxxxxxxx",
        "channel_name": "チャンネル名",
        "rss_url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCxxxxxxxxxxxxxxxxxx",
        "is_active": true,
        "subscriber_count": 1000000,
        "thumbnail_url": "https://yt3.ggpht.com/...",
        "created_at": "2025-08-21T07:00:00.000Z",
        "updated_at": "2025-08-21T07:00:00.000Z"
      }
    ],
    "count": 1
  },
  "error": null,
  "timestamp": "2025-08-21T07:00:00.000Z"
}
```

#### POST /channels
新しいチャンネルを追加

**リクエスト**
```http
POST /channels
Content-Type: application/json
x-api-key: YOUR_API_KEY

{
  "channel_id": "UCxxxxxxxxxxxxxxxxxx",
  "channel_name": "チャンネル名"
}
```

**レスポンス**
```json
{
  "success": true,
  "data": {
    "channel": {
      "channel_id": "UCxxxxxxxxxxxxxxxxxx",
      "channel_name": "チャンネル名",
      "rss_url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCxxxxxxxxxxxxxxxxxx",
      "is_active": true,
      "subscriber_count": 1000000,
      "thumbnail_url": "https://yt3.ggpht.com/...",
      "created_at": "2025-08-21T07:00:00.000Z",
      "updated_at": "2025-08-21T07:00:00.000Z"
    }
  },
  "error": null,
  "timestamp": "2025-08-21T07:00:00.000Z"
}
```

#### PUT /channels/{channel_id}
チャンネル情報を更新

**リクエスト**
```http
PUT /channels/UCxxxxxxxxxxxxxxxxxx
Content-Type: application/json
x-api-key: YOUR_API_KEY

{
  "is_active": false
}
```

**レスポンス**
```json
{
  "success": true,
  "data": {
    "channel": {
      "channel_id": "UCxxxxxxxxxxxxxxxxxx",
      "channel_name": "チャンネル名",
      "is_active": false,
      "updated_at": "2025-08-21T08:00:00.000Z"
    }
  },
  "error": null,
  "timestamp": "2025-08-21T08:00:00.000Z"
}
```

#### DELETE /channels/{channel_id}
チャンネルを削除（監視停止）

**リクエスト**
```http
DELETE /channels/UCxxxxxxxxxxxxxxxxxx
x-api-key: YOUR_API_KEY
```

**レスポンス**
```json
{
  "success": true,
  "data": {
    "message": "Channel monitoring stopped successfully"
  },
  "error": null,
  "timestamp": "2025-08-21T08:00:00.000Z"
}
```

### 1.3 配信管理API

#### GET /streams
配信一覧を取得

**リクエスト**
```http
GET /streams
x-api-key: YOUR_API_KEY
```

**クエリパラメータ**
- `status` (optional): `upcoming,live,detected` - 特定ステータスの配信のみ（カンマ区切りで複数指定可能）
- `channel_id` (optional): 特定チャンネルの配信のみ
- `limit` (optional): 取得件数制限 (デフォルト: 50, 最大: 100)
- `last_key` (optional): ページネーション用の最後のキー

**レスポンス**
```json
{
  "success": true,
  "data": {
    "streams": [
      {
        "video_id": "xxxxxxxxxxx",
        "channel_id": "UCxxxxxxxxxxxxxxxxxx",
        "title": "【ライブ配信】今日も元気に配信するよ！",
        "status": "live",
        "scheduled_start_time": "2025-08-21T12:00:00.000Z",
        "actual_start_time": "2025-08-21T12:05:00.000Z",
        "actual_end_time": null,
        "thumbnail_url": "https://i.ytimg.com/vi/xxxxxxxxxxx/maxresdefault.jpg",
        "viewer_count": 1500,
        "created_at": "2025-08-21T07:00:00.000Z",
        "updated_at": "2025-08-21T12:05:00.000Z"
      }
    ],
    "count": 1,
    "last_key": "xxxxxxxxxxx"
  },
  "error": null,
  "timestamp": "2025-08-21T07:00:00.000Z"
}
```

#### GET /streams/{video_id}
特定配信の詳細を取得

**リクエスト**
```http
GET /streams/xxxxxxxxxxx
x-api-key: YOUR_API_KEY
```

**レスポンス**
```json
{
  "success": true,
  "data": {
    "stream": {
      "video_id": "xxxxxxxxxxx",
      "channel_id": "UCxxxxxxxxxxxxxxxxxx",
      "title": "【ライブ配信】今日も元気に配信するよ！",
      "status": "live",
      "scheduled_start_time": "2025-08-21T12:00:00.000Z",
      "actual_start_time": "2025-08-21T12:05:00.000Z",
      "actual_end_time": null,
      "thumbnail_url": "https://i.ytimg.com/vi/xxxxxxxxxxx/maxresdefault.jpg",
      "viewer_count": 1500,
      "created_at": "2025-08-21T07:00:00.000Z",
      "updated_at": "2025-08-21T12:05:00.000Z"
    }
  },
  "error": null,
  "timestamp": "2025-08-21T07:00:00.000Z"
}
```

### 1.4 コメント取得API

#### GET /streams/{video_id}/comments
特定配信のコメント一覧を取得

**リクエスト**
```http
GET /streams/xxxxxxxxxxx/comments
x-api-key: YOUR_API_KEY
```

**クエリパラメータ**
- `limit` (optional): 取得件数制限 (デフォルト: 100, 最大: 1000)
- `start_time` (optional): 開始時刻 (ISO8601形式)
- `end_time` (optional): 終了時刻 (ISO8601形式)
- `last_key` (optional): ページネーション用の最後のキー

**レスポンス**
```json
{
  "success": true,
  "data": {
    "comments": [
      {
        "comment_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        "video_id": "xxxxxxxxxxx",
        "author_name": "視聴者名",
        "message": "こんにちは！楽しい配信ですね",
        "timestamp": "2025-08-21T12:10:30.000Z",
        "superchat_amount": 0,
        "created_at": "2025-08-21T12:10:30.500Z"
      }
    ],
    "count": 1,
    "last_key": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  },
  "error": null,
  "timestamp": "2025-08-21T07:00:00.000Z"
}
```

### 1.5 システム統計API

#### GET /stats
システム統計情報を取得

**リクエスト**
```http
GET /stats
x-api-key: YOUR_API_KEY
```

**レスポンス**
```json
{
  "success": true,
  "data": {
    "stats": {
      "total_channels": 6,
      "active_channels": 5,
      "total_streams": 30,
      "active_streams": 2,
      "total_comments": 2920,
      "system_uptime": "99.9%",
      "last_updated": "2025-08-21T12:00:00.000Z"
    }
  },
  "error": null,
  "timestamp": "2025-08-21T12:00:00.000Z"
}
```

## 2. SQS メッセージ仕様

### 2.1 Task制御メッセージ

#### Task起動メッセージ
```json
{
  "action": "start_collection",
  "video_id": "xxxxxxxxxxx",
  "channel_id": "UCxxxxxxxxxxxxxxxxxx",
  "timestamp": "2025-08-21T12:05:00.000Z",
  "metadata": {
    "title": "配信タイトル",
    "scheduled_start_time": "2025-08-21T12:00:00.000Z"
  }
}
```

#### Task停止メッセージ
```json
{
  "action": "stop_collection",
  "video_id": "xxxxxxxxxxx",
  "channel_id": "UCxxxxxxxxxxxxxxxxxx",
  "timestamp": "2025-08-21T14:30:00.000Z",
  "reason": "stream_ended"
}
```

### 2.2 メッセージ属性
- **MessageGroupId**: video_id (FIFO Queueの場合)
- **MessageDeduplicationId**: action + video_id + timestamp
- **DelaySeconds**: 0 (即座実行)
- **VisibilityTimeout**: 300秒

### 2.3 Dead Letter Queue
- **最大受信回数**: 3回
- **DLQ保持期間**: 14日間
- **アラート設定**: DLQにメッセージが入った場合

## 3. 環境変数仕様

### 3.1 Lambda関数共通
```bash
AWS_REGION=ap-northeast-1
LOG_LEVEL=INFO
ENVIRONMENT=dev
DYNAMODB_TABLE_CHANNELS=dev-Channels
DYNAMODB_TABLE_LIVESTREAMS=dev-LiveStreams
DYNAMODB_TABLE_COMMENTS=dev-Comments
DYNAMODB_TABLE_TASKSTATUS=dev-TaskStatus
```

### 3.2 RSS Monitor Lambda
```bash
SQS_QUEUE_URL=https://sqs.ap-northeast-1.amazonaws.com/123456789012/dev-task-control-queue
YOUTUBE_API_KEY_PARAM=/dev/youtube-chat-collector/youtube-api-key
RSS_CHECK_INTERVAL=300
```

### 3.3 Stream Status Checker Lambda
```bash
YOUTUBE_API_KEY_PARAM=/dev/youtube-chat-collector/youtube-api-key
SQS_QUEUE_URL=https://sqs.ap-northeast-1.amazonaws.com/123456789012/dev-task-control-queue
STATUS_CHECK_INTERVAL=300
```

### 3.4 ECS Task Launcher Lambda
```bash
ECS_CLUSTER_NAME=dev-youtube-comment-collector
ECS_TASK_DEFINITION=dev-comment-collector
ECS_SUBNETS=subnet-xxxxxxxxx,subnet-yyyyyyyyy
ECS_SECURITY_GROUPS=sg-xxxxxxxxx
SQS_QUEUE_URL=https://sqs.ap-northeast-1.amazonaws.com/123456789012/dev-task-control-queue
```

### 3.5 API Handler Lambda
```bash
CORS_ALLOWED_ORIGINS=*
API_VERSION=v1
YOUTUBE_API_KEY_PARAM=/dev/youtube-chat-collector/youtube-api-key
```

### 3.6 ECS Comment Collector
```bash
VIDEO_ID=xxxxxxxxxxx
CHANNEL_ID=UCxxxxxxxxxxxxxxxxxx
DYNAMODB_TABLE_COMMENTS=dev-Comments
DYNAMODB_TABLE_TASKSTATUS=dev-TaskStatus
COMMENT_BATCH_SIZE=10
HEALTH_CHECK_INTERVAL=30
```

## 4. エラーコード定義

### 4.1 共通エラーコード
| コード | HTTPステータス | 説明 |
|--------|----------------|------|
| INVALID_PARAMETER | 400 | パラメータが不正 |
| MISSING_PARAMETER | 400 | 必須パラメータが不足 |
| UNAUTHORIZED | 401 | 認証エラー |
| FORBIDDEN | 403 | 権限エラー |
| NOT_FOUND | 404 | リソースが見つからない |
| METHOD_NOT_ALLOWED | 405 | HTTPメソッドが許可されていない |
| INTERNAL_ERROR | 500 | 内部エラー |
| SERVICE_UNAVAILABLE | 503 | サービス利用不可 |

### 4.2 機能固有エラーコード
| コード | HTTPステータス | 説明 |
|--------|----------------|------|
| CHANNEL_ALREADY_EXISTS | 409 | チャンネルが既に存在 |
| INVALID_CHANNEL_ID | 400 | チャンネルIDの形式が不正 |
| STREAM_NOT_FOUND | 404 | 配信が見つからない |
| TASK_ALREADY_RUNNING | 409 | Taskが既に実行中 |
| YOUTUBE_API_ERROR | 502 | YouTube API エラー |
| QUOTA_EXCEEDED | 429 | APIクォータ超過 |
| INVALID_VIDEO_ID | 400 | 動画IDの形式が不正 |
| COMMENT_LIMIT_EXCEEDED | 400 | コメント取得件数制限超過 |

## 5. レート制限

### 5.1 API制限
| エンドポイント | 制限 | 期間 |
|----------------|------|------|
| GET /channels | 100 requests | 1分間 |
| POST /channels | 10 requests | 1分間 |
| GET /streams | 100 requests | 1分間 |
| GET /comments | 50 requests | 1分間 |
| GET /stats | 20 requests | 1分間 |

### 5.2 制限超過時のレスポンス
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 60 seconds."
  },
  "timestamp": "2025-08-21T07:00:00.000Z"
}
```

## 6. ログ出力仕様

### 6.1 ログレベル
- **ERROR**: エラー発生時
- **WARN**: 警告事項
- **INFO**: 一般的な情報
- **DEBUG**: デバッグ情報

### 6.2 ログ形式
```json
{
  "timestamp": "2025-08-21T07:00:00.000Z",
  "level": "INFO",
  "function": "rss-monitor-lambda",
  "request_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "message": "New live stream detected",
  "data": {
    "channel_id": "UCxxxxxxxxxxxxxxxxxx",
    "video_id": "xxxxxxxxxxx",
    "title": "配信タイトル"
  }
}
```

### 6.3 重要ログイベント
- **API Request/Response**: 全APIリクエストとレスポンス
- **チャンネル操作**: 追加/削除/更新
- **配信検出**: 新しいライブ配信検出
- **配信状態変更**: 開始/終了
- **Task制御**: 起動/停止
- **エラー発生**: 全エラーイベント
- **APIクォータ**: 使用量監視

## 7. セキュリティ仕様

### 7.1 API認証
- **API Key**: リクエストヘッダーでの認証
- **CORS**: 適切なオリジン制限
- **HTTPS**: 全通信の暗号化

### 7.2 入力検証
- **パラメータ検証**: 型・形式・範囲チェック
- **SQLインジェクション対策**: パラメータ化クエリ
- **XSS対策**: 出力エスケープ

### 7.3 監査ログ
- **アクセスログ**: 全APIアクセス記録
- **操作ログ**: データ変更操作記録
- **エラーログ**: エラー発生記録

---

**作成日**: 2025-08-21  
**最終更新**: 2025-08-23  
**バージョン**: 2.0  
**作成者**: Amazon Q Developer
