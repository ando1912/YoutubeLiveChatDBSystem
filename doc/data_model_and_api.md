# データモデル・API仕様書

## 1. DynamoDB データモデル詳細

### 1.1 Channels テーブル

#### テーブル設定
- **テーブル名**: `Channels`
- **パーティションキー**: `channel_id` (String)
- **課金モード**: On-Demand
- **暗号化**: AWS Managed Key

#### 項目定義
```json
{
  "channel_id": "UCxxxxxxxxxxxxxxxxxx",
  "channel_name": "チャンネル名",
  "rss_url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCxxxxxxxxxxxxxxxxxx",
  "is_active": true,
  "created_at": "2025-08-21T07:00:00.000Z",
  "updated_at": "2025-08-21T07:00:00.000Z"
}
```

#### アクセスパターン
- **チャンネル一覧取得**: Scan (is_active = true)
- **特定チャンネル取得**: GetItem (channel_id)
- **チャンネル追加**: PutItem
- **チャンネル更新**: UpdateItem

### 1.2 LiveStreams テーブル

#### テーブル設定
- **テーブル名**: `LiveStreams`
- **パーティションキー**: `video_id` (String)
- **課金モード**: On-Demand
- **暗号化**: AWS Managed Key

#### GSI設定
- **インデックス名**: `channel_id-index`
- **パーティションキー**: `channel_id` (String)
- **ソートキー**: `created_at` (String)

#### 項目定義
```json
{
  "video_id": "xxxxxxxxxxx",
  "channel_id": "UCxxxxxxxxxxxxxxxxxx",
  "title": "【ライブ配信】今日も元気に配信するよ！",
  "status": "live",
  "scheduled_start_time": "2025-08-21T12:00:00.000Z",
  "actual_start_time": "2025-08-21T12:05:00.000Z",
  "actual_end_time": null,
  "created_at": "2025-08-21T07:00:00.000Z",
  "updated_at": "2025-08-21T12:05:00.000Z"
}
```

#### ステータス定義
- **upcoming**: 配信予定（まだ開始していない）
- **live**: 配信中
- **ended**: 配信終了

#### アクセスパターン
- **全配信一覧**: Scan
- **チャンネル別配信一覧**: Query (GSI: channel_id-index)
- **ステータス別配信一覧**: Scan with FilterExpression
- **特定配信取得**: GetItem (video_id)
- **配信状態更新**: UpdateItem

### 1.3 Comments テーブル

#### テーブル設定
- **テーブル名**: `Comments`
- **パーティションキー**: `comment_id` (String)
- **ソートキー**: `video_id` (String)
- **課金モード**: On-Demand
- **暗号化**: AWS Managed Key

#### GSI設定
- **インデックス名**: `video_id-timestamp-index`
- **パーティションキー**: `video_id` (String)
- **ソートキー**: `timestamp` (String)

#### 項目定義
```json
{
  "comment_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "video_id": "xxxxxxxxxxx",
  "author_name": "視聴者名",
  "message": "こんにちは！楽しい配信ですね",
  "timestamp": "2025-08-21T12:10:30.000Z",
  "superchat_amount": 0,
  "created_at": "2025-08-21T12:10:30.500Z"
}
```

#### アクセスパターン
- **配信別コメント一覧**: Query (GSI: video_id-timestamp-index)
- **コメント追加**: PutItem
- **時系列コメント取得**: Query with SortKey range

### 1.4 TaskStatus テーブル

#### テーブル設定
- **テーブル名**: `TaskStatus`
- **パーティションキー**: `video_id` (String)
- **課金モード**: On-Demand
- **暗号化**: AWS Managed Key

#### 項目定義
```json
{
  "video_id": "xxxxxxxxxxx",
  "task_arn": "arn:aws:ecs:ap-northeast-1:123456789012:task/youtube-comment-collector/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "status": "RUNNING",
  "started_at": "2025-08-21T12:05:00.000Z",
  "stopped_at": null
}
```

#### ステータス定義
- **RUNNING**: Task実行中
- **STOPPED**: Task停止済み
- **FAILED**: Task実行失敗

#### アクセスパターン
- **Task状態確認**: GetItem (video_id)
- **Task状態更新**: UpdateItem
- **実行中Task一覧**: Scan with FilterExpression (status = RUNNING)

## 2. REST API 仕様

### 2.1 共通仕様

#### ベースURL
```
https://api.example.com/v1
```

#### 認証
- **方式**: API Key
- **ヘッダー**: `X-API-Key: YOUR_API_KEY`

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

### 2.2 チャンネル管理API

#### GET /channels
チャンネル一覧を取得

