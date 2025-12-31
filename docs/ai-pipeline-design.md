# AIパイプライン設計書

## 概要
TONARI for M&AのAIパイプラインは、リアルタイム音声処理と水野メソッドの実装を担当する。

## 使用モデル

| 用途 | モデル | 備考 |
|------|--------|------|
| 音声文字起こし | Deepgram nova-2 | 日本語対応、リアルタイム |
| 情報抽出 | Claude claude-sonnet-4-20250514 | 構造化出力 |
| 構造分析 | Claude claude-sonnet-4-20250514 | 推論 |
| サジェスト生成 | Claude claude-sonnet-4-20250514 | 文脈理解 |
| 成果物生成 | Claude claude-sonnet-4-20250514 | 文章生成 |

## 処理フロー

### リアルタイム処理パイプライン

```
┌─────────────┐
│   マイク    │
│  (Browser)  │
└──────┬──────┘
       │ 音声ストリーム
       ▼
┌─────────────┐
│ AudioAPI    │  MediaRecorder APIで音声キャプチャ
│ (Frontend)  │  Opus/WebMでエンコード
└──────┬──────┘
       │ WebSocket (binary)
       ▼
┌─────────────┐
│ FastAPI     │  WebSocketハンドラで受信
│ WebSocket   │  音声バッファリング
└──────┬──────┘
       │ 音声バイナリ
       ▼
┌─────────────┐
│ Deepgram    │  リアルタイムSTT
│ WebSocket   │  日本語モデル (nova-2-ja)
└──────┬──────┘
       │ テキスト (interim/final)
       ▼
┌─────────────┐
│ テキスト    │  5〜10秒分をバッファリング
│ バッファ    │  finalのみ蓄積
└──────┬──────┘
       │ バッチテキスト
       ▼
┌─────────────────────────────────────────┐
│           Claude API 処理               │
│                                         │
│  ┌─────────────┐                       │
│  │ 情報抽出    │ ← 最優先              │
│  │ Extraction  │                       │
│  └──────┬──────┘                       │
│         │                               │
│         ├──────────┬──────────┐        │
│         ▼          ▼          ▼        │
│  ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │ 構造分析 │ │ 買い手像 │ │サジェスト│ │
│  │ Analysis │ │ Buyer    │ │Suggest │ │
│  └──────────┘ └──────────┘ └────────┘ │
│         │          │          │        │
│         └──────────┴──────────┘        │
│                    │                    │
└────────────────────┼────────────────────┘
                     │
                     ▼
              ┌─────────────┐
              │ クライアント │
              │ UI更新      │
              └─────────────┘
```

## Deepgram連携

### 設定
```python
DEEPGRAM_CONFIG = {
    "model": "nova-2",
    "language": "ja",
    "punctuate": True,
    "diarize": True,  # 話者分離
    "smart_format": True,
    "encoding": "opus",
    "sample_rate": 48000,
    "channels": 1,
}
```

### WebSocket接続
```python
async def connect_deepgram(session_id: str) -> DeepgramConnection:
    """Deepgram WebSocketに接続する.

    Args:
        session_id: セッションID（ログ用）

    Returns:
        DeepgramConnection: WebSocket接続オブジェクト
    """
    client = DeepgramClient(settings.deepgram_api_key)
    connection = client.listen.websocket.v("1")

    connection.on(LiveTranscriptionEvents.Transcript, handle_transcript)
    connection.on(LiveTranscriptionEvents.Error, handle_error)

    await connection.start(DEEPGRAM_CONFIG)
    return connection
```

## Claude API連携

### レート制限対策
```python
class ClaudeRateLimiter:
    """Claude APIのレート制限を管理する.

    Attributes:
        rpm_limit: 1分あたりのリクエスト上限
        tpm_limit: 1分あたりのトークン上限
    """

    def __init__(self, rpm_limit: int = 60, tpm_limit: int = 100000):
        self.rpm_limit = rpm_limit
        self.tpm_limit = tpm_limit
        self.request_times: list[float] = []
        self.token_counts: list[tuple[float, int]] = []

    async def acquire(self, estimated_tokens: int) -> None:
        """レート制限をチェックし、必要なら待機する."""
        await self._wait_for_rpm()
        await self._wait_for_tpm(estimated_tokens)
        self._record(estimated_tokens)
```

