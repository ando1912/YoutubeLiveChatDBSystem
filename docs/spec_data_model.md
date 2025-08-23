# データモデル仕様書

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
  "is_active": true,
  "created_at": "2025-08-21T07:00:00.000Z",
  "updated_at": "2025-08-21T07:00:00.000Z",
  "subscriber_count": "1000000",
  "custom_url": "@channelname",
  "view_count": "500000000",
  "video_count": "1000",
  "country": "JP",
  "default_language": "ja",
  "description": "チャンネル説明文",
  "published_at": "2018-01-01T00:00:00Z",
  "api_retrieved_at": "2025-08-21T07:00:00.000Z",
  "thumbnail_default": "https://yt3.ggpht.com/.../s88-c-k-c0x00ffffff-no-rj",
  "thumbnail_medium": "https://yt3.ggpht.com/.../s240-c-k-c0x00ffffff-no-rj",
  "thumbnail_high": "https://yt3.ggpht.com/.../s800-c-k-c0x00ffffff-no-rj"
}
```

#### 項目説明
| 項目名 | 型 | 必須 | 説明 |
|--------|----|----|------|
| channel_id | String | ✅ | YouTubeチャンネルID（UC形式、24文字）。プライマリキー |
| channel_name | String | ✅ | チャンネル表示名。YouTube Data API v3から取得 |
| is_active | Boolean | ✅ | 監視状態フラグ。true=監視中、false=監視停止 |
| created_at | String | ✅ | チャンネル登録日時（ISO8601形式） |
| updated_at | String | ✅ | 最終更新日時（ISO8601形式） |
| subscriber_count | String | ❌ | 登録者数。YouTube Data API v3から取得（文字列形式） |
| custom_url | String | ❌ | チャンネルカスタムURL（@形式） |
| view_count | String | ❌ | 総再生回数。YouTube Data API v3から取得（文字列形式） |
| video_count | String | ❌ | 動画投稿数。YouTube Data API v3から取得（文字列形式） |
| country | String | ❌ | チャンネルの国・地域コード（ISO 3166-1 alpha-2） |
| default_language | String | ❌ | チャンネルのデフォルト言語コード（ISO 639-1） |
| description | String | ❌ | チャンネル説明文。YouTube Data API v3から取得 |
| published_at | String | ❌ | チャンネル作成日時（ISO8601形式） |
| api_retrieved_at | String | ❌ | YouTube Data API v3からの情報取得日時 |
| thumbnail_default | String | ❌ | チャンネルサムネイル（88x88px） |
| thumbnail_medium | String | ❌ | チャンネルサムネイル（240x240px） |
| thumbnail_high | String | ❌ | チャンネルサムネイル（800x800px） |

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
  "description": "配信の詳細説明文",
  "published_at": "2025-08-21T12:00:00.000Z",
  "started_at": "2025-08-21T12:05:00.000Z",
  "ended_at": "2025-08-21T14:30:00.000Z",
  "created_at": "2025-08-21T07:00:00.000Z",
  "updated_at": "2025-08-21T12:05:00.000Z"
}
```

#### 項目説明
| 項目名 | 型 | 必須 | 説明 |
|--------|----|----|------|
| video_id | String | ✅ | YouTube動画ID（11文字）。プライマリキー |
| channel_id | String | ✅ | 配信者のYouTubeチャンネルID。GSIのパーティションキー |
| title | String | ✅ | 配信タイトル。YouTube Data API v3から取得 |
| status | String | ✅ | 配信状態。upcoming/live/ended/detected |
| description | String | ❌ | 配信の詳細説明文。YouTube Data API v3から取得 |
| published_at | String | ❌ | 配信の公開日時（ISO8601形式） |
| started_at | String | ❌ | 実際の配信開始日時（ISO8601形式） |
| ended_at | String | ❌ | 実際の配信終了日時（ISO8601形式）。配信中はnull |
| created_at | String | ✅ | レコード作成日時（ISO8601形式）。GSIのソートキー |
| updated_at | String | ✅ | 最終更新日時（ISO8601形式） |

#### ステータス定義
- **upcoming**: 配信予定（まだ開始していない）
- **live**: 配信中
- **ended**: 配信終了
- **detected**: RSS検出済み（状態未確認）

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

#### 項目説明
| 項目名 | 型 | 必須 | 説明 |
|--------|----|----|------|
| comment_id | String | ✅ | コメント一意識別子（UUID v4形式）。プライマリキー |
| video_id | String | ✅ | 配信のYouTube動画ID。ソートキー、GSIのパーティションキー |
| author_name | String | ✅ | コメント投稿者の表示名。pytchatから取得 |
| message | String | ✅ | コメント本文。絵文字・特殊文字含む |
| timestamp | String | ✅ | コメント投稿日時（ISO8601形式）。GSIのソートキー |
| superchat_amount | Number | ❌ | スーパーチャット金額（円）。通常コメントは0 |
| created_at | String | ✅ | レコード作成日時（ISO8601形式） |

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
  "channel_id": "UCxxxxxxxxxxxxxxxxxx",
  "task_arn": "arn:aws:ecs:ap-northeast-1:123456789012:task/youtube-comment-collector/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "status": "running",
  "started_at": "2025-08-21T12:05:00.000Z",
  "stopped_at": null,
  "updated_at": "2025-08-21T12:05:00.000Z"
}
```

#### 項目説明
| 項目名 | 型 | 必須 | 説明 |
|--------|----|----|------|
| video_id | String | ✅ | 配信のYouTube動画ID。プライマリキー |
| channel_id | String | ✅ | 配信者のYouTubeチャンネルID |
| task_arn | String | ❌ | 実行中のECS TaskのARN。タスク停止時に使用 |
| status | String | ✅ | タスク実行状態。running/stopped/failed |
| started_at | String | ❌ | タスク開始日時（ISO8601形式） |
| stopped_at | String | ❌ | タスク停止日時（ISO8601形式）。実行中はnull |
| updated_at | String | ✅ | 最終更新日時（ISO8601形式） |

#### ステータス定義
- **running**: Task実行中
- **stopped**: Task停止済み
- **failed**: Task実行失敗

#### アクセスパターン
- **Task状態確認**: GetItem (video_id)
- **Task状態更新**: UpdateItem
- **実行中Task一覧**: Scan with FilterExpression (status = running)

## 2. データ関係図

```
Channels (1) ──────── (N) LiveStreams
    │                      │
    │                      │
    │                      │ (1)
    │                      │
    │                      ▼
    │                 TaskStatus (1)
    │                      │
    │                      │
    │ (1)                  │
    │                      │
    ▼                      ▼
