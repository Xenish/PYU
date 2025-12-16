"use client";

import { useEffect, useState } from "react";
import { JobConsole } from "@/components/JobConsole";
import { PlanningView } from "@/components/PlanningView";
import { SpecWizard } from "@/components/SpecWizard";
import { CreateProjectForm } from "@/components/CreateProjectForm";
import { ProjectSelect } from "@/components/ProjectSelect";
import { ReadyTasksList } from "@/components/ReadyTasksList";
import { SprintSelect } from "@/components/SprintSelect";
import { SprintTaskBoard } from "@/components/SprintTaskBoard";
import { StatusView } from "@/components/StatusView";
import { getProjects, getSprints, Project, Sprint, deleteProject, getLlmInfo, setLlm, LLMInfo, updateProject } from "@/lib/api";
import { runObjective } from "@/lib/api";

export default function Home() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [sprints, setSprints] = useState<Sprint[]>([]);
  const [selectedProject, setSelectedProject] = useState<number | null>(null);
  const [selectedSprint, setSelectedSprint] = useState<number | null>(null);
  const [loadingProjects, setLoadingProjects] = useState(false);
  const [loadingSprints, setLoadingSprints] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCreateOnly, setShowCreateOnly] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [llmInfo, setLlmInfo] = useState<LLMInfo | null>(null);
  const [llmPanelOpen, setLlmPanelOpen] = useState(false);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [llmSaving, setLlmSaving] = useState(false);
  const [showPurposeModal, setShowPurposeModal] = useState(false);
  const [purposeDraft, setPurposeDraft] = useState("");
  const [purposeSaving, setPurposeSaving] = useState(false);
  const currentProject = projects.find((p) => p.id === selectedProject) || null;
  const heroPrompts = [
    "Hadi başlayalım: Projen için ilk adımı at.",
    "Hazırsan üretmeye başlayalım, planlar seni bekliyor.",
    "Yeni bir proje, yeni bir yolculuk: başlatmaya ne dersin?",
    "Adını koy, amacını yaz; geri kalanını akış halletsin.",
    "Hoş geldin, Proje oluşturmaya hazır mısın?",
  ];
  const [heroIndex, setHeroIndex] = useState(0);
  const [heroVisible, setHeroVisible] = useState(true);
  const [heroSharp, setHeroSharp] = useState(true);
  const [hideHero, setHideHero] = useState(false);
  const [sidebarDraft, setSidebarDraft] = useState<string | null>(null);
  const [sidebarDraftDesc, setSidebarDraftDesc] = useState<string | null>(null);
  const [sidebarDraftSuggestions, setSidebarDraftSuggestions] = useState<any[] | null>(null);
  const DRAFT_KEY = "create_project_draft";
  const [draftSession, setDraftSession] = useState(0);
  const startNewDraft = () => {
    // Yeni proje ekranına geç; mevcut taslağı sıfırla
    setSelectedProject(null);
    setSelectedSprint(null);
    setShowCreateOnly(true);
    setSidebarOpen(false);
    setHideHero(false);
    setSidebarDraft(null);
    setSidebarDraftDesc(null);
    setSidebarDraftSuggestions(null);
    try {
      localStorage.removeItem(DRAFT_KEY);
    } catch (err) {
      console.warn("Draft clear error", err);
    }
    setDraftSession((n) => n + 1);
  };

  useEffect(() => {
    refreshProjects();
  }, []);

  useEffect(() => {
    getLlmInfo()
      .then((info) => {
        setLlmInfo(info);
        setSelectedModel(info.model);
      })
      .catch((err) => console.warn("LLM info alınamadı", err));
  }, []);

  const handleModelChange = async (val: string) => {
    if (!val) return;
    setSelectedModel(val);
    setLlmSaving(true);
    try {
      const updated = await setLlm({ model: val });
      setLlmInfo(updated);
      setSelectedModel(updated.model);
    } catch (err) {
      console.error("LLM modeli güncellenemedi", err);
      alert("Model güncellenemedi. Sunucu ayarlarını kontrol edin.");
    } finally {
      setLlmSaving(false);
    }
  };

  useEffect(() => {
    let timeoutSwitch: ReturnType<typeof setTimeout> | null = null;
    let timeoutSharpen: ReturnType<typeof setTimeout> | null = null;
    const interval = setInterval(() => {
      setHeroVisible(false);
      setHeroSharp(false);
      timeoutSwitch = setTimeout(() => {
        setHeroIndex((prev) => (prev + 1) % heroPrompts.length);
        setHeroVisible(true);
        timeoutSharpen = setTimeout(() => setHeroSharp(true), 300);
      }, 1800);
    }, 8000);
    return () => {
      clearInterval(interval);
      if (timeoutSwitch) clearTimeout(timeoutSwitch);
      if (timeoutSharpen) clearTimeout(timeoutSharpen);
    };
  }, [heroPrompts.length]);

  const handleDeleteProject = async (id: number) => {
    if (!confirm(`"${projects.find((p) => p.id === id)?.name || "Bu proje"}" silinsin mi?`)) return;
    try {
      await deleteProject(id);
      setProjects((prev) => prev.filter((p) => p.id !== id));
      if (selectedProject === id) {
        setSelectedProject(null);
        setSelectedSprint(null);
      }
      refreshProjects();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const refreshProjects = () => {
    setLoadingProjects(true);
    getProjects()
      .then(setProjects)
      .catch((err) => setError(err.message))
      .finally(() => setLoadingProjects(false));
  };

  useEffect(() => {
    if (!selectedProject) {
      setSprints([]);
      return;
    }
    setLoadingSprints(true);
    getSprints(selectedProject)
      .then((data) => setSprints(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoadingSprints(false));
  }, [selectedProject]);

  // Load draft name for sidebar when entering create mode or on mount
  const loadDraftForSidebar = () => {
    try {
      const stored = localStorage.getItem(DRAFT_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (parsed) {
          setSidebarDraft(parsed.name || null);
          setSidebarDraftDesc(parsed.description || null);
          setSidebarDraftSuggestions(Array.isArray(parsed.suggestions) ? parsed.suggestions : null);
        }
      }
    } catch (err) {
      console.warn("Sidebar draft load error", err);
    }
  };

  useEffect(() => {
    loadDraftForSidebar();
  }, [showCreateOnly]);

  useEffect(() => {
    loadDraftForSidebar();
  }, []);

  const [activeTab, setActiveTab] = useState<"jobs" | "wizard" | "planning" | "status">("jobs");

  return (
    <div className="relative flex min-h-screen h-screen overflow-hidden">
      {/* LLM model hızlı erişim: sağ üstte soru işaretli buton */}
      <button
        onClick={() => setLlmPanelOpen((o) => !o)}
        className="fixed top-4 right-4 z-50 h-11 w-11 rounded-full bg-emerald-400 text-slate-900 font-bold shadow-xl hover:scale-105 active:scale-95 transition-transform"
        aria-label="LLM model bilgisi"
      >
        ?
      </button>
      {llmPanelOpen && (
        <div className="fixed top-16 right-4 z-50 w-80 rounded-2xl border border-slate-700 bg-slate-900/95 p-4 shadow-2xl backdrop-blur">
          <div className="flex items-start justify-between">
            <div>
              <div className="text-sm font-semibold text-slate-100">Aktif LLM Modeli</div>
              <div className="text-xs text-slate-400">
                Sağlayıcı: {llmInfo?.provider || "—"}
              </div>
            </div>
            <button
              onClick={() => setLlmPanelOpen(false)}
              className="text-slate-400 hover:text-white text-sm"
              aria-label="Kapat"
            >
              ✕
            </button>
          </div>
          <div className="mt-3 space-y-2">
            <label className="text-xs text-slate-300 block">Model seçin</label>
            <div className="flex flex-wrap gap-2">
              {(llmInfo?.available_models && llmInfo.available_models.length > 0
                ? llmInfo.available_models
                : selectedModel
                ? [selectedModel]
                : []
              ).map((m) => {
                const active = m === selectedModel;
                return (
                  <button
                    key={m}
                    onClick={() => handleModelChange(m)}
                    disabled={llmSaving}
                    className={`rounded-xl px-3 py-2 text-sm transition border ${
                      active
                        ? "border-emerald-400 bg-emerald-500/20 text-emerald-100 shadow-[0_0_0_1px_rgba(16,185,129,0.35)]"
                        : "border-slate-700 bg-slate-800/80 text-slate-200 hover:border-emerald-300 hover:text-emerald-100"
                    }`}
                    aria-pressed={active}
                  >
                    {m}
                  </button>
                );
              })}
              {(!llmInfo?.available_models || llmInfo.available_models.length === 0) && (
                <div className="text-xs text-slate-400">Modeller yükleniyor...</div>
              )}
            </div>
            <div className="text-[11px] text-slate-400">
              Sunucu modeli: <span className="text-emerald-300">{llmInfo?.model || "—"}</span>
              <br />
              Seçtiğiniz model anlık olarak backend'e uygulanır; kalıcı yapmak için .env içindeki LLM_MODEL değerini güncelleyip sunucuyu yeniden başlatın.
            </div>
            {llmSaving && <div className="text-[11px] text-emerald-300">Güncelleniyor...</div>}
          </div>
        </div>
      )}
      {showPurposeModal && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-950/70 backdrop-blur-sm px-4">
          <div className="w-full max-w-4xl rounded-3xl border border-slate-700 bg-slate-900/95 p-6 shadow-2xl relative">
            <button
              onClick={() => setShowPurposeModal(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white text-xl"
              aria-label="Kapat"
            >
              ✕
            </button>
            <h3 className="text-xl font-semibold text-emerald-200 mb-2">Güncel Amaç</h3>
            <div className="text-sm text-slate-300 space-y-3">
              {currentProject ? (
                <>
                  <div className="text-base font-semibold text-slate-100">
                    {currentProject.name}
                  </div>
                  <textarea
                    value={purposeDraft}
                    onChange={(e) => setPurposeDraft(e.target.value)}
                    className="w-full h-64 rounded-2xl border border-slate-800 bg-slate-950/60 p-4 text-sm leading-relaxed text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    placeholder="Proje amacını güncelleyin..."
                  />
                  <div className="flex justify-end gap-2 pt-2">
                    <button
                      onClick={() => setShowPurposeModal(false)}
                      className="rounded-xl px-4 py-2 text-sm text-slate-300 hover:text-white"
                      disabled={purposeSaving}
                    >
                      Vazgeç
                    </button>
                    <button
                      onClick={async () => {
                        if (!currentProject) return;
                        if (!purposeDraft.trim()) {
                          setError("Proje amacı boş olamaz.");
                          return;
                        }
                        setPurposeSaving(true);
                        try {
                          const updated = await updateProject(currentProject.id, { description: purposeDraft.trim() });
                          setProjects((prev) =>
                            prev.map((p) => (p.id === updated.id ? { ...p, description: updated.description } : p))
                          );
                          await runObjective(updated.id);
                          setShowPurposeModal(false);
                        } catch (err: any) {
                          setError(err.message || "Amaç güncellenemedi.");
                        } finally {
                          setPurposeSaving(false);
                        }
                      }}
                      disabled={purposeSaving}
                      className="rounded-xl px-4 py-2 text-sm font-semibold text-white bg-gradient-to-r from-emerald-600 via-emerald-500 to-teal-500 hover:scale-[1.01] transition"
                    >
                      {purposeSaving ? "Kaydediliyor..." : "Onayla ve Güncelle"}
                    </button>
                  </div>
                  <div className="text-[11px] text-slate-400">
                    Güncelleme sonrası amaç LLM adımlarında (özellikle Hedefler) yeniden kullanılacak.
                  </div>
                </>
              ) : (
                <div className="text-slate-400">Amaç görüntülemek için bir proje seçin veya oluşturun.</div>
              )}
            </div>
          </div>
        </div>
      )}
      {/* Sabit sol panel: başlık + proje kontrolleri (animasyonlu aç/kapa) */}
      <aside
        className={`absolute inset-y-0 left-0 z-20 w-72 overflow-y-auto border-r border-slate-800 bg-slate-900/60 p-4 space-y-3 shadow-lg transition-all duration-[1200ms] ease-in-out ${
          sidebarOpen ? "translate-x-0 opacity-100" : "-translate-x-full opacity-0 pointer-events-none"
        }`}
      >
        <button
          onClick={() => setSidebarOpen(false)}
          aria-label="Paneli gizle"
          className="absolute right-3 top-8 inline-flex h-8 w-8 items-center justify-center rounded-full border border-slate-700 bg-slate-800 text-slate-200 hover:bg-slate-700"
        >
          ←
        </button>
        <div className="pr-8 space-y-1">
          <div className="text-2xl md:text-3xl font-semibold tracking-wide text-slate-50 font-['Pacifico',cursive]">
            Planlayıcı <span className="text-sm text-emerald-300/80 align-middle">· AI</span>
          </div>
          <p className="text-xs text-slate-300 font-['Caveat',cursive]">Sprint ve plan akışlarını buradan yönet.</p>
        </div>
          <ProjectSelect
            projects={projects}
            selectedProject={selectedProject}
            onSelect={(id) => {
              setSelectedProject(id);
            setSelectedSprint(null);
            setShowCreateOnly(false);
          }}
          loading={loadingProjects}
          onAdd={() => {
            startNewDraft();
          }}
          onDelete={handleDeleteProject}
          draftName={sidebarDraft || undefined}
          onDraftSelect={() => {
            setShowCreateOnly(true);
            setSidebarOpen(false);
            setSelectedProject(null);
            try {
              const stored = localStorage.getItem(DRAFT_KEY);
              if (stored) {
                const parsed = JSON.parse(stored);
                if (parsed?.name) {
                    setSidebarDraft(parsed.name);
                    setSidebarDraftDesc(parsed.description || null);
                    setSidebarDraftSuggestions(Array.isArray(parsed.suggestions) ? parsed.suggestions : null);
                  }
                }
              } catch (err) {
                console.warn("Draft reload error", err);
              }
              setDraftSession((n) => n + 1);
            }}
            draftSelected={!selectedProject && !!sidebarDraft && showCreateOnly}
          />
      </aside>

      {/* Sağ ana içerik */}
      <main
        className={`flex-1 px-4 pt-0 pb-6 space-y-4 overflow-y-auto relative transition-all duration-[1200ms] ease-in-out ${
          sidebarOpen ? "md:pl-80" : "md:pl-0"
        }`}
      >
        {!sidebarOpen && (
          <div className="absolute left-4 top-6 z-20">
            <button
              onClick={() => setSidebarOpen(true)}
              aria-label="Paneli aç"
              className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-slate-700 bg-slate-800 text-slate-200 hover:bg-slate-700"
            >
              ☰
            </button>
          </div>
        )}
        {showCreateOnly ? (
          <div className="flex min-h-[calc(100vh-3rem)] items-center justify-center">
            <div className="w-full max-w-4xl px-4 space-y-8 text-center">
              {!hideHero && (
                <div className="relative inline-flex items-center justify-center px-5 py-3">
                  <div
                    className={`absolute inset-0 rounded-full bg-slate-800/60 shadow-xl backdrop-blur animate-[hero-breathe_8s_ease-in-out_infinite] transition-all duration-[1800ms] ease-in-out ${
                      heroVisible ? "opacity-80 scale-100" : "opacity-50 scale-95"
                    }`}
                  />
                  <div
                    className={`relative text-2xl md:text-3xl font-semibold bg-gradient-to-r from-emerald-300 via-sky-300 to-indigo-300 bg-[length:300%_100%] bg-clip-text text-transparent drop-shadow transition-all duration-[2000ms] ease-in-out animate-[gradient-slide_10s_linear_infinite] ${
                      heroVisible
                        ? heroSharp
                          ? "opacity-100 translate-y-0 scale-100 blur-0"
                          : "opacity-100 translate-y-0.5 scale-[0.995] blur-sm"
                        : "opacity-0 -translate-y-2 scale-97 blur-sm"
                    }`}
                    key={heroIndex}
                  >
                    {heroPrompts[heroIndex]}
                  </div>
                </div>
              )}
              <CreateProjectForm
                key={`create-${draftSession}`}
                onCreated={(project) => {
                  refreshProjects();
                  setSelectedProject(project.id);
                  setShowCreateOnly(false);
                  setActiveTab("wizard");
                }}
                onSuggestionsToggle={(v) => setHideHero(v)}
                onSuggestPreview={(name) => setSidebarDraft(name)}
                initialDraftName={sidebarDraft || undefined}
                initialDraftDescription={sidebarDraftDesc || undefined}
                initialDraftSuggestions={sidebarDraftSuggestions || undefined}
              />
            </div>
          </div>
        ) : (
          <>
            {error && (
              <div className="rounded border border-red-500 bg-red-500/10 p-3 text-sm text-red-200">
                {error}
              </div>
            )}

            <div className="sticky top-0 z-10 flex flex-col items-center transition-all duration-300 mt-2">
              <div className="relative w-full">
                <div className="absolute inset-0 mx-auto h-16 w-full rounded-full bg-slate-950/80 shadow-[0_10px_40px_rgba(0,0,0,0.35)] backdrop-blur" />
                <div className="relative flex flex-wrap items-center justify-center gap-3 px-4 py-2">
                  {[
                    { key: "wizard", label: "Spec Sihirbazı" },
                    { key: "planning", label: "Planlama" },
                    { key: "jobs", label: "İşler & Task'ler" },
                    { key: "status", label: "Durum" },
                  ].map((tab) => (
                    <button
                      key={tab.key}
                      onClick={() => setActiveTab(tab.key as typeof activeTab)}
                      className={`flex-none ${sidebarOpen ? "min-w-[170px]" : "min-w-[200px]"} px-3 py-2.5 text-sm font-semibold rounded-xl transition-all duration-300 shadow-md ${
                        activeTab === tab.key
                          ? "bg-gradient-to-r from-emerald-600 via-emerald-500 to-teal-500 text-white scale-[1.02]"
                          : "bg-slate-800/80 text-slate-100 hover:bg-slate-700 hover:scale-[1.01]"
                      }`}
                    >
                      {tab.label}
                    </button>
                  ))}
                  <button
                    onClick={() => {
                      if (currentProject) {
                        setPurposeDraft(currentProject.description || "");
                      }
                      setShowPurposeModal(true);
                    }}
                    disabled={!currentProject}
                    className={`flex-none ${sidebarOpen ? "min-w-[170px]" : "min-w-[200px]"} px-3 py-2.5 text-sm font-semibold rounded-xl transition-all duration-300 shadow-md ${
                      currentProject
                        ? "bg-slate-800/80 text-slate-100 hover:bg-slate-700 hover:scale-[1.01]"
                        : "bg-slate-800/40 text-slate-500 cursor-not-allowed"
                    }`}
                  >
                    Güncel Amaç
                  </button>
                </div>
              </div>
            </div>

            {activeTab !== "wizard" && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <SprintSelect
                  sprints={sprints}
                  selectedSprint={selectedSprint}
                  onSelect={setSelectedSprint}
                  loading={loadingSprints}
                  disabled={!selectedProject}
                />
              </div>
            )}

            {activeTab === "jobs" ? (
              <>
                <JobConsole projectId={selectedProject} sprintId={selectedSprint} />
                <ReadyTasksList sprintId={selectedSprint} />
                <SprintTaskBoard sprintId={selectedSprint} />
              </>
            ) : activeTab === "wizard" ? (
              <div className="px-2 md:px-4">
                <SpecWizard projectId={selectedProject} />
              </div>
            ) : activeTab === "planning" ? (
              <>
                <PlanningView projectId={selectedProject} />
                <SprintTaskBoard sprintId={selectedSprint} />
              </>
            ) : (
              <StatusView projectId={selectedProject} />
            )}
          </>
        )}
      </main>
    </div>
  );
}
