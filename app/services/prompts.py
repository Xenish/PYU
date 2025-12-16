from typing import List, Optional

from app.core.enums import PlanningDetailLevel
from app.models.project import (
    ArchitectureComponent,
    Feature,
    Project,
    ProjectObjective,
    TechStackOption,
)
from app.models.quality import DoDItem, NFRItem, RiskItem


def _detail_hint(detail_level: PlanningDetailLevel) -> str:
    if detail_level == PlanningDetailLevel.LOW:
        return "Daha az ve yüksek seviye maddeler üret."
    if detail_level == PlanningDetailLevel.HIGH:
        return "Daha detaylı ve kapsamlı maddeler üret."
    return "Varsayılan detay seviyesinde üret."


def _append_selected_hint(base: str, header: str, lines: List[str]) -> str:
    if not lines:
        return base
    approved_text = "\n".join(lines)
    base += f"\n\n{header}\n{approved_text}\n"
    base += "Yeni maddeler bunları tamamlasın, tekrar etmesin."
    return base


def build_objective_prompt(
    project: Project, selected_items: Optional[List[ProjectObjective]] = None
) -> str:
    prompt = (
        f"Proje adı: {project.name}\n"
        f"Açıklama: {project.description or ''}\n"
        "Türkçe proje hedefleri üret. En fazla 10 yeni hedef öner; onaylı hedefleri tekrar etme.\n"
        "Her hedef için decision-support alanlarını doldur: "
        "priority_score(1-5), impact_level(low|medium|high|critical), recommendation_type(recommended|optional|critical), "
        "category_tags, rationale, advantages, disadvantages, conflicts_with[], requires[], category_exclusive (true/false).\n"
        "Sadece aşağıdaki JSON formatında cevap ver:\n"
        '{\n'
        '  "objectives": [\n'
        '    {"title": "...", "description": "...", "priority": 1, "priority_score": 3, "impact_level": "high", "recommendation_type": "recommended", "category_tags": ["strategy"], "rationale": "...", "advantages": ["..."], "disadvantages": ["..."], "conflicts_with": [], "requires": [], "category_exclusive": false}\n'
        "  ]\n"
        "}\n"
        "priority 1-5 arası sayı olsun."
    )

    if selected_items:
        lines = [f"- {obj.title}: {obj.text or ''}" for obj in selected_items]
        prompt = _append_selected_hint(prompt, "Onaylanmış hedefler:", lines)

    return prompt


def build_tech_stack_prompt(
    project: Project, selected_items: Optional[List[TechStackOption]] = None
) -> str:
    prompt = (
        f"Proje: {project.name}\n"
        f"Açıklama: {project.description or ''}\n"
        f"Detay seviyesi: {_detail_hint(project.planning_detail_level)}\n"
        "Frontend/Backend/Database/Infra/Analytics/CI-CD için teknoloji önerileri üret. En fazla 10 yeni tercih öner; onaylı tercihleri tekrar etme.\n"
        "Her tercih için decision-support alanlarını doldur: priority_score(1-5), impact_level(low|medium|high|critical), recommendation_type(recommended|optional|critical), "
        "category_tags, rationale, advantages, disadvantages, conflicts_with[], requires[], category_exclusive(true/false).\n"
        "Sadece aşağıdaki JSON formatında cevap ver:\n"
        '{\n'
        '  "items": [\n'
        '    {"category": "frontend", "name": "React", "rationale": "...", "priority_score": 5, "impact_level": "critical", "recommendation_type": "recommended", "category_tags": ["ui"], "advantages": ["..."], "disadvantages": ["..."], "conflicts_with": [], "requires": [], "category_exclusive": true},\n'
        '    {"category": "backend", "name": "FastAPI", "rationale": "..."},\n'
        '    {"category": "db", "name": "PostgreSQL", "rationale": "..."},\n'
        '    {"category": "infra", "name": "Docker", "rationale": "..."}\n'
        "  ]\n"
        "}\n"
        "category değerleri: frontend, backend, db, infra, analytics, ci_cd"
    )

    if selected_items:
        lines = []
        for item in selected_items:
            for section in ["frontend", "backend", "database", "infra", "analytics", "ci_cd"]:
                section_data = getattr(item, section, None) or {}
                if section_data.get("name"):
                    lines.append(f"- {section}: {section_data.get('name')}")
        prompt = _append_selected_hint(prompt, "Onaylanmış teknoloji tercihleri:", lines)

    return prompt


