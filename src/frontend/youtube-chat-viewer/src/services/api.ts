/**
 * YouTube Live Chat Collector - API Service
 * 
 * このファイルはAWS API Gatewayとの通信を担当するサービスクラスです。
 * バックエンドのLambda関数群と連携してデータの取得・更新を行います。
 */

// ===== データ型定義 =====

/**
 * チャンネル情報の型定義
 * DynamoDB Channelsテーブルの構造に対応
 */
export interface Channel {
  channel_id: string;        // YouTubeチャンネルID (例: UC1CfXB_kRs3C-zaeTG3oGyg)
  channel_name: string;      // チャンネル名 (例: 赤井はあと)
  is_active: boolean;        // 監視状態 (true: 監視中, false: 停止中)
  created_at: string;        // 登録日時 (ISO 8601形式)
  updated_at?: string;       // 最終更新日時 (ISO 8601形式)
  subscriber_count?: number; // 登録者数 (YouTube Data APIから取得)
  thumbnail_url?: string;    // チャンネルサムネイルURL
}

/**
 * ライブ配信情報の型定義
 * DynamoDB LiveStreamsテーブルの構造に対応
 */
export interface Stream {
  video_id: string;              // YouTube動画ID (例: CkZ2jBMWJNo)
  channel_id: string;            // 所属チャンネルID
  title: string;                 // 配信タイトル
  status: StreamStatus;          // 配信ステータス
  created_at: string;            // 検出日時 (ISO 8601形式)
  updated_at?: string;           // 最終更新日時
  scheduled_start_time?: string; // 開始予定時刻 (upcoming時)
  actual_start_time?: string;    // 実際の開始時刻 (live時)
  actual_end_time?: string;      // 実際の終了時刻 (ended時)
}

/**
 * 配信ステータスの型定義
 * YouTube Data APIのliveBroadcastContentに対応
 */
export type StreamStatus = 'live' | 'upcoming' | 'ended' | 'detected';

/**
 * コメント情報の型定義
 * DynamoDB Commentsテーブルの構造に対応
 */
export interface Comment {
  comment_id: string;         // コメント一意ID
  video_id: string;           // 対象動画ID
  author_name: string;        // コメント投稿者名
  message_text: string;       // コメント本文
  timestamp: string;          // 投稿時刻 (ISO 8601形式)
  author_channel_id?: string; // 投稿者チャンネルID (取得可能な場合)
}

/**
 * システム統計情報の型定義
 * ダッシュボード表示用の集計データ
 */
export interface SystemStats {
  totalChannels: number;    // 総チャンネル数
  activeChannels: number;   // アクティブチャンネル数
  totalStreams: number;     // 総配信数
  activeStreams: number;    // 現在アクティブな配信数 (live + upcoming)
  totalComments: number;    // 総コメント数
  lastUpdate: string;       // 最終更新時刻
}

/**
 * コメント収集状況の型定義
 * ECSタスクの実行状況とコメント収集実績
 */
export interface CollectionStatus {
  active_collections: number;      // 実行中のコメント収集タスク数
  running_video_ids: string[];     // 収集中の動画ID一覧
  today_comments: number;          // 今日収集したコメント数
  last_collection_time: string | null;  // 最後の収集時刻
  task_details: TaskDetail[];      // タスク詳細情報
  timestamp: string;               // 取得時刻
}

/**
 * タスク詳細情報の型定義
 */
export interface TaskDetail {
  video_id: string;          // 対象動画ID
  task_status: string;       // タスク状態 (running/stopped/failed)
  started_at: string;        // 開始時刻
  channel_id?: string;       // チャンネルID
  task_arn?: string;         // ECSタスクARN
}

// ===== API Serviceクラス =====

/**
 * AWS API Gatewayとの通信を担当するメインサービスクラス
 * 
 * 機能:
 * - チャンネル管理 (取得・追加・更新・削除)
 * - ライブ配信情報取得 (全配信・アクティブ配信・フィルタリング)
 * - コメント取得 (配信別・ページネーション対応)
 * - システム統計情報取得 (ダッシュボード用)
 */
class ApiService {
  private baseURL: string;
  private apiKey: string;

