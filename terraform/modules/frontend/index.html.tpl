<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Live Chat Collector - ${environment}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .status {
            background-color: #e7f3ff;
            padding: 15px;
            border-radius: 4px;
            margin: 20px 0;
        }
        .environment {
            background-color: #fff3cd;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>YouTube Live Chat Collector</h1>
        
        <div class="environment">
            Environment: ${environment}
        </div>
        
        <div class="status">
            <h3>🚧 システム構築中</h3>
            <p>現在、YouTube Live Chat Collectorシステムを構築中です。</p>
            <p>インフラストラクチャの準備が完了次第、Reactアプリケーションをデプロイします。</p>
        </div>
        
        <div class="status">
            <h3>📋 次のステップ</h3>
            <ul>
                <li>✅ インフラストラクチャ構築</li>
                <li>⏳ Lambda関数実装</li>
                <li>⏳ ECSコンテナ実装</li>
                <li>⏳ Reactアプリケーション実装</li>
                <li>⏳ 統合テスト</li>
            </ul>
        </div>
    </div>
    
    <script src="config.js"></script>
    <script>
        console.log('App Config:', window.APP_CONFIG);
    </script>
</body>
</html>