def build_feature_prompt(
    project: Project, selected_items: Optional[List[Feature]] = None
) -> str:
    prompt = (
        f"Proje: {project.name}\n"
        f"Açıklama: {project.description or ''}\n"
        f"Detay seviyesi: {_detail_hint(project.planning_detail_level)}\n"
        "Must ve optional özellikler öner. En fazla 10 yeni özellik ekle; onaylı özellikleri tekrar etme.\n"
        "Her özellik için decision-support alanlarını doldur: priority_score(1-5), impact_level(low|medium|high|critical), recommendation_type(recommended|optional|critical), "
        "category_tags, rationale, advantages, disadvantages, conflicts_with[], requires[], category_exclusive(true/false).\n"
        "Sadece aşağıdaki JSON formatında cevap ver:\n"
        '{\n'
        '  "features": [\n'
        '    {"title": "Kullanıcı Girişi", "description": "...", "importance": 5, "feature_type": "must", "group": "auth", "priority_score": 5, "impact_level": "critical", "recommendation_type": "recommended", "category_tags": ["auth"], "rationale": "...", "advantages": ["..."], "disadvantages": ["..."], "conflicts_with": [], "requires": [], "category_exclusive": false},\n'
        '    {"title": "Dashboard", "description": "...", "importance": 4, "feature_type": "must", "group": "core"}\n'
        "  ]\n"
        "}\n"
        "importance: 1-5 arası, feature_type: must veya optional"
    )

    if selected_items:
        lines = [
            f"- {feat.name} ({feat.type}): {feat.description or ''}"
            for feat in selected_items
        ]
        prompt = _append_selected_hint(prompt, "Onaylanmış özellikler:", lines)

    return prompt


def build_architecture_prompt(
    project: Project, selected_items: Optional[List[ArchitectureComponent]] = None
) -> str:
    prompt = (
        f"Proje: {project.name}\n"
        f"Açıklama: {project.description or ''}\n"
        f"Detay seviyesi: {_detail_hint(project.planning_detail_level)}\n"
        "Katmanlı mimari bileşenlerini listele. En fazla 10 yeni bileşen ekle; onaylı bileşenleri tekrar etme.\n"
        "Her bileşen için decision-support alanlarını doldur: priority_score(1-5), impact_level(low|medium|high|critical), recommendation_type(recommended|optional|critical), "
        "category_tags, rationale, advantages, disadvantages, conflicts_with[], requires[], category_exclusive(true/false).\n"
        "Sadece aşağıdaki JSON formatında cevap ver:\n"
        '{\n'
        '  "components": [\n'
        '    {"name": "API Gateway", "layer": "backend", "description": "...", "responsibilities": ["routing", "auth"], "priority_score": 5, "impact_level": "critical", "recommendation_type": "recommended", "category_tags": ["backend"], "rationale": "...", "advantages": ["..."], "disadvantages": ["..."], "conflicts_with": [], "requires": [], "category_exclusive": false},\n'
        '    {"name": "React App", "layer": "frontend", "description": "...", "responsibilities": ["UI", "state"]}\n'
        "  ]\n"
        "}\n"
        "layer değerleri: frontend, backend, infra, data, shared"
    )

    if selected_items:
        lines = [
            f"- {comp.name} ({comp.layer}): {comp.description or ''}"
            for comp in selected_items
        ]
        prompt = _append_selected_hint(prompt, "Onaylanmış mimari bileşenler:", lines)

    return prompt


