"""
YouTube Live Chat Collector - API Handler Lambda Function

REST APIエンドポイントを提供するLambda関数
- チャンネル管理 (GET, POST /channels)
- ライブ配信一覧 (GET /streams)
- コメント取得 (GET /streams/{video_id}/comments)
"""

import json
import boto3
import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from botocore.exceptions import ClientError
import logging

# ログ設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS クライアント初期化
dynamodb = boto3.resource('dynamodb')
ssm = boto3.client('ssm')

# 環境変数
CHANNELS_TABLE = os.environ.get('CHANNELS_TABLE', 'dev-Channels')
LIVESTREAMS_TABLE = os.environ.get('LIVESTREAMS_TABLE', 'dev-LiveStreams')
COMMENTS_TABLE = os.environ.get('COMMENTS_TABLE', 'dev-Comments')
TASKSTATUS_TABLE = os.environ.get('TASKSTATUS_TABLE', 'dev-TaskStatus')
YOUTUBE_API_KEY_PARAM = os.environ.get('YOUTUBE_API_KEY_PARAM', '/dev/youtube-chat-collector/youtube-api-key')

def get_youtube_api_key() -> Optional[str]:
    """
    SSMパラメータストアからYouTube API Keyを取得
    
    Returns:
        YouTube API Key または None
    """
    try:
        response = ssm.get_parameter(
            Name=YOUTUBE_API_KEY_PARAM,
            WithDecryption=True
        )
        return response['Parameter']['Value']
    except ClientError as e:
        logger.error(f"Failed to get YouTube API key: {str(e)}")
        return None

def get_channel_info_from_youtube_api(channel_id: str) -> Optional[Dict[str, Any]]:
    """
    YouTube Data APIからチャンネル情報を取得
    
    Args:
        channel_id: YouTubeチャンネルID
        
    Returns:
        チャンネル情報辞書 または None
    """
    try:
        # YouTube API Keyを取得
        api_key = get_youtube_api_key()
        if not api_key:
            logger.error("YouTube API key not available")
            return None
        
        # YouTube Data API v3でチャンネル情報を取得
        url = "https://www.googleapis.com/youtube/v3/channels"
        params = {
            'part': 'snippet,statistics,brandingSettings',
            'id': channel_id,
            'key': api_key
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get('items'):
            logger.warning(f"Channel not found: {channel_id}")
            return None
            
        channel_data = data['items'][0]
        snippet = channel_data.get('snippet', {})
        statistics = channel_data.get('statistics', {})
        branding = channel_data.get('brandingSettings', {})
        
        # サムネイル情報を取得（複数サイズ）
        thumbnails = snippet.get('thumbnails', {})
        thumbnail_info = {}
        for size in ['default', 'medium', 'high']:
            if size in thumbnails:
                thumbnail_info[f'thumbnail_{size}'] = thumbnails[size].get('url', '')
        
        # チャンネル情報を構築
        channel_info = {
            'channel_name': snippet.get('title', ''),
            'description': snippet.get('description', ''),
            'custom_url': snippet.get('customUrl', ''),
            'published_at': snippet.get('publishedAt', ''),
            'country': snippet.get('country', ''),
            'default_language': snippet.get('defaultLanguage', ''),
            'subscriber_count': statistics.get('subscriberCount', '0'),
            'video_count': statistics.get('videoCount', '0'),
            'view_count': statistics.get('viewCount', '0'),
            'api_retrieved_at': datetime.now(timezone.utc).isoformat(),
            **thumbnail_info
        }
        
        logger.info(f"Retrieved channel info from YouTube API: {channel_id} - {channel_info['channel_name']}")
        return channel_info
        
    except requests.RequestException as e:
        logger.error(f"YouTube API request failed for channel {channel_id}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error getting channel info from YouTube API: {str(e)}")
        return None

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda関数のメインハンドラー
    
    Args:
        event: API Gatewayからのイベント
        context: Lambda実行コンテキスト
        
    Returns:
        API Gatewayレスポンス
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # HTTPメソッドとパスを取得
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        path_parameters = event.get('pathParameters') or {}
        query_parameters = event.get('queryStringParameters') or {}
        
        # ルーティング
        if path == '/channels':
            if http_method == 'GET':
                return get_channels(query_parameters)
            elif http_method == 'POST':
                body = json.loads(event.get('body', '{}'))
                return create_channel(body)
                
        elif path.startswith('/channels/'):
            # /channels/{channel_id} パターン
            channel_id = path.split('/')[-1]
            if http_method == 'PUT':
                body = json.loads(event.get('body', '{}'))
                return update_channel(channel_id, body)
            elif http_method == 'DELETE':
                return delete_channel(channel_id)
                
        elif path == '/streams':
            if http_method == 'GET':
                return get_streams(query_parameters)
                
        elif path.startswith('/streams/') and path.endswith('/comments'):
            if http_method == 'GET':
                video_id = path_parameters.get('video_id')
                return get_comments(video_id, query_parameters)
                
        elif path == '/collection-status':
            if http_method == 'GET':
                return get_collection_status(query_parameters)
        
        # 未対応のエンドポイント
        return create_response(404, {'error': 'Endpoint not found'})
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})

