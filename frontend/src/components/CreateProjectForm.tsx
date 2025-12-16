import { useEffect, useState } from "react";
import { createProject, generateProjectSuggestions, reviewProjectSuggestions, markExampleAsAdded, expandSuggestion, ProjectSuggestion, ProjectReviewResponse, Project } from "@/lib/api";

type Suggestion = { title: string; examples: string[] };

const buildSuggestions = (name: string, description: string): Suggestion[] => {
  const trimmedName = name.trim();
  const trimmedDesc = description.trim();
  const baseKeywords = `${trimmedName} ${trimmedDesc}`
    .split(/\s+/)
    .map((w) => w.toLowerCase())
    .filter((w) => w.length > 3);
  const uniqueKeywords = Array.from(new Set(baseKeywords)).slice(0, 4);

  const hints: Suggestion[] = [
    {
      title: uniqueKeywords.length
        ? `Bu ifadeleri aç: ${uniqueKeywords.join(", ")}`
        : "Önemli akışları netleştir",
      examples: [
        "Ne için, kim kullanacak, hangi cihazdan ve başarı ölçütü nedir?",
        "Günlük kaç kullanıcı/ekip bu akışı kullanacak ve pik zamanları nedir?",
      ],
    },
    {
      title: "Kullanıcı rolleri ve yetkilendirme",
      examples: [
        "Patron, yönetici, çalışan rollerinin hangi ekranlara eriştiğini yaz.",
        "Rol bazlı onay/iptal yetkisi, vardiya değişikliği sınırları neler?",
      ],
    },
    {
      title: "Vardiya kuralları",
      examples: [
        "Vardiya uzunluğu, fazla mesai limiti, dinlenme arası süresi ve çakışma kuralını belirt.",
        "Vardiya swap/değiş-tokuş akışı nasıl işliyor? Onay gerektiriyor mu?",
      ],
    },
    {
      title: "Bildirim ve onay akışları",
      examples: [
        "Hangi aksiyonlarda e-posta/SMS/push gönderilecek? (vardiya değişikliği, onay, reddetme)",
        "Bildirim gecikme/tekrar deneme ve sessize alma kuralları var mı?",
      ],
    },
    {
      title: "Raporlama ihtiyacı",
      examples: [
        "Kim hangi vardiyada çalıştı, toplam saat ve maliyet raporlarını tanımla.",
        "Filtreler: tarih aralığı, lokasyon, rol; dışa aktarma (CSV/PDF) ihtiyacı var mı?",
      ],
    },
  ];

  if (trimmedDesc.toLowerCase().includes("mobil") || trimmedName.toLowerCase().includes("mobil")) {
    hints.unshift({
      title: "Mobil ve çevrimdışı kullanım",
      examples: [
        "Bağlantı yokken hangi işlemler yapılabilir, veri nasıl saklanır ve ne zaman senkron olur?",
        "Arka planda konum/bildirim izinleri gerekiyor mu? Platformlara göre farklar neler?",
      ],
    });
  }

  return hints;
};

type Props = {
  onCreated: (project: Project) => void;
  onSuggestionsToggle?: (visible: boolean) => void;
  onSuggestPreview?: (name: string | null) => void;
  initialDraftName?: string | null;
  initialDraftDescription?: string | null;
  initialDraftSuggestions?: Suggestion[] | null;
};

