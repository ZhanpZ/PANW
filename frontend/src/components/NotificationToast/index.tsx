import { useUiStore } from "../../store/uiStore";

const TYPE_CONFIG = {
  success: {
    bar: "bg-emerald-500",
    icon: (
      <svg className="w-4 h-4 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
      </svg>
    ),
  },
  error: {
    bar: "bg-rose-500",
    icon: (
      <svg className="w-4 h-4 text-rose-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
      </svg>
    ),
  },
  info: {
    bar: "bg-sky-500",
    icon: (
      <svg className="w-4 h-4 text-sky-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
};

export function NotificationToast() {
  const { toasts, removeToast } = useUiStore();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-5 right-5 z-[100] flex flex-col gap-2">
      {toasts.map((t) => {
        const cfg = TYPE_CONFIG[t.type];
        return (
          <div
            key={t.id}
            className="flex items-center gap-3 bg-white border border-zinc-200 rounded-xl
              shadow-lg shadow-black/8 px-4 py-3 min-w-[240px] max-w-sm overflow-hidden
              relative"
          >
            {/* Left accent bar */}
            <span className={`absolute left-0 top-2 bottom-2 w-0.5 rounded-full ${cfg.bar}`} />
            {/* Icon */}
            <span className="flex-shrink-0 ml-2">{cfg.icon}</span>
            <span className="flex-1 text-[13px] text-zinc-700 leading-snug">{t.message}</span>
            <button
              onClick={() => removeToast(t.id)}
              className="flex-shrink-0 text-zinc-400 hover:text-zinc-700 transition-colors"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        );
      })}
    </div>
  );
}