LiveStreams (1) ──────── (N) Comments
```

### 2.1 データ型説明

#### 共通データ型
- **String**: UTF-8文字列。DynamoDBのS型
- **Number**: 数値。DynamoDBのN型
- **Boolean**: 真偽値。DynamoDBのBOOL型
- **ISO8601**: 日時文字列形式（例: 2025-08-21T12:00:00.000Z）

#### 特殊な形式
- **YouTube Channel ID**: UC + 22文字の英数字（例: UCxxxxxxxxxxxxxxxxxx）
- **YouTube Video ID**: 11文字の英数字（例: xxxxxxxxxxx）
- **UUID v4**: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx形式
- **ECS Task ARN**: arn:aws:ecs:region:account:task/cluster/task-id形式

### 2.2 必須項目の説明
- **✅ 必須**: レコード作成時に必ず設定される項目
- **❌ オプション**: 条件により設定される項目、またはnull許可項目

## 3. インデックス設計

### 3.1 プライマリインデックス
| テーブル | パーティションキー | ソートキー |
|----------|-------------------|------------|
| Channels | channel_id | - |
| LiveStreams | video_id | - |
| Comments | comment_id | video_id |
| TaskStatus | video_id | - |

### 3.2 グローバルセカンダリインデックス (GSI)
| テーブル | インデックス名 | パーティションキー | ソートキー |
|----------|----------------|-------------------|------------|
| LiveStreams | channel_id-index | channel_id | created_at |
| Comments | video_id-timestamp-index | video_id | timestamp |

## 4. データ容量見積もり

### 4.1 想定データ量
- **チャンネル数**: 10チャンネル
- **月間配信数**: 300配信
- **配信あたりコメント数**: 1,000件
- **月間コメント数**: 300,000件

### 4.2 ストレージ容量
| テーブル | 1レコードサイズ | 月間レコード数 | 月間容量 |
|----------|----------------|----------------|----------|
| Channels | 2,000 bytes | 10 | 20 KB |
| LiveStreams | 1,500 bytes | 300 | 450 KB |
| Comments | 300 bytes | 300,000 | 90 MB |
| TaskStatus | 400 bytes | 300 | 120 KB |
| **合計** | - | - | **約91 MB** |

#### 容量計算根拠
- **Channels**: YouTube Data API v3の詳細情報含む（サムネイル、説明文等）
- **LiveStreams**: 配信詳細情報含む（説明文、各種日時等）
- **Comments**: コメント本文、投稿者名、メタデータ
- **TaskStatus**: ECS Task管理情報

### 4.3 読み書き容量
| テーブル | 読み込み (RCU/月) | 書き込み (WCU/月) |
|----------|-------------------|-------------------|
| Channels | 1,000 | 100 |
| LiveStreams | 10,000 | 1,000 |
| Comments | 100,000 | 300,000 |
| TaskStatus | 5,000 | 1,000 |

## 5. データライフサイクル

### 5.1 データ保持期間
- **Channels**: 永続保持
- **LiveStreams**: 1年間保持
- **Comments**: 6ヶ月間保持
- **TaskStatus**: 1ヶ月間保持

### 5.2 アーカイブ戦略
- **Comments**: 3ヶ月経過後にS3 Glacierに移行
- **LiveStreams**: 6ヶ月経過後にS3 Standard-IAに移行
- **TaskStatus**: 1週間経過後に削除

## 6. パフォーマンス設計

### 6.1 読み込み最適化
- **ホットパーティション回避**: channel_idの分散
- **GSI活用**: 頻繁なクエリパターンに対応
- **バッチ読み込み**: BatchGetItemの活用

### 6.2 書き込み最適化
- **バッチ書き込み**: BatchWriteItemの活用
- **条件付き書き込み**: 重複防止
- **非同期処理**: SQSを経由した書き込み

## 7. セキュリティ設計

### 7.1 暗号化
- **保存時暗号化**: AWS Managed Key使用
- **転送時暗号化**: HTTPS/TLS 1.2以上

### 7.2 アクセス制御
- **IAMロール**: 最小権限の原則
- **VPCエンドポイント**: プライベート接続
- **リソースベースポリシー**: 必要に応じて設定

## 8. 監視・運用

### 8.1 CloudWatch メトリクス
- **読み書き容量使用率**
- **スロットリング発生率**
- **エラー率**
- **レイテンシ**

### 8.2 アラート設定
- **容量使用率 > 80%**
- **エラー率 > 1%**
- **レイテンシ > 100ms**

---

**作成日**: 2025-08-21  
**最終更新**: 2025-08-23  
**バージョン**: 2.0  
**作成者**: Amazon Q Developer