def build_quality_prompt(
    project: Project,
    selected_dod: Optional[List[DoDItem]] = None,
    selected_nfr: Optional[List[NFRItem]] = None,
    selected_risks: Optional[List[RiskItem]] = None,
) -> str:
    prompt = (
        f"Proje: {project.name}\n"
        f"Açıklama: {project.description or ''}\n"
        f"Detay seviyesi: {_detail_hint(project.planning_detail_level)}\n"
        "DoD maddeleri, NFR maddeleri ve riskleri öner. Toplamda en fazla 10 yeni madde üret; onaylı maddeleri tekrar etme.\n"
        "Her madde için decision-support alanlarını doldur: priority_score(1-5), impact_level(low|medium|high|critical), recommendation_type(recommended|optional|critical), "
        "category_tags, rationale, advantages, disadvantages, conflicts_with[], requires[], category_exclusive(true/false).\n"
        "Sadece aşağıdaki JSON formatında cevap ver:\n"
        '{\n'
        '  "dod_items": [\n'
        '    {"description": "Unit test coverage %80", "category": "functional", "test_method": "pytest", "done_when": "all tests pass", "priority": 5, "priority_score": 5, "impact_level": "high", "recommendation_type": "recommended", "category_tags": ["quality"], "rationale": "...", "advantages": ["..."], "disadvantages": ["..."], "conflicts_with": [], "requires": [], "category_exclusive": false}\n'
        "  ],\n"
        '  "nfr_items": [\n'
        '    {"type": "performance", "description": "API yanıt süresi <200ms", "measurable_target": "p95 < 200ms", "priority_score": 5, "impact_level": "critical", "recommendation_type": "recommended"}\n'
        "  ],\n"
        '  "risks": [\n'
        '    {"description": "Üçüncü parti API kesintisi", "impact": 4, "likelihood": 3, "mitigation": "Fallback mekanizması", "priority_score": 5, "impact_level": "critical", "recommendation_type": "critical"}\n'
        "  ]\n"
        "}\n"
        "dod category: functional, non_functional, process | nfr type: performance, security, reliability, ux, observability, other"
    )

    lines: list[str] = []
    if selected_dod:
        lines.extend([f"- DoD ({d.category}): {d.description}" for d in selected_dod])
    if selected_nfr:
        lines.extend([f"- NFR ({n.type}): {n.description}" for n in selected_nfr])
    if selected_risks:
        lines.extend([f"- Risk: {r.description}" for r in selected_risks])

    if lines:
        prompt = _append_selected_hint(prompt, "Onaylı girdiler:", lines)

    return prompt


def build_task_draft_prompt(epic, sprint, detail_level: PlanningDetailLevel) -> str:
    return (
        f"Epik: {epic.name}\n"
        f"Epik açıklaması: {epic.description or ''}\n"
        f"Sprint: {sprint.name}\n"
        f"Detay seviyesi: {_detail_hint(detail_level)}\n"
        "Bu epik için 5-15 arası yüksek seviye, 1-2 günlük iş paketi taslak task üret. "
        "Her biri net bir başlık ve kısa açıklama içersin."
    )


def build_task_refinement_prompt(tasks, dod_items, nfr_items, detail_level: PlanningDetailLevel) -> str:
    dod_hint = ", ".join(
        [
            getattr(d, "description", "") or getattr(d, "category", "")
            for d in dod_items
            if (getattr(d, "description", None) or getattr(d, "category", None))
        ]
    ) or "DoD yok"
    nfr_hint = ", ".join(
        [
            getattr(n, "type", "") or getattr(n, "category", "")
            for n in nfr_items
            if (getattr(n, "type", None) or getattr(n, "category", None))
        ]
    ) or "NFR yok"
    task_lines = "\n".join(
        [f"- ({t.id}) {t.title}: {t.description or ''}" for t in tasks]
    )
    return (
        "Aşağıdaki taslak task'leri daha net hale getir:\n"
        f"{task_lines}\n"
        f"Detay seviyesi: {_detail_hint(detail_level)}\n"
        f"DoD odakları: {dod_hint}\n"
        f"NFR odakları: {nfr_hint}\n"
        "Her task için başlık, açıklama, 3-5 acceptance criteria, opsiyonel dod_focus/nfr_focus, "
        "ve depend_on_task_ids listesi ver."
    )


