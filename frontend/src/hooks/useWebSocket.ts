/**
 * TONARI for M&A - WebSocket管理フック
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import type { WSClientMessage, WSServerMessage } from '../types/websocket';

type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

interface UseWebSocketOptions {
  onMessage?: (message: WSServerMessage) => void;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
  reconnectAttempts?: number;
  reconnectInterval?: number;
}

interface UseWebSocketReturn {
  status: ConnectionStatus;
  send: (message: WSClientMessage) => void;
  connect: () => void;
  disconnect: () => void;
}

/**
 * WebSocket接続を管理するフック
 */
export function useWebSocket(
  sessionId: string | null,
  options: UseWebSocketOptions = {}
): UseWebSocketReturn {
  const {
    onMessage,
    onOpen,
    onClose,
    onError,
    reconnectAttempts = 3,
    reconnectInterval = 3000,
  } = options;

  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const getWebSocketUrl = useCallback(() => {
    const baseUrl = import.meta.env.VITE_WS_URL || window.location.origin.replace('http', 'ws');
    return `${baseUrl}/api/mna/sessions/${sessionId}/ws`;
  }, [sessionId]);

  const connect = useCallback(() => {
    if (!sessionId) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setStatus('connecting');

    const ws = new WebSocket(getWebSocketUrl());

    ws.onopen = () => {
      setStatus('connected');
      reconnectCountRef.current = 0;
      onOpen?.();
    };

    ws.onclose = () => {
      setStatus('disconnected');
      onClose?.();

      // 自動再接続
      if (reconnectCountRef.current < reconnectAttempts) {
        reconnectCountRef.current += 1;
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, reconnectInterval);
      }
    };

    ws.onerror = (event) => {
      setStatus('error');
      onError?.(event);
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WSServerMessage;
        onMessage?.(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    wsRef.current = ws;
  }, [sessionId, getWebSocketUrl, onMessage, onOpen, onClose, onError, reconnectAttempts, reconnectInterval]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setStatus('disconnected');
  }, []);

  const send = useCallback((message: WSClientMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  // セッションIDが変わったら再接続
  useEffect(() => {
    if (sessionId) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [sessionId, connect, disconnect]);

  return {
    status,
    send,
    connect,
    disconnect,
  };
}
