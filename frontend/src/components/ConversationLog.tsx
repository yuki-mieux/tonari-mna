/**
 * 会話ログコンポーネント
 */
import { useEffect, useRef } from 'react';
import type { Utterance } from '../types/api';

interface ConversationLogProps {
  utterances: Utterance[];
  onPin?: (id: string, note?: string) => void;
  isRecording?: boolean;
  interimTranscript?: string;
}

export function ConversationLog({
  utterances,
  onPin,
  isRecording = false,
  interimTranscript = '',
}: ConversationLogProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // 新しい発話が追加されたら自動スクロール
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [utterances]);

  return (
    <div className="flex flex-col h-full">
      {/* ヘッダー */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gray-50">
        <h2 className="text-lg font-semibold text-gray-900">会話ログ</h2>
        {isRecording && (
          <div className="flex items-center text-sm text-red-600">
            <span className="w-2 h-2 bg-red-600 rounded-full animate-pulse mr-2" />
            録音中
          </div>
        )}
      </div>

      {/* ログエリア */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {utterances.length === 0 && !interimTranscript ? (
          <div className="text-center text-gray-400 py-8">
            <p>会話ログがありません</p>
            <p className="text-sm mt-1">録音を開始すると、会話が表示されます</p>
          </div>
        ) : (
          <>
            {utterances.map((utterance) => (
              <UtteranceItem
                key={utterance.id}
                utterance={utterance}
                onPin={onPin}
              />
            ))}
            {/* 中間トランスクリプト（確定前のテキスト） */}
            {interimTranscript && (
              <div className="flex justify-end">
                <div className="max-w-[80%] rounded-lg px-4 py-2 bg-primary-400 text-white opacity-70">
                  <div className="text-xs mb-1 text-primary-200">
                    認識中...
                  </div>
                  <p className="text-sm whitespace-pre-wrap">{interimTranscript}</p>
                </div>
              </div>
            )}
          </>
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}

interface UtteranceItemProps {
  utterance: Utterance;
  onPin?: (id: string, note?: string) => void;
}

function UtteranceItem({ utterance, onPin }: UtteranceItemProps) {
  const isUser = utterance.speaker === 'user';

  const handlePin = () => {
    onPin?.(utterance.id);
  };

  return (
    <div
      className={`group flex ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div
        className={`max-w-[80%] rounded-lg px-4 py-2 ${
          isUser
            ? 'bg-primary-600 text-white'
            : 'bg-gray-100 text-gray-900'
        } ${utterance.is_pinned ? 'ring-2 ring-yellow-400' : ''} ${
          utterance.is_important ? 'border-l-4 border-yellow-500' : ''
        }`}
      >
        {/* 話者ラベル */}
        <div
          className={`text-xs mb-1 ${
            isUser ? 'text-primary-200' : 'text-gray-500'
          }`}
        >
          {isUser ? 'アドバイザー' : '売り手'} ・{' '}
          {new Date(utterance.timestamp).toLocaleTimeString('ja-JP', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </div>

        {/* テキスト */}
        <p className="text-sm whitespace-pre-wrap">{utterance.text}</p>

        {/* ピン留めメモ */}
        {utterance.is_pinned && utterance.pin_note && (
          <div
            className={`mt-2 text-xs ${
              isUser ? 'text-primary-200' : 'text-gray-500'
            }`}
          >
            📌 {utterance.pin_note}
          </div>
        )}
      </div>

      {/* ピン留めボタン */}
      {onPin && !utterance.is_pinned && (
        <button
          onClick={handlePin}
          className="opacity-0 group-hover:opacity-100 ml-2 p-1 text-gray-400 hover:text-yellow-500 transition-opacity"
          title="ピン留め"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
            />
          </svg>
        </button>
      )}
    </div>
  );
}