def build_task_split_prompt(tasks, detail_level: PlanningDetailLevel) -> str:
    task_lines = "\n".join(
        [f"- ({t.id}) {t.title}: {t.description or ''}" for t in tasks]
    )
    return (
        "Aşağıdaki medium seviyedeki task'leri dev'e hazır fine task'lere böl:\n"
        f"{task_lines}\n"
        f"Detay seviyesi: {_detail_hint(detail_level)}\n"
        "Her parent task için 0-N adet küçük task üret; her biri tek deliverable içersin, "
        "açıklama ve 2-5 acceptance criteria net olsun, estimate_sp (1-5 arası) varsa ekle. "
        "Her fine task çıktısında parent_task_id'yi belirt."
    )


def build_project_suggestion_prompt(project_name: str, project_description: str) -> str:
    """Build prompt for initial project suggestions."""
    return f"""Sen bir yazılım proje danışmanısın. Kullanıcının proje fikri hakkında stratejik, teknik ve operasyonel öneriler sunuyorsun.

Proje Adı: {project_name}
Proje Amacı: {project_description}

Görevin:
1. Projenin amacını analiz et
2. En fazla 10 öneri sun (az ama kaliteli)
3. Her öneri için kategori belirle: strategy (strateji), technical (teknik), process (süreç), quality (kalite)
4. Her öneriye 2-3 örnek kullanım senaryosu ekle
5. Öncelik puanı (1-5), etki seviyesi ve tavsiye türü belirle

SADECE aşağıdaki JSON formatında cevap ver:
{{
  "suggestions": [
    {{
      "title": "Kısa başlık",
      "description": "Detaylı açıklama",
      "category": "strategy|technical|process|quality",
      "examples": ["Örnek 1", "Örnek 2"],
      "priority_score": 1-5,
      "impact_level": "low|medium|high|critical",
      "recommendation_type": "recommended|optional|critical",
      "category_tags": ["tag1", "tag2"],
      "rationale": "Bu neden önemli",
      "advantages": ["Avantaj 1", "Avantaj 2"],
      "disadvantages": ["Dezavantaj 1"]
    }}
  ]
}}

Türkçe yaz. JSON formatı bozma."""


