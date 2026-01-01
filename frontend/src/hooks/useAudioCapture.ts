/**
 * TONARI for M&A - 音声キャプチャフック
 * ブラウザのマイクから音声をキャプチャしてDeepgramに送信
 */
import { useCallback, useRef, useState } from 'react';

interface UseAudioCaptureOptions {
  onTranscript?: (text: string, isFinal: boolean, speaker?: string) => void;
  onError?: (error: Error) => void;
  language?: string;
}

interface UseAudioCaptureReturn {
  isRecording: boolean;
  isConnecting: boolean;
  error: string | null;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
}

// Deepgram WebSocket URL
const DEEPGRAM_WS_URL = 'wss://api.deepgram.com/v1/listen';

/**
 * 音声キャプチャとDeepgram文字起こしを管理するフック
 */
export function useAudioCapture(
  apiKey: string,
  options: UseAudioCaptureOptions = {}
): UseAudioCaptureReturn {
  const { language = 'ja' } = options;

  const [isRecording, setIsRecording] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mediaStreamRef = useRef<MediaStream | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const websocketRef = useRef<WebSocket | null>(null);
  const optionsRef = useRef(options);
  const isRecordingRef = useRef(false);
  optionsRef.current = options;

  const stopRecording = useCallback(() => {
    // MediaRecorderを停止
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    mediaRecorderRef.current = null;

    // MediaStreamのトラックを停止
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
    }
    mediaStreamRef.current = null;

    // WebSocketを閉じる
    if (websocketRef.current) {
      if (websocketRef.current.readyState === WebSocket.OPEN) {
        websocketRef.current.close();
      }
      websocketRef.current = null;
    }

    isRecordingRef.current = false;
    setIsRecording(false);
    setIsConnecting(false);
  }, []);

  const startRecording = useCallback(async () => {
    if (isRecordingRef.current || isConnecting) return;

    setError(null);
    setIsConnecting(true);

    try {
      // マイクアクセスを取得
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });
      mediaStreamRef.current = stream;

      // Deepgram WebSocket接続を確立
      const params = new URLSearchParams({
        model: 'nova-2',
        language,
        punctuate: 'true',
        interim_results: 'true',
        utterance_end_ms: '1000',
        vad_events: 'true',
        smart_format: 'true',
        diarize: 'true',
      });

      const ws = new WebSocket(`${DEEPGRAM_WS_URL}?${params}`, ['token', apiKey]);
      websocketRef.current = ws;

      ws.onopen = () => {
        console.log('Deepgram WebSocket connected');
        setIsConnecting(false);
        isRecordingRef.current = true;
        setIsRecording(true);

        // MediaRecorderを設定
        const mediaRecorder = new MediaRecorder(stream, {
          mimeType: 'audio/webm;codecs=opus',
        });
        mediaRecorderRef.current = mediaRecorder;

        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0 && ws.readyState === WebSocket.OPEN) {
            ws.send(event.data);
          }
        };

        // 250msごとにデータを送信
        mediaRecorder.start(250);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('Deepgram message:', data.type, data);

          if (data.type === 'Results' && data.channel?.alternatives?.[0]) {
            const alternative = data.channel.alternatives[0];
            const transcript = alternative.transcript;

            if (transcript) {
              const isFinal = data.is_final;
              // Diarizationの結果からスピーカーを取得
              const speaker =
                alternative.words?.[0]?.speaker !== undefined
                  ? `speaker_${alternative.words[0].speaker}`
                  : undefined;

              console.log('Transcript:', { transcript, isFinal, speaker });
              optionsRef.current.onTranscript?.(transcript, isFinal, speaker);
            }
          }
        } catch (e) {
          console.error('Failed to parse Deepgram message:', e);
        }
      };

      ws.onerror = (event) => {
        console.error('Deepgram WebSocket error:', event);
        setError('文字起こしサービスへの接続に失敗しました');
        optionsRef.current.onError?.(new Error('Deepgram WebSocket error'));
        stopRecording();
      };

      ws.onclose = (event) => {
        console.log('Deepgram WebSocket closed:', event.code, event.reason);
        if (isRecordingRef.current) {
          stopRecording();
        }
      };
    } catch (err) {
      console.error('Failed to start recording:', err);
      const errorMessage =
        err instanceof Error ? err.message : 'マイクへのアクセスに失敗しました';
      setError(errorMessage);
      optionsRef.current.onError?.(err instanceof Error ? err : new Error(errorMessage));
      setIsConnecting(false);
      stopRecording();
    }
  }, [apiKey, language, isConnecting, stopRecording]);

  return {
    isRecording,
    isConnecting,
    error,
    startRecording,
    stopRecording,
  };
}
