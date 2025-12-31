/**
 * サジェストパネルコンポーネント
 */
import type { ReframingSuggestion, Suggestion } from '../types/api';
import { Badge } from './ui/Badge';
import { Button } from './ui/Button';

interface SuggestionPanelProps {
  suggestions: Suggestion[];
  reframings: ReframingSuggestion[];
  onUseSuggestion?: (id: string) => void;
  onDismissSuggestion?: (id: string) => void;
}

export function SuggestionPanel({
  suggestions,
  reframings,
  onUseSuggestion,
  onDismissSuggestion,
}: SuggestionPanelProps) {
  const activeSuggestions = suggestions.filter((s) => !s.was_used && !s.was_dismissed);

  return (
    <div className="h-full flex flex-col">
      {/* リフレーミング提案（優先表示） */}
      {reframings.length > 0 && (
        <div className="p-4 border-b border-gray-200 bg-yellow-50">
          <h3 className="text-sm font-semibold text-yellow-800 mb-2 flex items-center">
            <svg
              className="w-4 h-4 mr-1"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            リフレーミング提案
          </h3>
          {reframings.map((reframe, index) => (
            <ReframingCard key={index} reframing={reframe} />
          ))}
        </div>
      )}

      {/* 質問サジェスト */}
      <div className="flex-1 overflow-y-auto p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">
          次に聞くべき質問
        </h3>

        {activeSuggestions.length === 0 ? (
          <div className="text-center text-gray-400 py-8">
            <svg
              className="w-12 h-12 mx-auto mb-2 text-gray-300"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <p>サジェストを生成中...</p>
          </div>
        ) : (
          <div className="space-y-3">
            {activeSuggestions.map((suggestion) => (
              <SuggestionCard
                key={suggestion.id}
                suggestion={suggestion}
                onUse={() => onUseSuggestion?.(suggestion.id)}
                onDismiss={() => onDismissSuggestion?.(suggestion.id)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

interface SuggestionCardProps {
  suggestion: Suggestion;
  onUse?: () => void;
  onDismiss?: () => void;
}

function SuggestionCard({ suggestion, onUse, onDismiss }: SuggestionCardProps) {
  const layerLabels: Record<string, { label: string; color: 'info' | 'warning' | 'success' | 'danger' }> = {
    surface: { label: '表層', color: 'info' },
    structure: { label: '構造', color: 'warning' },
    essence: { label: '本質', color: 'success' },
    exit: { label: '出口', color: 'danger' },
  };

  const layer = layerLabels[suggestion.layer] || { label: suggestion.layer, color: 'info' };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-3 shadow-sm hover:shadow-md transition-shadow">
      {/* ヘッダー */}
      <div className="flex items-center justify-between mb-2">
        <Badge variant={layer.color}>{layer.label}</Badge>
        <div className="text-xs text-gray-400">
          優先度: {(suggestion.priority * 100).toFixed(0)}%
        </div>
      </div>

      {/* 質問内容 */}
      <p className="text-sm text-gray-900 mb-2">{suggestion.content}</p>

      {/* 理由 */}
      <p className="text-xs text-gray-500 mb-3">{suggestion.reason}</p>

      {/* アクション */}
      <div className="flex gap-2">
        <Button size="sm" variant="primary" onClick={onUse}>
          使用
        </Button>
        <Button size="sm" variant="ghost" onClick={onDismiss}>
          スキップ
        </Button>
      </div>
    </div>
  );
}

interface ReframingCardProps {
  reframing: ReframingSuggestion;
}

function ReframingCard({ reframing }: ReframingCardProps) {
  return (
    <div className="bg-white border border-yellow-200 rounded-lg p-3 mt-2">
      {/* ネガティブワード */}
      <div className="text-xs text-gray-500 mb-1">
        検出: 「{reframing.negative_word}」
      </div>

      {/* ポジティブな解釈 */}
      <div className="text-sm text-gray-900 mb-2">
        <span className="font-medium text-green-700">→ </span>
        {reframing.positive_interpretation}
      </div>

      {/* フォローアップ質問 */}
      <div className="bg-blue-50 rounded p-2 text-sm text-blue-800">
        <span className="font-medium">確認質問: </span>
        {reframing.follow_up_question}
      </div>
    </div>
  );
}