def build_project_review_prompt(
    project_name: str,
    project_description: str,
    existing_suggestions: list[dict],
) -> str:
    """Build prompt for project review and new suggestions."""
    suggestions_text = []
    for s in existing_suggestions:
        title = s['title']
        desc = s.get('description', 'N/A')
        examples = s.get('examples', [])
        added = s.get('user_added_examples', [])

        suggestion_line = f"- {title}: {desc}"
        if examples:
            unused = [ex for ex in examples if ex not in added]
            if unused:
                suggestion_line += f"\n  Kullanılmayan örnekler: {', '.join(unused)}"
            if added:
                suggestion_line += f"\n  Kullanıcının eklediği: {', '.join(added)}"

        suggestions_text.append(suggestion_line)

    suggestions_formatted = "\n".join(suggestions_text)

    return f"""Sen bir yazılım proje danışmanısın. Kullanıcının proje açıklamasını ve verdiği yanıtları değerlendiriyorsun.

Proje Adı: {project_name}
Proje Amacı: {project_description}

Mevcut Öneriler ve Kullanıcı Yanıtları:
{suggestions_formatted}

ÖNEMLİ: Kullanıcı zaten bazı örnekleri proje açıklamasına ekledi. Bu önerileri TEKRAR VERME.
Sadece henüz kullanılmayan örnekler için değerlendirme yap ve FARKLI, YENİ öneriler sun.

Görevlerin:
1. Her öneri için kullanıcının yanıtını değerlendir:
   - Kullanıcı bu örnekleri projeye ekledi mi? (user_added_examples'a bak)
   - Eğer tüm örnekler eklendiyse, bu öneri tamamlanmış sayılır
   - Sadece kullanılmayan örnekler için geri bildirim ver

2. Proje açıklamasına göre YENİ, FARKLI öneriler sun:
   - Daha önce verilmemiş konular
   - Eksik kalan noktalar
   - İyileştirme fırsatları
   - Risk azaltma stratejileri
   - Mevcut önerilerden FARKLI olmalı!

3. Genel değerlendirme yap:
   - Proje açıklaması yeterince detaylı mı?
   - Kritik eksikler var mı?
   - Bir sonraki adım ne olmalı?

ÖNEMLİ: Eğer bir öneri yetersiz (is_adequate=false) ise:
1. expanded_suggestions'a o öneriyi detaylandıran 2-3 alternatif ekle
2. Her alternatif kısa ve net olsun (max 100 karakter description)
3. Fazla alan kullanma, JSON'ı kompakt tut

SADECE geçerli JSON formatında cevap ver, başka metin ekleme:
{{
  "reviews": [
    {{
      "suggestion_title": "string",
      "is_adequate": true,
      "feedback": null,
      "new_questions": null,
      "expanded_suggestions": null
    }}
  ],
  "new_suggestions": [],
  "overall_feedback": "string"
}}

Yetersiz öneri için expanded_suggestions örneği:
{{
  "suggestion_title": "Hedef kitle",
  "is_adequate": false,
  "feedback": "Çok genel, detaylandır",
  "new_questions": null,
  "expanded_suggestions": [
    {{
      "title": "Hedef kitle - Demografik",
      "description": "Yaş, cinsiyet, gelir düzeyi bazında hedef kitle",
      "category": "strategy",
      "examples": ["18-35 yaş kadınlar", "Orta gelir seviyesi"],
      "priority_score": 4,
      "impact_level": "high",
      "recommendation_type": "recommended",
      "category_tags": ["demographics"],
      "rationale": "Pazarlama stratejisi için kritik",
      "advantages": ["Net hedefleme"],
      "disadvantages": ["Dar segment"]
    }},
    {{
      "title": "Hedef kitle - Davranışsal",
      "description": "Kullanıcı davranışları ve alışkanlıkları",
      "category": "strategy",
      "examples": ["Online alışveriş yapanlar", "Mobil kullanıcılar"],
      "priority_score": 4,
      "impact_level": "high",
      "recommendation_type": "recommended",
      "category_tags": ["behavior"],
      "rationale": "Kullanıcı deneyimi tasarımı için gerekli",
      "advantages": ["Kişiselleştirme"],
      "disadvantages": ["Veri toplama gerekir"]
    }},
    {{
      "title": "Hedef kitle - İş profili",
      "description": "Sektör, pozisyon, şirket büyüklüğü",
      "category": "strategy",
      "examples": ["KOBİ sahipleri", "Teknoloji startupları"],
      "priority_score": 3,
      "impact_level": "medium",
      "recommendation_type": "optional",
      "category_tags": ["b2b"],
      "rationale": "B2B için önemli",
      "advantages": ["Net değer önerisi"],
      "disadvantages": ["Sınırlı pazar"]
    }}
  ]
}}

Kurallar:
- Türkçe karakter kullan ama JSON string'lerinde tırnak işareti ve backslash kullanma
- Çift tırnak yerine tek tırnak kullan
- Yeni satır yerine nokta kullan
- Sadece geçerli JSON döndür, başka açıklama ekleme"""



def build_expand_suggestion_prompt(
    project_name: str,
    project_description: str,
    suggestion_title: str,
    suggestion_description: str,
) -> str:
    """Build prompt for expanding a single suggestion into 3 detailed versions."""
    return f"""Sen bir yazılım proje danışmanısın. Kullanıcının bir önerisini 3 farklı şekilde detaylandırıyorsun.

Proje Adı: {project_name}
Proje Amacı: {project_description}

Detaylandırılacak Öneri:
Başlık: {suggestion_title}
Açıklama: {suggestion_description}

Görevin:
Bu öneriyi 3 FARKLI açıdan detaylandır. Her versiyon:
1. Farklı bir yönü vurgulasın (örn: güvenlik, performans, kullanıcı deneyimi)
2. Somut, uygulanabilir örnekler içersin
3. Kısa ve net olsun (max 100 karakter açıklama)

SADECE geçerli JSON formatında cevap ver:
{{
  "suggestions": [
    {{
      "title": "{suggestion_title} - Detay 1",
      "description": "Kısa açıklama",
      "category": "strategy",
      "examples": ["Örnek 1", "Örnek 2", "Örnek 3"],
      "priority_score": 4,
      "impact_level": "high",
      "recommendation_type": "recommended",
      "category_tags": ["tag1"],
      "rationale": "Neden önemli",
      "advantages": ["Avantaj 1"],
      "disadvantages": []
    }}
  ]
}}

Türkçe yaz. Geçerli JSON üret."""