### 構造化出力
```python
async def call_claude_structured(
    prompt: str,
    output_schema: dict,
) -> dict:
    """Claude APIを構造化出力モードで呼び出す.

    Args:
        prompt: プロンプト
        output_schema: 出力スキーマ（JSON Schema形式）

    Returns:
        構造化された出力
    """
    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
        tools=[{
            "name": "output",
            "description": "構造化出力",
            "input_schema": output_schema,
        }],
        tool_choice={"type": "tool", "name": "output"},
    )
    return response.content[0].input
```

## プロンプト設計

### 情報抽出（extraction.j2）
```jinja2
あなたはM&Aアドバイザーのアシスタントです。
以下の会話から、M&A検討に必要な情報を抽出してください。

## これまでの抽出情報
{% for category, fields in current_extractions.items() %}
### {{ category }}
{% for field, value in fields.items() %}
- {{ field }}: {{ value.value if value.value else "(未取得)" }}
{% endfor %}
{% endfor %}

## 新しい会話
{% for utterance in new_utterances %}
[{{ utterance.speaker }}] {{ utterance.text }}
{% endfor %}

## 抽出対象
- 基本情報: 会社名、所在地、業種、設立年、従業員数、代表者
- 財務情報: 売上高、営業利益、純資産、借入金
- 事業情報: 事業内容、主要取引先、競合優位性
- 組織情報: 組織体制、キーパーソン、後継者有無
- 譲渡情報: 譲渡理由、希望価格、希望時期

新しく抽出できた情報のみを出力してください。
```

### 構造分析（analysis.j2）
```jinja2
あなたは経験豊富なM&Aアドバイザーです。
以下の企業情報から、事業構造と本質的な価値を分析してください。

## 企業情報
{% for category, fields in extractions.items() %}
### {{ category }}
{% for field, value in fields.items() %}
{% if value.value %}
- {{ field }}: {{ value.value }}（確信度: {{ value.confidence|round(2) }}）
{% endif %}
{% endfor %}
{% endfor %}

## 分析観点
1. **事業構造**: なぜこの事業で利益が出ているか
2. **競合優位性**: 他社にない強み
3. **リスク要因**: 買い手が懸念しそうな点
4. **隠れた価値**: 表面的には見えにくい強み

各観点について、根拠とともに簡潔に分析してください。
```

### サジェスト生成（suggestion.j2）
```jinja2
あなたはM&Aヒアリングの専門家「水野メソッド」を実践するアシスタントです。

## 水野メソッドの4原則
1. **多層的情報収集**: 表層→構造→本質→出口の4レイヤーで情報を集める
2. **仮説駆動**: 仮説を立て、検証する質問をする
3. **リフレーミング**: ネガティブ情報をポジティブに転換
4. **出口逆算**: 買い手が知りたい情報を優先

## 現在の状況
### 抽出済み情報
{% for category, fields in extractions.items() %}
{% for field, value in fields.items() %}
{% if value.value %}
- {{ field }}: {{ value.value }}
{% endif %}
{% endfor %}
{% endfor %}

### 未取得の重要情報
{% for field in missing_fields %}
- {{ field }}
{% endfor %}

### 直近の会話
{% for utterance in recent_utterances[-5:] %}
[{{ utterance.speaker }}] {{ utterance.text }}
{% endfor %}

### 現在の仮説
{% for hypothesis in hypotheses %}
- {{ hypothesis.content }}（確信度: {{ hypothesis.confidence }}）
{% endfor %}

## 出力
以下を生成してください：
1. 今聞くべき質問（文脈に自然に乗る形で）
2. その理由
3. 対応するレイヤー（surface/structure/essence/exit）
4. 優先度（0-1）
```

### リフレーミング（reframing.j2）
```jinja2
以下の発言にネガティブな内容が含まれています。
M&Aの観点から、ポジティブに解釈できる可能性を提示してください。

## 発言
{{ utterance.text }}

## 検知されたネガティブワード
{{ negative_word }}

## 出力
1. 別の見方（ポジティブな解釈）
2. 確認すべき質問（真因を探る）
3. ポジティブに転換できる条件
```

