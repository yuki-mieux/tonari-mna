/**
 * TONARI for M&A - APIクライアント
 */
import type {
  CreateSessionResponse,
  ExtractionsResponse,
  Output,
  OutputListResponse,
  Project,
  ProjectCreate,
  ProjectListResponse,
  ProjectUpdate,
  SessionState,
  SessionSummary,
} from '../types/api';

const API_BASE = import.meta.env.VITE_API_URL || '';

/**
 * APIリクエストを実行する
 */
async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${path}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `API Error: ${response.status}`);
  }

  return response.json();
}

// ========================
// プロジェクトAPI
// ========================

export const projectApi = {
  /**
   * プロジェクト一覧を取得
   */
  list: (params?: { status?: string; limit?: number; offset?: number }) => {
    const query = new URLSearchParams();
    if (params?.status) query.set('status', params.status);
    if (params?.limit) query.set('limit', params.limit.toString());
    if (params?.offset) query.set('offset', params.offset.toString());

    const path = `/api/mna/projects${query.toString() ? `?${query}` : ''}`;
    return request<ProjectListResponse>(path);
  },

  /**
   * プロジェクトを作成
   */
  create: (data: ProjectCreate) => {
    return request<Project>('/api/mna/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * プロジェクトを取得
   */
  get: (projectId: string) => {
    return request<Project>(`/api/mna/projects/${projectId}`);
  },

  /**
   * プロジェクトを更新
   */
  update: (projectId: string, data: ProjectUpdate) => {
    return request<Project>(`/api/mna/projects/${projectId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  /**
   * プロジェクトを削除
   */
  delete: (projectId: string) => {
    return request<{ message: string }>(`/api/mna/projects/${projectId}`, {
      method: 'DELETE',
    });
  },

  /**
   * 成果物一覧を取得
   */
  listOutputs: (projectId: string) => {
    return request<OutputListResponse>(`/api/mna/projects/${projectId}/outputs`);
  },

  /**
   * 成果物を作成
   */
  createOutput: (projectId: string, outputType: 'non_name' | 'im') => {
    return request<Output>(`/api/mna/projects/${projectId}/outputs`, {
      method: 'POST',
      body: JSON.stringify({ output_type: outputType }),
    });
  },
};

// ========================
// セッションAPI
// ========================

// ========================
// 設定API
// ========================

interface AppConfig {
  deepgram_api_key: string;
}

export const configApi = {
  /**
   * アプリ設定を取得
   */
  get: () => {
    return request<AppConfig>('/api/config');
  },
};

// ========================
// セッションAPI
// ========================

export const sessionApi = {
  /**
   * セッションを作成
   */
  create: (projectId: string) => {
    return request<CreateSessionResponse>('/api/mna/sessions', {
      method: 'POST',
      body: JSON.stringify({ project_id: projectId }),
    });
  },

  /**
   * セッションを取得
   */
  get: (sessionId: string) => {
    return request<SessionState>(`/api/mna/sessions/${sessionId}`);
  },

  /**
   * セッションを終了
   */
  end: (sessionId: string) => {
    return request<SessionSummary>(`/api/mna/sessions/${sessionId}/end`, {
      method: 'POST',
    });
  },

  /**
   * 抽出情報を取得
   */
  getExtractions: (sessionId: string) => {
    return request<ExtractionsResponse>(`/api/mna/sessions/${sessionId}/extractions`);
  },

  /**
   * 抽出情報を更新
   */
  updateExtraction: (sessionId: string, fieldKey: string, value: string) => {
    return request<{ success: boolean }>(
      `/api/mna/sessions/${sessionId}/extractions/${fieldKey}`,
      {
        method: 'PUT',
        body: JSON.stringify({ value }),
      }
    );
  },
};
