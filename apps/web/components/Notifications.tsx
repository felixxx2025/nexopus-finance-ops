"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useWebSocket } from "@/hooks/useWebSocket";
import { AlertTriangle, Bell, CheckCircle, Info, X } from "lucide-react";
import { useEffect, useState } from "react";

interface Notification {
  id: string;
  type: "info" | "success" | "warning" | "error";
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}

const NOTIFICATION_ICONS = {
  info: Info,
  success: CheckCircle,
  warning: AlertTriangle,
  error: AlertTriangle,
};

const NOTIFICATION_COLORS = {
  info: "bg-blue-900/40 text-blue-400 border-blue-700",
  success: "bg-green-900/40 text-green-400 border-green-700",
  warning: "bg-yellow-900/40 text-yellow-400 border-yellow-700",
  error: "bg-red-900/40 text-red-400 border-red-700",
};

export function Notifications() {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const unreadCount = notifications.filter((n) => !n.read).length;

  const { isConnected, lastMessage } = useWebSocket("/api/ws/notifications");

  useEffect(() => {
    if (lastMessage) {
      const newNotification: Notification = {
        id: Date.now().toString(),
        type: (lastMessage.type as "info" | "success" | "warning" | "error") || "info",
        title: lastMessage.data?.title || "Notificação",
        message: lastMessage.data?.message || "",
        timestamp: lastMessage.timestamp || new Date().toISOString(),
        read: false,
      };
      setNotifications((prev) => [newNotification, ...prev]);
    }
  }, [lastMessage]);

  const markAsRead = (id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    );
  };

  const markAllAsRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  const removeNotification = (id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  };

  return (
    <div className="relative">
      <Button
        variant="ghost"
        size="icon"
        onClick={() => setIsOpen(!isOpen)}
        className="relative"
        aria-label={`Notificações ${unreadCount > 0 ? `(${unreadCount} não lidas)` : ''}`}
        aria-expanded={isOpen}
        aria-haspopup="true"
      >
        <Bell className="h-5 w-5" aria-hidden="true" />
        {unreadCount > 0 && (
          <Badge
            variant="destructive"
            className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 text-xs"
            aria-label={`${unreadCount} notificações não lidas`}
          >
            {unreadCount}
          </Badge>
        )}
      </Button>

      {isOpen && (
        <Card
          className="absolute right-0 top-12 w-96 bg-gray-900 border-gray-800 shadow-xl z-50"
          role="dialog"
          aria-label="Notificações"
          aria-modal="true"
        >
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-white font-semibold">Notificações</h3>
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1 text-xs text-gray-400">
                  <div
                    className={`w-2 h-2 rounded-full ${isConnected ? "bg-green-500" : "bg-red-500"
                      }`}
                    aria-hidden="true"
                  />
                  <span aria-live="polite">{isConnected ? "Conectado" : "Desconectado"}</span>
                </div>
                {unreadCount > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={markAllAsRead}
                    className="text-xs h-6"
                    aria-label="Marcar todas as notificações como lidas"
                  >
                    Marcar todas
                  </Button>
                )}
              </div>
            </div>

            <div className="space-y-2 max-h-96 overflow-y-auto" role="list" aria-label="Lista de notificações">
              {notifications.length === 0 ? (
                <p className="text-gray-400 text-sm text-center py-4" role="status">
                  Nenhuma notificação
                </p>
              ) : (
                notifications.map((notification) => {
                  const Icon = NOTIFICATION_ICONS[notification.type];
                  return (
                    <div
                      key={notification.id}
                      className={`p-3 rounded-lg border transition-colors ${notification.read
                        ? "bg-gray-800 border-gray-700 opacity-60"
                        : "bg-gray-800/80 border-gray-700"
                        }`}
                      role="listitem"
                      aria-label={`${notification.title}: ${notification.message}`}
                    >
                      <div className="flex items-start gap-3">
                        <Icon
                          className={`h-4 w-4 mt-0.5 ${NOTIFICATION_COLORS[notification.type].split(" ")[1]
                            }`}
                          aria-hidden="true"
                        />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-2">
                            <h4 className="text-white text-sm font-medium truncate">
                              {notification.title}
                            </h4>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => removeNotification(notification.id)}
                              className="h-4 w-4"
                              aria-label={`Remover notificação: ${notification.title}`}
                            >
                              <X className="h-3 w-3" aria-hidden="true" />
                            </Button>
                          </div>
                          <p className="text-gray-400 text-xs mt-1">
                            {notification.message}
                          </p>
                          <p className="text-gray-500 text-xs mt-2">
                            {new Date(notification.timestamp).toLocaleString("pt-BR")}
                          </p>
                        </div>
                      </div>
                      {!notification.read && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => markAsRead(notification.id)}
                          className="text-xs mt-2 w-full"
                          aria-label={`Marcar como lida: ${notification.title}`}
                        >
                          Marcar como lida
                        </Button>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
