"""HireMate - Vercel Serverless Function for AI Advice"""

import json
import os
import anthropic
from http.server import BaseHTTPRequestHandler


client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

DEFAULT_SYSTEM_PROMPT = """あなたはパンハウスのAI研修営業アシスタントです。
商談の会話を聞いて、営業担当に短いアドバイスを返します。

## 確認すべき項目
- 担当者の役割（AI推進担当か）
- 面談参加の背景
- 現在使っているAIツール
- AI活用の課題
- 決裁者は誰か
- 予算・時期

## 出力ルール
必ず1つアドバイスを返してください（20文字以内）
例：「📋 課題をもう1つ聞いて」「🎯 決裁者を確認」「👍 いい流れ」"""


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            data = json.loads(body)

            transcript = data.get('transcript', '')
            system_prompt = data.get('system_prompt', DEFAULT_SYSTEM_PROMPT)

            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=100,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": f"直近の会話:\n{transcript}\n\n自然に返答してください。"}
                ]
            )

            advice = message.content[0].text

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'advice': advice}).encode())

        except Exception as e:
            print(f"Error: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
