"""
YouTube Live Chat Collector - ECS Task Launcher Lambda Function

SQSメッセージを受信してECS Fargateタスクを起動・停止
- Stream Status CheckerからのSQSメッセージを処理
- ライブ配信開始時にコメント収集タスクを起動
- ライブ配信終了時にコメント収集タスクを停止
- TaskStatusテーブルで状態管理
"""

import json
import boto3
import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from botocore.exceptions import ClientError
import logging

# ログ設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS クライアント初期化
ecs = boto3.client('ecs')
dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')

# 環境変数
ECS_CLUSTER_NAME = os.environ.get('ECS_CLUSTER_NAME', 'dev-comment-collector-cluster')
ECS_SERVICE_NAME = os.environ.get('ECS_SERVICE_NAME', 'dev-comment-collector-service')
ECS_TASK_DEFINITION = os.environ.get('ECS_TASK_DEFINITION', 'dev-comment-collector-task')
TASK_STATUS_TABLE = os.environ.get('DYNAMODB_TABLE_TASKSTATUS', 'dev-TaskStatus')
SUBNET_IDS = os.environ.get('ECS_SUBNETS', '').split(',')
SECURITY_GROUP_IDS = os.environ.get('ECS_SECURITY_GROUPS', '').split(',')

def check_running_tasks_for_video(video_id: str) -> List[str]:
    """
    指定された動画IDで実行中のECSタスクを確認
    
    Args:
        video_id: YouTube動画ID
        
    Returns:
        実行中のタスクARNのリスト
    """
    try:
        # 実行中のタスク一覧を取得
        response = ecs.list_tasks(
            cluster=ECS_CLUSTER_NAME,
            desiredStatus='RUNNING'
        )
        
        if not response.get('taskArns'):
            return []
        
        # タスクの詳細を取得
        tasks_response = ecs.describe_tasks(
            cluster=ECS_CLUSTER_NAME,
            tasks=response['taskArns']
        )
        
        running_tasks = []
        for task in tasks_response.get('tasks', []):
            # 環境変数からVIDEO_IDを確認
            for container_override in task.get('overrides', {}).get('containerOverrides', []):
                for env_var in container_override.get('environment', []):
                    if env_var.get('name') == 'VIDEO_ID' and env_var.get('value') == video_id:
                        running_tasks.append(task['taskArn'])
                        break
        
        return running_tasks
        
    except Exception as e:
        logger.error(f"Error checking running tasks for video {video_id}: {str(e)}")
        return []

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:

    """
    Lambda関数のメインハンドラー
    
    Args:
        event: SQSからのイベント
        context: Lambda実行コンテキスト
        
    Returns:
        実行結果
    """
    try:
        logger.info("ECS Task Launcher started")
        
        processed_messages = 0
        successful_actions = 0
        
        # SQSメッセージを処理
        for record in event.get('Records', []):
            try:
                # SQSメッセージを解析
                message_body = json.loads(record['body'])
                logger.info(f"Processing message: {message_body}")
                
                action = message_body.get('action')
                video_id = message_body.get('video_id')
                channel_id = message_body.get('channel_id')
                
                if not all([action, video_id, channel_id]):
                    logger.error(f"Invalid message format: {message_body}")
                    continue
                
                # アクションに応じて処理
                if action == 'start_collection':
                    success = start_comment_collection(video_id, channel_id)
                elif action == 'stop_collection':
                    success = stop_comment_collection(video_id, channel_id)
                else:
                    logger.error(f"Unknown action: {action}")
                    continue
                
                if success:
                    successful_actions += 1
                
                processed_messages += 1
                
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                continue
        
        result = {
            'processed_messages': processed_messages,
            'successful_actions': successful_actions,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"ECS Task Launcher completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in ECS Task Launcher: {str(e)}")
        raise

def start_comment_collection(video_id: str, channel_id: str) -> bool:
    """
    コメント収集タスクを開始
    
    Args:
        video_id: YouTube動画ID
        channel_id: YouTubeチャンネルID
        
    Returns:
        成功した場合True
    """
    try:
        # 既存のタスクがあるかチェック（DynamoDB）
        existing_task = get_task_status(video_id)
        if existing_task and existing_task.get('status') in ['running', 'collecting']:
            logger.info(f"Task already running for video {video_id} (status: {existing_task.get('status')})")
            return True
        
        # ECSクラスターでも重複チェック（追加の安全策）
        running_tasks = check_running_tasks_for_video(video_id)
        if running_tasks:
            logger.warning(f"Found {len(running_tasks)} running tasks for video {video_id} in ECS cluster, but not in DynamoDB")
            # DynamoDBの状態を修正
            update_task_status(video_id, channel_id, 'collecting', running_tasks[0])
            return True
        
        # ECS Fargateタスクを起動
        task_arn = launch_ecs_task(video_id, channel_id)
        
        if task_arn:
            # TaskStatusテーブルを更新
            update_task_status(video_id, channel_id, 'running', task_arn)
            logger.info(f"Started comment collection task for video {video_id}: {task_arn}")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error starting comment collection for {video_id}: {str(e)}")
        return False