def get_channels(query_params: Dict[str, str]) -> Dict[str, Any]:
    """
    アクティブなチャンネル一覧を取得
    
    Args:
        query_params: クエリパラメータ
        
    Returns:
        アクティブなチャンネル一覧のレスポンス
    """
    try:
        table = dynamodb.Table(CHANNELS_TABLE)
        
        # アクティブなチャンネルのみを取得
        response = table.scan(
            FilterExpression='is_active = :active',
            ExpressionAttributeValues={
                ':active': True
            }
        )
        channels = response.get('Items', [])
        
        # 日時フィールドを文字列に変換（既に文字列の場合はそのまま）
        for channel in channels:
            if 'created_at' in channel:
                if hasattr(channel['created_at'], 'isoformat'):
                    channel['created_at'] = channel['created_at'].isoformat()
                # 既に文字列の場合はそのまま使用
            if 'updated_at' in channel:
                if hasattr(channel['updated_at'], 'isoformat'):
                    channel['updated_at'] = channel['updated_at'].isoformat()
                # 既に文字列の場合はそのまま使用
        
        return create_response(200, {
            'channels': channels,
            'count': len(channels)
        })
        
    except ClientError as e:
        logger.error(f"DynamoDB error in get_channels: {str(e)}")
        return create_response(500, {'error': 'Database error'})

