import { useUiStore } from "../../store/uiStore";

const TYPE_STYLES = {
  success: "bg-green-600",
  error: "bg-red-600",
  info: "bg-gray-700",
};

export function NotificationToast() {
  const { toasts, removeToast } = useUiStore();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg text-white text-sm
            min-w-[220px] max-w-sm animate-fade-in ${TYPE_STYLES[t.type]}`}
        >
          <span className="flex-1">{t.message}</span>
          <button
            onClick={() => removeToast(t.id)}
            className="opacity-70 hover:opacity-100 text-lg leading-none"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
}
