/**
 * TONARI for M&A - セッション状態管理
 */
import { create } from 'zustand';
import type {
  ExtractionField,
  InfoLayer,
  ReframingSuggestion,
  Suggestion,
  Utterance,
} from '../types/api';

interface SessionStore {
  // 状態
  sessionId: string | null;
  projectId: string | null;
  status: 'idle' | 'active' | 'completed';
  isRecording: boolean;
  currentLayer: InfoLayer;

  // データ
  utterances: Utterance[];
  extractions: Record<string, ExtractionField>;
  suggestions: Suggestion[];
  reframings: ReframingSuggestion[];

  // アクション
  startSession: (sessionId: string, projectId: string) => void;
  endSession: () => void;
  setRecording: (isRecording: boolean) => void;
  setCurrentLayer: (layer: InfoLayer) => void;

  // 発話
  addUtterance: (utterance: Utterance) => void;
  updateUtterance: (id: string, updates: Partial<Utterance>) => void;
  pinUtterance: (id: string, note?: string) => void;

  // 抽出
  updateExtraction: (fieldKey: string, field: ExtractionField) => void;

  // サジェスト
  addSuggestion: (suggestion: Suggestion) => void;
  dismissSuggestion: (id: string) => void;
  useSuggestion: (id: string) => void;

  // リフレーミング
  addReframing: (reframing: ReframingSuggestion) => void;
  clearReframings: () => void;

  // リセット
  reset: () => void;
}

const initialState = {
  sessionId: null,
  projectId: null,
  status: 'idle' as const,
  isRecording: false,
  currentLayer: 'surface' as InfoLayer,
  utterances: [],
  extractions: {},
  suggestions: [],
  reframings: [],
};

export const useSessionStore = create<SessionStore>((set) => ({
  ...initialState,

  startSession: (sessionId, projectId) =>
    set({
      sessionId,
      projectId,
      status: 'active',
      isRecording: false,
      utterances: [],
      extractions: {},
      suggestions: [],
      reframings: [],
    }),

  endSession: () =>
    set((state) => ({
      ...state,
      status: 'completed',
      isRecording: false,
    })),

  setRecording: (isRecording) =>
    set({ isRecording }),

  setCurrentLayer: (currentLayer) =>
    set({ currentLayer }),

  addUtterance: (utterance) =>
    set((state) => ({
      utterances: [...state.utterances, utterance],
    })),

  updateUtterance: (id, updates) =>
    set((state) => ({
      utterances: state.utterances.map((u) =>
        u.id === id ? { ...u, ...updates } : u
      ),
    })),

  pinUtterance: (id, note) =>
    set((state) => ({
      utterances: state.utterances.map((u) =>
        u.id === id ? { ...u, is_pinned: true, pin_note: note || null } : u
      ),
    })),

  updateExtraction: (fieldKey, field) =>
    set((state) => ({
      extractions: {
        ...state.extractions,
        [fieldKey]: field,
      },
    })),

  addSuggestion: (suggestion) =>
    set((state) => ({
      suggestions: [...state.suggestions, suggestion].slice(-10), // 最新10件を保持
    })),

  dismissSuggestion: (id) =>
    set((state) => ({
      suggestions: state.suggestions.filter((s) => s.id !== id),
    })),

  useSuggestion: (id) =>
    set((state) => ({
      suggestions: state.suggestions.map((s) =>
        s.id === id ? { ...s, was_used: true } : s
      ),
    })),

  addReframing: (reframing) =>
    set((state) => ({
      reframings: [...state.reframings, reframing].slice(-5), // 最新5件を保持
    })),

  clearReframings: () =>
    set({ reframings: [] }),

  reset: () =>
    set(initialState),
}));
