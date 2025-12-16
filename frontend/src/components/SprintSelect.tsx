type Props = {
  sprints: { id: number; name: string; index: number }[];
  selectedSprint: number | null;
  onSelect: (id: number) => void;
  loading?: boolean;
  disabled?: boolean;
};

export function SprintSelect({
  sprints,
  selectedSprint,
  onSelect,
  loading,
  disabled,
}: Props) {
  return (
    <div className="rounded border border-slate-800 bg-slate-900 p-4">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-sm font-semibold">Sprint</h2>
        {loading && <span className="text-xs text-slate-400">yükleniyor...</span>}
      </div>
      <select
        className="w-full rounded bg-slate-800 border border-slate-700 p-2 text-sm"
        value={selectedSprint ?? ""}
        onChange={(e) => onSelect(Number(e.target.value))}
        disabled={disabled}
      >
        <option value="">{disabled ? "Önce proje seçin" : "Sprint seçin"}</option>
        {sprints.map((s) => (
          <option key={s.id} value={s.id}>
            Sprint {s.index}: {s.name}
          </option>
        ))}
      </select>
      {sprints.length === 0 && !loading && !disabled && (
        <p className="text-xs text-slate-500 mt-2">Sprint bulunamadı.</p>
      )}
    </div>
  );
}
