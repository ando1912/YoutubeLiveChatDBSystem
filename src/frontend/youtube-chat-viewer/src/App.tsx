import React, { useState, useEffect } from 'react';
import './App.css';
import { apiService, Channel, Stream, SystemStats, CollectionStatus } from './services/api';
import ChannelManager from './components/ChannelManager';

/**
 * YouTube Live Chat Collector - メインアプリケーション
 * 
 * Phase 12 Step 2: チャンネル管理機能統合
 * Phase 12 Step 3: コメント収集状況表示追加
 * - ダッシュボード表示
 * - チャンネル管理機能
 * - タブ切り替え
 * - 実際のECSタスク実行状況表示
 */
function App() {
  // ===== State管理 =====
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null);
  const [collectionStatus, setCollectionStatus] = useState<CollectionStatus | null>(null);
  const [channels, setChannels] = useState<Channel[]>([]);
  const [activeStreams, setActiveStreams] = useState<Stream[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'dashboard' | 'channels'>('dashboard');

  // ===== データ取得関数 =====
  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      console.log('🔄 ダッシュボードデータ取得開始...');

      // 並列でデータ取得
      const [channelsData, activeStreamsData, collectionStatusData] = await Promise.all([
        apiService.getChannels(),
        apiService.getActiveStreams(),
        apiService.getCollectionStatus(),
      ]);

      // システム統計を計算
      const stats: SystemStats = {
        totalChannels: channelsData.length,
        activeChannels: channelsData.filter(ch => ch.is_active).length,
        totalStreams: activeStreamsData.length,
        activeStreams: activeStreamsData.filter(s => ['live', 'upcoming'].includes(s.status)).length,
        totalComments: collectionStatusData.today_comments, // 今日のコメント数を使用
        lastUpdate: new Date().toISOString(),
      };

      // State更新
      setChannels(channelsData);
      setActiveStreams(activeStreamsData);
      setSystemStats(stats);
      setCollectionStatus(collectionStatusData);
      setLastUpdate(new Date().toLocaleString('ja-JP'));

      console.log('✅ ダッシュボードデータ取得完了', {
        channels: channelsData.length,
        streams: activeStreamsData.length,
        activeTasks: collectionStatusData.active_collections,
      });

    } catch (err) {
      console.error('❌ ダッシュボードデータ取得エラー:', err);
      setError(err instanceof Error ? err.message : 'データ取得に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  // ===== 初期データ読み込み =====
  useEffect(() => {
    fetchDashboardData();

    // 30秒間隔で自動更新
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  // ===== タブ切り替え処理 =====
  const handleTabChange = (tab: 'dashboard' | 'channels') => {
    setActiveTab(tab);
    // チャンネル管理タブに切り替えた時は最新データを取得
    if (tab === 'channels') {
      fetchDashboardData();
    }
  };

  // ===== レンダリング =====
  return (
    <div className="app">
      {/* ヘッダー */}
      <header className="app-header">
        <div className="header-content">
          <h1>🎬 YouTube Live Chat Collector</h1>
          <div className="header-info">
            <span className="environment">Environment: dev</span>
            <span className="last-update">最終更新: {lastUpdate}</span>
            <button 
              className="refresh-btn"
              onClick={fetchDashboardData}
              disabled={loading}
            >
              {loading ? '🔄' : '↻'} 更新
            </button>
          </div>
        </div>
      </header>

      {/* ナビゲーションタブ */}
      <nav className="app-nav">
        <div className="nav-content">
          <button 
            className={`nav-tab ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => handleTabChange('dashboard')}
          >
            📊 ダッシュボード
          </button>
          <button 
            className={`nav-tab ${activeTab === 'channels' ? 'active' : ''}`}
            onClick={() => handleTabChange('channels')}
          >
            📺 チャンネル管理
          </button>
        </div>
      </nav>

      {/* メインコンテンツ */}
      <main className="app-main">
        {/* エラー表示 */}
        {error && (
          <div className="error-banner">
            <span>❌ エラー: {error}</span>
            <button onClick={fetchDashboardData}>再試行</button>
          </div>
        )}

        {/* ローディング表示 */}
        {loading && (
          <div className="loading-banner">
            <span>🔄 データ読み込み中...</span>
          </div>
        )}

        {/* タブコンテンツ */}
        {activeTab === 'dashboard' && (
          <>
            {/* システム統計カード */}
            {systemStats && (
              <section className="stats-section">
                <h2>📊 システム統計</h2>
                <div className="stats-grid">
                  <div className="stat-card">
                    <div className="stat-icon">📺</div>
                    <div className="stat-content">
                      <div className="stat-number">{systemStats.totalChannels}</div>
                      <div className="stat-label">監視チャンネル</div>
                      <div className="stat-detail">
                        アクティブ: {systemStats.activeChannels}
                      </div>
                    </div>
                  </div>

                  <div className="stat-card">
                    <div className="stat-icon">🎥</div>
                    <div className="stat-content">
                      <div className="stat-number">{systemStats.totalStreams}</div>
                      <div className="stat-label">検出配信</div>
                      <div className="stat-detail">
                        アクティブ: {systemStats.activeStreams}
                      </div>
                    </div>
                  </div>

                  <div className="stat-card">
                    <div className="stat-icon">💬</div>
                    <div className="stat-content">
                      <div className="stat-number">{systemStats.totalComments.toLocaleString()}</div>
                      <div className="stat-label">今日の収集コメント</div>
                      <div className="stat-detail">
                        実行中タスク: {collectionStatus?.active_collections || 0}
                      </div>
                    </div>
                  </div>

                  <div className="stat-card">
                    <div className="stat-icon">⚡</div>
                    <div className="stat-content">
                      <div className="stat-number">
                        {collectionStatus?.active_collections || 0}
                      </div>
                      <div className="stat-label">コメント収集中</div>
                      <div className="stat-detail">
                        ECSタスク実行数
                      </div>
                    </div>
                  </div>
                </div>
              </section>
            )}

            {/* コメント収集状況セクション */}
            {collectionStatus && (
              <section className="collection-section">
                <h2>💬 コメント収集状況</h2>
                <div className="collection-info">
                  <div className="collection-summary">
                    <div className="summary-item">
                      <span className="summary-label">実行中タスク:</span>
                      <span className="summary-value">{collectionStatus.active_collections}個</span>
                    </div>
                    <div className="summary-item">
                      <span className="summary-label">今日の収集:</span>
                      <span className="summary-value">{collectionStatus.today_comments.toLocaleString()}コメント</span>
                    </div>
                    <div className="summary-item">
                      <span className="summary-label">最終収集:</span>
                      <span className="summary-value">
                        {collectionStatus.last_collection_time 
                          ? new Date(collectionStatus.last_collection_time).toLocaleString('ja-JP')
                          : '未実行'
                        }
                      </span>
                    </div>
                  </div>
                  
                  {collectionStatus.running_video_ids.length > 0 && (
                    <div className="running-tasks">
                      <h3>収集中の配信:</h3>
                      <div className="task-list">
                        {collectionStatus.running_video_ids.map((videoId) => (
                          <div key={videoId} className="task-item">
                            <span className="task-status">🟢</span>
                            <span className="task-video-id">{videoId}</span>
                            <a 
                              href={`https://www.youtube.com/watch?v=${videoId}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="task-link"
                            >
                              YouTube で開く
                            </a>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </section>
            )}

            {/* アクティブ配信セクション */}
            <section className="streams-section">
              <h2>🔴 検出済み配信</h2>
              {activeStreams.length > 0 ? (
                <div className="streams-grid">
                  {activeStreams.slice(0, 6).map((stream) => (
                    <div key={stream.video_id} className="stream-card">
                      <div className={`stream-status ${stream.status}`}>
                        {stream.status === 'live' ? '🔴 LIVE' : 
                         stream.status === 'upcoming' ? '⏰ 予約配信' : 
                         '🆕 検出済み'}
                      </div>
                      <div className="stream-title">{stream.title}</div>
                      <div className="stream-channel">
                        チャンネル: {stream.channel_id}
                      </div>
                      <div className="stream-time">
                        {stream.status === 'upcoming' && stream.scheduled_start_time
                          ? `開始予定: ${new Date(stream.scheduled_start_time).toLocaleString('ja-JP')}`
                          : `検出時刻: ${new Date(stream.created_at).toLocaleString('ja-JP')}`
                        }
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="no-data">
                  現在アクティブな配信はありません
                </div>
              )}
            </section>

            {/* API接続状況 */}
            <section className="api-status-section">
              <h2>🔗 API接続状況</h2>
              <div className="api-info">
                <div className="api-endpoint">
                  <strong>エンドポイント:</strong> {process.env.REACT_APP_API_BASE_URL}
                </div>
                <div className="api-status">
                  <strong>接続状態:</strong> 
                  <span className={error ? 'status-error' : 'status-ok'}>
                    {error ? '❌ エラー' : '✅ 正常'}
                  </span>
                </div>
                <div className="api-version">
                  <strong>アプリバージョン:</strong> {process.env.REACT_APP_VERSION}
                </div>
              </div>
            </section>
          </>
        )}

        {/* チャンネル管理タブ */}
        {activeTab === 'channels' && (
          <ChannelManager 
            channels={channels}
            onChannelsUpdate={fetchDashboardData}
          />
        )}
      </main>

      {/* フッター */}
      <footer className="app-footer">
        <div className="footer-content">
          <span>YouTube Live Chat Collector - Phase 12 Step 2</span>
          <span>Build Time: {process.env.REACT_APP_BUILD_TIME}</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
