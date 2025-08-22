import React, { useState } from 'react';
import { Channel, apiService } from '../services/api';
import './ChannelManager.css';

/**
 * チャンネル管理コンポーネント
 * 
 * Phase 12 Step 2: チャンネル管理機能実装
 * - 新規チャンネル追加
 * - 監視状態切り替え（開始/停止）
 * - 詳細情報表示・編集
 */

interface ChannelManagerProps {
  channels: Channel[];
  onChannelsUpdate: () => void;
}

interface AddChannelForm {
  channelId: string;
  isSubmitting: boolean;
  error: string | null;
}

export const ChannelManager: React.FC<ChannelManagerProps> = ({
  channels,
  onChannelsUpdate
}) => {
  // ===== State管理 =====
  const [addForm, setAddForm] = useState<AddChannelForm>({
    channelId: '',
    isSubmitting: false,
    error: null
  });
  const [updatingChannels, setUpdatingChannels] = useState<Set<string>>(new Set());
  const [showAddForm, setShowAddForm] = useState(false);

  // ===== チャンネル追加処理 =====
  const handleAddChannel = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!addForm.channelId.trim()) {
      setAddForm(prev => ({ ...prev, error: 'チャンネルIDを入力してください' }));
      return;
    }

    // YouTube チャンネルID形式チェック
    const channelIdPattern = /^UC[a-zA-Z0-9_-]{22}$/;
    if (!channelIdPattern.test(addForm.channelId.trim())) {
      setAddForm(prev => ({ 
        ...prev, 
        error: 'チャンネルIDの形式が正しくありません (例: UC1CfXB_kRs3C-zaeTG3oGyg)' 
      }));
      return;
    }

    // 重複チェック
    if (channels.some(ch => ch.channel_id === addForm.channelId.trim())) {
      setAddForm(prev => ({ ...prev, error: 'このチャンネルは既に登録されています' }));
      return;
    }

    try {
      setAddForm(prev => ({ ...prev, isSubmitting: true, error: null }));

      console.log('🔄 新規チャンネル追加開始:', addForm.channelId.trim());
      
      await apiService.addChannel(addForm.channelId.trim());
      
      console.log('✅ チャンネル追加成功');
      
      // フォームリセット
      setAddForm({
        channelId: '',
        isSubmitting: false,
        error: null
      });
      setShowAddForm(false);
      
      // 親コンポーネントに更新通知
      onChannelsUpdate();
      
    } catch (error) {
      console.error('❌ チャンネル追加エラー:', error);
      setAddForm(prev => ({
        ...prev,
        isSubmitting: false,
        error: error instanceof Error ? error.message : 'チャンネル追加に失敗しました'
      }));
    }
  };

  // ===== 監視状態切り替え処理 =====
  const handleToggleMonitoring = async (channel: Channel) => {
    const newStatus = !channel.is_active;
    
    // 監視停止の場合は確認ダイアログを表示
    if (channel.is_active) {
      if (!window.confirm(`チャンネル「${channel.channel_name}」の監視を停止しますか？\n\n⚠️ 実行される処理：\n• 監視の停止\n• 一覧からの削除\n• 過去のデータ（配信履歴・コメント）は保持\n\n再度監視したい場合は、チャンネルを追加し直してください。`)) {
        return;
      }
    }
    
    try {
      setUpdatingChannels(prev => new Set(prev).add(channel.channel_id));
      
      console.log(`🔄 チャンネル監視状態変更: ${channel.channel_name} → ${newStatus ? '監視開始' : '監視停止'}`);
      
      await apiService.updateChannelStatus(channel.channel_id, newStatus);
      
      console.log('✅ 監視状態変更成功');
      
      // 親コンポーネントに更新通知
      onChannelsUpdate();
      
    } catch (error) {
      console.error('❌ 監視状態変更エラー:', error);
      // TODO: エラー通知表示
    } finally {
      setUpdatingChannels(prev => {
        const newSet = new Set(prev);
        newSet.delete(channel.channel_id);
        return newSet;
      });
    }
  };

  // ===== YouTube チャンネルURL生成 =====
  const getChannelUrl = (channelId: string) => {
    return `https://www.youtube.com/channel/${channelId}`;
  };

  // ===== レンダリング =====
  return (
    <div className="channel-manager">
      {/* ヘッダー */}
      <div className="channel-manager-header">
        <h2>📺 チャンネル管理</h2>
        <button 
          className="add-channel-btn"
          onClick={() => setShowAddForm(!showAddForm)}
          disabled={addForm.isSubmitting}
        >
          {showAddForm ? '❌ キャンセル' : '➕ チャンネル追加'}
        </button>
      </div>

      {/* チャンネル追加フォーム */}
      {showAddForm && (
        <div className="add-channel-form">
          <h3>新規チャンネル追加</h3>
          <form onSubmit={handleAddChannel}>
            <div className="form-group">
              <label htmlFor="channelId">YouTubeチャンネルID</label>
              <input
                type="text"
                id="channelId"
                value={addForm.channelId}
                onChange={(e) => setAddForm(prev => ({ 
                  ...prev, 
                  channelId: e.target.value,
                  error: null 
                }))}
                placeholder="UC1CfXB_kRs3C-zaeTG3oGyg"
                disabled={addForm.isSubmitting}
                className={addForm.error ? 'error' : ''}
              />
              <div className="form-help">
                チャンネルページのURLから「UC」で始まる24文字のIDを入力してください
              </div>
            </div>
            
            {addForm.error && (
              <div className="form-error">
                ❌ {addForm.error}
              </div>
            )}
            
            <div className="form-actions">
              <button 
                type="submit" 
                disabled={addForm.isSubmitting || !addForm.channelId.trim()}
                className="submit-btn"
              >
                {addForm.isSubmitting ? '🔄 追加中...' : '✅ チャンネル追加'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* チャンネル一覧 */}
      <div className="channels-list">
        {channels.length > 0 ? (
          <div className="channels-grid">
            {channels.map((channel) => (
              <div key={channel.channel_id} className="channel-management-card">
                {/* チャンネル基本情報 */}
                <div className="channel-info">
                  <div className="channel-header">
                    <div className={`channel-status ${channel.is_active ? 'active' : 'inactive'}`}>
                      {channel.is_active ? '✅ 監視中' : '⏸️ 停止中'}
                    </div>
                    <div className="channel-actions">
                      <a 
                        href={getChannelUrl(channel.channel_id)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="youtube-link"
                        title="YouTubeで開く"
                      >
                        🔗
                      </a>
                    </div>
                  </div>
                  
                  <div className="channel-name">{channel.channel_name}</div>
                  <div className="channel-id">ID: {channel.channel_id}</div>
                  
                  {channel.subscriber_count && (
                    <div className="channel-subscribers">
                      👥 登録者: {channel.subscriber_count.toLocaleString()}人
                    </div>
                  )}
                  
                  <div className="channel-dates">
                    <div>📅 登録: {new Date(channel.created_at).toLocaleDateString('ja-JP')}</div>
                    {channel.updated_at && (
                      <div>🔄 更新: {new Date(channel.updated_at).toLocaleDateString('ja-JP')}</div>
                    )}
                  </div>
                </div>

                {/* 管理アクション */}
                <div className="channel-management-actions">
                  <button
                    className={`toggle-monitoring-btn ${channel.is_active ? 'stop' : 'start'}`}
                    onClick={() => handleToggleMonitoring(channel)}
                    disabled={updatingChannels.has(channel.channel_id)}
                  >
                    {updatingChannels.has(channel.channel_id) ? (
                      '🔄 更新中...'
                    ) : channel.is_active ? (
                      '⏸️ 監視停止'
                    ) : (
                      '▶️ 監視開始'
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="no-channels">
            <div className="no-channels-icon">📺</div>
            <div className="no-channels-message">
              監視チャンネルがありません
            </div>
            <div className="no-channels-help">
              「チャンネル追加」ボタンから新しいチャンネルを追加してください
            </div>
          </div>
        )}
      </div>

      {/* 統計情報 */}
      <div className="channel-stats">
        <div className="stat-item">
          <span className="stat-label">総チャンネル数:</span>
          <span className="stat-value">{channels.length}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">監視中:</span>
          <span className="stat-value">{channels.filter(ch => ch.is_active).length}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">停止中:</span>
          <span className="stat-value">{channels.filter(ch => !ch.is_active).length}</span>
        </div>
      </div>
    </div>
  );
};

export default ChannelManager;
