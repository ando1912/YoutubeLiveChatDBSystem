"""
YouTube Live Chat Collector - Full Version with pytchat

完全版: pytchatライブラリを統合したリアルタイムコメント収集
- 最小構成版で検証済みの基本機能
- pytchatライブラリの正しい使用方法
- 実際のYouTubeライブチャットからのコメント取得
"""

import os
import sys
import time
import boto3
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import pytchat
from botocore.exceptions import ClientError

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# AWS クライアント初期化
dynamodb = boto3.resource('dynamodb')

# 環境変数
VIDEO_ID = os.environ.get('VIDEO_ID')
CHANNEL_ID = os.environ.get('CHANNEL_ID')
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')
COMMENTS_TABLE = os.environ.get('DYNAMODB_TABLE_COMMENTS', f'{ENVIRONMENT}-Comments')
TASKSTATUS_TABLE = os.environ.get('DYNAMODB_TABLE_TASKSTATUS', f'{ENVIRONMENT}-TaskStatus')

# 設定
MAX_RETRY_COUNT = 3
RETRY_DELAY = 5  # 秒
HEALTH_CHECK_INTERVAL = 30  # 秒
BATCH_SIZE = 25  # DynamoDB書き込みバッチサイズ
COMMENT_CHECK_INTERVAL = 2  # コメント取得間隔（秒）

