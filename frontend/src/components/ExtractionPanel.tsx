/**
 * 抽出情報パネルコンポーネント
 */
import { useState } from 'react';
import type { ExtractionCategory, ExtractionField, MissingField } from '../types/api';
import { Badge } from './ui/Badge';

interface ExtractionPanelProps {
  extractions: Record<string, ExtractionField>;
  missingFields: MissingField[];
  onUpdateExtraction?: (fieldKey: string, value: string) => void;
}

// カテゴリ順序
const CATEGORY_ORDER: ExtractionCategory[] = [
  'basic_info',
  'financial',
  'business',
  'organization',
  'transfer',
];

// カテゴリラベル
const CATEGORY_LABELS: Record<ExtractionCategory, string> = {
  basic_info: '会社概要',
  financial: '財務情報',
  business: '事業情報',
  organization: '組織情報',
  transfer: '譲渡条件',
};

// フィールドラベル
const FIELD_LABELS: Record<string, string> = {
  company_name: '会社名',
  location: '所在地',
  established_year: '設立年',
  capital: '資本金',
  employee_count: '従業員数',
  representative: '代表者',
  representative_profile: '代表者プロフィール',
  history: '沿革',
  revenue_latest: '売上高（直近）',
  revenue_trend: '売上高推移',
  operating_profit: '営業利益',
  ordinary_profit: '経常利益',
  net_assets: '純資産',
  adjusted_net_assets: '調整後純資産',
  debt: '借入金',
  main_kpis: '主要KPI',
  business_description: '事業内容',
  main_products_services: '主要サービス/製品',
  main_clients: '主要取引先',
  client_composition: '顧客構成',
  competitive_advantage: '競合優位性',
  strengths: '強み',
  weaknesses: '弱み',
  industry_trends: '業界動向',
  market_position: '市場ポジション',
  org_structure: '組織体制',
  key_persons: 'キーパーソン',
  successor_status: '後継者有無',
  employee_treatment: '従業員の処遇',
  executive_retention: '役員の残留意向',
  transfer_scheme: '譲渡スキーム',
  transfer_reason: '譲渡理由',
  desired_price: '希望価格',
  desired_timing: '希望時期',
  desired_conditions: '希望条件',
  dd_notes: 'DD留意事項',
};

