import { useEffect, useMemo, useState } from "react";
import { getTasksForBoard, updateTaskStatus, Task } from "@/lib/api";

type Props = {
  sprintId: number | null;
};

const STATUS_COLUMNS: { key: string; label: string }[] = [
  { key: "todo", label: "Planlandı" },
  { key: "ready_for_dev", label: "Hazır" },
  { key: "in_progress", label: "Devam Ediyor" },
  { key: "blocked", label: "Engelli" },
  { key: "done", label: "Bitti" },
];

export function SprintTaskBoard({ sprintId }: Props) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<number | null>(null);

  const load = () => {
    if (!sprintId) return;
    setLoading(true);
    setError(null);
    getTasksForBoard(sprintId)
      .then(setTasks)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (!sprintId) {
      setTasks([]);
      return;
    }
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sprintId]);

  const grouped = useMemo(() => {
    const map: Record<string, Task[]> = {};
    STATUS_COLUMNS.forEach((c) => (map[c.key] = []));
    tasks.forEach((t) => {
      const bucket = map[t.status || "todo"];
      if (bucket) bucket.push(t);
    });
    return map;
  }, [tasks]);

  const handleStatusChange = (taskId: number, status: string) => {
    setUpdatingId(taskId);
    updateTaskStatus(taskId, status)
      .then((updated) => {
        setTasks((prev) => prev.map((t) => (t.id === taskId ? { ...t, ...updated } : t)));
      })
      .catch((err) => setError(err.message))
      .finally(() => setUpdatingId(null));
  };

  if (!sprintId) {
    return <div className="text-sm text-slate-300">Önce sprint seçin.</div>;
  }

  return (
    <div className="grid grid-cols-1 gap-4">
      <div className="flex items-center justify-between">
        <div className="text-sm font-semibold text-slate-200">Sprint Task Panosu</div>
        <button
          onClick={load}
          className="rounded bg-slate-700 px-3 py-1 text-xs text-slate-100 hover:bg-slate-600"
        >
          Yenile
        </button>
      </div>
      {error && (
        <div className="rounded border border-red-500 bg-red-500/10 p-3 text-sm text-red-200">
          {error}
        </div>
      )}
      {loading ? (
        <div className="text-sm text-slate-300">Task’ler yükleniyor...</div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-5">
          {STATUS_COLUMNS.map((col) => (
            <div key={col.key} className="rounded border border-slate-700 bg-slate-800/40">
              <div className="border-b border-slate-700 px-3 py-2 text-xs font-semibold uppercase text-slate-200">
                {col.label}
              </div>
              <div className="p-2 space-y-2">
                {grouped[col.key]?.map((t) => (
                  <div key={t.id} className="rounded border border-slate-700 bg-slate-900 p-2 text-sm">
                    <div className="font-semibold text-slate-100">{t.title}</div>
                    <div className="text-xs text-slate-400">Epic: {t.epic_name || "–"}</div>
                    {t.estimate_sp !== undefined && t.estimate_sp !== null && (
                      <div className="text-xs text-slate-400">SP: {t.estimate_sp}</div>
                    )}
                    <div className="mt-2">
                      <label className="text-xs text-slate-400">Durum</label>
                      <select
                        value={t.status}
                        onChange={(e) => handleStatusChange(t.id, e.target.value)}
                        disabled={updatingId === t.id}
                        className="mt-1 w-full rounded border border-slate-700 bg-slate-800 p-1 text-xs text-slate-100"
                      >
                        {STATUS_COLUMNS.map((s) => (
                          <option key={s.key} value={s.key}>
                            {s.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                ))}
                {!grouped[col.key]?.length && (
                  <div className="text-xs text-slate-500">Bu statüde task yok.</div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
