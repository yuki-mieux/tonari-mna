# データベース設計書

## 概要
TONARI for M&AのデータベースはSupabase（PostgreSQL）で構築する。

## ER図

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   users     │       │  projects   │       │  sessions   │
│  (auth)     │──1:N──│             │──1:N──│             │
└─────────────┘       └─────────────┘       └──────┬──────┘
                                                   │
                      ┌────────────────────────────┼────────────────────────────┐
                      │                            │                            │
                      ▼                            ▼                            ▼
              ┌─────────────┐              ┌─────────────┐              ┌─────────────┐
              │ utterances  │              │ extractions │              │ suggestions │
              │             │              │             │              │             │
              └─────────────┘              └─────────────┘              └─────────────┘
                                                  │
                                                  ▼
                                          ┌─────────────┐
                                          │  analyses   │
                                          │             │
                                          └─────────────┘

┌─────────────┐
│   outputs   │──N:1── projects
│             │
└─────────────┘
```

## テーブル定義

### projects（プロジェクト/案件）

| カラム | 型 | 制約 | 説明 |
|--------|-----|------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 主キー |
| user_id | UUID | FK → auth.users(id), NOT NULL | 所有者 |
| name | TEXT | NOT NULL | プロジェクト名 |
| company_name | TEXT | | 対象会社名 |
| status | TEXT | DEFAULT 'active' | ステータス（active/completed/archived） |
| created_at | TIMESTAMPTZ | DEFAULT now() | 作成日時 |
| updated_at | TIMESTAMPTZ | DEFAULT now() | 更新日時 |

```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    company_name TEXT,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'archived')),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_projects_status ON projects(status);
```

### sessions（面談セッション）

| カラム | 型 | 制約 | 説明 |
|--------|-----|------|------|
| id | UUID | PK | 主キー |
| project_id | UUID | FK → projects(id), NOT NULL | プロジェクト |
| started_at | TIMESTAMPTZ | DEFAULT now() | 開始日時 |
| ended_at | TIMESTAMPTZ | | 終了日時 |
| duration_seconds | INTEGER | | 録音時間（秒） |
| status | TEXT | DEFAULT 'active' | ステータス（active/completed） |

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    started_at TIMESTAMPTZ DEFAULT now(),
    ended_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed'))
);

CREATE INDEX idx_sessions_project_id ON sessions(project_id);
CREATE INDEX idx_sessions_status ON sessions(status);
```

### utterances（発話）

| カラム | 型 | 制約 | 説明 |
|--------|-----|------|------|
| id | UUID | PK | 主キー |
| session_id | UUID | FK → sessions(id), NOT NULL | セッション |
| timestamp | TIMESTAMPTZ | NOT NULL | 発話時刻 |
| speaker | TEXT | NOT NULL | 話者（user/customer） |
| text | TEXT | NOT NULL | 発話テキスト |
| is_important | BOOLEAN | DEFAULT false | 重要フラグ（システム判定） |
| is_pinned | BOOLEAN | DEFAULT false | ピン留めフラグ（ユーザー操作） |
| pin_note | TEXT | | ピン留めメモ |
| created_at | TIMESTAMPTZ | DEFAULT now() | 作成日時 |

```sql
CREATE TABLE utterances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL,
    speaker TEXT NOT NULL CHECK (speaker IN ('user', 'customer')),
    text TEXT NOT NULL,
    is_important BOOLEAN DEFAULT false,
    is_pinned BOOLEAN DEFAULT false,
    pin_note TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_utterances_session_id ON utterances(session_id);
CREATE INDEX idx_utterances_timestamp ON utterances(timestamp);
CREATE INDEX idx_utterances_is_pinned ON utterances(is_pinned) WHERE is_pinned = true;
```

### extractions（抽出情報）

| カラム | 型 | 制約 | 説明 |
|--------|-----|------|------|
| id | UUID | PK | 主キー |
| session_id | UUID | FK → sessions(id), NOT NULL | セッション |
| category | TEXT | NOT NULL | カテゴリ |
| field | TEXT | NOT NULL | フィールド名 |
| value | TEXT | | 抽出値 |
| confidence | FLOAT | | 確信度（0-1） |
| source_utterance_id | UUID | FK → utterances(id) | 根拠発話 |
| created_at | TIMESTAMPTZ | DEFAULT now() | 作成日時 |
| updated_at | TIMESTAMPTZ | DEFAULT now() | 更新日時 |

```sql
CREATE TABLE extractions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    category TEXT NOT NULL CHECK (category IN (
        'basic_info', 'financial', 'business', 'organization', 'transfer'
    )),
    field TEXT NOT NULL,
    value TEXT,
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    source_utterance_id UUID REFERENCES utterances(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(session_id, category, field)
);

CREATE INDEX idx_extractions_session_id ON extractions(session_id);
CREATE INDEX idx_extractions_category ON extractions(category);
```

