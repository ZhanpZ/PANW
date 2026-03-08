import type { Resource } from "../../types";

interface Props {
  resources: Resource[];
}

export function ResourceList({ resources }: Props) {
  const free = resources.filter((r) => r.resource_type === "free");
  const paid = resources.filter((r) => r.resource_type === "paid");

  const Section = ({ title, items }: { title: string; items: Resource[] }) => (
    <div className="mb-3">
      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
        {title}
      </p>
      <ul className="space-y-1">
        {items.map((r) => (
          <li key={r.id}>
            {r.url ? (
              <a
                href={r.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-600 hover:underline flex items-center gap-1"
              >
                <span className="truncate">{r.title}</span>
                {r.platform && (
                  <span className="text-xs text-gray-400 flex-shrink-0">— {r.platform}</span>
                )}
              </a>
            ) : (
              <span className="text-sm text-gray-700">
                {r.title}
                {r.platform && (
                  <span className="text-xs text-gray-400 ml-1">— {r.platform}</span>
                )}
              </span>
            )}
          </li>
        ))}
      </ul>
    </div>
  );

  return (
    <div>
      {free.length > 0 && <Section title="Free" items={free} />}
      {paid.length > 0 && <Section title="Paid" items={paid} />}
      {resources.length === 0 && (
        <p className="text-sm text-gray-400">No resources listed.</p>
      )}
    </div>
  );
}
