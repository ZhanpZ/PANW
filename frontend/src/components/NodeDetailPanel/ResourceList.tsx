import type { Resource } from "../../types";

interface Props {
  resources: Resource[];
}

export function ResourceList({ resources }: Props) {
  const free = resources.filter((r) => r.resource_type === "free");
  const paid = resources.filter((r) => r.resource_type === "paid");

  const Section = ({ title, items, accent }: { title: string; items: Resource[]; accent: string }) => (
    <div className="mb-4">
      <p className={`text-[10px] font-semibold uppercase tracking-widest mb-2 ${accent}`}>
        {title}
      </p>
      <ul className="space-y-2">
        {items.map((r) => (
          <li key={r.id}>
            {r.url ? (
              <a
                href={r.url}
                target="_blank"
                rel="noopener noreferrer"
                className="group flex items-start gap-2 text-[13px] text-zinc-700
                  hover:text-orange-500 transition-colors"
              >
                <svg className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-zinc-300 group-hover:text-orange-500 transition-colors"
                  fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round"
                    d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                </svg>
                <span>
                  {r.title}
                  {r.platform && (
                    <span className="text-zinc-400 ml-1 text-[11px]">— {r.platform}</span>
                  )}
                </span>
              </a>
            ) : (
              <span className="flex items-start gap-2 text-[13px] text-zinc-600">
                <svg className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-zinc-300"
                  fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
                </svg>
                <span>
                  {r.title}
                  {r.platform && (
                    <span className="text-zinc-400 ml-1 text-[11px]">— {r.platform}</span>
                  )}
                </span>
              </span>
            )}
          </li>
        ))}
      </ul>
    </div>
  );

  return (
    <div>
      {free.length > 0 && <Section title="Free" items={free} accent="text-emerald-600" />}
      {paid.length > 0 && <Section title="Paid" items={paid} accent="text-amber-600" />}
      {resources.length === 0 && (
        <p className="text-[13px] text-zinc-400">No resources listed.</p>
      )}
    </div>
  );
}
