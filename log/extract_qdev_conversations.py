#!/usr/bin/env python3
"""
Q Developerのログファイルからプロンプト入力と出力を抽出して、
読みやすい形式で1つのファイルにまとめるスクリプト（重複除去機能付き）
"""

import json
import os
import glob
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Set

def parse_log_file(log_file_path: str) -> Dict[str, Any]:
    """ログファイルを解析してJSONデータを返す"""
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error parsing {log_file_path}: {e}")
        return None

def create_conversation_hash(conversation: Dict[str, Any]) -> str:
    """会話の内容からハッシュを生成して重複判定に使用"""
    # 重複判定に使用するフィールドを組み合わせ
    hash_content = {
        'conversation_id': conversation.get('conversation_id', ''),
        'user_prompt': conversation.get('user_prompt', ''),
        'assistant_response': conversation.get('assistant_response', ''),
        'timestamp': conversation.get('timestamp', ''),
        'tool_count': len(conversation.get('tool_uses', []))
    }
    
    # JSON文字列にしてハッシュ化
    content_str = json.dumps(hash_content, sort_keys=True)
    return hashlib.md5(content_str.encode()).hexdigest()

def extract_conversation_data(log_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """ログデータから会話データを抽出"""
    conversations = []
    
    if not log_data or 'history' not in log_data:
        return conversations
    
    conversation_id = log_data.get('conversation_id', 'unknown')
    
    for entry in log_data['history']:
        if 'user' in entry and 'assistant' in entry:
            user_data = entry['user']
            assistant_data = entry['assistant']
            
            # ユーザープロンプトを取得
            user_prompt = ""
            if 'content' in user_data:
                if 'Prompt' in user_data['content']:
                    user_prompt = user_data['content']['Prompt']['prompt']
                elif 'ToolUseResults' in user_data['content']:
                    # ツール実行結果の場合、結果の概要を表示
                    results = user_data['content']['ToolUseResults'].get('tool_use_results', [])
                    if results:
                        user_prompt = f"[ツール実行結果] {len(results)}個の結果"
            
            # アシスタントの応答を取得
            assistant_response = ""
            tool_uses = []
            
            if 'ToolUse' in assistant_data:
                assistant_response = assistant_data['ToolUse'].get('content', '')
                tool_uses = assistant_data['ToolUse'].get('tool_uses', [])
            elif 'Response' in assistant_data:
                assistant_response = assistant_data['Response'].get('content', '')
            elif 'Message' in assistant_data:
                assistant_response = assistant_data['Message'].get('content', '')
            elif 'ToolUseResults' in assistant_data:
                # ToolUseResultsの場合、結果の内容を抽出
                results = assistant_data['ToolUseResults'].get('tool_use_results', [])
                if results:
                    result_contents = []
                    for result in results:
                        if 'content' in result:
                            for content_item in result['content']:
                                if 'Text' in content_item:
                                    result_contents.append(content_item['Text'])
                                elif 'Json' in content_item:
                                    # JSON結果の場合、stdoutがあれば使用
                                    json_content = content_item['Json']
                                    if 'stdout' in json_content and json_content['stdout']:
                                        result_contents.append(json_content['stdout'])
                    assistant_response = '\n'.join(result_contents)
            elif 'CancelledToolUses' in assistant_data:
                # キャンセルされたツール使用の場合
                prompt = assistant_data['CancelledToolUses'].get('prompt', '')
                assistant_response = f"[ツール使用がキャンセルされました] {prompt}"
            
            # タイムスタンプを取得（複数のソースから）
            timestamp = user_data.get('timestamp', '')
            
            # timestampがnullまたは空の場合、request_metadataから取得を試行
            if not timestamp and 'request_metadata' in entry:
                request_start_ms = entry['request_metadata'].get('request_start_timestamp_ms')
                if request_start_ms:
                    # ミリ秒のタイムスタンプをISO形式に変換
                    from datetime import datetime, timezone
                    dt = datetime.fromtimestamp(request_start_ms / 1000, tz=timezone.utc)
                    timestamp = dt.isoformat()
            
            conversation = {
                'conversation_id': conversation_id,
                'timestamp': timestamp,
                'user_prompt': user_prompt,
                'assistant_response': assistant_response,
                'tool_uses': tool_uses
            }
            
            conversations.append(conversation)
    
    return conversations

def remove_duplicates(conversations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """重複する会話を除去"""
    seen_hashes: Set[str] = set()
    unique_conversations = []
    duplicate_count = 0
    
    for conversation in conversations:
        conv_hash = create_conversation_hash(conversation)
        
        if conv_hash not in seen_hashes:
            seen_hashes.add(conv_hash)
            unique_conversations.append(conversation)
        else:
            duplicate_count += 1
    
    print(f"🔍 重複除去: {duplicate_count}個の重複会話を除去しました")
    return unique_conversations

def format_conversation_output(conversations: List[Dict[str, Any]]) -> str:
    """会話データを読みやすい形式でフォーマット"""
    output = []
    output.append("=" * 80)
    output.append("Q Developer 会話ログ（重複除去済み）")
    output.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output.append("=" * 80)
    output.append("")
    
    for i, conv in enumerate(conversations, 1):
        # タイムスタンプをフォーマット
        timestamp = conv['timestamp']
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
            except:
                formatted_time = timestamp
        else:
            formatted_time = "不明"
        
        output.append(f"【会話 {i}】")
        output.append(f"会話ID: {conv['conversation_id']}")
        output.append(f"日時: {formatted_time}")
        output.append("-" * 60)
        
        # ユーザープロンプト
        output.append("🔵 ユーザー入力:")
        output.append(conv['user_prompt'])
        output.append("")
        
        # アシスタント応答
        output.append("🤖 Q Developer応答:")
        output.append(conv['assistant_response'])
        output.append("")
        
        # ツール使用がある場合
        if conv['tool_uses']:
            output.append("🔧 実行されたツール:")
            for j, tool in enumerate(conv['tool_uses'], 1):
                tool_name = tool.get('name', '不明')
                tool_summary = tool.get('args', {}).get('summary', '')
                output.append(f"  {j}. {tool_name}")
                if tool_summary:
                    output.append(f"     概要: {tool_summary}")
            output.append("")
        
        output.append("=" * 80)
        output.append("")
    
    return "\n".join(output)

def main():
    """メイン処理"""
    log_dir = "/home/ando-pvt/github/250820_YoutubeLiveChatCollector/log"
    
    # ログファイルを取得（.pyファイルは除外）
    log_files = [f for f in glob.glob(os.path.join(log_dir, "*.log")) 
                 if not f.endswith('.py')]
    
    if not log_files:
        print("ログファイルが見つかりません。")
        return
    
    print(f"見つかったログファイル: {len(log_files)}個")
    
    all_conversations = []
    
    # 各ログファイルを処理
    for log_file in sorted(log_files):
        print(f"処理中: {os.path.basename(log_file)}")
        log_data = parse_log_file(log_file)
        if log_data:
            conversations = extract_conversation_data(log_data)
            all_conversations.extend(conversations)
    
    if not all_conversations:
        print("会話データが見つかりませんでした。")
        return
    
    print(f"📊 抽出された会話数（重複除去前）: {len(all_conversations)}")
    
    # 重複を除去
    unique_conversations = remove_duplicates(all_conversations)
    
    # タイムスタンプでソート（Noneの場合は空文字として扱う）
    unique_conversations.sort(key=lambda x: x['timestamp'] or '')
    
    # 出力ファイルを生成
    output_content = format_conversation_output(unique_conversations)
    output_file = os.path.join(log_dir, "qdev_conversations_summary.txt")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output_content)
    
    print(f"\n✅ 完了!")
    print(f"📁 出力ファイル: {output_file}")
    print(f"📊 最終的な会話数（重複除去後）: {len(unique_conversations)}")
    print(f"🗑️  除去された重複: {len(all_conversations) - len(unique_conversations)}個")

if __name__ == "__main__":
    main()