export function CreateProjectForm({
  onCreated,
  onSuggestionsToggle,
  onSuggestPreview,
  initialDraftName,
  initialDraftDescription,
  initialDraftSuggestions,
}: Props) {
  const DRAFT_KEY = "create_project_draft";
  const [name, setName] = useState(initialDraftName || "");
  const [description, setDescription] = useState(initialDraftDescription || "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<Suggestion[]>(initialDraftSuggestions || []);
  const [projectId, setProjectId] = useState<number | null>(null);
  const [llmSuggestions, setLlmSuggestions] = useState<ProjectSuggestion[]>([]);
  const [reviewFeedback, setReviewFeedback] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [expandingId, setExpandingId] = useState<number | null>(null);
  const [expandedSuggestions, setExpandedSuggestions] = useState<Record<number, ProjectSuggestion[]>>({});
  const [showExpandPopup, setShowExpandPopup] = useState<number | null>(null);
  const showSplit = suggestions.length > 0 || llmSuggestions.length > 0;
  useEffect(() => {
    onSuggestionsToggle?.(suggestions.length > 0);
  }, [suggestions.length, onSuggestionsToggle]);

  // Draft load
  useEffect(() => {
    if (initialDraftName || initialDraftDescription || (initialDraftSuggestions && initialDraftSuggestions.length)) {
      return;
    }
    try {
      const stored = localStorage.getItem(DRAFT_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        setName(parsed.name || "");
        setDescription(parsed.description || "");
        if (Array.isArray(parsed.suggestions)) {
          setSuggestions(parsed.suggestions);
        }
      }
    } catch (err) {
      console.warn("Draft load error", err);
    }
  }, [initialDraftName, initialDraftDescription, initialDraftSuggestions]);

  // Draft save
  useEffect(() => {
    try {
      localStorage.setItem(DRAFT_KEY, JSON.stringify({ name, description, suggestions }));
    } catch (err) {
      console.warn("Draft save error", err);
    }
  }, [name, description, suggestions]);

  // Sidebar preview update from persisted state as well
  useEffect(() => {
    onSuggestPreview?.(showSplit && name.trim() ? name.trim() : null);
  }, [showSplit, name, onSuggestPreview]);

  const appendToDescription = (text: string) => {
    setDescription((prev) => {
      const alreadyHas = prev.toLowerCase().includes(text.toLowerCase());
      if (alreadyHas) return prev;
      const trimmed = prev.trim();
      const prefix = trimmed ? "\n" : "";
      return `${trimmed}${prefix}- ${text}`;
    });
  };

  const addLLMExample = async (suggestionId: number, exampleText: string) => {
    if (!projectId) return;

    // Add to description
    appendToDescription(exampleText);

    // Mark as added in backend
    try {
      await markExampleAsAdded(projectId, suggestionId, exampleText);

      // Update local state to reflect the change
      setLlmSuggestions(prev =>
        prev.map(s =>
          s.id === suggestionId
            ? {
                ...s,
                user_added_examples: [...(s.user_added_examples || []), exampleText],
              }
            : s
        )
      );
    } catch (err: any) {
      setError(`Örnek eklenirken hata: ${err.message}`);
    }
  };

  const handleExpandSuggestion = async (suggestionId: number) => {
    if (!projectId) return;

    // If already expanded and showing popup, just toggle popup
    if (expandedSuggestions[suggestionId]) {
      setShowExpandPopup(showExpandPopup === suggestionId ? null : suggestionId);
      return;
    }

    // Otherwise, expand it
    setExpandingId(suggestionId);
    setError(null);

    try {
      const result = await expandSuggestion(projectId, suggestionId);
      setExpandedSuggestions(prev => ({
        ...prev,
        [suggestionId]: result.expanded_suggestions,
      }));
      setShowExpandPopup(suggestionId);
    } catch (err: any) {
      setError(`Detaylandırma hatası: ${err.message}`);
    } finally {
      setExpandingId(null);
    }
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    if (!description.trim()) {
      setError("Proje amacı gerekli; diğer adımlar buna göre üretilecek.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const project = await createProject(name.trim(), description.trim() || undefined);
      setName("");
      setDescription("");
      onCreated(project);
      onSuggestPreview?.(null);
      try {
        localStorage.removeItem(DRAFT_KEY);
      } catch (err) {
        console.warn("Draft clear error", err);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const suggest = async () => {
    if (!name.trim() || !description.trim()) {
      setError("Önce proje adı ve amacı girin, sonra öneri isteyin.");
      return;
    }

    if (description.trim().length < 20) {
      setError("Proje amacı en az 20 karakter olmalıdır.");
      return;
    }

    setError(null);
    setGenerating(true);

    try {
      // Create project first
      const project = await createProject(name.trim(), description.trim());
      setProjectId(project.id);

      // Generate LLM suggestions
      const llmSuggs = await generateProjectSuggestions(project.id);
      setLlmSuggestions(llmSuggs);

      // Keep old heuristic suggestions as fallback/additional context
      setSuggestions(buildSuggestions(name, description));
      onSuggestPreview?.(name.trim());
    } catch (err: any) {
      setError(`Öneri üretilirken hata: ${err.message}`);
    } finally {
      setGenerating(false);
    }
  };

  const aiReview = async () => {
    if (!projectId) {
      setError("Önce 'Öneri ver' butonuna tıklayın.");
      return;
    }

    if (!name.trim() || !description.trim()) {
      setError("Proje adı ve amacı boş olamaz.");
      return;
    }

    setError(null);
    setGenerating(true);

    try {
      const result: ProjectReviewResponse = await reviewProjectSuggestions(projectId);

      // Merge new suggestions with existing
      setLlmSuggestions(prev => [...prev, ...result.new_suggestions]);
      setReviewFeedback(result.overall_feedback);

      // Show reviews to user
      const inadequateReviews = result.reviews.filter(r => !r.is_adequate);
      if (inadequateReviews.length > 0) {
        const expandedCount = inadequateReviews.reduce(
          (sum, r) => sum + (r.expanded_suggestions?.length || 0),
          0
        );
        const feedbackText = inadequateReviews
          .map(r => `• ${r.suggestion_title}: ${r.feedback || 'Yetersiz'}`)
          .join("\n");
        setReviewFeedback(
          `Yetersiz yanıtlar bulundu:\n${feedbackText}\n\n✨ ${expandedCount} detaylandırılmış öneri aşağıda eklendi.`
        );
      }
    } catch (err: any) {
      setError(`Kontrol sırasında hata: ${err.message}`);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <form
      onSubmit={submit}
      className="w-full space-y-4"
    >
      <div
        className={`flex justify-center overflow-hidden transition-all duration-[1500ms] ease-in-out ${
          showSplit && name ? "mb-4 md:mb-6 max-h-24 opacity-100" : "mb-0 max-h-0 opacity-0"
        }`}
      >
        {showSplit && name && (
          <span className="relative inline-block text-2xl md:text-3xl uppercase tracking-[0.3em] bg-gradient-to-r from-emerald-300 via-sky-300 to-indigo-300 bg-[length:300%_100%] bg-clip-text text-transparent drop-shadow animate-[gradient-slide_10s_linear_infinite]">
            {name.toLocaleUpperCase("tr-TR")}
          </span>
        )}
      </div>
      <div
        className={`${
          showSplit ? "md:flex md:items-start md:gap-4 md:justify-center" : "space-y-3"
        } transition-all duration-[1500ms] ease-in-out`}
      >
        <div className={`${showSplit ? "md:w-[520px] md:max-w-[700px] md:flex-shrink-0 md:space-y-4" : "space-y-3"}`}>
          <div className="rounded-2xl border border-slate-700/70 bg-slate-900/70 p-3 shadow-lg">
            {showSplit && <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Proje Adı</div>}
            <div className="mt-2 flex items-center gap-2">
              <input
                className="w-full rounded border border-slate-700 bg-slate-900 p-2 text-sm text-slate-100"
                placeholder="Proje adı"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
          </div>

          <div className="rounded-2xl border border-slate-700/70 bg-slate-900/70 p-3 shadow-lg h-full mt-3">
            {showSplit && <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Proje Amacı</div>}
            <textarea
              className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-900 p-3 text-sm text-slate-100 min-h-[180px]"
              placeholder="Proje amacı / iş problemi (zorunlu)"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
            {error && <div className="text-xs text-red-300">{error}</div>}
            <div className="mt-3 flex flex-col gap-2 md:flex-row md:items-center md:gap-3">
              <button
                type="button"
                onClick={suggest}
                disabled={generating || !name.trim() || !description.trim()}
                className="w-full md:w-auto rounded-lg border border-slate-600 bg-slate-800 px-4 py-2 text-sm font-semibold text-slate-100 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {generating ? "Üretiliyor..." : "Öneri ver"}
              </button>
              {(suggestions.length > 0 || llmSuggestions.length > 0) && (
                <button
                  type="button"
                  onClick={aiReview}
                  disabled={generating || !projectId}
                  className="w-full md:w-auto rounded-lg border border-amber-500/70 bg-amber-500/20 px-4 py-2 text-sm font-semibold text-amber-100 hover:bg-amber-500/30 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {generating ? "Kontrol ediliyor..." : "Kontrol ve yenilik"}
                </button>
              )}
              <div className="flex-1" />
              <button
                type="submit"
                disabled={loading}
                className="w-full md:w-auto rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-50"
              >
                {loading ? "Oluşturuluyor..." : "Oluştur"}
              </button>
            </div>
          </div>
        </div>

        {(suggestions.length > 0 || llmSuggestions.length > 0) && (
          <div className="mt-2 space-y-2 md:mt-0 md:w-[520px] md:max-w-[700px] md:flex-none">
            <div className="rounded-2xl border border-slate-700/70 bg-slate-900/80 p-3 shadow-lg h-full space-y-2">
              <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Öneriler</div>

              {/* Review feedback */}
              {reviewFeedback && (
                <div className="mb-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded text-sm text-blue-200">
                  <strong>AI Değerlendirmesi:</strong> {reviewFeedback}
                </div>
              )}

              {/* LLM Suggestions */}
              {llmSuggestions.length > 0 && (
                <div className="space-y-2">
                  <div className="text-xs font-semibold text-emerald-300">AI Önerileri</div>
                  <ul className="space-y-3 text-sm text-slate-100">
                    {llmSuggestions.map((sug) => (
                      <li key={sug.id} className="rounded border border-emerald-700/60 bg-slate-900/60 p-3">
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="font-semibold text-slate-50">{sug.title}</span>
                              {sug.recommendation_type && (
                                <span className={`text-xs px-2 py-0.5 rounded ${
                                  sug.recommendation_type === 'critical' ? 'bg-red-500/20 text-red-200' :
                                  sug.recommendation_type === 'recommended' ? 'bg-emerald-500/20 text-emerald-200' :
                                  'bg-slate-500/20 text-slate-300'
                                }`}>
                                  {sug.recommendation_type}
                                </span>
                              )}
                              <button
                                type="button"
                                onClick={() => handleExpandSuggestion(sug.id)}
                                disabled={expandingId === sug.id}
                                className={`text-xs px-2 py-0.5 rounded border ${
                                  expandedSuggestions[sug.id]
                                    ? 'border-purple-500/50 bg-purple-500/20 text-purple-200'
                                    : 'border-slate-600 bg-slate-800 text-slate-300'
                                } hover:bg-slate-700 disabled:opacity-50`}
                              >
                                {expandingId === sug.id ? 'Detaylandırılıyor...' :
                                 expandedSuggestions[sug.id] ? 'Detaylandırıldı ✓' :
                                 'Detaylandır'}
                              </button>
                            </div>
                            {sug.description && (
                              <p className="text-xs text-slate-400 mt-1">{sug.description}</p>
                            )}
                            {sug.rationale && (
                              <p className="text-xs text-slate-500 mt-1">
                                <strong>Neden:</strong> {sug.rationale}
                              </p>
                            )}
                            {sug.examples && sug.examples.length > 0 && (
                              <ul className="mt-2 space-y-1">
                                {sug.examples.map((ex, i) => {
                                  const isAdded = sug.user_added_examples?.includes(ex);
                                  return (
                                    <li key={i} className="text-xs text-slate-400 flex items-start gap-2">
                                      <span className={`flex-1 ${isAdded ? 'line-through opacity-50' : ''}`}>
                                        • {ex}
                                      </span>
                                      {!isAdded && (
                                        <button
                                          type="button"
                                          onClick={() => addLLMExample(sug.id, ex)}
                                          className="whitespace-nowrap rounded border border-slate-600 px-2 py-0.5 text-[11px] font-semibold text-slate-100 hover:bg-slate-700"
                                        >
                                          Ekle
                                        </button>
                                      )}
                                      {isAdded && (
                                        <span className="text-[10px] text-emerald-400">✓ Eklendi</span>
                                      )}
                                    </li>
                                  );
                                })}
                              </ul>
                            )}
                          </div>
                        </div>

                        {/* Popup for expanded suggestions */}
                        {showExpandPopup === sug.id && expandedSuggestions[sug.id] && (
                          <div className="mt-3 pt-3 border-t border-purple-500/30">
                            <div className="flex items-center justify-between mb-2">
                              <div className="text-xs font-semibold text-purple-300">
                                Detaylandırılmış Versiyonlar ({expandedSuggestions[sug.id].length})
                              </div>
                              <button
                                type="button"
                                onClick={() => setShowExpandPopup(null)}
                                className="text-xs text-slate-400 hover:text-slate-200"
                              >
                                ✕ Kapat
                              </button>
                            </div>
                            <ul className="space-y-2">
                              {expandedSuggestions[sug.id].map((exp) => (
                                <li key={exp.id} className="rounded border border-purple-600/40 bg-purple-900/10 p-2">
                                  <div className="flex items-start justify-between gap-2">
                                    <div className="flex-1">
                                      <div className="text-xs font-semibold text-purple-200">{exp.title}</div>
                                      {exp.description && (
                                        <p className="text-xs text-slate-400 mt-1">{exp.description}</p>
                                      )}
                                      {exp.examples && exp.examples.length > 0 && (
                                        <ul className="mt-1 space-y-1">
                                          {exp.examples.map((ex, i) => {
                                            const isAdded = exp.user_added_examples?.includes(ex);
                                            return (
                                              <li key={i} className="text-xs text-slate-400 flex items-start gap-2">
                                                <span className={`flex-1 ${isAdded ? 'line-through opacity-50' : ''}`}>
                                                  • {ex}
                                                </span>
                                                {!isAdded && (
                                                  <button
                                                    type="button"
                                                    onClick={() => addLLMExample(exp.id, ex)}
                                                    className="whitespace-nowrap rounded border border-purple-600 px-2 py-0.5 text-[10px] font-semibold text-purple-200 hover:bg-purple-700"
                                                  >
                                                    Ekle
                                                  </button>
                                                )}
                                                {isAdded && (
                                                  <span className="text-[9px] text-emerald-400">✓</span>
                                                )}
                                              </li>
                                            );
                                          })}
                                        </ul>
                                      )}
                                    </div>
                                  </div>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Heuristic Suggestions */}
              {suggestions.length > 0 && (
                <div className="space-y-2">
                  {llmSuggestions.length > 0 && (
                    <div className="text-xs font-semibold text-slate-400 mt-3">Ek Öneriler</div>
                  )}
                  <ul className="space-y-3 text-sm text-slate-100">
                    {suggestions.map((s, idx) => (
                      <li key={idx} className="rounded border border-slate-700/60 bg-slate-900/60 p-3">
                        <div className="font-semibold text-slate-50">{s.title}</div>
                        <ul className="mt-2 list-disc space-y-1 pl-5 text-slate-200/90">
                          {s.examples.map((ex, exIdx) => (
                            <li key={exIdx} className="flex items-start gap-2">
                              <span className="flex-1">{ex}</span>
                              <button
                                type="button"
                                onClick={() => appendToDescription(ex)}
                                className="whitespace-nowrap rounded border border-slate-600 px-2 py-0.5 text-[11px] font-semibold text-slate-100 hover:bg-slate-700"
                              >
                                Ekle
                              </button>
                            </li>
                          ))}
                        </ul>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </form>
  );
}
