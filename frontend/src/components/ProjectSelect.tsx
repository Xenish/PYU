type Props = {
  projects: { id: number; name: string }[];
  selectedProject: number | null;
  onSelect: (id: number) => void;
  loading?: boolean;
  onAdd?: () => void;
  onDelete?: (id: number) => void;
  draftName?: string | null;
  onDraftSelect?: () => void;
  draftSelected?: boolean;
};

export function ProjectSelect({
  projects,
  selectedProject,
  onSelect,
  loading,
  onAdd,
  onDelete,
  draftName,
  onDraftSelect,
  draftSelected,
}: Props) {
  return (
    <div className="rounded-2xl border border-slate-800/70 bg-slate-900/70 p-4 space-y-3 shadow-lg backdrop-blur">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-semibold tracking-wide text-slate-100">Projelerin</h2>
          {loading && <span className="text-xs text-slate-400">yükleniyor...</span>}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onAdd?.()}
            className="h-8 w-8 rounded-full border border-emerald-500/60 bg-emerald-600/20 text-emerald-100 hover:bg-emerald-600/30 text-base leading-none"
            aria-label="Proje ekle"
          >
            +
          </button>
        </div>
      </div>
      <div className="rounded-2xl bg-slate-800/0 border border-slate-800/40 max-h-64 overflow-auto shadow-inner backdrop-blur">
        {projects.length === 0 && !loading ? (
          <p className="text-xs text-slate-400 p-3">Henüz proje yok.</p>
        ) : (
          <ul className="divide-y divide-slate-800/80">
            {projects.map((p) => {
              const active = selectedProject === p.id;
              return (
                <li key={p.id} className="group">
                  <div
                    className={`flex items-center justify-between px-3 py-2 text-sm transition-colors ${
                      active
                        ? "bg-gradient-to-r from-emerald-600/30 via-emerald-500/10 to-slate-800/60 text-emerald-50 border-l-2 border-emerald-400"
                        : "hover:bg-slate-800/70 text-slate-100"
                    }`}
                  >
                    <button onClick={() => onSelect(p.id)} className="flex-1 text-left">
                      <span className="inline-flex items-center gap-2">
                        <span
                          className={`h-2 w-2 rounded-full ${
                            active ? "bg-emerald-300 shadow-[0_0_0_4px_rgba(16,185,129,0.2)]" : "bg-slate-500"
                          }`}
                        />
                        {p.name}
                      </span>
                    </button>
                    <button
                      onClick={() => onDelete?.(p.id)}
                      aria-label="Proje sil"
                      className="ml-2 inline-flex h-8 w-8 items-center justify-center rounded-full border border-red-500/60 bg-red-600/10 text-red-200 opacity-0 transition-all duration-200 hover:bg-red-600/30 hover:border-red-400 group-hover:opacity-100"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="h-4 w-4">
                        <path
                          fillRule="evenodd"
                          d="M9 3.75A1.75 1.75 0 0 1 10.75 2h2.5A1.75 1.75 0 0 1 15 3.75V5h4a.75.75 0 0 1 0 1.5h-.76l-.74 12.17A2.25 2.25 0 0 1 15.26 21H8.74a2.25 2.25 0 0 1-2.24-2.33L5.76 6.5H5a.75.75 0 0 1 0-1.5h4V3.75ZM13.5 5v-.25a.25.25 0 0 0-.25-.25h-2.5a.25.25 0 0 0-.25.25V5h3Zm-4.99 1.5.73 12.07a.75.75 0 0 0 .75.68h6.52a.75.75 0 0 0 .75-.68L17.99 6.5H8.51Zm2.24 2.75a.75.75 0 0 1 .75.7l.25 6.5a.75.75 0 0 1-1.5.06l-.25-6.5a.75.75 0 0 1 .7-.76Zm3.5 0a.75.75 0 0 1 .7.76l-.25 6.5a.75.75 0 0 1-1.5-.06l.25-6.5a.75.75 0 0 1 .8-.7Z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </button>
                  </div>
                </li>
              );
            })}
            {draftName && (
              <li>
                <button
                  onClick={onDraftSelect}
                  className={`w-full px-3 py-2 text-sm italic flex items-center gap-2 rounded transition-colors ${
                    draftSelected
                      ? "bg-gradient-to-r from-emerald-600/20 via-emerald-500/10 to-slate-800/50 text-emerald-100 border-l-2 border-emerald-400"
                      : "text-slate-400 hover:bg-slate-800/50"
                  }`}
                >
                  <span
                    className={`h-2 w-2 rounded-full ${
                      draftSelected ? "bg-emerald-300 shadow-[0_0_0_4px_rgba(16,185,129,0.2)]" : "bg-slate-600/60"
                    }`}
                  />
                  {draftName}
                </button>
              </li>
            )}
          </ul>
        )}
      </div>
    </div>
  );
}
