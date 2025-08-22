"""
YouTube Live Chat Collector - RSS Monitor Lambda Function

YouTubeチャンネルのRSSフィードを監視してライブ配信を検出
- 5分間隔でEventBridgeから実行
- 新しいライブ配信を検出してDynamoDBに保存
- Stream Status CheckerにSQSメッセージを送信
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
sqs = boto3.client('sqs')
ssm = boto3.client('ssm')

# 環境変数
CHANNELS_TABLE = os.environ.get('CHANNELS_TABLE', 'dev-Channels')
LIVESTREAMS_TABLE = os.environ.get('LIVESTREAMS_TABLE', 'dev-LiveStreams')
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
        logger.info("RSS Monitor started")
        
        # アクティブなチャンネル一覧を取得
        channels = get_active_channels()
        logger.info(f"Found {len(channels)} active channels")
        
        new_streams_count = 0
        
        # 各チャンネルのRSSフィードをチェック
        for channel in channels:
            try:
                new_streams = check_channel_rss(channel)
                new_streams_count += len(new_streams)
                
                # 新しいライブ配信があればStream Status Checkerに通知
                for stream in new_streams:
                    send_stream_check_message(stream)
                    
            except Exception as e:
                logger.error(f"Error checking channel {channel['channel_id']}: {str(e)}")
                continue
        
        result = {
            'channels_checked': len(channels),
            'new_streams_found': new_streams_count,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"RSS Monitor completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in RSS Monitor: {str(e)}")
        raise

def get_active_channels() -> List[Dict[str, Any]]:
    """
    アクティブなチャンネル一覧を取得
    
    Returns:
        アクティブなチャンネルのリスト
    """
    try:
        table = dynamodb.Table(CHANNELS_TABLE)
        
        # アクティブなチャンネルのみを取得
        response = table.scan(
            FilterExpression='is_active = :active',
            ExpressionAttributeValues={':active': True}
        )
        
        return response.get('Items', [])
        
    except ClientError as e:
        logger.error(f"Error getting active channels: {str(e)}")
        return []

def check_channel_rss(channel: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    チャンネルのRSSフィードをチェックして新しいライブ配信を検出
    
    Args:
        channel: チャンネル情報
        
    Returns:
        新しいライブ配信のリスト
    """
    channel_id = channel['channel_id']
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    
    try:
        # RSSフィードを取得
        response = requests.get(rss_url, timeout=10)
        response.raise_for_status()
        
        # XMLを解析
        root = ET.fromstring(response.content)
        
        # 名前空間を定義
        namespaces = {
            'atom': 'http://www.w3.org/2005/Atom',
            'yt': 'http://www.youtube.com/xml/schemas/2015',
            'media': 'http://search.yahoo.com/mrss/'
        }
        
        new_streams = []
        
        # 各エントリをチェック（最新の5件のみ）
        entries = root.findall('atom:entry', namespaces)[:5]
        
        for entry in entries:
            video_id = entry.find('yt:videoId', namespaces).text
            title = entry.find('atom:title', namespaces).text
            published = entry.find('atom:published', namespaces).text
            
            # 公開日が24時間以内の動画のみをチェック
            published_dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
            if datetime.now(timezone.utc) - published_dt > timedelta(hours=24):
                continue
            
            # 既存のレコードをチェック
            if not is_stream_already_detected(video_id):
                # YouTube Data APIでライブ配信かどうかを確認
                if is_live_stream(video_id):
                    stream_info = {
                        'video_id': video_id,
                        'channel_id': channel_id,
                        'title': title,
                        'published_at': published,
                        'detected_at': datetime.now(timezone.utc).isoformat()
                    }
                    new_streams.append(stream_info)
                    logger.info(f"New live stream detected: {video_id} - {title}")
        
        return new_streams
        
    except requests.RequestException as e:
        logger.error(f"Error fetching RSS for channel {channel_id}: {str(e)}")
        return []
    except ET.ParseError as e:
        logger.error(f"Error parsing RSS XML for channel {channel_id}: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error checking RSS for channel {channel_id}: {str(e)}")
        return []

