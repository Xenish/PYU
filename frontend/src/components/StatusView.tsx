import { useEffect, useState } from "react";
import {
  getProjectDiagnostics,
  getStatusOverview,
  ProjectDiagnostics,
  StatusOverview,
} from "@/lib/api";

type Props = {
  projectId: number | null;
};

export function StatusView({ projectId }: Props) {
  const [system, setSystem] = useState<StatusOverview | null>(null);
  const [projectDiag, setProjectDiag] = useState<ProjectDiagnostics | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    setError(null);
    getStatusOverview()
      .then(setSystem)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
    if (projectId) {
      getProjectDiagnostics(projectId)
        .then(setProjectDiag)
        .catch((err) => setError(err.message));
    } else {
      setProjectDiag(null);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  return (
    <div className="grid grid-cols-1 gap-4">
      <div className="flex items-center justify-between">
        <div className="text-sm font-semibold text-slate-200">Durum / Yönetim</div>
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

      {loading && <div className="text-sm text-slate-300">Yükleniyor...</div>}

      {system && (
        <div className="rounded border border-slate-700 bg-slate-800/60 p-3 text-sm text-slate-200">
          <div className="font-semibold mb-2">Sistem Durumu</div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <StatusCard label="Projeler" value={system.projects_count} />
            <StatusCard
              label="İşler"
              value={`kuyruk:${system.jobs?.queued || 0} / çalışan:${system.jobs?.running || 0} / tamam:${system.jobs?.completed || 0} / hata:${system.jobs?.failed || 0}`}
            />
            <StatusCard label="Bugünkü LLM Çağrısı" value={system.llm_calls_today} />
            <StatusCard label="LLM Günlük Kota" value={system.llm_quota_limit ?? "n/a"} />
          </div>
          <div className="mt-2 text-xs text-slate-400">
            Metrikler: <a className="underline" href="/metrics" target="_blank" rel="noreferrer">/metrics</a>
          </div>
        </div>
      )}

      {projectDiag && (
        <div className="rounded border border-slate-700 bg-slate-800/60 p-3 text-sm text-slate-200">
          <div className="font-semibold mb-2">Proje Diagnostiği</div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            <StatusCard label="Epikler" value={projectDiag.epic_count} />
            <StatusCard label="Sprintler" value={projectDiag.sprint_count} />
            <StatusCard
              label="Task'ler"
              value={`yapılacak:${projectDiag.task_count?.todo || 0} / hazır:${projectDiag.task_count?.ready_for_dev || 0} / devam:${projectDiag.task_count?.in_progress || 0} / bitti:${projectDiag.task_count?.done || 0}`}
            />
          </div>
          <div className="mt-3 text-xs text-slate-300">
            Son sihirbaz çalıştırma: {projectDiag.last_wizard_run_at || "yok"}
            <br />
            Son pipeline işi:{" "}
            {projectDiag.last_task_pipeline_job
              ? `${projectDiag.last_task_pipeline_job.status} (id ${projectDiag.last_task_pipeline_job.job_id})`
              : "yok"}
          </div>
        </div>
      )}
    </div>
  );
}

function StatusCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded border border-slate-700 bg-slate-900/60 p-2">
      <div className="text-xs text-slate-400">{label}</div>
      <div className="text-base font-semibold text-slate-100">{value}</div>
    </div>
  );
}
