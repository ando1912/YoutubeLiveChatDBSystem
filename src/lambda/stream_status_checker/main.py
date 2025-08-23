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
CHANNELS_TABLE = os.environ.get('DYNAMODB_TABLE_CHANNELS', 'dev-Channels')
LIVESTREAMS_TABLE = os.environ.get('DYNAMODB_TABLE_LIVESTREAMS', 'dev-LiveStreams')
TASK_STATUS_TABLE = os.environ.get('DYNAMODB_TABLE_TASK_STATUS', 'dev-TaskStatus')
TASK_CONTROL_QUEUE_URL = os.environ.get('SQS_QUEUE_URL')
ECS_CLUSTER_NAME = os.environ.get('ECS_CLUSTER_NAME', 'dev-youtube-comment-collector')
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
    監視対象のライブ配信を取得（アクティブなチャンネルのみ、終了済み配信は除外）
    
    Returns:
        監視対象のライブ配信リスト
    """
    try:
        # まずアクティブなチャンネル一覧を取得
        channels_table = dynamodb.Table(CHANNELS_TABLE)
        active_channels_response = channels_table.scan(
            FilterExpression='is_active = :active',
            ExpressionAttributeValues={':active': True},
            ProjectionExpression='channel_id'
        )
        
        active_channel_ids = {item['channel_id'] for item in active_channels_response.get('Items', [])}
        logger.info(f"Found {len(active_channel_ids)} active channels")
        
        if not active_channel_ids:
            logger.info("No active channels found, skipping stream check")
            return []
        
        # 次に配信を取得（終了済み配信は除外）
        table = dynamodb.Table(LIVESTREAMS_TABLE)
        
        # アクティブなライブ配信のみを取得（live, upcoming, detected のみ）
        # ended ステータスの配信は監視対象から除外
        response = table.scan(
            FilterExpression='#status IN (:live, :upcoming, :detected)',
            ExpressionAttributeNames={
                '#status': 'status'
            },
            ExpressionAttributeValues={
                ':live': 'live',
                ':upcoming': 'upcoming', 
                ':detected': 'detected'
            }
        )
        
        # アクティブなチャンネルの配信のみをフィルタリング
        all_streams = response.get('Items', [])
        active_streams = [
            stream for stream in all_streams 
            if stream.get('channel_id') in active_channel_ids
        ]
        
        logger.info(f"Found {len(all_streams)} active streams (live/upcoming/detected only)")
        logger.info(f"Filtered to {len(active_streams)} streams from active channels")
        logger.info("Excluded 'ended' status streams from monitoring to save API quota")
        return active_streams
        
    except ClientError as e:
        logger.error(f"Error getting streams to check: {str(e)}")
        return []

def check_and_update_stream_status(stream: Dict[str, Any]) -> bool:
    """
    ライブ配信の状態をチェックして更新し、必要に応じてタスクを制御
    
    Args:
        stream: ライブ配信情報
        
    Returns:
        アクションが実行された場合True
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
        action_taken = False
        
        # DynamoDBの状態を更新（状態が変わった場合のみ）
        if new_status != current_status:
            logger.info(f"Status change for {video_id}: {current_status} -> {new_status}")
            update_stream_status(stream, live_status)
            action_taken = True
        
        # タスク実行状態をチェックして制御
        if new_status == 'live':
            # ライブ配信中の場合、タスクが実行されているかチェック
            if not is_task_running(video_id):
                logger.info(f"Starting collection task for live stream {video_id}")
                send_task_control_message('start_collection', video_id, stream['channel_id'])
                action_taken = True
            else:
                logger.debug(f"Collection task already running for {video_id}")
                
        elif new_status == 'ended' and current_status == 'live':
            # ライブ配信終了の場合、タスクを停止
            logger.info(f"Stopping collection task for ended stream {video_id}")
            send_task_control_message('stop_collection', video_id, stream['channel_id'])
            action_taken = True
        
        return action_taken
        
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

def is_task_running(video_id: str) -> bool:
    """
    指定された動画IDのコメント収集タスクが実行中かチェック
    
    Args:
        video_id: YouTube動画ID
        
    Returns:
        タスクが実行中の場合True
    """
    try:
        task_status_table = dynamodb.Table(TASK_STATUS_TABLE)
        
        response = task_status_table.get_item(
            Key={'video_id': video_id}
        )
        
        if 'Item' not in response:
            return False
        
        task_status = response['Item']
        status = task_status.get('status', 'stopped')
        
        # running または collecting 状態のタスクがある場合はTrue
        if status in ['running', 'collecting']:
            # タスクが実際に実行中かECS APIで確認
            task_arn = task_status.get('task_arn')
            if task_arn and is_ecs_task_actually_running(task_arn):
                return True
            else:
                # タスクが実際には停止している場合、ステータスを更新
                logger.warning(f"Task {task_arn} for {video_id} is marked as {status} but not actually running")
                update_task_status(video_id, 'stopped')
                return False
        
        return False
        
    except ClientError as e:
        logger.error(f"Error checking task status for {video_id}: {str(e)}")
        return False

def is_ecs_task_actually_running(task_arn: str) -> bool:
    """
    ECS APIでタスクが実際に実行中かチェック
    
    Args:
        task_arn: ECSタスクARN
        
    Returns:
        タスクが実行中の場合True
    """
    try:
        ecs = boto3.client('ecs')
        
        # クラスター名を環境変数から取得
        cluster_name = os.environ.get('ECS_CLUSTER_NAME', 'dev-youtube-comment-collector')
        
        response = ecs.describe_tasks(
            cluster=cluster_name,
            tasks=[task_arn]
        )
        
        if not response.get('tasks'):
            return False
        
        task = response['tasks'][0]
        last_status = task.get('lastStatus', '')
        
        # RUNNING状態の場合のみTrue
        return last_status == 'RUNNING'
        
    except Exception as e:
        logger.error(f"Error checking ECS task {task_arn}: {str(e)}")
        return False

def update_task_status(video_id: str, status: str, task_arn: str = None) -> None:
    """
    TaskStatusテーブルを更新
    
    Args:
        video_id: YouTube動画ID
        status: タスク状態
        task_arn: ECSタスクARN（オプション）
    """
    try:
        task_status_table = dynamodb.Table(TASK_STATUS_TABLE)
        
        update_expression = "SET #status = :status, updated_at = :updated_at"
        expression_attribute_names = {'#status': 'status'}
        expression_attribute_values = {
            ':status': status,
            ':updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        if task_arn:
            update_expression += ", task_arn = :task_arn"
            expression_attribute_values[':task_arn'] = task_arn
        
        if status == 'stopped':
            update_expression += ", stopped_at = :stopped_at"
            expression_attribute_values[':stopped_at'] = datetime.now(timezone.utc).isoformat()
        elif status == 'running':
            update_expression += ", started_at = :started_at"
            expression_attribute_values[':started_at'] = datetime.now(timezone.utc).isoformat()
        
        task_status_table.update_item(
            Key={'video_id': video_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values
        )
        
        logger.info(f"Updated task status for {video_id}: {status}")
        
    except ClientError as e:
        logger.error(f"Error updating task status for {video_id}: {str(e)}")

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
