import { useState, useEffect, useRef, useCallback } from 'react';
import { WS_BASE } from '../lib/api';

interface WSMessage {
    type: 'typing' | 'response' | 'error';
    content?: string;
    conversation_id?: string;
}

interface UseWebSocketResult {
    send: (message: string, conversation_id?: string) => void;
    lastMessage: WSMessage | null;
    isConnected: boolean;
    isTyping: boolean;
    conversationId: string | null;
}

/**
 * WebSocket hook for /ws/chat with auto-reconnect (exponential backoff).
 */
export function useWebSocket(): UseWebSocketResult {
    const wsRef = useRef<WebSocket | null>(null);
    const retryRef = useRef(0);
    const maxRetry = 30_000;

    const [isConnected, setIsConnected] = useState(false);
    const [isTyping, setIsTyping] = useState(false);
    const [lastMessage, setLastMessage] = useState<WSMessage | null>(null);
    const [conversationId, setConversationId] = useState<string | null>(null);

    const connect = useCallback(() => {
        const url = `${WS_BASE}/ws/chat`;
        const ws = new WebSocket(url);
        wsRef.current = ws;

        ws.onopen = () => {
            setIsConnected(true);
            retryRef.current = 0; // reset backoff
        };

        ws.onclose = () => {
            setIsConnected(false);
            // Exponential backoff reconnect
            const delay = Math.min(1000 * 2 ** retryRef.current, maxRetry);
            retryRef.current += 1;
            setTimeout(connect, delay);
        };

        ws.onerror = () => {
            ws.close();
        };

        ws.onmessage = (event) => {
            try {
                const msg: WSMessage = JSON.parse(event.data);

                if (msg.conversation_id) {
                    setConversationId(msg.conversation_id);
                }

                if (msg.type === 'typing') {
                    setIsTyping(true);
                } else {
                    setIsTyping(false);
                    setLastMessage(msg);
                }
            } catch {
                console.error('[ws] Failed to parse message');
            }
        };
    }, []);

    useEffect(() => {
        connect();
        return () => {
            wsRef.current?.close();
        };
    }, [connect]);

    const send = useCallback((message: string, conversation_id?: string) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
                message,
                conversation_id: conversation_id ?? conversationId,
            }));
            setIsTyping(true); // Optimistic typing indicator
        }
    }, [conversationId]);

    return { send, lastMessage, isConnected, isTyping, conversationId };
}
