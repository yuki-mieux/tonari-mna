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
  const isConnectingRef = useRef(false);

  // コールバックをrefで保持して依存配列の問題を回避
  const optionsRef = useRef(options);
  optionsRef.current = options;

  const getWebSocketUrl = useCallback((sid: string) => {
    const baseUrl = import.meta.env.VITE_WS_URL || window.location.origin.replace('http', 'ws');
    return `${baseUrl}/api/mna/sessions/${sid}/ws`;
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = undefined;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    isConnectingRef.current = false;
    setStatus('disconnected');
  }, []);

  const connect = useCallback(() => {
    if (!sessionId) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    if (isConnectingRef.current) return;

    isConnectingRef.current = true;
    setStatus('connecting');

    const ws = new WebSocket(getWebSocketUrl(sessionId));

    ws.onopen = () => {
      isConnectingRef.current = false;
      setStatus('connected');
      reconnectCountRef.current = 0;
      optionsRef.current.onOpen?.();
    };

    ws.onclose = (event) => {
      isConnectingRef.current = false;
      wsRef.current = null;
      setStatus('disconnected');
      optionsRef.current.onClose?.();

      // セッションが見つからない場合（4004）は再接続しない
      if (event.code === 4004) {
        console.warn('Session not found, not reconnecting');
        return;
      }

      // 自動再接続
      if (reconnectCountRef.current < reconnectAttempts) {
        reconnectCountRef.current += 1;
        reconnectTimeoutRef.current = setTimeout(() => {
          if (sessionId) {
            connect();
          }
        }, reconnectInterval);
      }
    };

    ws.onerror = (event) => {
      isConnectingRef.current = false;
      setStatus('error');
      optionsRef.current.onError?.(event);
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WSServerMessage;
        optionsRef.current.onMessage?.(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    wsRef.current = ws;
  }, [sessionId, getWebSocketUrl, reconnectAttempts, reconnectInterval]);

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
      reconnectCountRef.current = 0;
      connect();
    }

    return () => {
      disconnect();
    };
  }, [sessionId]); // connect/disconnectを依存配列から除外

  return {
    status,
    send,
    connect,
    disconnect,
  };
}