def is_live_stream(video_id: str) -> bool:
    """
    YouTube Data APIを使用して動画がライブ配信かどうかを確認
    
    Args:
        video_id: YouTube動画ID
        
    Returns:
        ライブ配信の場合True
    """
    try:
        # YouTube API Keyを取得
        api_key = get_youtube_api_key()
        if not api_key:
            logger.error("YouTube API key not found")
            return False
        
        # YouTube Data API v3で動画情報を取得
        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            'id': video_id,
            'part': 'liveStreamingDetails,snippet',
            'key': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get('items'):
            return False
        
        video_info = data['items'][0]
        snippet = video_info.get('snippet', {})
        live_details = video_info.get('liveStreamingDetails', {})
        
        # ライブ配信の判定
        live_broadcast_content = snippet.get('liveBroadcastContent', 'none')
        
        # live, upcoming, または liveStreamingDetails が存在する場合のみライブ配信とみなす
        return (live_broadcast_content in ['live', 'upcoming'] or 
                bool(live_details))
        
    except requests.RequestException as e:
        logger.error(f"Error checking live stream status for {video_id}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking live stream {video_id}: {str(e)}")
        return False
        
        # XMLを解析
        root = ET.fromstring(response.content)
        
        # 名前空間の定義
        namespaces = {
            'atom': 'http://www.w3.org/2005/Atom',
            'yt': 'http://www.youtube.com/xml/schemas/2015',
            'media': 'http://search.yahoo.com/mrss/'
        }
        
        new_streams = []
        
        # エントリーを処理
        for entry in root.findall('atom:entry', namespaces):
            try:
                video_id = entry.find('yt:videoId', namespaces).text
                title = entry.find('atom:title', namespaces).text
                published = entry.find('atom:published', namespaces).text
                
                # 既存のライブ配信かチェック
                if not is_existing_stream(video_id):
                    # YouTube Data APIでライブ配信かどうか確認
                    if is_live_stream(video_id):
                        stream_data = {
                            'video_id': video_id,
                            'channel_id': channel_id,
                            'title': title,
                            'published_at': published,
                            'status': 'detected',
                            'created_at': datetime.now(timezone.utc).isoformat()
                        }
                        
                        # DynamoDBに保存
                        save_stream(stream_data)
                        new_streams.append(stream_data)
                        
                        logger.info(f"New live stream detected: {video_id} - {title}")
                
            except Exception as e:
                logger.error(f"Error processing RSS entry: {str(e)}")
                continue
        
        return new_streams
        
    except requests.RequestException as e:
        logger.error(f"Error fetching RSS for channel {channel_id}: {str(e)}")
        return []
    except ET.ParseError as e:
        logger.error(f"Error parsing RSS XML for channel {channel_id}: {str(e)}")
        return []

def is_existing_stream(video_id: str) -> bool:
    """
    既存のライブ配信かどうかチェック
    
    Args:
        video_id: YouTube動画ID
        
    Returns:
        既存の場合True
    """
    try:
        table = dynamodb.Table(LIVESTREAMS_TABLE)
        response = table.get_item(Key={'video_id': video_id})
        return 'Item' in response
        
    except ClientError as e:
        logger.error(f"Error checking existing stream {video_id}: {str(e)}")
        return False

def is_live_stream(video_id: str) -> bool:
    """
    YouTube Data APIを使用してライブ配信かどうか確認
    
    Args:
        video_id: YouTube動画ID
        
    Returns:
        ライブ配信の場合True
    """
    try:
        # YouTube API Keyを取得
        api_key = get_youtube_api_key()
        if not api_key:
            logger.error("YouTube API key not found")
            return False
        
        # YouTube Data API v3で動画情報を取得
        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            'id': video_id,
            'part': 'liveStreamingDetails,snippet',
            'key': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get('items'):
            return False
        
        video_info = data['items'][0]
        
        # ライブ配信の詳細があるかチェック
        live_details = video_info.get('liveStreamingDetails')
        if live_details:
            # 実際のライブ配信または予定されたライブ配信
            return True
        
        # snippetでライブ配信かどうか確認
        snippet = video_info.get('snippet', {})
        live_broadcast_content = snippet.get('liveBroadcastContent', 'none')
        
        return live_broadcast_content in ['live', 'upcoming']
        
    except requests.RequestException as e:
        logger.error(f"Error checking live stream status for {video_id}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking live stream {video_id}: {str(e)}")
        return False

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

def save_stream(stream_data: Dict[str, Any]) -> None:
    """
    ライブ配信情報をDynamoDBに保存
    
    Args:
        stream_data: ライブ配信データ
    """
    try:
        table = dynamodb.Table(LIVESTREAMS_TABLE)
        table.put_item(Item=stream_data)
        
    except ClientError as e:
        logger.error(f"Error saving stream {stream_data['video_id']}: {str(e)}")
        raise

def send_stream_check_message(stream_data: Dict[str, Any]) -> None:
    """
    Stream Status CheckerにSQSメッセージを送信
    
    Args:
        stream_data: ライブ配信データ
    """
    try:
        if not TASK_CONTROL_QUEUE_URL:
            logger.warning("Task control queue URL not configured")
            return
        
        message = {
            'action': 'check_stream_status',
            'video_id': stream_data['video_id'],
            'channel_id': stream_data['channel_id'],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        sqs.send_message(
            QueueUrl=TASK_CONTROL_QUEUE_URL,
            MessageBody=json.dumps(message)
        )
        
        logger.info(f"Sent stream check message for {stream_data['video_id']}")
        
    except ClientError as e:
        logger.error(f"Error sending SQS message: {str(e)}")
