import { useEffect, useState } from "react";
import { Task, getReadyForDevTasks } from "@/lib/api";

type Props = {
  sprintId: number | null;
};

export function ReadyTasksList({ sprintId }: Props) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sprintId) {
      setTasks([]);
      return;
    }
    setLoading(true);
    getReadyForDevTasks(sprintId)
      .then((res) => {
        setTasks(res);
        setError(null);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [sprintId]);

  return (
    <div className="rounded border border-slate-800 bg-slate-900 p-4">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-sm font-semibold">Geliştirmeye Hazır Task&apos;ler</h2>
        {loading && <span className="text-xs text-slate-400">yükleniyor...</span>}
      </div>
      {error && (
        <div className="mb-2 rounded border border-red-500 bg-red-500/10 p-2 text-xs text-red-200">
          {error}
        </div>
      )}
      {tasks.length === 0 && !loading ? (
        <p className="text-xs text-slate-500">
          {sprintId ? "Henüz hazır task yok." : "Task görmek için sprint seçin."}
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="text-xs uppercase text-slate-400">
              <tr>
                <th className="px-2 py-1">Başlık</th>
                <th className="px-2 py-1">Tahmin</th>
                <th className="px-2 py-1">DoD</th>
                <th className="px-2 py-1">NFR</th>
                <th className="px-2 py-1">Üst Görev</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((t) => (
                <tr key={t.id} className="border-t border-slate-800">
                  <td className="px-2 py-2">{t.title}</td>
                  <td className="px-2 py-2">{t.estimate_sp ?? "-"}</td>
                  <td className="px-2 py-2">{t.dod_focus ?? "-"}</td>
                  <td className="px-2 py-2">{t.nfr_focus?.join(", ") ?? "-"}</td>
                  <td className="px-2 py-2">{t.parent_task_id ?? "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
