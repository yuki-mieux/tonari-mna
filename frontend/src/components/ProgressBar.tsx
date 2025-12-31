/**
 * 抽出進捗バーコンポーネント
 */
import type { ExtractionProgress } from '../types/api';

interface ProgressBarProps {
  progress: ExtractionProgress | null;
  className?: string;
}

export function ProgressBar({ progress, className = '' }: ProgressBarProps) {
  if (!progress) return null;

  const percentage = progress.percentage;

  // 進捗に応じた色
  const getColor = (pct: number) => {
    if (pct < 30) return 'bg-red-500';
    if (pct < 60) return 'bg-yellow-500';
    if (pct < 90) return 'bg-blue-500';
    return 'bg-green-500';
  };

  return (
    <div className={`space-y-2 ${className}`}>
      {/* メイン進捗 */}
      <div className="flex items-center justify-between text-sm">
        <span className="text-gray-600">抽出進捗</span>
        <span className="font-medium text-gray-900">
          {progress.filled}/{progress.total} ({percentage.toFixed(0)}%)
        </span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2.5">
        <div
          className={`h-2.5 rounded-full transition-all duration-300 ${getColor(percentage)}`}
          style={{ width: `${percentage}%` }}
        />
      </div>

      {/* カテゴリ別進捗 */}
      <div className="grid grid-cols-5 gap-2 mt-3">
        {Object.entries(progress.by_category).map(([category, data]) => (
          <div key={category} className="text-center">
            <div className="text-xs text-gray-500 mb-1 truncate" title={getCategoryLabel(category)}>
              {getCategoryLabel(category)}
            </div>
            <div className="w-full bg-gray-200 rounded-full h-1.5">
              <div
                className={`h-1.5 rounded-full ${getColor(data.percentage)}`}
                style={{ width: `${data.percentage}%` }}
              />
            </div>
            <div className="text-xs text-gray-400 mt-0.5">
              {data.filled}/{data.total}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function getCategoryLabel(category: string): string {
  const labels: Record<string, string> = {
    basic_info: '基本',
    financial: '財務',
    business: '事業',
    organization: '組織',
    transfer: '譲渡',
  };
  return labels[category] || category;
}