def stop_comment_collection(video_id: str, channel_id: str) -> bool:
    """
    コメント収集タスクを停止
    
    Args:
        video_id: YouTube動画ID
        channel_id: YouTubeチャンネルID
        
    Returns:
        成功した場合True
    """
    try:
        # 現在のタスク状態を取得
        task_status = get_task_status(video_id)
        
        if not task_status or task_status.get('status') not in ['running', 'collecting']:
            logger.info(f"No running task found for video {video_id} (status: {task_status.get('status') if task_status else 'None'})")
            return True
        
        task_arn = task_status.get('task_arn')
        
        if task_arn:
            # ECSタスクを停止
            success = stop_ecs_task(task_arn)
            
            if success:
                # TaskStatusテーブルを更新
                update_task_status(video_id, channel_id, 'stopped', task_arn)
                logger.info(f"Stopped comment collection task for video {video_id}: {task_arn}")
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error stopping comment collection for {video_id}: {str(e)}")
        return False

def launch_ecs_task(video_id: str, channel_id: str) -> Optional[str]:
    """
    ECS Fargateタスクを起動
    
    Args:
        video_id: YouTube動画ID
        channel_id: YouTubeチャンネルID
        
    Returns:
        タスクARN または None
    """
    try:
        # タスク定義の環境変数を設定
        task_overrides = {
            'containerOverrides': [
                {
                    'name': 'comment-collector',
                    'environment': [
                        {'name': 'VIDEO_ID', 'value': video_id},
                        {'name': 'CHANNEL_ID', 'value': channel_id},
                        {'name': 'ENVIRONMENT', 'value': 'dev'}
                    ]
                }
            ]
        }
        
        # ECS Fargateタスクを起動
        response = ecs.run_task(
            cluster=ECS_CLUSTER_NAME,
            taskDefinition=ECS_TASK_DEFINITION,
            launchType='FARGATE',
            networkConfiguration={
                'awsvpcConfiguration': {
                    'subnets': [subnet for subnet in SUBNET_IDS if subnet.strip()],
                    'securityGroups': [sg for sg in SECURITY_GROUP_IDS if sg.strip()],
                    'assignPublicIp': 'ENABLED'
                }
            },
            overrides=task_overrides,
            tags=[
                {'key': 'VideoId', 'value': video_id},
                {'key': 'ChannelId', 'value': channel_id},
                {'key': 'Environment', 'value': 'dev'}
            ]
        )
        
        if response.get('tasks'):
            task_arn = response['tasks'][0]['taskArn']
            logger.info(f"ECS task launched successfully: {task_arn}")
            return task_arn
        
        logger.error(f"Failed to launch ECS task: {response}")
        return None
        
    except ClientError as e:
        logger.error(f"Error launching ECS task: {str(e)}")
        return None

def stop_ecs_task(task_arn: str) -> bool:
    """
    ECSタスクを停止
    
    Args:
        task_arn: ECSタスクARN
        
    Returns:
        成功した場合True
    """
    try:
        response = ecs.stop_task(
            cluster=ECS_CLUSTER_NAME,
            task=task_arn,
            reason='Live stream ended'
        )
        
        logger.info(f"ECS task stopped successfully: {task_arn}")
        return True
        
    except ClientError as e:
        logger.error(f"Error stopping ECS task {task_arn}: {str(e)}")
        return False

def get_task_status(video_id: str) -> Optional[Dict[str, Any]]:
    """
    TaskStatusテーブルからタスク状態を取得
    
    Args:
        video_id: YouTube動画ID
        
    Returns:
        タスク状態情報 または None
    """
    try:
        table = dynamodb.Table(TASK_STATUS_TABLE)
        response = table.get_item(Key={'video_id': video_id})
        
        return response.get('Item')
        
    except ClientError as e:
        logger.error(f"Error getting task status for {video_id}: {str(e)}")
        return None

def update_task_status(video_id: str, channel_id: str, status: str, task_arn: str) -> None:
    """
    TaskStatusテーブルを更新
    
    Args:
        video_id: YouTube動画ID
        channel_id: YouTubeチャンネルID
        status: タスク状態
        task_arn: ECSタスクARN
    """
    try:
        table = dynamodb.Table(TASK_STATUS_TABLE)
        
        item = {
            'video_id': video_id,
            'channel_id': channel_id,
            'status': status,
            'task_arn': task_arn,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        if status == 'running':
            item['started_at'] = datetime.now(timezone.utc).isoformat()
        elif status == 'stopped':
            item['stopped_at'] = datetime.now(timezone.utc).isoformat()
        
        table.put_item(Item=item)
        
        logger.info(f"Updated task status for {video_id}: {status}")
        
    except ClientError as e:
        logger.error(f"Error updating task status for {video_id}: {str(e)}")
        raise
