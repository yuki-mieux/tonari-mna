# Supabase CLI

## 目的
- ローカル開発環境の起動とDBマイグレーションの管理
- リモートプロジェクトとのリンクや型生成

## コマンド一覧（主要）
- `supabase login`（認証）
- `supabase init`（ローカル初期化）
- `supabase start`（ローカル起動）
- `supabase stop`（ローカル停止）
- `supabase status`（ローカル状態確認）
- `supabase link`（リモートにリンク）
- `supabase migration new`（マイグレーション作成）
- `supabase db push`（リモートへ反映）
- `supabase db reset`（ローカルDB初期化）
- `supabase gen types`（型生成）

## パラメーター / 仕様
### グローバル
- `--debug`
- `--dns-resolver <native|https>`
- `--experimental`
- `-h, --help`
- `--workdir <path>`
- `-v, --version`
- `--output <pretty|json|toml|yaml>`
- `--create-ticket`

### supabase login
- `-n, --name <name>`
- `-t, --token <access-token>`
- `--no-browser`
- `--create-ticket`

### supabase init
- `--force`
- `--project-id <id>`
- `--no-cli-login`
- `--no-config`
- `--workdir <path>`

### supabase start
- `-x, --exclude <service>`
- `--ignore-health-check`

### supabase stop
- `--all`
- `--no-backup`
- `--project-id <id>`
- `--output <pretty|json|toml|yaml>`

### supabase status
- `--override-name <name>`
- `--output <pretty|json|toml|yaml>`

### supabase link
- `-p, --project-ref <ref>`
- `--password <db_password>`
- `--workdir <path>`

### supabase migration new
- `-d, --db-url <postgres_url>`
- `--use-pgtool`

### supabase db push
- `--db-url <postgres_url>`
- `--dry-run`
- `--include-all`
- `--include-roles`
- `--include-seed`
- `--local`
- `--password <db_password>`
- `--schema <name>`

### supabase db reset
- `--db-url <postgres_url>`
- `--debug`
- `--linked`
- `--no-seed`
- `--password <db_password>`
- `--schema <name>`

### supabase gen types
- `-d, --db-url <postgres_url>`
- `-l, --lang <typescript|go|swift>`
- `--linked`
- `--local`

## 最小サンプル
```bash
supabase login
supabase init
supabase start
supabase status -o env

supabase link --project-ref <ref>
supabase migration new init
supabase db push

supabase gen types --lang typescript --linked > src/types/supabase.ts
```

## Storage（ファイル管理）
### できること
- バケット作成/一覧/削除
- ファイルのアップロード/ダウンロード/削除
- 公開/非公開、署名付きURLでアクセス制御
- RLSでユーザー単位の権限を制御
- S3互換APIで外部ツールから操作可能

### 最小サンプル（TypeScript）
```ts
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!,
);

// バケット作成
await supabase.storage.createBucket("uploads", { public: false });

// アップロード
await supabase.storage.from("uploads").upload("docs/readme.txt", fileBlob);

// 署名付きURL
const { data } = await supabase.storage
  .from("uploads")
  .createSignedUrl("docs/readme.txt", 60);
```
