"use client";

import { useEffect, useRef, useState } from "react";

interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

export function useWebSocket(url: string, token?: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;

    // Get API URL from environment or default
    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    // Convert HTTP to WebSocket protocol
    const wsProtocol = API_URL.startsWith("https") ? "wss" : "ws";
    const wsHost = API_URL.replace(/^https?:\/\//, "").replace(/\/$/, "");

    // Build WebSocket URL with token as query param
    const wsUrl = token
      ? `${wsProtocol}://${wsHost}${url}?token=${token}`
      : `${wsProtocol}://${wsHost}${url}`;

    const connect = () => {
      try {
        wsRef.current = new WebSocket(wsUrl);

        wsRef.current.onopen = () => {
          setIsConnected(true);

          // Clear any pending reconnect
          if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = null;
          }
        };

        wsRef.current.onclose = (event) => {
          setIsConnected(false);

          // Auto-reconnect after 3 seconds if not a normal close
          if (event.code !== 1000) {
            reconnectTimeoutRef.current = setTimeout(() => {
              connect();
            }, 3000);
          }
        };

        wsRef.current.onerror = (error) => {
          console.error("WebSocket error:", error);
        };

        wsRef.current.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            setLastMessage(message);
            setMessages((prev) => [...prev, message]);
          } catch (error) {
            console.error("Failed to parse WebSocket message:", error);
          }
        };
      } catch (error) {
        console.error("Failed to create WebSocket connection:", error);
      }
    };

    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [url, token]);

  const sendMessage = (message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  };

  const sendPing = () => {
    sendMessage("ping");
  };

  return {
    isConnected,
    lastMessage,
    messages,
    sendMessage,
    sendPing,
  };
}
