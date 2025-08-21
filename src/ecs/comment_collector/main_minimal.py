"""
YouTube Live Chat Collector - Minimal Version for Testing

最小構成でのテスト用バージョン
- pytchatなし
- DynamoDB接続テスト
- TaskStatus管理テスト
- 基本的なログ出力
"""

import os
import sys
import time
import boto3
import logging
from datetime import datetime, timezone
from typing import Dict, Any
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

class MinimalCommentCollector:
    """最小構成のコメント収集クラス"""
    
    def __init__(self, video_id: str, channel_id: str):
        self.video_id = video_id
        self.channel_id = channel_id
        self.comments_table = dynamodb.Table(COMMENTS_TABLE)
        self.taskstatus_table = dynamodb.Table(TASKSTATUS_TABLE)
        self.comment_count = 0
        
    def test_basic_functionality(self) -> None:
        """基本機能のテスト"""
        logger.info(f"Starting minimal test for video: {self.video_id}")
        
        try:
            # Step 1: TaskStatus更新テスト
            logger.info("Step 1: Testing TaskStatus update...")
            self.update_task_status("testing")
            
            # Step 2: モックコメントデータ作成・保存テスト
            logger.info("Step 2: Testing comment data creation and saving...")
            mock_comments = self.create_mock_comments(5)
            self.save_comments_batch(mock_comments)
            
            # Step 3: ヘルスチェックテスト
            logger.info("Step 3: Testing health check...")
            self.perform_health_check()
            
            # Step 4: 完了状態更新
            logger.info("Step 4: Testing completion status update...")
            self.update_task_status("completed")
            
            logger.info("✅ All minimal tests completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Test failed: {str(e)}")
            self.update_task_status("failed")
            raise
    
    def create_mock_comments(self, count: int) -> list:
        """モックコメントデータを作成"""
        mock_comments = []
        
        for i in range(count):
            timestamp = datetime.now(timezone.utc)
            comment_data = {
                'comment_id': f"{self.video_id}#mock_{i}_{int(timestamp.timestamp())}",
                'video_id': self.video_id,
                'channel_id': self.channel_id,
                'author_name': f"TestUser_{i}",
                'author_channel_id': f"test_channel_{i}",
                'message': f"This is a test comment #{i} for minimal testing",
                'timestamp': timestamp.isoformat(),
                'datetime': timestamp.isoformat(),
                'is_owner': False,
                'is_moderator': False,
                'is_verified': False,
                'created_at': timestamp.isoformat()
            }
            mock_comments.append(comment_data)
            
        logger.info(f"Created {count} mock comments")
        return mock_comments
    
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
            self.update_task_status("testing")
            logger.info(f"✅ Health check completed. Comments processed: {self.comment_count}")
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {str(e)}")
            raise
    
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
            
            logger.info(f"✅ Updated task status to: {status}")
            
        except ClientError as e:
            logger.error(f"❌ Error updating task status: {str(e)}")
            raise

def main():
    """メイン関数"""
    logger.info("🧪 YouTube Comment Collector - Minimal Test Version")
    
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
        # 最小構成テスト開始
        collector = MinimalCommentCollector(VIDEO_ID, CHANNEL_ID)
        collector.test_basic_functionality()
        
        logger.info("🎉 Minimal test completed successfully")
        
    except KeyboardInterrupt:
        logger.info("⏹️ Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