### analyses（分析結果）

| カラム | 型 | 制約 | 説明 |
|--------|-----|------|------|
| id | UUID | PK | 主キー |
| session_id | UUID | FK → sessions(id), NOT NULL | セッション |
| analysis_type | TEXT | NOT NULL | 分析タイプ |
| content | JSONB | NOT NULL | 分析内容 |
| created_at | TIMESTAMPTZ | DEFAULT now() | 作成日時 |

```sql
CREATE TABLE analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    analysis_type TEXT NOT NULL CHECK (analysis_type IN (
        'structure', 'buyer_profile', 'risk', 'hypothesis'
    )),
    content JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_analyses_session_id ON analyses(session_id);
CREATE INDEX idx_analyses_type ON analyses(analysis_type);
```

### suggestions（サジェスト履歴）

| カラム | 型 | 制約 | 説明 |
|--------|-----|------|------|
| id | UUID | PK | 主キー |
| session_id | UUID | FK → sessions(id), NOT NULL | セッション |
| suggestion_type | TEXT | NOT NULL | タイプ（question/reframing） |
| content | TEXT | NOT NULL | サジェスト内容 |
| reason | TEXT | | 理由 |
| layer | TEXT | | レイヤー（surface/structure/essence/exit） |
| priority | FLOAT | | 優先度（0-1） |
| was_used | BOOLEAN | DEFAULT false | 使用されたか |
| was_dismissed | BOOLEAN | DEFAULT false | 非表示にされたか |
| created_at | TIMESTAMPTZ | DEFAULT now() | 作成日時 |

```sql
CREATE TABLE suggestions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    suggestion_type TEXT NOT NULL CHECK (suggestion_type IN ('question', 'reframing')),
    content TEXT NOT NULL,
    reason TEXT,
    layer TEXT CHECK (layer IN ('surface', 'structure', 'essence', 'exit')),
    priority FLOAT CHECK (priority >= 0 AND priority <= 1),
    was_used BOOLEAN DEFAULT false,
    was_dismissed BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_suggestions_session_id ON suggestions(session_id);
```

### outputs（成果物）

| カラム | 型 | 制約 | 説明 |
|--------|-----|------|------|
| id | UUID | PK | 主キー |
| project_id | UUID | FK → projects(id), NOT NULL | プロジェクト |
| output_type | TEXT | NOT NULL | タイプ（non_name/im） |
| content | JSONB | NOT NULL | 成果物内容 |
| file_url | TEXT | | ファイルURL（Storage） |
| created_at | TIMESTAMPTZ | DEFAULT now() | 作成日時 |

```sql
CREATE TABLE outputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    output_type TEXT NOT NULL CHECK (output_type IN ('non_name', 'im')),
    content JSONB NOT NULL,
    file_url TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_outputs_project_id ON outputs(project_id);
CREATE INDEX idx_outputs_type ON outputs(output_type);
```

## RLS（Row Level Security）

```sql
-- RLS有効化
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE utterances ENABLE ROW LEVEL SECURITY;
ALTER TABLE extractions ENABLE ROW LEVEL SECURITY;
ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE suggestions ENABLE ROW LEVEL SECURITY;
ALTER TABLE outputs ENABLE ROW LEVEL SECURITY;

-- projects: 所有者のみアクセス可
CREATE POLICY "Users can access own projects"
ON projects FOR ALL
USING (auth.uid() = user_id);

-- sessions: プロジェクト所有者のみアクセス可
CREATE POLICY "Users can access sessions of own projects"
ON sessions FOR ALL
USING (
    project_id IN (SELECT id FROM projects WHERE user_id = auth.uid())
);

-- utterances: セッション経由でアクセス
CREATE POLICY "Users can access utterances of own sessions"
ON utterances FOR ALL
USING (
    session_id IN (
        SELECT s.id FROM sessions s
        JOIN projects p ON s.project_id = p.id
        WHERE p.user_id = auth.uid()
    )
);

-- extractions, analyses, suggestions: 同様のパターン
-- （省略：sessionsと同じロジック）

-- outputs: プロジェクト所有者のみ
CREATE POLICY "Users can access outputs of own projects"
ON outputs FOR ALL
USING (
    project_id IN (SELECT id FROM projects WHERE user_id = auth.uid())
);
```

## マイグレーション

```bash
# マイグレーション作成
supabase migration new create_initial_tables

# ローカルDB反映
supabase db reset

# リモート反映
supabase db push
```

## 型生成

```bash
# TypeScript型生成
supabase gen types typescript --linked > frontend/src/types/supabase.ts
```
