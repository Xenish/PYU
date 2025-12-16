"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Job,
  createTaskPipelineJob,
  getJob,
  getJobs,
  cancelJob,
  runNextJob,
} from "@/lib/api";

type Props = {
  projectId: number | null;
  sprintId: number | null;
};

export function JobConsole({ projectId, sprintId }: Props) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!projectId) return;
    getJobs(projectId)
      .then((res) => {
        setJobs(res);
        setError(null);
      })
      .catch((err) => setError(err.message));
  }, [projectId]);

  useEffect(() => {
    if (!selectedJobId) return;
    const interval = setInterval(() => {
      getJob(selectedJobId)
        .then((job) => {
          setJobs((prev) => prev.map((j) => (j.id === job.id ? job : j)));
        })
        .catch(() => {});
    }, 3000);
    return () => clearInterval(interval);
  }, [selectedJobId]);

  const selectedJob = useMemo(
    () => jobs.find((j) => j.id === selectedJobId) || null,
    [jobs, selectedJobId]
  );

  async function handleRun() {
    if (!projectId || !sprintId) return;
    setError(null);
    setLoading(true);
    try {
      const job = await createTaskPipelineJob(projectId, sprintId);
      setJobs((prev) => [job, ...prev]);
      setSelectedJobId(job.id);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleCancel(id: number) {
    try {
      const job = await cancelJob(id);
      setJobs((prev) => prev.map((j) => (j.id === id ? job : j)));
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function handleRunNext() {
    try {
      const job = await runNextJob();
      if (job) {
        setJobs((prev) => prev.map((j) => (j.id === job.id ? job : j)));
        setSelectedJobId(job.id);
      }
    } catch (err: any) {
      setError(err.message);
    }
  }

  return (
    <div className="rounded border border-slate-800 bg-slate-900 p-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h2 className="text-sm font-semibold">Task Pipeline İşleri</h2>
          <p className="text-xs text-slate-400">Seçili sprint için pipeline işleri oluşturun ve izleyin.</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleRun}
            disabled={!projectId || !sprintId || loading}
            className="rounded bg-emerald-600 px-3 py-2 text-xs font-semibold disabled:opacity-50"
          >
            Pipeline çalıştır
          </button>
          <button
            onClick={handleRunNext}
            className="rounded bg-slate-700 px-3 py-2 text-xs font-semibold"
          >
            Sıradaki işi çalıştır
          </button>
        </div>
      </div>
      {error && (
        <div className="mb-3 rounded border border-red-500 bg-red-500/10 p-2 text-xs text-red-200">
          {error}
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="text-xs uppercase text-slate-400">
            <tr>
              <th className="px-2 py-1">Tip</th>
              <th className="px-2 py-1">Durum</th>
              <th className="px-2 py-1">İlerleme</th>
              <th className="px-2 py-1">Adım</th>
              <th className="px-2 py-1">Oluşturuldu</th>
              <th className="px-2 py-1">İşlemler</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((job) => (
              <tr
                key={job.id}
                className={`border-t border-slate-800 cursor-pointer ${
                  selectedJobId === job.id ? "bg-slate-800/50" : ""
                }`}
                onClick={() => setSelectedJobId(job.id)}
              >
                <td className="px-2 py-2">{job.type}</td>
                <td className="px-2 py-2 capitalize">{job.status}</td>
                <td className="px-2 py-2">
                  {job.progress_pct ?? 0}%
                  <div className="h-1 bg-slate-800 rounded mt-1">
                    <div
                      className="h-1 rounded bg-emerald-500"
                      style={{ width: `${job.progress_pct ?? 0}%` }}
                    />
                  </div>
                </td>
                <td className="px-2 py-2">{job.current_step || "-"}</td>
                <td className="px-2 py-2 text-xs text-slate-400">
                  {job.created_at ? new Date(job.created_at).toLocaleString() : "-"}
                </td>
                <td className="px-2 py-2 text-xs">
                  {job.status === "running" && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCancel(job.id);
                      }}
                      className="rounded bg-red-600 px-2 py-1 text-[11px]"
                    >
                      İptal
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {jobs.length === 0 && (
          <p className="text-xs text-slate-500 mt-3">Bu proje için henüz iş yok.</p>
        )}
      </div>
      {selectedJob && (
        <div className="mt-3 rounded border border-slate-800 bg-slate-800/50 p-3 text-sm">
          <div className="flex justify-between">
            <div>
              <div className="font-semibold">İş #{selectedJob.id}</div>
              <div className="text-xs text-slate-400">
                {selectedJob.status} – adım: {selectedJob.current_step || "-"}
              </div>
            </div>
            {selectedJob.error_message && (
              <div className="text-xs text-red-300 max-w-md text-right">
                {selectedJob.error_message}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
