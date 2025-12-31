/**
 * TONARI for M&A - WebSocket型定義
 */
import type { ExtractionField, ReframingSuggestion, Suggestion, Utterance } from './api';

// ========================
// メッセージタイプ
// ========================

export type WSMessageType =
  // クライアント → サーバー
  | 'audio_chunk'
  | 'pin_utterance'
  | 'dismiss_suggestion'
  | 'use_suggestion'
  | 'update_extraction'
  | 'set_layer'
  | 'transcript'
  // サーバー → クライアント
  | 'extraction_update'
  | 'analysis_update'
  | 'suggestion'
  | 'reframing'
  | 'error'
  | 'session_status';

// ========================
// クライアント → サーバー
// ========================

export interface WSTranscriptMessage {
  type: 'transcript';
  text: string;
  speaker: 'user' | 'customer';
  is_final: boolean;
}

export interface WSPinUtteranceMessage {
  type: 'pin_utterance';
  utterance_id: string;
  note?: string;
}

export interface WSDismissSuggestionMessage {
  type: 'dismiss_suggestion';
  suggestion_id: string;
}

export interface WSUseSuggestionMessage {
  type: 'use_suggestion';
  suggestion_id: string;
}

export interface WSUpdateExtractionMessage {
  type: 'update_extraction';
  field_key: string;
  value: string;
}

export interface WSSetLayerMessage {
  type: 'set_layer';
  layer: 'surface' | 'structure' | 'essence' | 'exit';
}

export type WSClientMessage =
  | WSTranscriptMessage
  | WSPinUtteranceMessage
  | WSDismissSuggestionMessage
  | WSUseSuggestionMessage
  | WSUpdateExtractionMessage
  | WSSetLayerMessage;

// ========================
// サーバー → クライアント
// ========================

export interface WSTranscriptResponse {
  type: 'transcript';
  data: {
    utterance: Utterance;
    is_final: boolean;
  };
  timestamp: string;
}

export interface WSExtractionUpdateResponse {
  type: 'extraction_update';
  data: {
    field_key: string;
    field: ExtractionField;
  };
  timestamp: string;
}

export interface WSSuggestionResponse {
  type: 'suggestion';
  data: Suggestion;
  timestamp: string;
}

export interface WSReframingResponse {
  type: 'reframing';
  data: ReframingSuggestion;
  timestamp: string;
}

export interface WSErrorResponse {
  type: 'error';
  data: {
    message: string;
    code?: string;
  };
  timestamp: string;
}

export interface WSSessionStatusResponse {
  type: 'session_status';
  data: {
    status: 'active' | 'completed';
  };
  timestamp: string;
}

export type WSServerMessage =
  | WSTranscriptResponse
  | WSExtractionUpdateResponse
  | WSSuggestionResponse
  | WSReframingResponse
  | WSErrorResponse
  | WSSessionStatusResponse;
