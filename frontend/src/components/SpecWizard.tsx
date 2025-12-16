"use client";

import { useEffect, useState } from "react";
import {
  StepStatus,
  WizardDetail,
  WizardSummary,
  approveStep,
  getWizardDetail,
  getWizardSummary,
  regenerateStep,
  runArchitecture,
  runFeatures,
  runObjective,
  runQuality,
  runTechStack,
  selectAllItems,
  deselectAllItems,
  toggleItemSelection,
} from "@/lib/api";

function PriorityBadge({
  priority,
  recommendation,
}: {
  priority?: number | null;
  recommendation?: string | null;
}) {
  const type = recommendation || "optional";
  const badges: Record<string, string> = {
    critical: "bg-red-500/20 text-red-200 border-red-500/50",
    recommended: "bg-emerald-500/20 text-emerald-200 border-emerald-500/50",
    optional: "bg-slate-500/20 text-slate-300 border-slate-500/50",
  };
  const icons: Record<string, string> = {
    critical: "⚠️",
    recommended: "⭐",
    optional: "💡",
  };

  return (
    <span className={`px-2 py-0.5 rounded text-[10px] border ${badges[type] || badges.optional}`}>
      {icons[type] || icons.optional} {(type || "optional").toUpperCase()}
      {priority ? ` • ${priority}/5` : ""}
    </span>
  );
}

function ItemFilters({ onFilterChange }: FilterProps) {
  const [filters, setFilters] = useState<FilterState>({
    recommendation: "all",
    category: "all",
    showSelected: false,
  });

  return (
    <div className="flex gap-2 mb-3 flex-wrap">
      <select
        value={filters.recommendation}
        onChange={(e) => {
          const newFilters = { ...filters, recommendation: e.target.value };
          setFilters(newFilters);
          onFilterChange(newFilters);
        }}
        className="text-xs bg-slate-800 border border-slate-700 rounded px-2 py-1"
      >
        <option value="all">Tüm Öneriler</option>
        <option value="critical">⚠️ Kritik</option>
        <option value="recommended">⭐ Önerilen</option>
        <option value="optional">💡 Opsiyonel</option>
      </select>

      <label className="flex items-center gap-1 text-xs text-slate-200">
        <input
          type="checkbox"
          checked={filters.showSelected}
          onChange={(e) => {
            const newFilters = { ...filters, showSelected: e.target.checked };
            setFilters(newFilters);
            onFilterChange(newFilters);
          }}
        />
        Sadece Seçilenleri Göster
      </label>
    </div>
  );
}

type ItemCardProps = {
  item: any;
  title: string;
  description?: string | null;
  onToggle: (id: number) => void;
  disabled: boolean;
  tags?: string[];
  advantages?: string[] | null;
  disadvantages?: string[] | null;
  subtitle?: string | null;
  onCompare?: (item: any) => void;
};

type QuickSelectionProps = {
  items: any[];
  onBulkSelect: (ids: number[], opts?: { preserveExisting?: boolean }) => void;
};

type FilterState = { recommendation: string; category: string; showSelected: boolean };
type FilterProps = { onFilterChange: (filters: FilterState) => void };

type CompareItem = { item: any; itemType: string };
type ValidationProps = { items: any[]; selectedIds: number[] };
type SummaryProps = { items: any[]; selectedIds: number[] };

function QuickSelectionBar({ items, onBulkSelect }: QuickSelectionProps) {
  const handleSmartSelect = () => {
    const smartSelection = items
      .filter((i) => ["critical", "recommended"].includes(i.recommendation_type))
      .map((i) => i.id);
    onBulkSelect(smartSelection, { preserveExisting: true });
  };

  const handleSelectCritical = () => {
    const critical = items.filter((i) => i.recommendation_type === "critical").map((i) => i.id);
    onBulkSelect(critical, { preserveExisting: true });
  };

  return (
    <div className="flex flex-wrap gap-2 mb-3">
      <button
        onClick={handleSmartSelect}
        className="rounded bg-emerald-600 px-3 py-1 text-xs font-semibold text-white hover:bg-emerald-500 disabled:opacity-50"
      >
        ⚡ Önerilenleri Seç
      </button>
      <button
        onClick={handleSelectCritical}
        className="rounded bg-amber-600 px-3 py-1 text-xs font-semibold text-white hover:bg-amber-500 disabled:opacity-50"
      >
        ⚠️ Kritik Olanları Seç
      </button>
      <button
        onClick={() => onBulkSelect(items.map((i) => i.id))}
        className="rounded bg-slate-700 px-3 py-1 text-xs font-semibold text-white hover:bg-slate-600 disabled:opacity-50"
      >
        Tümünü Seç
      </button>
    </div>
  );
}