export function ExtractionPanel({
  extractions,
  missingFields,
  onUpdateExtraction,
}: ExtractionPanelProps) {
  const [activeCategory, setActiveCategory] = useState<ExtractionCategory>('basic_info');
  const [editingField, setEditingField] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');

  // カテゴリごとにグループ化
  const groupedExtractions = CATEGORY_ORDER.reduce((acc, category) => {
    const categoryFields = Object.entries(extractions).filter(
      ([_, field]) => field.category === category
    );
    acc[category] = categoryFields;
    return acc;
  }, {} as Record<ExtractionCategory, [string, ExtractionField][]>);

  // カテゴリの未取得フィールド
  const categoryMissing = missingFields.filter((f) => f.category === activeCategory);

  const handleEdit = (fieldKey: string, currentValue: string | null) => {
    setEditingField(fieldKey);
    setEditValue(currentValue || '');
  };

  const handleSave = (fieldKey: string) => {
    onUpdateExtraction?.(fieldKey, editValue);
    setEditingField(null);
    setEditValue('');
  };

  const handleCancel = () => {
    setEditingField(null);
    setEditValue('');
  };

  return (
    <div className="h-full flex flex-col">
      {/* カテゴリタブ */}
      <div className="flex border-b border-gray-200 bg-gray-50 overflow-x-auto">
        {CATEGORY_ORDER.map((category) => {
          const filled = groupedExtractions[category]?.filter(
            ([_, f]) => f.value
          ).length || 0;
          const total =
            (groupedExtractions[category]?.length || 0) +
            missingFields.filter((m) => m.category === category).length;

          return (
            <button
              key={category}
              onClick={() => setActiveCategory(category)}
              className={`px-4 py-2 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
                activeCategory === category
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {CATEGORY_LABELS[category]}
              <span className="ml-1 text-xs text-gray-400">
                ({filled}/{total})
              </span>
            </button>
          );
        })}
      </div>

      {/* フィールドリスト */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-3">
          {/* 取得済みフィールド */}
          {groupedExtractions[activeCategory]?.map(([fieldKey, field]) => (
            <FieldItem
              key={fieldKey}
              field={field}
              label={FIELD_LABELS[field.field] || field.field}
              isEditing={editingField === fieldKey}
              editValue={editValue}
              onEdit={() => handleEdit(fieldKey, field.value)}
              onSave={() => handleSave(fieldKey)}
              onCancel={handleCancel}
              onEditValueChange={setEditValue}
            />
          ))}

          {/* 未取得フィールド */}
          {categoryMissing.map((missing) => {
            const fieldKey = `${missing.category}.${missing.field}`;
            return (
              <MissingFieldItem
                key={fieldKey}
                missing={missing}
                isEditing={editingField === fieldKey}
                editValue={editValue}
                onEdit={() => handleEdit(fieldKey, null)}
                onSave={() => handleSave(fieldKey)}
                onCancel={handleCancel}
                onEditValueChange={setEditValue}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
}

interface FieldItemProps {
  field: ExtractionField;
  label: string;
  isEditing: boolean;
  editValue: string;
  onEdit: () => void;
  onSave: () => void;
  onCancel: () => void;
  onEditValueChange: (value: string) => void;
}

function FieldItem({
  field,
  label,
  isEditing,
  editValue,
  onEdit,
  onSave,
  onCancel,
  onEditValueChange,
}: FieldItemProps) {
  const confidenceColor =
    field.confidence >= 0.8
      ? 'text-green-600'
      : field.confidence >= 0.5
      ? 'text-yellow-600'
      : 'text-red-600';

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-3">
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm font-medium text-gray-700">{label}</span>
        <div className="flex items-center gap-2">
          <Badge
            variant={
              field.layer === 'essence'
                ? 'success'
                : field.layer === 'exit'
                ? 'danger'
                : 'info'
            }
          >
            {field.layer}
          </Badge>
          <span className={`text-xs ${confidenceColor}`}>
            {(field.confidence * 100).toFixed(0)}%
          </span>
        </div>
      </div>

      {isEditing ? (
        <div className="flex gap-2 mt-2">
          <input
            type="text"
            value={editValue}
            onChange={(e) => onEditValueChange(e.target.value)}
            className="flex-1 input text-sm"
            autoFocus
          />
          <button
            onClick={onSave}
            className="px-3 py-1 text-sm bg-primary-600 text-white rounded hover:bg-primary-700"
          >
            保存
          </button>
          <button
            onClick={onCancel}
            className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
          >
            キャンセル
          </button>
        </div>
      ) : (
        <div
          onClick={onEdit}
          className="text-sm text-gray-900 cursor-pointer hover:bg-gray-50 p-1 -m-1 rounded"
        >
          {field.value || <span className="text-gray-400 italic">値なし</span>}
        </div>
      )}
    </div>
  );
}

interface MissingFieldItemProps {
  missing: MissingField;
  isEditing: boolean;
  editValue: string;
  onEdit: () => void;
  onSave: () => void;
  onCancel: () => void;
  onEditValueChange: (value: string) => void;
}

function MissingFieldItem({
  missing,
  isEditing,
  editValue,
  onEdit,
  onSave,
  onCancel,
  onEditValueChange,
}: MissingFieldItemProps) {
  return (
    <div className="bg-gray-50 border border-dashed border-gray-300 rounded-lg p-3">
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm font-medium text-gray-500">{missing.label}</span>
        <Badge variant="warning">未取得</Badge>
      </div>

      {isEditing ? (
        <div className="flex gap-2 mt-2">
          <input
            type="text"
            value={editValue}
            onChange={(e) => onEditValueChange(e.target.value)}
            className="flex-1 input text-sm"
            placeholder="値を入力..."
            autoFocus
          />
          <button
            onClick={onSave}
            className="px-3 py-1 text-sm bg-primary-600 text-white rounded hover:bg-primary-700"
          >
            保存
          </button>
          <button
            onClick={onCancel}
            className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
          >
            キャンセル
          </button>
        </div>
      ) : (
        <button
          onClick={onEdit}
          className="text-sm text-primary-600 hover:text-primary-700"
        >
          + 手動入力
        </button>
      )}
    </div>
  );
}