def create_channel(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    新しいチャンネルを作成（YouTube APIから情報を自動取得）
    
    Args:
        body: リクエストボディ
        
    Returns:
        作成結果のレスポンス
    """
    try:
        # 必須フィールドの検証
        channel_id = body.get('channel_id')
        
        if not channel_id:
            return create_response(400, {
                'error': 'channel_id is required'
            })
        
        table = dynamodb.Table(CHANNELS_TABLE)
        
        # チャンネルの存在確認と再アクティブ化処理
        try:
            existing = table.get_item(Key={'channel_id': channel_id})
            if 'Item' in existing:
                existing_channel = existing['Item']
                # 既存チャンネルがアクティブな場合はエラー
                if existing_channel.get('is_active', False):
                    return create_response(409, {'error': 'Channel already exists and is active'})
                
                # 非アクティブなチャンネルの場合は再アクティブ化
                logger.info(f"Reactivating inactive channel: {channel_id}")
                now = datetime.now(timezone.utc)
                
                # YouTube APIから最新情報を取得
                youtube_info = get_channel_info_from_youtube_api(channel_id)
                
                # 更新用の属性を準備
                update_expression = "SET is_active = :active, updated_at = :updated_at"
                expression_values = {
                    ':active': True,
                    ':updated_at': now.isoformat()
                }
                
                # YouTube APIから情報が取得できた場合は更新
                if youtube_info:
                    update_expression += ", channel_name = :channel_name, subscriber_count = :subscriber_count, video_count = :video_count, view_count = :view_count, api_retrieved_at = :api_retrieved_at"
                    expression_values.update({
                        ':channel_name': youtube_info.get('channel_name', existing_channel.get('channel_name', '')),
                        ':subscriber_count': youtube_info.get('subscriber_count', existing_channel.get('subscriber_count', '0')),
                        ':video_count': youtube_info.get('video_count', existing_channel.get('video_count', '0')),
                        ':view_count': youtube_info.get('view_count', existing_channel.get('view_count', '0')),
                        ':api_retrieved_at': youtube_info.get('api_retrieved_at', '')
                    })
                
                # チャンネルを再アクティブ化
                response = table.update_item(
                    Key={'channel_id': channel_id},
                    UpdateExpression=update_expression,
                    ExpressionAttributeValues=expression_values,
                    ReturnValues='ALL_NEW'
                )
                
                reactivated_channel = response['Attributes']
                
                # 日時フィールドを文字列に変換
                for field in ['created_at', 'updated_at', 'api_retrieved_at']:
                    if field in reactivated_channel and hasattr(reactivated_channel[field], 'isoformat'):
                        reactivated_channel[field] = reactivated_channel[field].isoformat()
                
                logger.info(f"Channel reactivated successfully: {channel_id}")
                return create_response(200, {
                    'message': 'Channel reactivated successfully',
                    'channel': reactivated_channel
                })
                
        except ClientError as e:
            logger.error(f"Error checking existing channel: {str(e)}")
            return create_response(500, {'error': 'Database error'})
        
        # YouTube APIからチャンネル情報を取得
        youtube_info = get_channel_info_from_youtube_api(channel_id)
        
        # 基本的なチャンネル情報を構築
        now = datetime.now(timezone.utc)
        channel_item = {
            'channel_id': channel_id,
            'is_active': body.get('is_active', True),
            'created_at': now.isoformat(),
            'updated_at': now.isoformat()
        }
        
        # YouTube APIから取得した情報をマージ
        if youtube_info:
            # 手動指定があれば優先、なければAPIから取得した情報を使用
            channel_item.update({
                'channel_name': body.get('channel_name', youtube_info.get('channel_name', '')),
                'description': body.get('description', youtube_info.get('description', '')),
                'custom_url': youtube_info.get('custom_url', ''),
                'published_at': youtube_info.get('published_at', ''),
                'country': youtube_info.get('country', ''),
                'default_language': youtube_info.get('default_language', ''),
                'subscriber_count': youtube_info.get('subscriber_count', '0'),
                'video_count': youtube_info.get('video_count', '0'),
                'view_count': youtube_info.get('view_count', '0'),
                'thumbnail_default': youtube_info.get('thumbnail_default', ''),
                'thumbnail_medium': youtube_info.get('thumbnail_medium', ''),
                'thumbnail_high': youtube_info.get('thumbnail_high', ''),
                'api_retrieved_at': youtube_info.get('api_retrieved_at', '')
            })
        else:
            # APIから取得できない場合は手動指定の情報を使用
            channel_item.update({
                'channel_name': body.get('channel_name', ''),
                'description': body.get('description', ''),
                'api_retrieved_at': '',
                'api_error': 'Failed to retrieve from YouTube API'
            })
            logger.warning(f"Could not retrieve YouTube API info for channel: {channel_id}")
        
        # DynamoDBに保存
        table.put_item(Item=channel_item)
        
        logger.info(f"Created channel: {channel_id} - {channel_item.get('channel_name', 'Unknown')}")
        return create_response(201, {
            'message': 'Channel created successfully',
            'channel': channel_item,
            'api_info_retrieved': youtube_info is not None
        })
        
    except ClientError as e:
        logger.error(f"DynamoDB error in create_channel: {str(e)}")
        return create_response(500, {'error': 'Database error'})
    except Exception as e:
        logger.error(f"Unexpected error in create_channel: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})

def update_channel(channel_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    チャンネル情報を更新（主に監視状態の切り替え）
    
    Args:
        channel_id: 更新対象のチャンネルID
        body: 更新データ
        
    Returns:
        更新されたチャンネル情報のレスポンス
    """
    try:
        if not channel_id:
            return create_response(400, {'error': 'channel_id is required'})
        
        table = dynamodb.Table(CHANNELS_TABLE)
        
        # チャンネルの存在確認
        try:
            response = table.get_item(Key={'channel_id': channel_id})
            if 'Item' not in response:
                return create_response(404, {'error': 'Channel not found'})
        except ClientError as e:
            logger.error(f"Error checking channel existence: {str(e)}")
            return create_response(500, {'error': 'Database error'})
        
        # 更新可能なフィールドを制限
        allowed_fields = ['is_active']
        update_data = {}
        
        for field in allowed_fields:
            if field in body:
                update_data[field] = body[field]
        
        if not update_data:
            return create_response(400, {'error': 'No valid fields to update'})
        
        # 更新実行
        now = datetime.now(timezone.utc)
        update_expression = "SET updated_at = :updated_at"
        expression_attribute_values = {':updated_at': now.isoformat()}
        
        for field, value in update_data.items():
            update_expression += f", {field} = :{field}"
            expression_attribute_values[f':{field}'] = value
        
        response = table.update_item(
            Key={'channel_id': channel_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues='ALL_NEW'
        )
        
        updated_channel = response['Attributes']
        
        # 日時フィールドを文字列に変換
        for field in ['created_at', 'updated_at', 'api_retrieved_at']:
            if field in updated_channel and hasattr(updated_channel[field], 'isoformat'):
                updated_channel[field] = updated_channel[field].isoformat()
        
        logger.info(f"Updated channel: {channel_id} - {update_data}")
        return create_response(200, {
            'message': 'Channel updated successfully',
            'channel': updated_channel
        })
        
    except ClientError as e:
        logger.error(f"DynamoDB error in update_channel: {str(e)}")
        return create_response(500, {'error': 'Database error'})
    except Exception as e:
        logger.error(f"Unexpected error in update_channel: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})

def delete_channel(channel_id: str) -> Dict[str, Any]:
    """
    チャンネル監視停止・除去（安全な停止として実装）
    
    Args:
        channel_id: 停止対象のチャンネルID
        
    Returns:
        停止結果のレスポンス
    """
    try:
        if not channel_id:
            return create_response(400, {'error': 'channel_id is required'})
        
        table = dynamodb.Table(CHANNELS_TABLE)
        
        # チャンネルの存在確認
        try:
            response = table.get_item(Key={'channel_id': channel_id})
            if 'Item' not in response:
                return create_response(404, {'error': 'Channel not found'})
        except ClientError as e:
            logger.error(f"Error checking channel existence: {str(e)}")
            return create_response(500, {'error': 'Database error'})
        
        # 安全な削除: 監視停止に変更（データは保持）
        now = datetime.now(timezone.utc)
        response = table.update_item(
            Key={'channel_id': channel_id},
            UpdateExpression="SET is_active = :inactive, updated_at = :updated_at",
            ExpressionAttributeValues={
                ':inactive': False,
                ':updated_at': now.isoformat()
            },
            ReturnValues='ALL_NEW'
        )
        
        updated_channel = response['Attributes']
        
        # 日時フィールドを文字列に変換
        for field in ['created_at', 'updated_at', 'api_retrieved_at']:
            if field in updated_channel and hasattr(updated_channel[field], 'isoformat'):
                updated_channel[field] = updated_channel[field].isoformat()
        
        logger.info(f"Channel monitoring stopped and removed from list: {channel_id}")
        return create_response(200, {
            'message': 'Channel monitoring stopped and removed from list (data preserved)',
            'channel': updated_channel
        })
        
    except ClientError as e:
        logger.error(f"DynamoDB error in delete_channel: {str(e)}")
        return create_response(500, {'error': 'Database error'})
    except Exception as e:
        logger.error(f"Unexpected error in delete_channel: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})

def get_streams(query_params: Dict[str, str]) -> Dict[str, Any]:
    """
    ライブ配信一覧を取得
    
    Args:
        query_params: クエリパラメータ
        
    Returns:
        ライブ配信一覧のレスポンス
    """
    try:
        table = dynamodb.Table(LIVESTREAMS_TABLE)
        
        # チャンネルIDでフィルタリング
        channel_id = query_params.get('channel_id')
        
        if channel_id:
            # GSIを使用してチャンネル別に取得
            response = table.query(
                IndexName='channel_id-index',
                KeyConditionExpression='channel_id = :channel_id',
                ExpressionAttributeValues={':channel_id': channel_id},
                ScanIndexForward=False  # 新しい順
            )
        else:
            # 全ライブ配信をスキャン
            response = table.scan()
        
        streams = response.get('Items', [])
        
        # 日時フィールドを文字列に変換（既に文字列の場合はそのまま）
        for stream in streams:
            for field in ['created_at', 'updated_at', 'scheduled_start_time', 'actual_start_time', 'actual_end_time']:
                if field in stream and stream[field]:
                    if hasattr(stream[field], 'isoformat'):
                        stream[field] = stream[field].isoformat()
                    # 既に文字列の場合はそのまま使用
        
        return create_response(200, {
            'streams': streams,
            'count': len(streams)
        })
        
    except ClientError as e:
        logger.error(f"DynamoDB error in get_streams: {str(e)}")
        return create_response(500, {'error': 'Database error'})

def get_comments(video_id: str, query_params: Dict[str, str]) -> Dict[str, Any]:
    """
    指定されたライブ配信のコメントを取得
    
    Args:
        video_id: YouTube動画ID
        query_params: クエリパラメータ
        
    Returns:
        コメント一覧のレスポンス
    """
    try:
        if not video_id:
            return create_response(400, {'error': 'video_id is required'})
        
        table = dynamodb.Table(COMMENTS_TABLE)
        
        # ページネーション対応
        limit = int(query_params.get('limit', '100'))
        limit = min(limit, 1000)  # 最大1000件
        
        # GSIを使用してvideo_id別に取得
        query_params_db = {
            'IndexName': 'video_id-timestamp-index',
            'KeyConditionExpression': 'video_id = :video_id',
            'ExpressionAttributeValues': {':video_id': video_id},
            'ScanIndexForward': False,  # 新しい順
            'Limit': limit
        }
        
        # カーソルベースのページネーション
        last_key = query_params.get('last_key')
        if last_key:
            try:
                query_params_db['ExclusiveStartKey'] = json.loads(last_key)
            except json.JSONDecodeError:
                return create_response(400, {'error': 'Invalid last_key format'})
        
        response = table.query(**query_params_db)
        comments = response.get('Items', [])
        
        # 日時フィールドを文字列に変換（既に文字列の場合はそのまま）
        for comment in comments:
            if 'timestamp' in comment:
                if hasattr(comment['timestamp'], 'isoformat'):
                    comment['timestamp'] = comment['timestamp'].isoformat()
                # 既に文字列の場合はそのまま使用
        
        result = {
            'comments': comments,
            'count': len(comments),
            'video_id': video_id
        }
        
        # 次のページがある場合はlast_keyを含める
        if 'LastEvaluatedKey' in response:
            result['last_key'] = json.dumps(response['LastEvaluatedKey'])
        
        return create_response(200, result)
        
    except ClientError as e:
        logger.error(f"DynamoDB error in get_comments: {str(e)}")
        return create_response(500, {'error': 'Database error'})

def get_collection_status(query_params: Dict[str, str]) -> Dict[str, Any]:
    """
    コメント収集タスクの実行状況を取得
    
    Args:
        query_params: クエリパラメータ
        
    Returns:
        コメント収集状況のレスポンス
    """
    try:
        table = dynamodb.Table(TASKSTATUS_TABLE)
        
        # 実行中のタスクを取得
        response = table.scan(
            FilterExpression='task_status = :status',
            ExpressionAttributeValues={
                ':status': 'running'
            }
        )
        
        running_tasks = response.get('Items', [])
        
        # 今日のコメント数を取得（簡易版）
        today_comments = 0
        try:
            comments_table = dynamodb.Table(COMMENTS_TABLE)
            today = datetime.now(timezone.utc).date().isoformat()
            
            # 今日のコメントを概算で取得（完全な実装は後で）
            comments_response = comments_table.scan(
                FilterExpression='begins_with(#ts, :today)',
                ExpressionAttributeNames={'#ts': 'timestamp'},
                ExpressionAttributeValues={':today': today},
                Select='COUNT'
            )
            today_comments = comments_response.get('Count', 0)
        except Exception as e:
            logger.warning(f"Failed to get today's comment count: {str(e)}")
            today_comments = 0
        
        # 最後の収集時刻を取得
        last_collection_time = None
        if running_tasks:
            # 最新のタスクの開始時刻を使用
            latest_task = max(running_tasks, key=lambda x: x.get('started_at', ''))
            last_collection_time = latest_task.get('started_at')
        
        # 日時フィールドを文字列に変換
        for task in running_tasks:
            for field in ['started_at', 'updated_at']:
                if field in task and hasattr(task[field], 'isoformat'):
                    task[field] = task[field].isoformat()
        
        result = {
            'active_collections': len(running_tasks),
            'running_video_ids': [task.get('video_id', '') for task in running_tasks],
            'today_comments': today_comments,
            'last_collection_time': last_collection_time,
            'task_details': running_tasks,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Collection status retrieved: {len(running_tasks)} active tasks")
        return create_response(200, result)
        
    except ClientError as e:
        logger.error(f"DynamoDB error in get_collection_status: {str(e)}")
        return create_response(500, {'error': 'Database error'})
    except Exception as e:
        logger.error(f"Unexpected error in get_collection_status: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})

def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    API Gatewayレスポンスを作成
    
    Args:
        status_code: HTTPステータスコード
        body: レスポンスボディ
        
    Returns:
        API Gatewayレスポンス形式
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(body, ensure_ascii=False, default=str)
    }
