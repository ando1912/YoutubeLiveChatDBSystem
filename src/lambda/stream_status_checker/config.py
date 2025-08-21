"""
Configuration management for Lambda functions
"""
import os
import boto3
from typing import Optional

class Config:
    def __init__(self):
        self.environment = os.environ.get('ENVIRONMENT', 'dev')
        self.aws_region = os.environ.get('AWS_REGION', 'ap-northeast-1')
        self._ssm_client = None
        self._youtube_api_key = None
    
    @property
    def ssm_client(self):
        if self._ssm_client is None:
            self._ssm_client = boto3.client('ssm', region_name=self.aws_region)
        return self._ssm_client
    
    @property
    def youtube_api_key(self) -> str:
        """YouTube Data API v3 Key from Parameter Store"""
        if self._youtube_api_key is None:
            parameter_name = f"/{self.environment}/youtube-chat-collector/youtube-api-key"
            try:
                response = self.ssm_client.get_parameter(
                    Name=parameter_name,
                    WithDecryption=True
                )
                self._youtube_api_key = response['Parameter']['Value']
            except Exception as e:
                raise ValueError(f"Failed to get YouTube API Key from Parameter Store: {e}")
        
        return self._youtube_api_key
    
    @property
    def dynamodb_table_names(self) -> dict:
        """DynamoDB table names"""
        return {
            'channels': f"{self.environment}-Channels",
            'livestreams': f"{self.environment}-LiveStreams", 
            'comments': f"{self.environment}-Comments",
            'taskstatus': f"{self.environment}-TaskStatus"
        }
    
    @property
    def sqs_queue_url(self) -> str:
        """SQS Queue URL for task control"""
        return os.environ.get('SQS_QUEUE_URL', '')

# Global config instance
config = Config()
