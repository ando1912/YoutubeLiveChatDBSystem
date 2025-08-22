#!/usr/bin/env python3
import json
import glob
import os
from datetime import datetime

def get_timestamps_from_log(log_file):
    """ログファイルから最初と最後のタイムスタンプを取得"""
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        timestamps = []
        if 'history' in data:
            for entry in data['history']:
                if 'user' in entry:
                    ts = entry['user'].get('timestamp')
                    if ts and ts != 'null':
                        timestamps.append(ts)
        
        if timestamps:
            return min(timestamps), max(timestamps)
        return None, None
    except Exception as e:
        print(f"Error processing {log_file}: {e}")
        return None, None

def main():
    log_files = sorted(glob.glob("*.log"))
    
    print("ログファイルの時間範囲分析:")
    print("=" * 80)
    
    prev_end = None
    gaps = []
    
    for log_file in log_files:
        start_ts, end_ts = get_timestamps_from_log(log_file)
        
        if start_ts and end_ts:
            start_dt = datetime.fromisoformat(start_ts.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_ts.replace('Z', '+00:00'))
            
            print(f"{log_file}:")
            print(f"  開始: {start_dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            print(f"  終了: {end_dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            print(f"  期間: {(end_dt - start_dt).total_seconds() / 3600:.1f}時間")
            
            if prev_end:
                gap = (start_dt - prev_end).total_seconds() / 60
                if gap > 1:  # 1分以上のギャップ
                    print(f"  ⚠️  前のログとのギャップ: {gap:.1f}分")
                    gaps.append((prev_end, start_dt, gap))
                else:
                    print(f"  ✅ 連続性: OK ({gap:.1f}分)")
            
            prev_end = end_dt
            print()
        else:
            print(f"{log_file}: タイムスタンプが見つかりません")
            print()
    
    if gaps:
        print("検出されたギャップ:")
        print("-" * 40)
        for i, (end_time, start_time, gap_minutes) in enumerate(gaps, 1):
            print(f"{i}. {end_time.strftime('%Y-%m-%d %H:%M:%S')} → {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   ギャップ: {gap_minutes:.1f}分")
    else:
        print("✅ ログファイル間にギャップは検出されませんでした")

if __name__ == "__main__":
    main()
