"""
YouTube Live Chat Collector - Stream Status Checker Lambda Function

ライブ配信の状態を監視し、開始・終了を検出
- 1分間隔でEventBridgeから実行
- アクティブなライブ配信の状態をチェック
- 開始時にECS Task Launcherに通知
- 終了時にタスクを停止
"""

import json
import boto3
import os
import requests
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from botocore.exceptions import ClientError
import logging

# ログ設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS クライアント初期化
dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')
ssm = boto3.client('ssm')

# 環境変数
LIVESTREAMS_TABLE = os.environ.get('LIVESTREAMS_TABLE', 'dev-LiveStreams')
TASK_STATUS_TABLE = os.environ.get('TASK_STATUS_TABLE', 'dev-TaskStatus')
TASK_CONTROL_QUEUE_URL = os.environ.get('TASK_CONTROL_QUEUE_URL')
YOUTUBE_API_KEY_PARAM = os.environ.get('YOUTUBE_API_KEY_PARAM', '/dev/youtube-chat-collector/youtube-api-key')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda関数のメインハンドラー
    
    Args:
        event: EventBridgeからのイベント
        context: Lambda実行コンテキスト
        
    Returns:
        実行結果
    """
    try:
        logger.info("Stream Status Checker started")
        
        # 監視対象のライブ配信を取得
        streams_to_check = get_streams_to_check()
        logger.info(f"Found {len(streams_to_check)} streams to check")
        
        status_changes = 0
        
        # 各ライブ配信の状態をチェック
        for stream in streams_to_check:
            try:
                if check_and_update_stream_status(stream):
                    status_changes += 1
                    
            except Exception as e:
                logger.error(f"Error checking stream {stream['video_id']}: {str(e)}")
                continue
        
        result = {
            'streams_checked': len(streams_to_check),
            'status_changes': status_changes,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Stream Status Checker completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in Stream Status Checker: {str(e)}")
        raise

def get_streams_to_check() -> List[Dict[str, Any]]:
    """
    監視対象のライブ配信を取得
    
    Returns:
        監視対象のライブ配信リスト
    """
    try:
        table = dynamodb.Table(LIVESTREAMS_TABLE)
        
        # 24時間以内に作成された、まだ終了していないライブ配信を取得
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        
        response = table.scan(
            FilterExpression='created_at > :cutoff AND attribute_not_exists(ended_at)',
            ExpressionAttributeValues={
                ':cutoff': cutoff_time.isoformat()
            }
        )
        
        return response.get('Items', [])
        
    except ClientError as e:
        logger.error(f"Error getting streams to check: {str(e)}")
        return []

def check_and_update_stream_status(stream: Dict[str, Any]) -> bool:
    """
    ライブ配信の状態をチェックして更新
    
    Args:
        stream: ライブ配信情報
        
    Returns:
        状態が変更された場合True
    """
    video_id = stream['video_id']
    current_status = stream.get('status', 'detected')
    
    try:
        # YouTube Data APIで現在の状態を取得
        live_status = get_live_stream_status(video_id)
        
        if not live_status:
            logger.warning(f"Could not get status for stream {video_id}")
            return False
        
        new_status = live_status['status']
        
        # 状態が変更された場合のみ処理
        if new_status != current_status:
            logger.info(f"Status change for {video_id}: {current_status} -> {new_status}")
            
            # DynamoDBを更新
            update_stream_status(stream, live_status)
            
            # 状態に応じてタスクを制御
            if new_status == 'live' and current_status in ['detected', 'upcoming']:
                # ライブ配信開始 - コメント収集タスクを開始
                send_task_control_message('start_collection', video_id, stream['channel_id'])
                
            elif new_status == 'ended' and current_status == 'live':
                # ライブ配信終了 - コメント収集タスクを停止
                send_task_control_message('stop_collection', video_id, stream['channel_id'])
            
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error checking status for stream {video_id}: {str(e)}")
        return False

def get_live_stream_status(video_id: str) -> Optional[Dict[str, Any]]:
    """
    YouTube Data APIでライブ配信の状態を取得
    
    Args:
        video_id: YouTube動画ID
        
    Returns:
        ライブ配信状態情報
    """
    try:
        # YouTube API Keyを取得
        api_key = get_youtube_api_key()
        if not api_key:
            logger.error("YouTube API key not found")
            return None
        
        # YouTube Data API v3で動画情報を取得
        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            'id': video_id,
            'part': 'liveStreamingDetails,snippet,status',
            'key': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get('items'):
            return None
        
        video_info = data['items'][0]
        snippet = video_info.get('snippet', {})
        live_details = video_info.get('liveStreamingDetails', {})
        status_info = video_info.get('status', {})
        
        # ライブ配信の状態を判定
        live_broadcast_content = snippet.get('liveBroadcastContent', 'none')
        
        if live_broadcast_content == 'live':
            status = 'live'
        elif live_broadcast_content == 'upcoming':
            status = 'upcoming'
        elif live_broadcast_content == 'none':
            # 終了したライブ配信かどうか確認
            if live_details.get('actualEndTime'):
                status = 'ended'
            else:
                status = 'not_live'
        else:
            status = 'unknown'
        
        result = {
            'status': status,
            'title': snippet.get('title', ''),
            'description': snippet.get('description', ''),
            'scheduled_start_time': live_details.get('scheduledStartTime'),
            'actual_start_time': live_details.get('actualStartTime'),
            'actual_end_time': live_details.get('actualEndTime'),
            'concurrent_viewers': live_details.get('concurrentViewers'),
            'privacy_status': status_info.get('privacyStatus', 'unknown')
        }
        
        return result
        
    except requests.RequestException as e:
        logger.error(f"Error fetching live stream status for {video_id}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting live stream status {video_id}: {str(e)}")
        return None

def get_youtube_api_key() -> Optional[str]:
    """
    Parameter StoreからYouTube API Keyを取得
    
    Returns:
        API Key または None
    """
    try:
        response = ssm.get_parameter(
            Name=YOUTUBE_API_KEY_PARAM,
            WithDecryption=True
        )
        return response['Parameter']['Value']
        
    except ClientError as e:
        logger.error(f"Error getting YouTube API key: {str(e)}")
        return None

def update_stream_status(stream: Dict[str, Any], live_status: Dict[str, Any]) -> None:
    """
    ライブ配信の状態をDynamoDBで更新
    
    Args:
        stream: 現在のライブ配信情報
        live_status: 新しい状態情報
    """
    try:
        table = dynamodb.Table(LIVESTREAMS_TABLE)
        
        # 更新する属性を準備
        update_expression = "SET #status = :status, updated_at = :updated_at"
        expression_attribute_names = {'#status': 'status'}
        expression_attribute_values = {
            ':status': live_status['status'],
            ':updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        # タイトルと説明を更新
        if live_status.get('title'):
            update_expression += ", title = :title"
            expression_attribute_values[':title'] = live_status['title']
        
        if live_status.get('description'):
            update_expression += ", description = :description"
            expression_attribute_values[':description'] = live_status['description']
        
        # ライブ配信開始時刻
        if live_status.get('actual_start_time'):
            update_expression += ", started_at = :started_at"
            expression_attribute_values[':started_at'] = live_status['actual_start_time']
        
        # ライブ配信終了時刻
        if live_status.get('actual_end_time'):
            update_expression += ", ended_at = :ended_at"
            expression_attribute_values[':ended_at'] = live_status['actual_end_time']
        
        # 同時視聴者数
        if live_status.get('concurrent_viewers'):
            update_expression += ", concurrent_viewers = :viewers"
            expression_attribute_values[':viewers'] = int(live_status['concurrent_viewers'])
        
        table.update_item(
            Key={'video_id': stream['video_id']},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values
        )
        
        logger.info(f"Updated stream status for {stream['video_id']}: {live_status['status']}")
        
    except ClientError as e:
        logger.error(f"Error updating stream status {stream['video_id']}: {str(e)}")
        raise

def send_task_control_message(action: str, video_id: str, channel_id: str) -> None:
    """
    ECS Task LauncherにSQSメッセージを送信
    
    Args:
        action: アクション ('start_collection' または 'stop_collection')
        video_id: YouTube動画ID
        channel_id: YouTubeチャンネルID
    """
    try:
        if not TASK_CONTROL_QUEUE_URL:
            logger.warning("Task control queue URL not configured")
            return
        
        message = {
            'action': action,
            'video_id': video_id,
            'channel_id': channel_id,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        sqs.send_message(
            QueueUrl=TASK_CONTROL_QUEUE_URL,
            MessageBody=json.dumps(message)
        )
        
        logger.info(f"Sent task control message: {action} for {video_id}")
        
    except ClientError as e:
        logger.error(f"Error sending task control message: {str(e)}")
