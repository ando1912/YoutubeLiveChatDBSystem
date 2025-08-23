# CI/CD Configuration

このディレクトリには、継続的インテグレーション・継続的デプロイメント（CI/CD）に関連する設定ファイルが含まれています。

## ファイル構成

### `buildspec.yml`
AWS CodeBuildで使用されるビルド仕様ファイル

**用途:**
- ECSコンテナ（Comment Collector）の自動ビルド
- DockerイメージのECRへのプッシュ
- ビルドプロセスの自動化

**実行環境:**
- Amazon Linux 2 (aws/codebuild/amazonlinux2-x86_64-standard:3.0)
- BUILD_GENERAL1_SMALL (コスト最適化)
- Privileged mode: 有効 (Docker操作のため)

**ビルドフロー:**
1. **pre_build**: ECRログイン、環境変数設定
2. **build**: Dockerイメージビルド、タグ付け
3. **post_build**: ECRプッシュ、アーティファクト生成

**コスト:**
- 約$0.015/ビルド
- 月間100分まで無料
- 推定ビルド時間: 2-5分

## 使用方法

### 手動ビルド実行
```bash
# AWS CLI経由
aws codebuild start-build --project-name dev-comment-collector-build

# Ansible経由
ansible-playbook playbooks/03-deploy-container.yml
```

### 自動ビルド
- GitHubへのpush時に自動実行（設定により）
- Ansibleプレイブックからのトリガー

## 関連リソース

- **CodeBuildプロジェクト**: `dev-comment-collector-build`
- **ECRリポジトリ**: `dev-comment-collector`
- **IAMロール**: `dev-codebuild-service-role`
- **Terraformモジュール**: `terraform/modules/compute/`

## トラブルシューティング

### よくある問題
1. **ECRログイン失敗**: IAM権限確認
2. **Docker権限エラー**: privileged_mode設定確認
3. **ビルドタイムアウト**: build_timeout設定調整

### ログ確認
```bash
# CodeBuildログ
aws logs get-log-events --log-group-name /aws/codebuild/dev-comment-collector-build

# ECRイメージ確認
aws ecr list-images --repository-name dev-comment-collector
```
