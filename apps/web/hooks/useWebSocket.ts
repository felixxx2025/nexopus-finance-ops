"use client";

import { useEffect, useRef, useState } from "react";

interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

export function useWebSocket(url: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const wsUrl = url.startsWith("ws://") || url.startsWith("wss://")
      ? url
      : `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}${url}`;

    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      setIsConnected(true);
      console.log("WebSocket connected");
    };

    wsRef.current.onclose = () => {
      setIsConnected(false);
      console.log("WebSocket disconnected");
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

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [url]);

  const sendMessage = (message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  };

  return {
    isConnected,
    lastMessage,
    messages,
    sendMessage,
  };
}
