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
YOUTUBE_API_KEY_PARAM = os.environ.get('YOUTUBE_API_KEY_PARAM', '/dev/youtube-chat-collector/youtube-api-key')

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
                
        elif path == '/streams':
            if http_method == 'GET':
                return get_streams(query_parameters)
                
        elif path.startswith('/streams/') and path.endswith('/comments'):
            if http_method == 'GET':
                video_id = path_parameters.get('video_id')
                return get_comments(video_id, query_parameters)
        
        # 未対応のエンドポイント
        return create_response(404, {'error': 'Endpoint not found'})
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})

def get_channels(query_params: Dict[str, str]) -> Dict[str, Any]:
    """
    チャンネル一覧を取得
    
    Args:
        query_params: クエリパラメータ
        
    Returns:
        チャンネル一覧のレスポンス
    """
    try:
        table = dynamodb.Table(CHANNELS_TABLE)
        
        # 全チャンネルをスキャン（実際の運用では改善が必要）
        response = table.scan()
        channels = response.get('Items', [])
        
        # 日時フィールドを文字列に変換
        for channel in channels:
            if 'created_at' in channel:
                channel['created_at'] = channel['created_at'].isoformat()
            if 'updated_at' in channel:
                channel['updated_at'] = channel['updated_at'].isoformat()
        
        return create_response(200, {
            'channels': channels,
            'count': len(channels)
        })
        
    except ClientError as e:
        logger.error(f"DynamoDB error in get_channels: {str(e)}")
        return create_response(500, {'error': 'Database error'})

def create_channel(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    新しいチャンネルを作成
    
    Args:
        body: リクエストボディ
        
    Returns:
        作成結果のレスポンス
    """
    try:
        # 必須フィールドの検証
        channel_id = body.get('channel_id')
        channel_name = body.get('channel_name')
        
        if not channel_id or not channel_name:
            return create_response(400, {
                'error': 'channel_id and channel_name are required'
            })
        
        table = dynamodb.Table(CHANNELS_TABLE)
        
        # チャンネルの存在確認
        try:
            existing = table.get_item(Key={'channel_id': channel_id})
            if 'Item' in existing:
                return create_response(409, {'error': 'Channel already exists'})
        except ClientError:
            pass
        
        # 新しいチャンネルを作成
        now = datetime.now(timezone.utc)
        channel_item = {
            'channel_id': channel_id,
            'channel_name': channel_name,
            'description': body.get('description', ''),
            'is_active': body.get('is_active', True),
            'created_at': now.isoformat(),
            'updated_at': now.isoformat()
        }
        
        table.put_item(Item=channel_item)
        
        logger.info(f"Created channel: {channel_id}")
        return create_response(201, {
            'message': 'Channel created successfully',
            'channel': channel_item
        })
        
    except ClientError as e:
        logger.error(f"DynamoDB error in create_channel: {str(e)}")
        return create_response(500, {'error': 'Database error'})

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
        
        # 日時フィールドを文字列に変換
        for stream in streams:
            for field in ['created_at', 'started_at', 'ended_at']:
                if field in stream and stream[field]:
                    stream[field] = stream[field].isoformat()
        
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
        
        # 日時フィールドを文字列に変換
        for comment in comments:
            if 'timestamp' in comment:
                comment['timestamp'] = comment['timestamp'].isoformat()
        
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
