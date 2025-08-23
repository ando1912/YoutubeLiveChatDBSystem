# 旧Ansibleプレイブック保管フォルダ

このフォルダには、新しい工程別デプロイシステム導入前の旧プレイブックが保管されています。

## 📁 保管されているファイル

### Lambda関数デプロイ関連
- `deploy-lambda.yml` - 旧Lambda関数一括デプロイ
- `deploy-api-handler.yml` - API Handler Lambda個別デプロイ
- `deploy-ecs-task-launcher.yml` - ECS Task Launcher Lambda個別デプロイ
- `deploy-rss-monitor.yml` - RSS Monitor Lambda個別デプロイ
- `deploy-stream-status.yml` - Stream Status Checker Lambda個別デプロイ

### コンテナデプロイ関連
- `deploy-container.yml` - 旧ECSコンテナデプロイ

### フロントエンドデプロイ関連
- `deploy-frontend.yml` - 基本フロントエンドデプロイ
- `deploy-frontend-simple.yml` - シンプルフロントエンドデプロイ
- `deploy-frontend-secure.yml` - セキュアフロントエンドデプロイ
- `deploy-frontend-fixed.yml` - 修正版フロントエンドデプロイ

## 🔄 新システムとの対応関係

| 旧ファイル | 新システム対応 |
|-----------|---------------|
| `deploy-lambda.yml` | `02-deploy-lambda.yml` |
| `deploy-container.yml` | `03-deploy-container.yml` |
| `deploy-frontend-simple.yml` | `04-deploy-frontend.yml` |
| 個別Lambda関数ファイル | `02-deploy-lambda.yml`に統合 |

## ⚠️ 注意事項

- これらのファイルは**参考用**として保管されています
- **新しいデプロイには使用しないでください**
- 新システムは以下を使用してください：
  - 完全デプロイ: `../deploy-all.yml`
  - 個別デプロイ: `../quick-deploy.yml`
  - 工程別実行: `../01-pre-checks.yml` ～ `../05-post-verification.yml`

## 🗑️ 削除について

これらのファイルは以下の場合に削除可能です：
- 新システムが十分に安定稼働している
- 旧システムへの回帰の必要性がない
- 開発チーム全体が新システムに慣れている

---

**移動日**: 2025-08-23  
**理由**: 新しい工程別デプロイシステム導入のため  
**新システム**: 5段階工程別 + 一括・個別デプロイ対応
