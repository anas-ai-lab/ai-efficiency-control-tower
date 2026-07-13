import { AlertCircle } from "lucide-react";

// Einheitliche Fehlerkomponente fuer alle Admin-Aktionen (V4.1-S5, Task D).
// Rendert den deutschen detail-Text des Backends (via actions.ts auf Deutsch
// aufgeloest) in einem konsistenten destructive-Kasten -- nie einen rohen
// Status. message === null -> nichts rendern (kein leerer Kasten).
export function ActionError({
  message,
  className = "",
}: {
  message: string | null;
  className?: string;
}) {
  if (message === null || message.length === 0) return null;
  return (
    <div
      role="alert"
      className={`flex items-start gap-2 rounded-lg border border-destructive/25 bg-destructive/5 px-4 py-3 text-sm text-destructive ${className}`}
    >
      <AlertCircle className="mt-0.5 size-4 shrink-0" aria-hidden />
      <span className="leading-relaxed">{message}</span>
    </div>
  );
}

export default ActionError;