**リクエスト**
```
GET /channels
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
```json
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
      "created_at": "2025-08-21T07:00:00.000Z",
      "updated_at": "2025-08-21T07:00:00.000Z"
    }
  },
  "error": null,
  "timestamp": "2025-08-21T07:00:00.000Z"
}
```

### 2.3 配信管理API

#### GET /streams
配信一覧を取得

**リクエスト**
```
GET /streams
```

**クエリパラメータ**
- `status` (optional): `upcoming` | `live` | `ended` - 特定ステータスの配信のみ
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
```
GET /streams/xxxxxxxxxxx
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
      "created_at": "2025-08-21T07:00:00.000Z",
      "updated_at": "2025-08-21T12:05:00.000Z"
    }
  },
  "error": null,
  "timestamp": "2025-08-21T07:00:00.000Z"
}
```

### 2.4 コメント取得API

#### GET /streams/{video_id}/comments
特定配信のコメント一覧を取得

**リクエスト**
```
GET /streams/xxxxxxxxxxx/comments
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

## 3. SQS メッセージ仕様

### 3.1 Task制御メッセージ

#### Task起動メッセージ
```json
{
  "action": "start",
  "video_id": "xxxxxxxxxxx",
  "channel_id": "UCxxxxxxxxxxxxxxxxxx",
  "timestamp": "2025-08-21T12:05:00.000Z"
}
```

#### Task停止メッセージ
```json
{
  "action": "stop",
  "video_id": "xxxxxxxxxxx",
  "channel_id": "UCxxxxxxxxxxxxxxxxxx",
  "timestamp": "2025-08-21T14:30:00.000Z"
}
```

### 3.2 メッセージ属性
- **MessageGroupId**: video_id (FIFO Queueの場合)
- **MessageDeduplicationId**: action + video_id + timestamp

## 4. 環境変数仕様

### 4.1 Lambda関数共通
```
AWS_REGION=ap-northeast-1
LOG_LEVEL=INFO
DYNAMODB_TABLE_CHANNELS=Channels
DYNAMODB_TABLE_LIVESTREAMS=LiveStreams
DYNAMODB_TABLE_COMMENTS=Comments
DYNAMODB_TABLE_TASKSTATUS=TaskStatus
```

### 4.2 RSS Monitor Lambda
```
SQS_QUEUE_URL=https://sqs.ap-northeast-1.amazonaws.com/123456789012/task-control-queue
```

### 4.3 Stream Status Checker Lambda
```
YOUTUBE_API_KEY=YOUR_YOUTUBE_API_KEY
SQS_QUEUE_URL=https://sqs.ap-northeast-1.amazonaws.com/123456789012/task-control-queue
```

### 4.4 ECS Task Launcher Lambda
```
ECS_CLUSTER_NAME=youtube-comment-collector
ECS_TASK_DEFINITION=comment-collector:1
ECS_SUBNETS=subnet-xxxxxxxxx,subnet-yyyyyyyyy
ECS_SECURITY_GROUPS=sg-xxxxxxxxx
```

### 4.5 ECS Comment Collector
```
VIDEO_ID=xxxxxxxxxxx
DYNAMODB_TABLE_COMMENTS=Comments
DYNAMODB_TABLE_TASKSTATUS=TaskStatus
```

## 5. エラーコード定義

### 5.1 共通エラーコード
| コード | 説明 |
|--------|------|
| INVALID_PARAMETER | パラメータが不正 |
| MISSING_PARAMETER | 必須パラメータが不足 |
| UNAUTHORIZED | 認証エラー |
| FORBIDDEN | 権限エラー |
| NOT_FOUND | リソースが見つからない |
| INTERNAL_ERROR | 内部エラー |
| SERVICE_UNAVAILABLE | サービス利用不可 |

### 5.2 機能固有エラーコード
| コード | 説明 |
|--------|------|
| CHANNEL_ALREADY_EXISTS | チャンネルが既に存在 |
| INVALID_CHANNEL_ID | チャンネルIDの形式が不正 |
| STREAM_NOT_FOUND | 配信が見つからない |
| TASK_ALREADY_RUNNING | Taskが既に実行中 |
| YOUTUBE_API_ERROR | YouTube API エラー |
| QUOTA_EXCEEDED | APIクォータ超過 |

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
  "message": "New live stream detected",
  "data": {
    "channel_id": "UCxxxxxxxxxxxxxxxxxx",
    "video_id": "xxxxxxxxxxx",
    "title": "配信タイトル"
  }
}
```

### 6.3 重要ログイベント
- チャンネル追加/削除
- 新しいライブ配信検出
- 配信開始/終了
- Task起動/停止
- エラー発生
- APIクォータ使用量

---

**作成日**: 2025-08-21  
**バージョン**: 1.0  
**作成者**: Amazon Q Developer