class FullCommentCollector:
    """完全版コメント収集クラス"""
    
    def __init__(self, video_id: str, channel_id: str):
        self.video_id = video_id
        self.channel_id = channel_id
        self.comments_table = dynamodb.Table(COMMENTS_TABLE)
        self.taskstatus_table = dynamodb.Table(TASKSTATUS_TABLE)
        self.chat = None
        self.is_running = False
        self.comment_count = 0
        self.last_health_check = time.time()
        
    def start_collection(self) -> None:
        """コメント収集を開始"""
        logger.info(f"🚀 Starting full comment collection for video: {self.video_id}")
        
        retry_count = 0
        while retry_count < MAX_RETRY_COUNT:
            try:
                # pytchatでライブチャットに接続
                logger.info(f"📡 Connecting to YouTube live chat...")
                self.chat = pytchat.create(video_id=self.video_id)
                self.is_running = True
                
                logger.info(f"✅ Successfully connected to live chat: {self.video_id}")
                
                # TaskStatusを更新
                self.update_task_status("collecting")
                
                # コメント収集ループ
                self.collect_comments()
                
                break
                
            except Exception as e:
                retry_count += 1
                logger.error(f"❌ Error connecting to live chat (attempt {retry_count}/{MAX_RETRY_COUNT}): {str(e)}")
                
                if retry_count < MAX_RETRY_COUNT:
                    logger.info(f"⏳ Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error("💥 Max retry count reached. Exiting.")
                    self.update_task_status("failed")
                    raise
    
    def collect_comments(self) -> None:
        """コメント収集メインループ"""
        comment_batch = []
        
        try:
            logger.info("🔄 Starting comment collection loop...")
            
            while self.chat.is_alive():
                try:
                    # pytchatの正しい使用方法: get()メソッドを使用
                    chat_data = self.chat.get()
                    
                    # chat_dataが存在し、コメントがある場合
                    if chat_data:
                        # chat_dataがitemsアトリビュートを持つ場合
                        if hasattr(chat_data, 'items') and chat_data.items:
                            for comment in chat_data.items:
                                comment_data = self.format_comment(comment)
                                comment_batch.append(comment_data)
                                
                                logger.info(f"💬 Comment from {comment.author.name}: {comment.message[:50]}...")
                                
                                # バッチサイズに達したら保存
                                if len(comment_batch) >= BATCH_SIZE:
                                    self.save_comments_batch(comment_batch)
                                    comment_batch = []
                        
                        # chat_dataが直接イテレート可能な場合
                        elif hasattr(chat_data, '__iter__') and not isinstance(chat_data, str):
                            for comment in chat_data:
                                if hasattr(comment, 'author') and hasattr(comment, 'message'):
                                    comment_data = self.format_comment(comment)
                                    comment_batch.append(comment_data)
                                    
                                    logger.info(f"💬 Comment from {comment.author.name}: {comment.message[:50]}...")
                                    
                                    # バッチサイズに達したら保存
                                    if len(comment_batch) >= BATCH_SIZE:
                                        self.save_comments_batch(comment_batch)
                                        comment_batch = []
                        
                        # 単一のコメントオブジェクトの場合
                        elif hasattr(chat_data, 'author') and hasattr(chat_data, 'message'):
                            comment_data = self.format_comment(chat_data)
                            comment_batch.append(comment_data)
                            
                            logger.info(f"💬 Comment from {chat_data.author.name}: {chat_data.message[:50]}...")
                            
                            # バッチサイズに達したら保存
                            if len(comment_batch) >= BATCH_SIZE:
                                self.save_comments_batch(comment_batch)
                                comment_batch = []
                    
                    # 定期的なヘルスチェック
                    if time.time() - self.last_health_check > HEALTH_CHECK_INTERVAL:
                        self.perform_health_check()
                    
                    # コメント取得間隔の待機
                    time.sleep(COMMENT_CHECK_INTERVAL)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error getting comments: {str(e)}")
                    # コメント取得エラーは継続
                    time.sleep(RETRY_DELAY)
                    continue
            
            # 残りのコメントを保存
            if comment_batch:
                self.save_comments_batch(comment_batch)
            
            logger.info("🏁 Live stream ended. Comment collection completed.")
            self.update_task_status("completed")
            
        except Exception as e:
            logger.error(f"💥 Error during comment collection: {str(e)}")
            self.update_task_status("failed")
            raise
        finally:
            self.cleanup()
    
    def format_comment(self, comment) -> Dict[str, Any]:
        """コメントデータをDynamoDB用にフォーマット"""
        timestamp = datetime.now(timezone.utc)
        
        return {
            'comment_id': f"{self.video_id}#{getattr(comment, 'id', f'unknown_{int(timestamp.timestamp())}')}",
            'video_id': self.video_id,
            'channel_id': self.channel_id,
            'author_name': getattr(comment.author, 'name', 'Unknown'),
            'author_channel_id': getattr(comment.author, 'channelId', 'unknown'),
            'message': getattr(comment, 'message', ''),
            'timestamp': timestamp.isoformat(),
            'datetime': getattr(comment, 'datetime', timestamp.isoformat()),
            'is_owner': getattr(comment.author, 'isOwner', False),
            'is_moderator': getattr(comment.author, 'isModerator', False),
            'is_verified': getattr(comment.author, 'isVerified', False),
            'created_at': timestamp.isoformat()
        }
    
    def save_comments_batch(self, comments: list) -> None:
        """コメントをバッチでDynamoDBに保存"""
        try:
            with self.comments_table.batch_writer() as batch:
                for comment in comments:
                    batch.put_item(Item=comment)
            
            self.comment_count += len(comments)
            logger.info(f"✅ Saved {len(comments)} comments. Total: {self.comment_count}")
            
        except ClientError as e:
            logger.error(f"❌ Error saving comments to DynamoDB: {str(e)}")
            raise
    
    def perform_health_check(self) -> None:
        """ヘルスチェックを実行"""
        try:
            # TaskStatusテーブルを更新して生存確認
            self.update_task_status("collecting")
            self.last_health_check = time.time()
            
            logger.info(f"💓 Health check completed. Comments collected: {self.comment_count}")
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {str(e)}")
    
    def update_task_status(self, status: str) -> None:
        """TaskStatusテーブルを更新"""
        try:
            timestamp = datetime.now(timezone.utc).isoformat()
            
            self.taskstatus_table.update_item(
                Key={'video_id': self.video_id},
                UpdateExpression='SET #status = :status, updated_at = :updated_at, comment_count = :comment_count',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': status,
                    ':updated_at': timestamp,
                    ':comment_count': self.comment_count
                }
            )
            
            logger.info(f"📊 Updated task status to: {status}")
            
        except ClientError as e:
            logger.error(f"❌ Error updating task status: {str(e)}")
    
    def cleanup(self) -> None:
        """リソースのクリーンアップ"""
        try:
            if self.chat:
                self.chat.terminate()
            self.is_running = False
            logger.info("🧹 Cleanup completed")
            
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {str(e)}")

def main():
    """メイン関数"""
    logger.info("🎬 YouTube Comment Collector - Full Version with pytchat")
    
    # 環境変数チェック
    if not VIDEO_ID:
        logger.error("❌ VIDEO_ID environment variable is required")
        sys.exit(1)
    
    if not CHANNEL_ID:
        logger.error("❌ CHANNEL_ID environment variable is required")
        sys.exit(1)
    
    logger.info(f"📋 Configuration:")
    logger.info(f"  VIDEO_ID: {VIDEO_ID}")
    logger.info(f"  CHANNEL_ID: {CHANNEL_ID}")
    logger.info(f"  ENVIRONMENT: {ENVIRONMENT}")
    logger.info(f"  COMMENTS_TABLE: {COMMENTS_TABLE}")
    logger.info(f"  TASKSTATUS_TABLE: {TASKSTATUS_TABLE}")
    
    try:
        # 完全版コメント収集開始
        collector = FullCommentCollector(VIDEO_ID, CHANNEL_ID)
        collector.start_collection()
        
        logger.info("🎉 Full comment collection completed successfully")
        
    except KeyboardInterrupt:
        logger.info("⏹️ Comment collection interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
