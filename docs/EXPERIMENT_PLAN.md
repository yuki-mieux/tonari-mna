# HireMate - 実験計画（コア技術検証）

最終更新: 2025-12-09
タグ: #HireMate #実験計画 #技術検証

---

## 核心課題

> 普通に会話してて、その間をリアルタイムに聞きつつ、横ですぐに画面表示する

これを分解すると：

```
[面接ツール] → [音声キャプチャ] → [リアルタイムSTT] → [横画面に表示]
     ↑              ↑                   ↑                ↑
   Zoom等        ここが鍵            遅延との戦い      UXの問題
```

---

## 実験ステップ（6段階）

### Step 0: 環境確認（5分）
**目的**: 必要なAPIキーがあるか確認

```bash
# 確認するもの
- Deepgram API Key（音声認識用）
- Anthropic API Key（Claude用、後で使う）
```

**成功基準**: APIキーが手元にある

---

### Step 1: マイク音声をブラウザで取得（15分）
**目的**: Web Audio APIの基本動作確認

**やること**:
```html
<!-- test1_mic.html -->
<!DOCTYPE html>
<html>
<head><title>Step1: マイク取得</title></head>
<body>
  <button id="start">開始</button>
  <div id="status">待機中</div>
  <script>
    document.getElementById('start').onclick = async () => {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      document.getElementById('status').textContent = '🎤 マイク取得成功！';

      // 音声レベルを表示（動作確認）
      const audioContext = new AudioContext();
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      source.connect(analyser);

      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      function checkLevel() {
        analyser.getByteFrequencyData(dataArray);
        const avg = dataArray.reduce((a, b) => a + b) / dataArray.length;
        document.getElementById('status').textContent = `🎤 音声レベル: ${avg.toFixed(0)}`;
        requestAnimationFrame(checkLevel);
      }
      checkLevel();
    };
  </script>
</body>
</html>
```

**成功基準**:
- マイクに話しかけると音声レベルの数字が動く
- 「マイク取得成功」が表示される

---

### Step 2: マイク音声 → Deepgram → テキスト表示（30分）
**目的**: リアルタイム音声認識の基本フローを確認

**やること**:
```html
<!-- test2_stt.html -->
<!DOCTYPE html>
<html>
<head><title>Step2: リアルタイムSTT</title></head>
<body>
  <button id="start">開始</button>
  <div id="transcript" style="white-space: pre-wrap; border: 1px solid #ccc; padding: 10px; min-height: 200px;"></div>

  <script>
    const DEEPGRAM_API_KEY = 'YOUR_API_KEY'; // ここに入れる

    document.getElementById('start').onclick = async () => {
      // 1. マイク取得
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      // 2. Deepgram WebSocket接続
      const socket = new WebSocket(
        'wss://api.deepgram.com/v1/listen?language=ja&punctuate=true',
        ['token', DEEPGRAM_API_KEY]
      );

      socket.onopen = () => {
        console.log('Deepgram接続成功');

        // 3. MediaRecorderで音声を送信
        const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0 && socket.readyState === WebSocket.OPEN) {
            socket.send(event.data);
          }
        };
        mediaRecorder.start(250); // 250msごとに送信
      };

      // 4. 結果を表示
      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        const transcript = data.channel?.alternatives?.[0]?.transcript;
        if (transcript) {
          document.getElementById('transcript').textContent += transcript + ' ';
        }
      };
    };
  </script>
</body>
</html>
```

**成功基準**:
- マイクに話しかけるとテキストが表示される
- 遅延が2秒以内

**計測ポイント**:
- 話してから表示までの遅延（体感でOK）

---

### Step 3: タブ音声のキャプチャ（45分）★最難関
**目的**: 面接ツール（Zoom等）の音声を取得する

**選択肢A: chrome.tabCapture API（Chrome拡張）**

```javascript
// background.js
chrome.action.onClicked.addListener(async (tab) => {
  const streamId = await chrome.tabCapture.getMediaStreamId({
    targetTabId: tab.id
  });

  // content scriptに送信
  chrome.tabs.sendMessage(tab.id, {
    type: 'START_CAPTURE',
    streamId
  });
});

// content.js
chrome.runtime.onMessage.addListener(async (message) => {
  if (message.type === 'START_CAPTURE') {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        mandatory: {
          chromeMediaSource: 'tab',
          chromeMediaSourceId: message.streamId
        }
      }
    });
    // このstreamをDeepgramに送る
  }
});
```

**選択肢B: 画面共有経由（シンプル）**

```javascript
// ユーザーに画面共有を選択させる
const stream = await navigator.mediaDevices.getDisplayMedia({
  audio: true,  // ← これでシステム音声も取れる
  video: true   // videoも必要（後で無視）
});

// 音声トラックだけ使う
const audioTrack = stream.getAudioTracks()[0];
```