function SelectionValidation({ items, selectedIds }: ValidationProps) {
  const selected = items.filter((i) => selectedIds.includes(i.id));
  const conflicts = selected.flatMap((item) => item.conflicts_with?.filter((id: number) => selectedIds.includes(id)) || []);
  const missingDeps = selected.flatMap((item) => item.requires?.filter((id: number) => !selectedIds.includes(id)) || []);
  const categoryViolations = selected.reduce((acc: any[], item) => {
    if (item.category_exclusive && item.category) {
      const sameCategory = selected.filter((i) => i.category === item.category && i.id !== item.id);
      if (sameCategory.length > 0) acc.push({ item, conflicts: sameCategory });
    }
    return acc;
  }, []);

  if (conflicts.length === 0 && missingDeps.length === 0 && categoryViolations.length === 0) {
    return (
      <div className="text-xs text-emerald-300 p-2 bg-emerald-500/10 rounded">
        ✓ Seçimleriniz uyumlu
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {conflicts.length > 0 && (
        <div className="text-xs text-red-300 p-2 bg-red-500/10 rounded border border-red-500/30">
          ⚠️ Çakışma: Bazı seçimler birbiriyle uyumsuz
        </div>
      )}
      {missingDeps.length > 0 && (
        <div className="text-xs text-amber-300 p-2 bg-amber-500/10 rounded border border-amber-500/30">
          ⚠️ Eksik bağımlılık: Bazı seçimler için gerekli öğeler seçilmemiş
        </div>
      )}
      {categoryViolations.length > 0 && (
        <div className="text-xs text-amber-300 p-2 bg-amber-500/10 rounded border border-amber-500/30">
          ⚠️ {categoryViolations[0].item.category} için birden fazla seçenek seçildi
        </div>
      )}
    </div>
  );
}

function SelectionSummary({ items, selectedIds }: SummaryProps) {
  const selected = items.filter((i) => selectedIds.includes(i.id));

  const stats = {
    total: selected.length,
    critical: selected.filter((i) => i.recommendation_type === "critical").length,
    recommended: selected.filter((i) => i.recommendation_type === "recommended").length,
    optional: selected.filter((i) => i.recommendation_type === "optional").length,
    categories: Array.from(new Set(selected.map((i) => i.category))).length,
  };

  const missing = items.filter(
    (i) => i.recommendation_type === "critical" && !selectedIds.includes(i.id)
  );

  return (
    <div className="bg-slate-800 rounded p-4 space-y-3 border border-slate-700">
      <h4 className="font-semibold text-slate-100">Seçim Özeti</h4>

      <div className="grid grid-cols-2 gap-2 text-sm text-slate-200">
        <div>Toplam: {stats.total}</div>
        <div>Kategori: {stats.categories}</div>
        <div className="text-red-300">⚠️ Kritik: {stats.critical}</div>
        <div className="text-emerald-300">⭐ Önerilen: {stats.recommended}</div>
      </div>

      {missing.length > 0 && (
        <div className="text-xs text-amber-300 p-2 bg-amber-500/10 rounded border border-amber-500/30">
          ⚠️ {missing.length} kritik öğe seçilmedi:
          <ul className="list-disc list-inside mt-1">
            {missing.slice(0, 3).map((m) => (
              <li key={m.id}>{m.name || m.title}</li>
            ))}
            {missing.length > 3 && <li>...ve {missing.length - 3} tane daha</li>}
          </ul>
        </div>
      )}

      <button className="w-full text-xs text-slate-400 hover:text-slate-300">Detaylı Rapor →</button>
    </div>
  );
}

function StepGuidance({ stepType }: { stepType: string }) {
  const guidance: Record<string, string> = {
    objective: "En az 3 ana hedef seçin. Kritik olanları mutlaka dahil edin.",
    tech_stack: "Her kategori için bir teknoloji seçin. Önerilen kombinasyonları tercih edin.",
    features: "Must-have özellikler kritiktir. Optional olanları projenin kapsamına göre seçin.",
    architecture: "Temel bileşenleri seçin. İleriye dönük ölçeklenebilirlik için önerilenleri göz önünde bulundurun.",
    quality: "DoD ve NFR'ları projenizin gereksinimlerine göre seçin. Risk yönetimi için yüksek etkili riskleri dahil edin.",
  };

  const tip = guidance[stepType];
  if (!tip) return null;
  return (
    <div className="bg-blue-500/10 border border-blue-500/30 rounded p-3 mb-3 text-sm text-blue-200">
      💡 <strong>İpucu:</strong> {tip}
    </div>
  );
}

function ComparisonPanel({ items, onClear }: { items: CompareItem[]; onClear: () => void }) {
  if (items.length < 2) return null;
  return (
    <div className="fixed bottom-0 left-0 right-0 bg-slate-800 border-t border-slate-700 p-4 z-50">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-semibold text-slate-100">Karşılaştırma</h4>
        <button onClick={onClear} className="text-xs text-slate-300 hover:text-white">
          ✕ Kapat
        </button>
      </div>
      <div className="grid grid-cols-2 gap-4">
        {items.slice(0, 2).map(({ item, itemType }, idx) => {
          const title = item.name || item.title || "Öneri";
          const advantages = item.advantages || [];
          const disadvantages = item.disadvantages || [];
          return (
            <div key={idx} className="space-y-2 border border-slate-700 rounded p-3">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-semibold">{title}</span>
                <span className="text-[11px] px-2 py-0.5 rounded bg-slate-700 text-slate-200 border border-slate-600">
                  {itemType}
                </span>
                <PriorityBadge priority={item.priority_score} recommendation={item.recommendation_type} />
              </div>
              <div className="text-sm space-y-1 text-slate-300">
                <div>Öncelik: {item.priority_score ?? "?"}/5</div>
                <div>Tip: {item.recommendation_type || "—"}</div>
                <div className="text-emerald-300 font-semibold">Avantajlar</div>
                <ul className="list-disc list-inside text-slate-200">
                  {advantages.length ? advantages.map((a: string, i: number) => <li key={i}>{a}</li>) : <li>—</li>}
                </ul>
                <div className="text-red-300 font-semibold">Dezavantajlar</div>
                <ul className="list-disc list-inside text-slate-200">
                  {disadvantages.length ? disadvantages.map((d: string, i: number) => <li key={i}>{d}</li>) : <li>—</li>}
                </ul>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ItemCard({
  item,
  title,
  description,
  onToggle,
  disabled,
  tags,
  advantages,
  disadvantages,
  subtitle,
  onCompare,
}: ItemCardProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border border-slate-700 rounded p-3 bg-slate-800/40">
      <div className="flex items-start gap-2">
        <input
          type="checkbox"
          checked={item.is_selected}
          onChange={() => onToggle(item.id)}
          disabled={disabled}
          className="mt-1 h-4 w-4 rounded border-slate-600 bg-slate-800 text-emerald-500 focus:ring-emerald-500 disabled:opacity-50"
        />
        <div className="flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-semibold">{title}</span>
            <PriorityBadge priority={item.priority_score} recommendation={item.recommendation_type} />
          </div>
          {subtitle && <div className="text-xs text-slate-400">{subtitle}</div>}
          {(description || item.rationale) && (
            <p className="text-sm text-slate-400 mt-0.5">{description || item.rationale}</p>
          )}
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-xs text-slate-400 hover:text-slate-200"
          aria-label="Detayları aç/kapat"
        >
          {expanded ? "▼" : "▶"}
        </button>
      </div>
      <div className="mt-2 flex gap-2">
        {onCompare && (
          <button
            onClick={() => onCompare(item)}
            className="text-xs text-slate-300 hover:text-white underline"
          >
            Karşılaştır
          </button>
        )}
      </div>
      {expanded && (
        <div className="mt-3 pt-3 border-t border-slate-700 space-y-2 text-sm">
          {advantages && advantages.length > 0 && (
            <div>
              <span className="font-semibold text-emerald-400">✓ Avantajlar:</span>
              <ul className="list-disc list-inside text-slate-300">
                {advantages.map((adv, i) => (
                  <li key={i}>{adv}</li>
                ))}
              </ul>
            </div>
          )}
          {disadvantages && disadvantages.length > 0 && (
            <div>
              <span className="font-semibold text-red-400">✗ Dezavantajlar:</span>
              <ul className="list-disc list-inside text-slate-300">
                {disadvantages.map((dis, i) => (
                  <li key={i}>{dis}</li>
                ))}
              </ul>
            </div>
          )}
          {tags && tags.length > 0 && (
            <div className="flex gap-1 flex-wrap">
              {tags.map((tag) => (
                <span key={tag} className="px-2 py-0.5 bg-slate-700 rounded text-xs">
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

const STEP_ORDER = [
  { key: "objective", label: "Hedefler", run: runObjective, type: "objective" },
  { key: "tech", label: "Teknoloji Yığını", run: runTechStack, type: "tech_stack" },
  { key: "features", label: "Özellikler", run: runFeatures, type: "features" },
  { key: "architecture", label: "Mimari", run: runArchitecture, type: "architecture" },
  { key: "quality", label: "Kalite", run: runQuality, type: "dod" },
];

function statusBadge(status: StepStatus) {
  const colors: Record<StepStatus, string> = {
    planned: "bg-slate-700 text-slate-100",
    in_progress: "bg-amber-500/20 text-amber-200",
    completed: "bg-emerald-500/20 text-emerald-200",
    stale: "bg-slate-600 text-slate-100",
    failed: "bg-red-500/20 text-red-200",
    locked: "bg-indigo-500/20 text-indigo-200",
  };
  return colors[status] || "bg-slate-700 text-slate-100";
}

function statusLabel(status: StepStatus) {
  const labels: Record<StepStatus, string> = {
    planned: "Planlandı",
    in_progress: "Devam ediyor",
    completed: "Tamamlandı",
    stale: "Güncel değil",
    failed: "Hata",
    locked: "Kilitli",
  };
  return labels[status] || status;
}

function SelectionCount({
  selected,
  total
}: {
  selected: number;
  total: number;
}) {
  return (
    <span className={selected === 0 ? "text-red-300" : ""}>
      {selected} / {total} öğe seçili
      {selected === 0 && " • En az birini seçin"}
    </span>
  );
}

export function SpecWizard({ projectId }: { projectId: number | null }) {
  const [summary, setSummary] = useState<WizardSummary | null>(null);
  const [detail, setDetail] = useState<WizardDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [runningStep, setRunningStep] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [compareItems, setCompareItems] = useState<CompareItem[]>([]);
  const [collapsedSteps, setCollapsedSteps] = useState<Record<string, boolean>>({});
  const [showSelectionSummary, setShowSelectionSummary] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (!projectId) {
      setSummary(null);
      setDetail(null);
      return;
    }
    setLoading(true);
    Promise.all([getWizardSummary(projectId), getWizardDetail(projectId)])
      .then(([s, d]) => {
        setSummary(s);
        setDetail(d);
        setError(null);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [projectId]);

  async function handleRun(stepKey: string, runFn: (projectId: number) => Promise<any>) {
    if (!projectId) return;
    setRunningStep(stepKey);
    try {
      await runFn(projectId);
      // Refresh both summary AND detail to show new data
      const [s, d] = await Promise.all([
        getWizardSummary(projectId),
        getWizardDetail(projectId),
      ]);
      setSummary(s);
      setDetail(d);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setRunningStep(null);
    }
  }

  async function handleApprove(stepType: string) {
    if (!projectId) return;
    setRunningStep(stepType);
    try {
      await approveStep(projectId, stepType);
      const s = await getWizardSummary(projectId);
      setSummary(s);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setRunningStep(null);
    }
  }

  async function handleRegenerate(stepType: string) {
    if (!projectId) return;
    setRunningStep(stepType);
    try {
      await regenerateStep(projectId, stepType);
      // Refresh both summary AND detail to show new items
      const [s, d] = await Promise.all([
        getWizardSummary(projectId),
        getWizardDetail(projectId),
      ]);
      setSummary(s);
      setDetail(d);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setRunningStep(null);
    }
  }

  async function handleItemToggle(itemType: string, itemId: number) {
    if (!projectId) return;
    try {
      await toggleItemSelection(projectId, itemType, itemId);
      const d = await getWizardDetail(projectId);
      setDetail(d);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function handleSelectAll(itemType: string) {
    if (!projectId) return;
    try {
      await selectAllItems(projectId, itemType);
      const d = await getWizardDetail(projectId);
      setDetail(d);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function handleDeselectAll(itemType: string) {
    if (!projectId) return;
    try {
      await deselectAllItems(projectId, itemType);
      const d = await getWizardDetail(projectId);
      setDetail(d);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function handleSmartBulk(ids: number[], itemType: string, opts?: { preserveExisting?: boolean }) {
    if (!projectId) return;
    try {
      if (!opts?.preserveExisting) {
        await deselectAllItems(projectId, itemType);
      }
      for (const id of ids) {
        await toggleItemSelection(projectId, itemType, id);
      }
      const d = await getWizardDetail(projectId);
      setDetail(d);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    }
  }

  function handleAddToCompare(item: any, itemType: string) {
    setCompareItems((prev) => {
      // Enforce same itemType; if different type, start fresh
      if (prev.length > 0 && prev[prev.length - 1].itemType !== itemType) {
        return [{ item, itemType }];
      }
      const next = [...prev, { item, itemType }];
      return next.slice(-2);
    });
  }

  const stepSummaries = summary?.steps || [];

  function getStepSummary(stepType: string) {
    return stepSummaries.find((s) => s.step_type === stepType);
  }

  function getSelectionState(stepKey: string) {
    if (!detail) return { selected: 0, total: 0 };
    if (stepKey === "objective") {
      const total = detail.objectives.length;
      const selected = detail.objectives.filter((i) => i.is_selected).length;
      return { selected, total };
    }
    if (stepKey === "tech") {
      const total = detail.tech_stack.length;
      const selected = detail.tech_stack.filter((i) => i.is_selected).length;
      return { selected, total };
    }
    if (stepKey === "features") {
      const total = detail.features.length;
      const selected = detail.features.filter((i) => i.is_selected).length;
      return { selected, total };
    }
    if (stepKey === "architecture") {
      const total = detail.architecture.length;
      const selected = detail.architecture.filter((i) => i.is_selected).length;
      return { selected, total };
    }
    if (stepKey === "quality") {
      const total =
        detail.dod_items.length + detail.nfr_items.length + detail.risk_items.length;
      const selected =
        detail.dod_items.filter((i) => i.is_selected).length +
        detail.nfr_items.filter((i) => i.is_selected).length +
        detail.risk_items.filter((i) => i.is_selected).length;
      return { selected, total };
    }
    return { selected: 0, total: 0 };
  }

  // Check if objective step is completed - this will re-evaluate when summary changes
  const objectiveSummary = getStepSummary("objective");
  const objectiveCompleted = objectiveSummary?.status === "completed";

  // Debug logging
  console.log("SpecWizard render:", {
    projectId,
    hasSummary: !!summary,
    stepCount: stepSummaries.length,
    objectiveSummary: objectiveSummary ? {
      status: objectiveSummary.status,
      approval_status: objectiveSummary.approval_status,
    } : null,
    objectiveCompleted,
  });

  return (
    <div className="rounded border border-slate-800 bg-slate-900 p-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h2 className="text-lg font-semibold">Spec Sihirbazı</h2>
          <p className="text-sm text-slate-400">Bu proje için LLM adımlarını çalıştırıp çıktıları inceleyin.</p>
        </div>
        {loading && <span className="text-xs text-slate-400">yükleniyor...</span>}
      </div>
      {objectiveCompleted && (
        <div className="mb-3 rounded bg-emerald-500/10 border border-emerald-500/30 px-3 py-2 text-xs text-emerald-200">
          ✓ Hedefler tamamlandı - Diğer adımları çalıştırabilirsiniz
        </div>
      )}
      {error && (
        <div className="mb-3 rounded border border-red-500 bg-red-500/10 p-2 text-xs text-red-200">
          {error}
        </div>
      )}
      {!projectId && <p className="text-xs text-slate-500">Sihirbaz için proje seçin.</p>}
      {projectId && (
        <div className="space-y-3">
          {STEP_ORDER.map((step) => {
            const s = getStepSummary(step.type) || {
              status: "planned" as StepStatus,
              approval_status: undefined,
              item_count: 0,
              summary: "",
              last_ai_run_at: null,
              last_approved_at: null,
            };
            const badge = statusBadge(s.status as StepStatus);
            const selectionState = getSelectionState(step.key);
            const isLocked = step.type !== "objective" && !objectiveCompleted;
            const collapsed = collapsedSteps[step.key] !== undefined ? collapsedSteps[step.key] : true;
            const summaryOpen = showSelectionSummary[step.key] || false;

            // Debug each step's lock status
            console.log(`Step ${step.type}:`, {
              isObjective: step.type === "OBJECTIVE",
              objectiveCompleted,
              isLocked,
              status: s.status,
            });
            return (
              <div key={step.key} className="rounded border border-slate-800 bg-slate-800/40 p-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() =>
                        setCollapsedSteps((prev) => ({ ...prev, [step.key]: !prev[step.key] }))
                      }
                      aria-label={collapsed ? "Aç" : "Kapat"}
                      className="h-8 w-8 rounded-full border border-slate-700/70 bg-slate-900 text-slate-100 flex items-center justify-center shadow-sm hover:bg-slate-800 transition-all"
                    >
                      <span
                        className={`inline-block transform transition-transform duration-200 ${
                          collapsed ? "" : "rotate-90"
                        }`}
                      >
                        ➤
                      </span>
                    </button>
                    <div>
                      <div className="text-sm font-semibold">{step.label}</div>
                      <div className="text-xs text-slate-400">
                        {s.item_count} öğe • {s.summary || "Özet yok"}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      className="text-[11px] text-slate-300 underline"
                      onClick={() =>
                        setShowSelectionSummary((prev) => ({
                          ...prev,
                          [step.key]: !summaryOpen,
                        }))
                      }
                    >
                      {summaryOpen ? "Seçim özetini gizle" : "Seçim özetini göster"}
                    </button>
                    <span className={`px-2 py-1 rounded text-[11px] ${badge}`}>
                      {statusLabel(s.status as StepStatus)}
                    </span>
                    <button
                      onClick={() => !isLocked && handleRun(step.key, step.run)}
                      disabled={runningStep === step.key || isLocked}
                      className="rounded bg-emerald-600 px-3 py-1 text-[11px] font-semibold disabled:opacity-50"
                    >
                      {runningStep === step.key ? "Çalışıyor..." : isLocked ? "Kilitli" : "Çalıştır"}
                    </button>
                    {isLocked && (
                      <span className="text-[11px] text-amber-300">Önce Hedefler adımını çalıştırın</span>
                    )}
                  </div>
                </div>
                {!collapsed && (
                  <>
                    {s.last_ai_run_at && (
                      <div className="text-[11px] text-slate-500 mt-1">
                        Son çalıştırma: {new Date(s.last_ai_run_at).toLocaleString()}
                      </div>
                    )}
                    {summaryOpen && (
                      <div className="mt-2 text-xs text-slate-400">
                        <SelectionCount selected={selectionState.selected} total={selectionState.total} />
                      </div>
                    )}
                    {s.approval_status === "pending" && s.status === "completed" && (
                      <div className="mt-3 flex gap-2 pt-2 border-t border-slate-700">
                        <button
                          onClick={() => handleRegenerate(step.type)}
                          disabled={runningStep === step.type}
                          className="rounded bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-50"
                        >
                          🔄 Yeniden Üret
                        </button>
                        <button
                          onClick={() => handleApprove(step.type)}
                          disabled={runningStep === step.type || selectionState.selected === 0}
                          className="rounded bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-50"
                        >
                          ✓ Adımı Onayla
                        </button>
                      </div>
                    )}
                    {s.approval_status === "approved" && (
                      <div className="mt-2 rounded bg-emerald-500/10 border border-emerald-500/30 px-3 py-2 text-sm text-emerald-200">
                        ✓ Adım Onaylandı {s.last_approved_at && `• ${new Date(s.last_approved_at).toLocaleString()}`}
                      </div>
                    )}
                    <StepDetails
                      stepKey={step.key}
                      detail={detail}
                      onItemToggle={handleItemToggle}
                      onSelectAll={handleSelectAll}
                      onDeselectAll={handleDeselectAll}
                      onSmartSelect={(ids, itemType, opts) => handleSmartBulk(ids, itemType, opts)}
                      onAddToCompare={(item, itemType) => handleAddToCompare(item, itemType)}
                      isApproved={s.approval_status === "approved"}
                      showSelectionSummary={summaryOpen}
                    />
                  </>
                )}
              </div>
            );
          })}
        </div>
      )}
      {compareItems.length >= 2 && (
        <ComparisonPanel items={compareItems} onClear={() => setCompareItems([])} />
      )}
    </div>
  );
}

function StepDetails({
  stepKey,
  detail,
  onItemToggle,
  onSelectAll,
  onDeselectAll,
  onSmartSelect,
  onAddToCompare,
  isApproved,
  showSelectionSummary,
}: {
  stepKey: string;
  detail: WizardDetail | null;
  onItemToggle: (itemType: string, itemId: number) => Promise<void>;
  onSelectAll: (itemType: string) => Promise<void>;
  onDeselectAll: (itemType: string) => Promise<void>;
  onSmartSelect: (ids: number[], itemType: string, opts?: { preserveExisting?: boolean }) => void;
  onAddToCompare: (item: any, itemType: string) => void;
  isApproved: boolean;
  showSelectionSummary: boolean;
}) {
  // Move all useState hooks to the top to comply with React rules of hooks
  const [filters, setFilters] = useState<FilterState>({
    recommendation: "all",
    category: "all",
    showSelected: false,
  });
  const [dodFilters, setDodFilters] = useState<FilterState>({
    recommendation: "all",
    category: "all",
    showSelected: false,
  });
  const [nfrFilters, setNfrFilters] = useState<FilterState>({
    recommendation: "all",
    category: "all",
    showSelected: false,
  });
  const [riskFilters, setRiskFilters] = useState<FilterState>({
    recommendation: "all",
    category: "all",
    showSelected: false,
  });

  if (!detail) return null;
  if (stepKey === "objective") {
    const selectedIds = detail.objectives.filter((i) => i.is_selected).map((i) => i.id);
    const filteredObjectives = detail.objectives.filter((o) => {
      if (filters.showSelected && !o.is_selected) return false;
      if (filters.recommendation !== "all" && o.recommendation_type !== filters.recommendation) {
        return false;
      }
      return true;
    });
    return (
      <div className="mt-2 text-sm">
        <StepGuidance stepType="objective" />
        <div className="flex items-center justify-between mb-2">
          <div className="font-semibold">Hedefler</div>
          <div className="flex gap-2">
            <button
              onClick={() => onSelectAll("objective")}
              disabled={isApproved}
              className="rounded bg-slate-700 px-2 py-1 text-[11px] text-slate-100 hover:bg-slate-600 disabled:opacity-50"
            >
              Tümünü Seç
            </button>
            <button
              onClick={() => onDeselectAll("objective")}
              disabled={isApproved}
              className="rounded bg-slate-700 px-2 py-1 text-[11px] text-slate-100 hover:bg-slate-600 disabled:opacity-50"
            >
              Seçimi Kaldır
            </button>
          </div>
        </div>
        <div className="space-y-2">
          <QuickSelectionBar
            items={detail.objectives}
            onBulkSelect={(ids, opts) => onSmartSelect(ids, "objective", opts)}
          />
          <ItemFilters
            onFilterChange={(f) => setFilters(f)}
          />
          {/* Hedefler adımında uyumluluk kontrolünü gizliyoruz; yalnızca özet isteğe bağlı */}
          {showSelectionSummary && (
            <SelectionSummary items={detail.objectives} selectedIds={selectedIds} />
          )}
          {filteredObjectives.map((o) => (
            <ItemCard
              key={o.id}
              item={o}
              title={o.title}
              description={o.text}
              tags={o.category_tags || undefined}
              advantages={o.advantages}
              disadvantages={o.disadvantages}
              onToggle={(id) => onItemToggle("objective", id)}
              disabled={isApproved}
            />
          ))}
        </div>
      </div>
    );
  }
  if (stepKey === "tech") {
    const selectedIds = detail.tech_stack.filter((i) => i.is_selected).map((i) => i.id);
    const filtered = detail.tech_stack.filter((t) => {
      if (filters.showSelected && !t.is_selected) return false;
      if (filters.recommendation !== "all" && t.recommendation_type !== filters.recommendation) {
        return false;
      }
      return true;
    });
    return (
      <div className="mt-2 text-sm">
        <StepGuidance stepType="tech_stack" />
        <div className="flex items-center justify-between mb-2">
          <div className="font-semibold">Teknoloji Yığını</div>
          <div className="flex gap-2">
            <button
              onClick={() => onSelectAll("tech_stack")}
              disabled={isApproved}
              className="rounded bg-slate-700 px-2 py-1 text-[11px] text-slate-100 hover:bg-slate-600 disabled:opacity-50"
            >
              Tümünü Seç
            </button>
            <button
              onClick={() => onDeselectAll("tech_stack")}
              disabled={isApproved}
              className="rounded bg-slate-700 px-2 py-1 text-[11px] text-slate-100 hover:bg-slate-600 disabled:opacity-50"
            >
              Seçimi Kaldır
            </button>
          </div>
        </div>
        {detail.tech_stack.length ? (
        <div className="space-y-2">
          <QuickSelectionBar
            items={detail.tech_stack}
            onBulkSelect={(ids, opts) => onSmartSelect(ids, "tech_stack", opts)}
          />
          <ItemFilters onFilterChange={(f) => setFilters(f)} />
          <SelectionValidation items={detail.tech_stack} selectedIds={selectedIds} />
          {filtered.map((stack) => {
              const section = (
                ["frontend", "backend", "database", "infra", "analytics", "ci_cd"] as const
              ).find((key) => (stack as any)[key]);
              const val = section ? (stack as any)[section] : null;
              const title = `${section || "Teknoloji"}: ${val?.name || "Öneri"}`;
              return (
                <ItemCard
                  key={stack.id}
                  item={stack}
                  title={title}
                  subtitle={stack.recommendation_type ? `Öneri: ${stack.recommendation_type}` : undefined}
                  description={stack.rationale}
                  tags={stack.category_tags || undefined}
                  advantages={stack.advantages}
                  disadvantages={stack.disadvantages}
                  onToggle={(id) => onItemToggle("tech_stack", id)}
                  disabled={isApproved}
                  onCompare={(item) => onAddToCompare(item, "tech_stack")}
                />
              );
            })}
          </div>
        ) : (
          <p className="text-xs text-slate-500">Henüz teknoloji önerisi yok.</p>
        )}
      </div>
    );
  }
  if (stepKey === "features") {
    const selectedIds = detail.features.filter((i) => i.is_selected).map((i) => i.id);
    const filtered = detail.features.filter((f) => {
      if (filters.showSelected && !f.is_selected) return false;
      if (filters.recommendation !== "all" && f.recommendation_type !== filters.recommendation) {
        return false;
      }
      return true;
    });
    return (
      <div className="mt-2 text-sm">
        <StepGuidance stepType="features" />
        <div className="flex items-center justify-between mb-2">
          <div className="font-semibold">Özellikler</div>
          <div className="flex gap-2">
            <button
              onClick={() => onSelectAll("feature")}
              disabled={isApproved}
              className="rounded bg-slate-700 px-2 py-1 text-[11px] text-slate-100 hover:bg-slate-600 disabled:opacity-50"
            >
              Tümünü Seç
            </button>
            <button
              onClick={() => onDeselectAll("feature")}
              disabled={isApproved}
              className="rounded bg-slate-700 px-2 py-1 text-[11px] text-slate-100 hover:bg-slate-600 disabled:opacity-50"
            >
              Seçimi Kaldır
            </button>
          </div>
        </div>
        <div className="space-y-2">
          <QuickSelectionBar
            items={detail.features}
            onBulkSelect={(ids, opts) => onSmartSelect(ids, "feature", opts)}
          />
          <ItemFilters onFilterChange={(f) => setFilters(f)} />
          {/* Özellikler adımında uyumluluk mesajını göstermiyoruz */}
          {filtered.map((f) => (
            <ItemCard
              key={f.id}
              item={f}
              title={f.name}
              description={f.description}
              tags={f.category_tags || undefined}
              advantages={f.advantages}
              disadvantages={f.disadvantages}
              onToggle={(id) => onItemToggle("feature", id)}
              disabled={isApproved}
              onCompare={(item) => onAddToCompare(item, "feature")}
            />
          ))}
        </div>
      </div>
    );
  }
  if (stepKey === "architecture") {
    const selectedIds = detail.architecture.filter((i) => i.is_selected).map((i) => i.id);
    const filtered = detail.architecture.filter((c) => {
      if (filters.showSelected && !c.is_selected) return false;
      if (filters.recommendation !== "all" && c.recommendation_type !== filters.recommendation) {
        return false;
      }
      return true;
    });
    return (
      <div className="mt-2 text-sm">
        <StepGuidance stepType="architecture" />
        <div className="flex items-center justify-between mb-2">
          <div className="font-semibold">Mimari</div>
          <div className="flex gap-2">
            <button
              onClick={() => onSelectAll("architecture")}
              disabled={isApproved}
              className="rounded bg-slate-700 px-2 py-1 text-[11px] text-slate-100 hover:bg-slate-600 disabled:opacity-50"
            >
              Tümünü Seç
            </button>
            <button
              onClick={() => onDeselectAll("architecture")}
              disabled={isApproved}
              className="rounded bg-slate-700 px-2 py-1 text-[11px] text-slate-100 hover:bg-slate-600 disabled:opacity-50"
            >
              Seçimi Kaldır
            </button>
          </div>
        </div>
        <div className="space-y-2">
          <QuickSelectionBar
            items={detail.architecture}
            onBulkSelect={(ids, opts) => onSmartSelect(ids, "architecture", opts)}
          />
          <ItemFilters onFilterChange={(f) => setFilters(f)} />
          <SelectionValidation items={detail.architecture} selectedIds={selectedIds} />
          {filtered.map((c) => (
            <ItemCard
              key={c.id}
              item={c}
              title={c.name}
              subtitle={c.layer}
              description={c.description}
              tags={c.category_tags || undefined}
              advantages={c.advantages}
              disadvantages={c.disadvantages}
              onToggle={(id) => onItemToggle("architecture", id)}
              disabled={isApproved}
              onCompare={(item) => onAddToCompare(item, "architecture")}
            />
          ))}
        </div>
      </div>
    );
  }
  if (stepKey === "quality") {
    const filterItems = (items: any[], filters: FilterState) =>
      items.filter((i) => {
        if (filters.showSelected && !i.is_selected) return false;
        if (filters.recommendation !== "all" && i.recommendation_type !== filters.recommendation) {
          return false;
        }
        return true;
      });

    return (
      <div className="mt-2 text-sm space-y-2">
        <StepGuidance stepType="quality" />
        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="font-semibold">DoD</div>
            <div className="flex gap-2">
              <button
                onClick={() => onSelectAll("dod")}
                disabled={isApproved}
                className="rounded bg-slate-700 px-2 py-1 text-[11px] text-slate-100 hover:bg-slate-600 disabled:opacity-50"
              >
                Tümünü Seç
              </button>
              <button
                onClick={() => onDeselectAll("dod")}
                disabled={isApproved}
                className="rounded bg-slate-700 px-2 py-1 text-[11px] text-slate-100 hover:bg-slate-600 disabled:opacity-50"
              >
                Seçimi Kaldır
              </button>
            </div>
          </div>
          <div className="space-y-2">
          <QuickSelectionBar
            items={detail.dod_items}
            onBulkSelect={(ids, opts) => onSmartSelect(ids, "dod", opts)}
          />
          <ItemFilters onFilterChange={(f) => setDodFilters(f)} />
          <SelectionValidation
            items={detail.dod_items}
            selectedIds={detail.dod_items.filter((i) => i.is_selected).map((i) => i.id)}
          />
          {filterItems(detail.dod_items, dodFilters).map((d) => (
            <ItemCard
              key={d.id}
              item={d}
              title={d.category || "DoD"}
                description={d.description}
                tags={d.category_tags || undefined}
                advantages={d.advantages}
                disadvantages={d.disadvantages}
                onToggle={(id) => onItemToggle("dod", id)}
                disabled={isApproved}
                onCompare={(item) => onAddToCompare(item, "dod")}
              />
            ))}
          </div>
        </div>
        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="font-semibold">NFR</div>
            <div className="flex gap-2">
              <button
                onClick={() => onSelectAll("nfr")}
                disabled={isApproved}
                className="rounded bg-slate-700 px-2 py-1 text-[11px] text-slate-100 hover:bg-slate-600 disabled:opacity-50"
              >
                Tümünü Seç
              </button>
              <button
                onClick={() => onDeselectAll("nfr")}
                disabled={isApproved}
                className="rounded bg-slate-700 px-2 py-1 text-[11px] text-slate-100 hover:bg-slate-600 disabled:opacity-50"
              >
                Seçimi Kaldır
              </button>
            </div>
          </div>
          <div className="space-y-2">
            <QuickSelectionBar
              items={detail.nfr_items}
              onBulkSelect={(ids, opts) => onSmartSelect(ids, "nfr", opts)}
            />
            <ItemFilters onFilterChange={(f) => setNfrFilters(f)} />
            <SelectionValidation
              items={detail.nfr_items}
              selectedIds={detail.nfr_items.filter((i) => i.is_selected).map((i) => i.id)}
            />
            {filterItems(detail.nfr_items, nfrFilters).map((n) => (
              <ItemCard
                key={n.id}
                item={n}
                title={n.type}
                description={n.description}
                tags={n.category_tags || undefined}
                advantages={n.advantages}
                disadvantages={n.disadvantages}
                onToggle={(id) => onItemToggle("nfr", id)}
                disabled={isApproved}
                onCompare={(item) => onAddToCompare(item, "nfr")}
              />
            ))}
          </div>
        </div>
        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="font-semibold">Riskler</div>
            <div className="flex gap-2">
              <button
                onClick={() => onSelectAll("risk")}
                disabled={isApproved}
                className="rounded bg-slate-700 px-2 py-1 text-[11px] text-slate-100 hover:bg-slate-600 disabled:opacity-50"
              >
                Tümünü Seç
              </button>
              <button
                onClick={() => onDeselectAll("risk")}
                disabled={isApproved}
                className="rounded bg-slate-700 px-2 py-1 text-[11px] text-slate-100 hover:bg-slate-600 disabled:opacity-50"
              >
                Seçimi Kaldır
              </button>
            </div>
          </div>
          <div className="space-y-2">
            <QuickSelectionBar
              items={detail.risk_items}
              onBulkSelect={(ids, opts) => onSmartSelect(ids, "risk", opts)}
            />
            <ItemFilters onFilterChange={(f) => setRiskFilters(f)} />
            <SelectionValidation
              items={detail.risk_items}
              selectedIds={detail.risk_items.filter((i) => i.is_selected).map((i) => i.id)}
            />
            {filterItems(detail.risk_items, riskFilters).map((r) => (
              <ItemCard
                key={r.id}
                item={r}
                title="Risk"
                description={r.description}
                tags={r.category_tags || undefined}
                advantages={r.advantages}
                disadvantages={r.disadvantages}
                onToggle={(id) => onItemToggle("risk", id)}
                disabled={isApproved}
                onCompare={(item) => onAddToCompare(item, "risk")}
              />
            ))}
          </div>
        </div>
      </div>
    );
  }
  return null;
}
