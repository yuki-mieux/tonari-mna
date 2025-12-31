/**
 * セッション（面談）画面
 */
import { useCallback, useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ConversationLog } from '../components/ConversationLog';
import { ExtractionPanel } from '../components/ExtractionPanel';
import { SuggestionPanel } from '../components/SuggestionPanel';
import { ProgressBar } from '../components/ProgressBar';
import { Button } from '../components/ui/Button';
import { useWebSocket } from '../hooks/useWebSocket';
import { useSessionStore } from '../stores/sessionStore';
import { sessionApi } from '../lib/api';
import type { ExtractionProgress, MissingField } from '../types/api';
import type { WSServerMessage } from '../types/websocket';

type TabType = 'extraction' | 'suggestion';

export function Session() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<TabType>('extraction');
  const [progress, setProgress] = useState<ExtractionProgress | null>(null);
  const [missingFields, setMissingFields] = useState<MissingField[]>([]);
  const [isEnding, setIsEnding] = useState(false);

  // セッション状態
  const {
    startSession,
    endSession,
    isRecording,
    setRecording,
    utterances,
    extractions,
    suggestions,
    reframings,
    addUtterance,
    updateExtraction,
    addSuggestion,
    dismissSuggestion,
    useSuggestion,
    addReframing,
    pinUtterance,
  } = useSessionStore();

  // WebSocketメッセージハンドラ
  const handleMessage = useCallback(
    (message: WSServerMessage) => {
      switch (message.type) {
        case 'transcript':
          if (message.data.is_final) {
            addUtterance(message.data.utterance);
          } else {
            // 中間結果の処理（必要に応じて）
          }
          break;

        case 'extraction_update':
          updateExtraction(message.data.field_key, message.data.field);
          // 進捗を再取得
          fetchExtractions();
          break;

        case 'suggestion':
          addSuggestion(message.data);
          break;

        case 'reframing':
          addReframing(message.data);
          break;

        case 'error':
          console.error('WebSocket error:', message.data.message);
          break;
      }
    },
    [addUtterance, updateExtraction, addSuggestion, addReframing]
  );

  // WebSocket接続
  const { status: wsStatus, send } = useWebSocket(sessionId || null, {
    onMessage: handleMessage,
    onOpen: () => {
      console.log('WebSocket connected');
    },
    onClose: () => {
      console.log('WebSocket disconnected');
    },
  });

  // 抽出情報を取得
  const fetchExtractions = useCallback(async () => {
    if (!sessionId) return;

    try {
      const response = await sessionApi.getExtractions(sessionId);
      Object.entries(response.extractions).forEach(([key, field]) => {
        updateExtraction(key, field);
      });
      setProgress(response.progress);
      setMissingFields(response.missing_fields);
    } catch (error) {
      console.error('Failed to fetch extractions:', error);
    }
  }, [sessionId, updateExtraction]);

  // セッション初期化
  useEffect(() => {
    if (sessionId) {
      startSession(sessionId, ''); // TODO: projectIdを取得
      fetchExtractions();
    }
  }, [sessionId, startSession, fetchExtractions]);

  // 録音開始/停止
  const toggleRecording = () => {
    setRecording(!isRecording);
    // TODO: 実際の音声キャプチャ実装
  };

  // 発話をピン留め
  const handlePinUtterance = (utteranceId: string, note?: string) => {
    pinUtterance(utteranceId, note);
    send({ type: 'pin_utterance', utterance_id: utteranceId, note });
  };

  // サジェストを使用
  const handleUseSuggestion = (suggestionId: string) => {
    useSuggestion(suggestionId);
    send({ type: 'use_suggestion', suggestion_id: suggestionId });
  };

  // サジェストをスキップ
  const handleDismissSuggestion = (suggestionId: string) => {
    dismissSuggestion(suggestionId);
    send({ type: 'dismiss_suggestion', suggestion_id: suggestionId });
  };

  // 抽出情報を更新
  const handleUpdateExtraction = (fieldKey: string, value: string) => {
    send({ type: 'update_extraction', field_key: fieldKey, value });
  };

  // セッション終了
  const handleEndSession = async () => {
    if (!sessionId) return;

    setIsEnding(true);
    try {
      await sessionApi.end(sessionId);
      endSession();
      navigate('/');
    } catch (error) {
      console.error('Failed to end session:', error);
    } finally {
      setIsEnding(false);
    }
  };

  return (
    <div className="h-[calc(100vh-64px)] flex flex-col">
      {/* 進捗バー */}
      <div className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="max-w-7xl mx-auto">
          <ProgressBar progress={progress} />
        </div>
      </div>

      {/* メインコンテンツ */}
      <div className="flex-1 flex overflow-hidden">
        {/* 左カラム: 会話ログ */}
        <div className="w-1/2 border-r border-gray-200 bg-white flex flex-col">
          <ConversationLog
            utterances={utterances}
            onPin={handlePinUtterance}
            isRecording={isRecording}
          />
        </div>

        {/* 右カラム: 抽出情報/サジェスト */}
        <div className="w-1/2 bg-gray-50 flex flex-col">
          {/* タブ */}
          <div className="flex border-b border-gray-200 bg-white">
            <button
              onClick={() => setActiveTab('extraction')}
              className={`flex-1 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'extraction'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              抽出情報
            </button>
            <button
              onClick={() => setActiveTab('suggestion')}
              className={`flex-1 px-4 py-3 text-sm font-medium border-b-2 transition-colors relative ${
                activeTab === 'suggestion'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              提案
              {suggestions.length > 0 && (
                <span className="absolute top-2 right-4 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                  {suggestions.length}
                </span>
              )}
            </button>
          </div>

          {/* タブコンテンツ */}
          <div className="flex-1 overflow-hidden">
            {activeTab === 'extraction' ? (
              <ExtractionPanel
                extractions={extractions}
                missingFields={missingFields}
                onUpdateExtraction={handleUpdateExtraction}
              />
            ) : (
              <SuggestionPanel
                suggestions={suggestions}
                reframings={reframings}
                onUseSuggestion={handleUseSuggestion}
                onDismissSuggestion={handleDismissSuggestion}
              />
            )}
          </div>
        </div>
      </div>

      {/* フッター: コントロール */}
      <div className="bg-white border-t border-gray-200 px-4 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          {/* WebSocket状態 */}
          <div className="flex items-center gap-2 text-sm">
            <span
              className={`w-2 h-2 rounded-full ${
                wsStatus === 'connected'
                  ? 'bg-green-500'
                  : wsStatus === 'connecting'
                  ? 'bg-yellow-500 animate-pulse'
                  : 'bg-red-500'
              }`}
            />
            <span className="text-gray-500">
              {wsStatus === 'connected'
                ? '接続中'
                : wsStatus === 'connecting'
                ? '接続中...'
                : '未接続'}
            </span>
          </div>

          {/* コントロール */}
          <div className="flex items-center gap-4">
            <Button
              variant={isRecording ? 'danger' : 'success'}
              onClick={toggleRecording}
              className="min-w-[120px]"
            >
              {isRecording ? '録音停止' : '録音開始'}
            </Button>
            <Button
              variant="secondary"
              onClick={handleEndSession}
              isLoading={isEnding}
            >
              セッション終了
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
