/**
 * TONARI for M&A - API型定義
 */

// ========================
// 列挙型
// ========================

export type ExtractionCategory =
  | 'basic_info'
  | 'financial'
  | 'business'
  | 'organization'
  | 'transfer';

export type InfoLayer = 'surface' | 'structure' | 'essence' | 'exit';

export type SuggestionType = 'question' | 'reframing';

export type OutputType = 'non_name' | 'im';

export type SessionStatus = 'active' | 'completed';

// ========================
// 発話
// ========================

export interface Utterance {
  id: string;
  session_id: string;
  timestamp: string;
  speaker: 'user' | 'customer';
  text: string;
  is_important: boolean;
  is_pinned: boolean;
  pin_note: string | null;
}

// ========================
// 抽出情報
// ========================

export interface ExtractionField {
  category: ExtractionCategory;
  field: string;
  value: string | null;
  confidence: number;
  source_utterance_id: string | null;
  layer: InfoLayer;
}

export interface ExtractionProgress {
  total: number;
  filled: number;
  percentage: number;
  by_category: Record<
    ExtractionCategory,
    { total: number; filled: number; percentage: number }
  >;
  by_layer: Record<InfoLayer, { total: number; filled: number; percentage: number }>;
}

export interface MissingField {
  category: ExtractionCategory;
  field: string;
  label: string;
  layer: InfoLayer;
}

// ========================
// サジェスト
// ========================

export interface Suggestion {
  id: string;
  session_id: string;
  suggestion_type: SuggestionType;
  content: string;
  reason: string;
  layer: InfoLayer;
  priority: number;
  target_field: string | null;
  was_used: boolean;
  was_dismissed: boolean;
  created_at: string;
}

export interface ReframingSuggestion {
  original_text: string;
  negative_word: string;
  positive_interpretation: string;
  follow_up_question: string;
  reframe_conditions: string;
}

// ========================
// セッション
// ========================

export interface SessionState {
  id: string;
  project_id: string;
  status: SessionStatus;
  started_at: string;
  ended_at: string | null;
  utterances: Utterance[];
  extractions: Record<string, ExtractionField>;
  current_layer: InfoLayer;
}

export interface SessionSummary {
  id: string;
  project_id: string;
  started_at: string;
  ended_at: string | null;
  duration_seconds: number | null;
  extraction_count: number;
  utterance_count: number;
}

// ========================
// プロジェクト
// ========================

export interface Project {
  id: string;
  user_id: string;
  name: string;
  company_name: string | null;
  status: 'active' | 'completed' | 'archived';
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  company_name?: string;
}

export interface ProjectUpdate {
  name?: string;
  company_name?: string;
  status?: 'active' | 'completed' | 'archived';
}

// ========================
// 成果物
// ========================

export interface Output {
  id: string;
  project_id: string;
  output_type: OutputType;
  content: Record<string, unknown>;
  file_url: string | null;
  created_at: string;
}

// ========================
// APIレスポンス
// ========================

export interface ProjectListResponse {
  projects: Project[];
  total: number;
}

export interface OutputListResponse {
  outputs: Output[];
}

export interface ExtractionsResponse {
  extractions: Record<string, ExtractionField>;
  progress: ExtractionProgress;
  missing_fields: MissingField[];
}

export interface CreateSessionResponse {
  session_id: string;
  project_id: string;
  status: SessionStatus;
}
