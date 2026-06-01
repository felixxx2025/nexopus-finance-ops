import { Button } from "@/components/ui/button";
import { FileText, Inbox, AlertCircle } from "lucide-react";

interface EmptyStateProps {
  icon?: "inbox" | "file" | "alert";
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export function EmptyState({ icon = "inbox", title, description, action }: EmptyStateProps) {
  const Icon = {
    inbox: Inbox,
    file: FileText,
    alert: AlertCircle,
  }[icon];

  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted">
        <Icon className="h-8 w-8 text-muted-foreground" />
      </div>
      <h3 className="mt-4 text-lg font-semibold">{title}</h3>
      {description && (
        <p className="mt-2 text-sm text-muted-foreground max-w-sm">{description}</p>
      )}
      {action && (
        <Button onClick={action.onClick} className="mt-4">
          {action.label}
        </Button>
      )}
    </div>
  );
}
