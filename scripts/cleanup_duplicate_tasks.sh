#!/bin/bash

# 重複ECSタスク一括停止スクリプト
# 同一配信IDで複数実行されているタスクを停止

echo "🚨 重複ECSタスク一括停止スクリプト"
echo "=================================="

CLUSTER_NAME="dev-youtube-comment-collector"
REGION="ap-northeast-1"

# 実行中タスク一覧を取得
echo "📋 実行中タスクを取得中..."
TASK_ARNS=$(aws ecs list-tasks \
  --cluster $CLUSTER_NAME \
  --region $REGION \
  --query 'taskArns[]' \
  --output text)

if [ -z "$TASK_ARNS" ]; then
  echo "✅ 実行中のタスクはありません"
  exit 0
fi

# タスク数をカウント
TASK_COUNT=$(echo "$TASK_ARNS" | wc -w)
echo "📊 実行中タスク数: $TASK_COUNT"

if [ $TASK_COUNT -le 1 ]; then
  echo "✅ 重複タスクはありません（1個以下）"
  exit 0
fi

echo "⚠️  重複タスクを検出しました"
echo "🛑 35個のタスクを停止します（1個は残す）"

# 最初の1個を除いて残りを停止
COUNTER=0
for TASK_ARN in $TASK_ARNS; do
  COUNTER=$((COUNTER + 1))
  
  if [ $COUNTER -eq 1 ]; then
    echo "✅ タスク $COUNTER: 継続実行 ($(basename $TASK_ARN))"
    continue
  fi
  
  echo "🛑 タスク $COUNTER を停止中: $(basename $TASK_ARN)"
  
  aws ecs stop-task \
    --cluster $CLUSTER_NAME \
    --region $REGION \
    --task $TASK_ARN \
    --reason "Duplicate task cleanup - keeping only one task per video" \
    --output text > /dev/null
  
  if [ $? -eq 0 ]; then
    echo "   ✅ 停止完了"
  else
    echo "   ❌ 停止失敗"
  fi
  
  # API制限を避けるため少し待機
  sleep 1
done

echo ""
echo "🎯 クリーンアップ完了"
echo "📊 停止したタスク数: $((TASK_COUNT - 1))"
echo "📊 継続実行タスク数: 1"
echo ""
echo "💰 コスト削減効果:"
echo "   - 停止前: ${TASK_COUNT}個のFargateタスク"
echo "   - 停止後: 1個のFargateタスク"
echo "   - 削減率: $((($TASK_COUNT - 1) * 100 / $TASK_COUNT))%"