  /**
   * コンストラクタ
   * 環境変数からAPI設定を読み込み
   */
  constructor() {
    this.baseURL = process.env.REACT_APP_API_BASE_URL || '';
    this.apiKey = process.env.REACT_APP_API_KEY || '';
    
    // 設定値の検証
    if (!this.baseURL) {
      console.error('REACT_APP_API_BASE_URL が設定されていません');
    }
    if (!this.apiKey) {
      console.error('REACT_APP_API_KEY が設定されていません');
    }
  }

  /**
   * 共通のHTTPリクエスト処理
   * 
   * @param endpoint - APIエンドポイント (例: '/channels')
   * @param options - fetch APIのオプション
   * @returns Promise<T> - レスポンスデータ
   * 
   * 機能:
   * - 共通ヘッダー設定 (Content-Type, x-api-key)
   * - エラーハンドリング
   * - レスポンスのJSON変換
   */
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': this.apiKey,
          ...options.headers,
        },
      });

      // HTTPステータスコードのチェック
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API Error: ${response.status} ${response.statusText} - ${errorText}`);
      }

      return response.json();
    } catch (error) {
      console.error(`API Request Failed: ${url}`, error);
      throw error;
    }
  }

  // ===== チャンネル管理メソッド =====

  /**
   * 全チャンネル一覧を取得
   * 
   * @returns Promise<Channel[]> - チャンネル一覧
   * 
   * 対応するLambda: API Handler Lambda
   * エンドポイント: GET /channels
   * 
   * 取得データ:
   * - 登録済み全チャンネル
   * - チャンネル名、登録者数、サムネイル等の詳細情報
   * - 監視状態 (is_active)
   */
  async getChannels(): Promise<Channel[]> {
    const response = await this.request<{channels: Channel[], count: number}>('/channels');
    return response.channels || [];
  }

  /**
   * 新しいチャンネルを監視対象に追加
   * 
   * @param channelId - YouTubeチャンネルID (例: UC1CfXB_kRs3C-zaeTG3oGyg)
   * @returns Promise<Channel> - 追加されたチャンネル情報
   * 
   * 対応するLambda: API Handler Lambda
   * エンドポイント: POST /channels
   * 
   * 処理内容:
   * 1. YouTube Data APIでチャンネル情報を取得
   * 2. DynamoDB Channelsテーブルに保存
   * 3. RSS Monitor Lambdaが自動的に監視開始
   */
  async addChannel(channelId: string): Promise<Channel> {
    return this.request<Channel>('/channels', {
      method: 'POST',
      body: JSON.stringify({ channel_id: channelId }),
    });
  }

  /**
   * チャンネルの監視状態を更新
   * 
   * @param channelId - 対象チャンネルID
   * @param isActive - 監視状態 (true: 監視開始, false: 監視停止)
   * @returns Promise<Channel> - 更新されたチャンネル情報
   * 
   * 対応するLambda: API Handler Lambda
   * エンドポイント: PUT /channels/{channelId}
   */
  async updateChannelStatus(channelId: string, isActive: boolean): Promise<Channel> {
    const response = await this.request<{message: string, channel: Channel}>(`/channels/${channelId}`, {
      method: 'PUT',
      body: JSON.stringify({ is_active: isActive }),
    });
    return response.channel;
  }

  /**
   * チャンネルを削除（安全な削除: 監視停止）
   * 
   * @param channelId - 削除対象チャンネルID
   * @returns Promise<{message: string, channel: Channel}> - 削除結果
   * 
   * 対応するLambda: API Handler Lambda
   * エンドポイント: DELETE /channels/{channelId}
   * 
   * 注意: 実際にはデータを削除せず、監視を停止してリストから除去
   */
  async deleteChannel(channelId: string): Promise<{message: string, channel: Channel}> {
    return this.request<{message: string, channel: Channel}>(`/channels/${channelId}`, {
      method: 'DELETE',
    });
  }

  // ===== 配信管理メソッド =====

  /**
   * ライブ配信一覧を取得 (フィルタリング対応)
   * 
   * @param filters - フィルター条件
   * @param filters.status - 配信ステータス (例: 'live,upcoming')
   * @param filters.channel_id - 特定チャンネルのみ取得
   * @returns Promise<Stream[]> - 配信一覧
   * 
   * 対応するLambda: API Handler Lambda
   * エンドポイント: GET /streams?status=live,upcoming&channel_id=xxx
   */
  async getStreams(filters?: { status?: string; channel_id?: string }): Promise<Stream[]> {
    const params = new URLSearchParams();
    if (filters?.status) params.append('status', filters.status);
    if (filters?.channel_id) params.append('channel_id', filters.channel_id);
    
    const endpoint = `/streams${params.toString() ? `?${params.toString()}` : ''}`;
    const response = await this.request<{streams: Stream[], count: number}>(endpoint);
    return response.streams || [];
  }

  /**
   * 現在アクティブな配信のみを取得
   * 
   * @returns Promise<Stream[]> - アクティブ配信一覧 (live + upcoming + detected)
   * 
   * 用途: ダッシュボードでの監視中配信表示
   * 
   * 取得対象:
   * - live: 現在配信中
   * - upcoming: 配信予約済み
   * - detected: 新規検出済み
   */
  async getActiveStreams(): Promise<Stream[]> {
    return this.getStreams({ status: 'live,upcoming,detected' });
  }

  /**
   * 特定配信の詳細情報を取得
   * 
   * @param videoId - YouTube動画ID
   * @returns Promise<Stream> - 配信詳細情報
   */
  async getStreamDetails(videoId: string): Promise<Stream> {
    return this.request<Stream>(`/streams/${videoId}`);
  }

  // ===== コメント管理メソッド =====

  /**
   * 特定配信のコメント一覧を取得
   * 
   * @param videoId - 対象動画ID
   * @param options - 取得オプション
   * @param options.limit - 取得件数制限 (デフォルト: 100)
   * @param options.offset - 取得開始位置 (ページネーション用)
   * @returns Promise<Comment[]> - コメント一覧
   * 
   * 対応するLambda: API Handler Lambda
   * エンドポイント: GET /comments/{videoId}?limit=100&offset=0
   */
  async getComments(videoId: string, options?: { limit?: number; offset?: number }): Promise<Comment[]> {
    const params = new URLSearchParams();
    if (options?.limit) params.append('limit', options.limit.toString());
    if (options?.offset) params.append('offset', options.offset.toString());
    
    const endpoint = `/comments/${videoId}${params.toString() ? `?${params.toString()}` : ''}`;
    const response = await this.request<{comments: Comment[], count: number, total: number}>(endpoint);
    return response.comments || [];
  }

  // ===== システム統計メソッド =====

  /**
   * コメント収集状況を取得
   * 
   * @returns Promise<CollectionStatus> - コメント収集状況
   * 
   * 用途: ダッシュボードでの実際のコメント収集状況表示
   * 
   * 取得内容:
   * - 実行中のECSタスク数
   * - 収集中の動画ID一覧
   * - 今日の収集コメント数
   * - 最後の収集時刻
   */
  async getCollectionStatus(): Promise<CollectionStatus> {
    return this.request<CollectionStatus>('/collection-status');
  }

  /**
   * システム全体の統計情報を取得
   * 
   * @returns Promise<SystemStats> - システム統計情報
   * 
   * 用途: ダッシュボードでのシステム状況表示
   * 
   * 取得内容:
   * - チャンネル数 (総数・アクティブ数)
   * - 配信数 (総数・アクティブ数)
   * - コメント数 (総数)
   * - 最終更新時刻
   */
  async getSystemStats(): Promise<SystemStats> {
    const [channels, streams] = await Promise.all([
      this.getChannels(),
      this.getStreams(),
    ]);

    return {
      totalChannels: channels.length,
      activeChannels: channels.filter(ch => ch.is_active).length,
      totalStreams: streams.length,
      activeStreams: streams.filter(s => ['live', 'upcoming', 'detected'].includes(s.status)).length,
      totalComments: 0, // TODO: 後でコメント総数API実装時に更新
      lastUpdate: new Date().toISOString(),
    };
  }
}

// ===== エクスポート =====

/**
 * APIサービスのシングルトンインスタンス
 * アプリケーション全体で共有して使用
 */
export const apiService = new ApiService();

/**
 * デフォルトエクスポート
 * import apiService from './services/api' で使用可能
 */
export default apiService;