**成功基準**:
- YouTubeや他のタブの音声がテキスト化される
- Zoomの音声が取れる（最終確認）

**判断ポイント**:
- 選択肢A（tabCapture）がうまくいかなければBで進む
- Bは「画面共有ダイアログ」が出るがシンプル

---

### Step 4: 2画面構成のUI確認（20分）
**目的**: 「面接ツール + 横のAIパネル」の配置を確認

**やること**:
```
┌─────────────────────────────────────────────────┐
│                   ブラウザ                       │
├────────────────────────┬────────────────────────┤
│                        │                        │
│     面接ツール         │    HireMateパネル      │
│     (Zoom等)           │    (テキスト表示)      │
│                        │                        │
│                        │  ┌──────────────────┐ │
│                        │  │ 今の発言:        │ │
│                        │  │ 「品質管理を...」│ │
│                        │  └──────────────────┘ │
│                        │                        │
└────────────────────────┴────────────────────────┘
```

**選択肢**:
1. **Chrome拡張 Side Panel API** - Chrome 114+で使える
2. **別ウィンドウ** - window.open()でポップアップ
3. **Split View** - ユーザーが手動でウィンドウ配置

**成功基準**:
- 面接しながらチラ見できる位置に表示できる
- 面接の邪魔にならない

---

### Step 5: 統合テスト（30分）
**目的**: Step 1-4を組み合わせてE2E動作確認

**テストシナリオ**:
1. Zoomで自分のマイクで話す
2. 横のパネルにリアルタイムでテキストが出る
3. 遅延が2秒以内

**計測**:
- 発話 → 表示の遅延
- 認識精度（日本語）
- CPU/メモリ使用量

---

### Step 6: 実際の面接シミュレーション（15分）
**目的**: 実運用に近い形でテスト

**やること**:
- 2人でZoom接続
- 面接っぽい会話をする
- HireMateパネルを横に表示
- 会話がリアルタイムで出るか確認

**成功基準**:
- 「これなら使える」と思える体験

---

## 実験の優先順位

```
重要度高 ─────────────────────────────────────> 低

Step 3    Step 2    Step 4    Step 5    Step 1, 6
(タブ音声) (STT)     (UI)     (統合)    (基礎/最終)
  ↑
  │
  └─ ここが一番リスク高い。最初に検証すべき。
```

**推奨順序**:
1. **Step 1** (5分) - 基礎確認
2. **Step 3** (45分) - 最難関を先に潰す
3. **Step 2** (30分) - STT接続
4. **Step 4** (20分) - UI配置
5. **Step 5** (30分) - 統合
6. **Step 6** (15分) - 最終確認

---

## リスクと代替案

### リスク1: tabCapture APIが使えない
**症状**: 権限エラー、音声が取れない
**代替案**:
- getDisplayMedia（画面共有経由）で音声取得
- デスクトップアプリ（Electron）に切り替え

### リスク2: Deepgramの遅延が大きい
**症状**: 3秒以上遅れる
**代替案**:
- Whisper API（ただし遅延は同等かそれ以上）
- ローカルWhisper（セットアップ重い）
- Google Cloud Speech-to-Text

### リスク3: Zoomの音声が取れない
**症状**: Zoomアプリは独自の音声処理をしている
**代替案**:
- ZoomをWebブラウザ版で使う
- システム音声をキャプチャ（OS依存）
- 仮想オーディオデバイス（BlackHole等）

---

## 今夜のフリーレ目標

**ゴール**: Step 5まで完了し、「これいける！」を確認する

**タイムライン**:
| 時間 | やること |
|------|----------|
| 0:00-0:05 | Step 1: マイク取得確認 |
| 0:05-0:50 | Step 3: タブ音声キャプチャ（最難関） |
| 0:50-1:20 | Step 2: Deepgram接続 |
| 1:20-1:40 | Step 4: UI配置 |
| 1:40-2:10 | Step 5: 統合テスト |
| 2:10-2:30 | Step 6: 面接シミュレーション |

**判断ポイント**:
- Step 3で詰まったら → getDisplayMediaに切り替え
- 2時間でStep 5まで行けなければ → 翌日に持ち越し

---

## 必要な準備

### API
- [ ] Deepgram API Key（https://console.deepgram.com/）
- [ ] Anthropic API Key（後で使う）

### ツール
- [ ] Chrome（最新版）
- [ ] Zoom（ブラウザ版でテスト）
- [ ] VSCode or エディタ

### 参考資料
- [Deepgram JavaScript SDK](https://developers.deepgram.com/docs/getting-started-with-live-streaming-audio)
- [Chrome tabCapture API](https://developer.chrome.com/docs/extensions/reference/tabCapture/)
- [Chrome Side Panel API](https://developer.chrome.com/docs/extensions/reference/sidePanel/)
