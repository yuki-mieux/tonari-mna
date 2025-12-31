# Railway CLI

## 目的
- RailwayのプロジェクトやサービスをCLIから操作する

## コマンド一覧（主要）
- `railway add`（サービスやDBを追加）
- `railway completion`（シェル補完を生成）
- `railway connect`（DB接続情報の取得）
- `railway deploy`（デプロイ実行）
- `railway domain`（ドメイン管理）
- `railway docs`（ドキュメントを開く）
- `railway down`（ローカル開発の終了）
- `railway environment`（環境の一覧/切替）
- `railway init`（新規プロジェクト作成）
- `railway link`（既存プロジェクトにリンク）
- `railway list`（プロジェクト一覧）
- `railway login`（認証）
- `railway logout`（ログアウト）
- `railway logs`（ログ確認）
- `railway open`（ダッシュボードを開く）
- `railway run`（環境変数つきでローカル実行）
- `railway service`（サービスの切替/指定）
- `railway shell`（環境変数つきシェル）
- `railway ssh`（デプロイ先へSSH）
- `railway status`（リンク状況確認）
- `railway unlink`（リンク解除）
- `railway up`（アップロードしてデプロイ）
- `railway variables`（環境変数の参照/設定）
- `railway whoami`（ログイン中のユーザー確認）
- `railway volume`（ボリューム管理）
- `railway redeploy`（直近デプロイを再実行）

## パラメーター / 仕様
### 認証
- `RAILWAY_TOKEN`（Project token）
- `RAILWAY_API_TOKEN`（Account/Team token）
- 両方がある場合は `RAILWAY_TOKEN` が優先

### railway add
- `-d, --database <postgres|mysql|redis|mongo>`
- `-s, --service [<name>]`
- `-r, --repo <repo>`
- `-i, --image <image>`
- `-v, --variables <key=value>`（複数可）
- `--json`

### railway environment
- `railway environment [ENVIRONMENT]`
  - `--json`
- `railway environment new [NAME]`
- `railway environment delete [ENVIRONMENT]`
  - `-y, --yes`

### railway init
- `-n, --name <name>`
- `-w, --workspace <name|id>`
- `--json`

### railway link
- `-e, --environment <name>`
- `-p, --project <project>`
- `-s, --service <service>`
- `-t, --team <team>`（`personal` 指定可）
- `--json`

### railway login
- `-b, --browserless`
- `--json`

### railway logs
- `-d, --deployment`
- `-b, --build`
- `--json`

### railway run
- `-s, --service <service>`
- `-e, --environment <environment>`
- `--json`

### railway shell
- `-s, --service <service>`
- `--json`

### railway ssh
- `-p, --project <project>`
- `-s, --service <service>`
- `-e, --environment <environment>`
- `-d, --deployment-instance <id>`
- `--json`

### railway up
- `-d, --detach`
- `-c, --ci`
- `-s, --service <service>`
- `-e, --environment <environment>`
- `--no-gitignore`
- `--verbose`
- `--json`

### railway variables
- `-s, --service <service>`
- `-e, --environment <environment>`
- `-k, --kv`
- `--set <key=value>`（複数可）
- `--json`

### railway volume
- `railway volume <list|add|delete|update|attach|detach>`
  - `-s, --service <service>`
  - `-e, --environment <environment>`
  - `--json`

### railway redeploy
- `-s, --service <service>`
- `-y, --yes`
- `--json`

## 最小サンプル
```bash
railway login
railway link
railway up
railway logs -d
railway run "python -V"
```
