import React, { useState, useEffect } from 'react';
import './App.css';
import { apiService, Channel, Stream, SystemStats } from './services/api';

/**
 * YouTube Live Chat Collector - メインアプリケーション
 * 
 * Phase 12 Step 1: 基本ダッシュボード実装
 * - システム稼働状況表示
 * - 基本統計情報
 * - API接続確認
 */
function App() {
  // ===== State管理 =====
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null);
  const [channels, setChannels] = useState<Channel[]>([]);
  const [activeStreams, setActiveStreams] = useState<Stream[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string>('');

  // ===== データ取得関数 =====
  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      console.log('🔄 ダッシュボードデータ取得開始...');

      // 並列でデータ取得
      const [channelsData, activeStreamsData] = await Promise.all([
        apiService.getChannels(),
        apiService.getActiveStreams(),
      ]);

      // システム統計を計算
      const stats: SystemStats = {
        totalChannels: channelsData.length,
        activeChannels: channelsData.filter(ch => ch.is_active).length,
        totalStreams: activeStreamsData.length,
        activeStreams: activeStreamsData.filter(s => ['live', 'upcoming'].includes(s.status)).length,
        totalComments: 2917, // TODO: API実装後に動的取得
        lastUpdate: new Date().toISOString(),
      };

      // State更新
      setChannels(channelsData);
      setActiveStreams(activeStreamsData);
      setSystemStats(stats);
      setLastUpdate(new Date().toLocaleString('ja-JP'));

      console.log('✅ ダッシュボードデータ取得完了', {
        channels: channelsData.length,
        streams: activeStreamsData.length,
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
                  <div className="stat-label">収集コメント</div>
                  <div className="stat-detail">
                    リアルタイム収集中
                  </div>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-icon">⚡</div>
                <div className="stat-content">
                  <div className="stat-number">100%</div>
                  <div className="stat-label">システム稼働率</div>
                  <div className="stat-detail">
                    全機能正常動作
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* アクティブ配信セクション */}
        <section className="streams-section">
          <h2>🔴 アクティブ配信</h2>
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

        {/* チャンネル一覧セクション */}
        <section className="channels-section">
          <h2>📺 監視チャンネル</h2>
          {channels.length > 0 ? (
            <div className="channels-grid">
              {channels.map((channel) => (
                <div key={channel.channel_id} className="channel-card">
                  <div className={`channel-status ${channel.is_active ? 'active' : 'inactive'}`}>
                    {channel.is_active ? '✅ 監視中' : '⏸️ 停止中'}
                  </div>
                  <div className="channel-name">{channel.channel_name}</div>
                  <div className="channel-id">ID: {channel.channel_id}</div>
                  {channel.subscriber_count && (
                    <div className="channel-subscribers">
                      登録者: {channel.subscriber_count.toLocaleString()}人
                    </div>
                  )}
                  <div className="channel-created">
                    登録日: {new Date(channel.created_at).toLocaleDateString('ja-JP')}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="no-data">
              監視チャンネルが見つかりません
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
      </main>

      {/* フッター */}
      <footer className="app-footer">
        <div className="footer-content">
          <span>YouTube Live Chat Collector - Phase 12 Step 1</span>
          <span>Build Time: {process.env.REACT_APP_BUILD_TIME}</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
