import { useEffect, useState } from "react";
import {
  getPlanningOverview,
  PlanningOverview,
  generateEpics,
  estimateStoryPoints,
  generateCapacityPlan,
} from "@/lib/api";

type Props = {
  projectId: number | null;
};

export function PlanningView({ projectId }: Props) {
  const [overview, setOverview] = useState<PlanningOverview | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState<string | null>(null);

  const refreshOverview = () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    getPlanningOverview(projectId)
      .then(setOverview)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (!projectId) {
      setOverview(null);
      return;
    }
    refreshOverview();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  async function handleGenerateEpics() {
    if (!projectId) return;
    setGenerating("epics");
    setError(null);
    try {
      await generateEpics(projectId);
      refreshOverview();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setGenerating(null);
    }
  }

  async function handleEstimateSP() {
    if (!projectId) return;
    setGenerating("sp");
    setError(null);
    try {
      await estimateStoryPoints(projectId);
      refreshOverview();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setGenerating(null);
    }
  }

  async function handleGeneratePlan() {
    if (!projectId) return;
    setGenerating("plan");
    setError(null);
    try {
      await generateCapacityPlan(projectId, 3, 40); // 3 sprints, 40 SP capacity
      refreshOverview();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setGenerating(null);
    }
  }

  if (!projectId) {
    return <div className="text-sm text-slate-300">Önce bir proje seçin.</div>;
  }

  if (loading) {
    return <div className="text-sm text-slate-300">Plan yükleniyor...</div>;
  }

  if (error) {
    return (
      <div className="rounded border border-red-500 bg-red-500/10 p-3 text-sm text-red-200">
        Plan çekilirken hata: {error}
      </div>
    );
  }

  if (!overview) return null;

  const hasEpics = overview.epics.length > 0;
  const hasSprints = overview.sprints.length > 0;

  return (
    <div className="grid grid-cols-1 gap-6">
      {/* Action Buttons Section */}
      <div className="rounded border border-slate-700 bg-slate-800/60 p-4">
        <div className="mb-3">
          <div className="text-sm font-semibold text-slate-200">Planlama Üreticisi</div>
          <p className="text-xs text-slate-400 mt-1">
            Spec Wizard tamamlandıktan sonra sırayla: 1 → 2 → 3 çalıştırın
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={handleGenerateEpics}
            disabled={generating === "epics"}
            className="rounded bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {generating === "epics" ? "Oluşturuluyor..." : "1. Epic Oluştur"}
          </button>
          <button
            onClick={handleEstimateSP}
            disabled={generating === "sp" || !hasEpics}
            className="rounded bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {generating === "sp" ? "Tahmin ediliyor..." : "2. Story Point Tahmin Et"}
          </button>
          <button
            onClick={handleGeneratePlan}
            disabled={generating === "plan" || !hasEpics}
            className="rounded bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {generating === "plan" ? "Planlanıyor..." : "3. Sprint Planı Üret"}
          </button>
          <button
            onClick={refreshOverview}
            disabled={loading}
            className="rounded bg-slate-700 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-600 disabled:opacity-50"
          >
            {loading ? "Yenileniyor..." : "Yenile"}
          </button>
        </div>
        {hasEpics && !hasSprints && (
          <div className="mt-3 rounded border border-amber-500/50 bg-amber-500/10 p-2 text-xs text-amber-200">
            ✓ Epics oluşturuldu. Şimdi Story Points tahmin edip Sprint Plan oluşturabilirsiniz.
          </div>
        )}
        {hasSprints && (
          <div className="mt-3 rounded border border-emerald-500/50 bg-emerald-500/10 p-2 text-xs text-emerald-200">
            ✓ Planning tamamlandı! Artık Sprint dropdown&apos;ından sprint seçip task pipeline çalıştırabilirsiniz.
          </div>
        )}
      </div>

      <div>
        <div className="mb-2 text-sm font-semibold text-slate-200">Epikler</div>
        <div className="overflow-auto rounded border border-slate-700">
          <table className="min-w-full text-sm text-slate-200">
            <thead className="bg-slate-800/70">
              <tr>
                <th className="px-3 py-2 text-left">Ad</th>
                <th className="px-3 py-2 text-left">Kategori</th>
                <th className="px-3 py-2 text-left">SP</th>
                <th className="px-3 py-2 text-left">Sprintler</th>
                <th className="px-3 py-2 text-left">Bağlılıklar</th>
              </tr>
            </thead>
            <tbody>
              {overview.epics.map((e) => (
                <tr key={e.id} className="border-t border-slate-800">
                  <td className="px-3 py-2">{e.name}</td>
                  <td className="px-3 py-2">
                    <span className="rounded bg-slate-700 px-2 py-1 text-xs uppercase">
                      {e.category || "n/a"}
                    </span>
                  </td>
                  <td className="px-3 py-2">{e.story_points ?? "-"}</td>
                  <td className="px-3 py-2">{e.sprint_ids.join(", ") || "-"}</td>
                  <td className="px-3 py-2">
                    {e.dependencies.length ? e.dependencies.join(", ") : "-"}
                  </td>
                </tr>
              ))}
              {!overview.epics.length && (
                <tr>
                  <td colSpan={5} className="px-3 py-3 text-center text-slate-400">
                    Henüz epic yok.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div>
        <div className="mb-2 text-sm font-semibold text-slate-200">Sprintler</div>
        <div className="overflow-auto rounded border border-slate-700">
          <table className="min-w-full text-sm text-slate-200">
            <thead className="bg-slate-800/70">
              <tr>
                <th className="px-3 py-2 text-left">Ad</th>
                <th className="px-3 py-2 text-left">Kapasite</th>
                <th className="px-3 py-2 text-left">Atanan</th>
                <th className="px-3 py-2 text-left">Kalan</th>
                <th className="px-3 py-2 text-left">Epikler</th>
                <th className="px-3 py-2 text-left">Kalite</th>
              </tr>
            </thead>
            <tbody>
              {overview.sprints.map((s) => {
                const capacity = s.capacity_sp ?? 0;
                const allocated = s.allocated_sp ?? 0;
                const remaining = capacity ? capacity - allocated : null;
                return (
                  <tr key={s.id} className="border-t border-slate-800">
                    <td className="px-3 py-2">{s.name}</td>
                    <td className="px-3 py-2">{capacity || "-"}</td>
                    <td className="px-3 py-2">
                      <div className="flex items-center gap-2">
                        <span>{allocated}</span>
                        {capacity ? (
                          <div className="h-2 w-24 rounded bg-slate-800">
                            <div
                              className="h-2 rounded bg-emerald-500"
                              style={{
                                width: `${Math.min(100, Math.round((allocated / capacity) * 100))}%`,
                              }}
                            />
                          </div>
                        ) : null}
                      </div>
                    </td>
                    <td className="px-3 py-2">{remaining !== null ? remaining : "-"}</td>
                    <td className="px-3 py-2">{s.epic_ids.length ? s.epic_ids.join(", ") : "-"}</td>
                    <td className="px-3 py-2">
                      DoD: {s.quality_summary?.dod_count ?? 0} • NFR:{" "}
                      {(s.quality_summary?.nfr_categories || []).join(", ") || "-"}
                    </td>
                  </tr>
                );
              })}
              {!overview.sprints.length && (
                <tr>
                  <td colSpan={6} className="px-3 py-3 text-center text-slate-400">
                    Henüz sprint yok.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