## バッファリング戦略

### 音声バッファ
```python
class AudioBuffer:
    """音声データをバッファリングする.

    Attributes:
        buffer_duration: バッファ時間（秒）
    """

    def __init__(self, buffer_duration: float = 5.0):
        self.buffer_duration = buffer_duration
        self.chunks: list[bytes] = []
        self.start_time: float | None = None

    def add(self, chunk: bytes) -> bytes | None:
        """チャンクを追加し、バッファ時間を超えたら返す."""
        if self.start_time is None:
            self.start_time = time.time()

        self.chunks.append(chunk)

        if time.time() - self.start_time >= self.buffer_duration:
            result = b"".join(self.chunks)
            self.chunks = []
            self.start_time = None
            return result

        return None
```

### テキストバッファ
```python
class TextBuffer:
    """テキストをバッファリングしてClaude APIに送る.

    Attributes:
        buffer_duration: バッファ時間（秒）
        min_utterances: 最小発話数
    """

    def __init__(self, buffer_duration: float = 10.0, min_utterances: int = 3):
        self.buffer_duration = buffer_duration
        self.min_utterances = min_utterances
        self.utterances: list[Utterance] = []
        self.last_flush: float = time.time()

    def add(self, utterance: Utterance) -> list[Utterance] | None:
        """発話を追加し、条件を満たしたら返す."""
        self.utterances.append(utterance)

        should_flush = (
            time.time() - self.last_flush >= self.buffer_duration
            and len(self.utterances) >= self.min_utterances
        )

        if should_flush:
            result = self.utterances
            self.utterances = []
            self.last_flush = time.time()
            return result

        return None
```

## 並列処理

### 分析の並列実行
```python
async def process_extraction_result(
    extraction: ExtractionResult,
    session_state: SessionState,
) -> ProcessingResult:
    """抽出結果を受けて各種分析を並列実行する.

    Args:
        extraction: 抽出結果
        session_state: セッション状態

    Returns:
        ProcessingResult: 分析結果・サジェスト等
    """
    # 情報抽出は完了している前提で、分析を並列実行
    # Why: 各分析は独立しており、並列化でレイテンシ削減
    tasks = [
        analyze_structure(extraction, session_state),
        infer_buyers(extraction, session_state),
        generate_suggestions(extraction, session_state),
        detect_reframing(extraction),
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    return ProcessingResult(
        structure=results[0] if not isinstance(results[0], Exception) else None,
        buyers=results[1] if not isinstance(results[1], Exception) else None,
        suggestions=results[2] if not isinstance(results[2], Exception) else None,
        reframing=results[3] if not isinstance(results[3], Exception) else None,
    )
```

## エラーハンドリング

### Deepgramエラー
```python
async def handle_deepgram_error(error: DeepgramError) -> None:
    """Deepgramエラーを処理する.

    Args:
        error: Deepgramエラー

    Raises:
        STTError: 回復不能なエラーの場合
    """
    if error.code == "RATE_LIMITED":
        # Why: レート制限は一時的なので再接続を試みる
        await asyncio.sleep(5)
        await reconnect_deepgram()
    else:
        raise STTError(f"Deepgram error: {error.message}")
```

### Claude APIエラー
```python
async def handle_claude_error(error: AnthropicError) -> None:
    """Claude APIエラーを処理する.

    Args:
        error: Anthropicエラー

    Raises:
        AIError: 回復不能なエラーの場合
    """
    if error.status_code == 429:
        # Why: レート制限は待機で回復可能
        retry_after = int(error.headers.get("retry-after", 60))
        await asyncio.sleep(retry_after)
    elif error.status_code >= 500:
        # Why: サーバーエラーは一時的な可能性
        await asyncio.sleep(10)
    else:
        raise AIError(f"Claude API error: {error.message}")
```

## 性能目標

| 指標 | 目標値 |
|------|--------|
| 音声→テキスト遅延 | < 1秒 |
| テキスト→抽出遅延 | < 3秒 |
| 分析・サジェスト遅延 | < 5秒 |
| エンドツーエンド遅延 | < 10秒 |
