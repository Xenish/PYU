# AI Sprint Planner - Teknik Kurallar & Guardrail'ler

> **Bu doküman, master spec'in ayrılmaz parçasıdır. Implementasyon sırasında mutlaka uyulması gereken teknik kurallardır.**

---

## İçindekiler

1. [LLM Schema/Validasyon Disiplini](#1-llm-schemavalidasyon-disiplini)
2. [Cache, Stale ve Transaction Kuralları](#2-cache-stale-ve-transaction-kuralları)
3. [Soft Delete ve Query Kuralları](#3-soft-delete-ve-query-kuralları)
4. [Spec Lock Mekanizması](#4-spec-lock-mekanizması)
5. [Planning Detail Level Kontrolü](#5-planning-detail-level-kontrolü)
6. [Epic/Sprint Point Hesaplamaları](#6-epicsprint-point-hesaplamaları)
7. [DoD/NFR Tamamlama Önerileri](#7-dodnfr-tamamlama-önerileri)
8. [Timezone ve Tarih Kuralları](#8-timezone-ve-tarih-kuralları)
9. [Enum/Field Drift Önleme](#9-enumfield-drift-önleme)
10. [Task Bağımlılık Çözümleme](#10-task-bağımlılık-çözümleme)
11. [LLM Adapter Policy](#11-llm-adapter-policy)
12. [Export Kaynağı ve Snapshot İlişkisi](#12-export-kaynağı-ve-snapshot-ilişkisi)
13. [Import Pipeline ve Snapshot Uyumu](#13-import-pipeline-ve-snapshot-uyumu)
14. [Gap Analizi Veri Akışı](#14-gap-analizi-veri-akışı)
15. [Sprint Kapasite Yönetimi](#15-sprint-kapasite-yönetimi)
16. [Task Pipeline Tetikleme Kuralları](#16-task-pipeline-tetikleme-kuralları)
17. [Comment vs Human Notes Ayrımı](#17-comment-vs-human-notes-ayrımı)
18. [State Machine Kuralları (ProjectStep)](#18-state-machine-kuralları-projectstep)
19. [CI/CD Test Gereksinimleri](#19-cicd-test-gereksinimleri)
20. [Sprint Başlangıç Checklist](#20-sprint-başlangıç-checklist)

---

## 1. LLM Schema/Validasyon Disiplini

### Kural 1.1: Her LLM fonksiyonu için Pydantic şema ZORUNLU

```python
# ❌ YANLIŞ - Şemasız çağrı
response = llm.call(prompt)
data = json.loads(response)  # Bozuk olabilir!

# ✅ DOĞRU - Şemalı çağrı
class ObjectiveOptionsResponse(BaseModel):
    options: List[ObjectiveOption]
    
response = llm.call(prompt)
validated = ObjectiveOptionsResponse.model_validate_json(response)
```

### Kural 1.2: Bozuk cevap asla kaydedilmez

```python
def call_llm_with_validation(prompt: str, response_schema: Type[BaseModel]) -> BaseModel:
    for attempt in range(MAX_RETRIES):
        try:
            raw_response = llm_adapter.call(prompt)
            validated = response_schema.model_validate_json(raw_response)
            return validated
        except ValidationError as e:
            log_llm_call(status="validation_failed", error=str(e))
            if attempt == MAX_RETRIES - 1:
                raise LLMValidationError("AI'den geçerli yanıt alınamadı")
    # DB'ye hiçbir şey yazılmadı
```

### Kural 1.3: Golden test her LLM fonksiyonu için ZORUNLU

```
tests/llm/golden/
  generate_objective_options/
    input_1.json
    expected_output_1.json
  generate_tech_stack_options/
    ...
```

---

## 2. Cache, Stale ve Transaction Kuralları

### Kural 2.1: Input Hash Deterministikliği

```python
def compute_input_hash(input_dict: dict) -> str:
    normalized = json.dumps(
        input_dict,
        sort_keys=True,          # Key sıralama zorunlu
        ensure_ascii=False,
        default=str              # datetime → string
    )
    return hashlib.sha256(normalized.encode()).hexdigest()
```

### Kural 2.2: Stale Trigger Servisi

```python
STALE_DEPENDENCIES = {
    "objective": ["tech_stack", "features", "architecture", "dod", "nfr", "risks", "epics", "sprint_plan"],
    "tech_stack": ["architecture", "sprint_plan"],
    "features": ["architecture", "dod", "epics", "sprint_plan"],
    "architecture": ["dod", "nfr", "epics", "sprint_plan"],
    "dod": ["sprint_plan"],
    "nfr": ["sprint_plan"],
    "risks": ["epics", "sprint_plan"],
    "epics": ["sprint_plan"],
}

def mark_dependent_steps_stale(project_id: int, changed_step: str, db: Session):
    project = db.query(Project).get(project_id)
    if project.status == "planned":
        raise SpecLockedException("Proje kilitli")
    
    dependent_steps = STALE_DEPENDENCIES.get(changed_step, [])
    db.query(ProjectStep).filter(
        ProjectStep.project_id == project_id,
        ProjectStep.step_type.in_(dependent_steps),
        ProjectStep.status == "approved"
    ).update({"status": "stale"})
```

### Kural 2.3: Transaction + Idempotency

```python
async def generate_and_save(project_id: int, input_data: dict, db: Session):
    input_hash = compute_input_hash(input_data)
    
    # Cache kontrolü
    existing = db.query(ProjectStep).filter(
        ProjectStep.project_id == project_id,
        ProjectStep.last_input_hash == input_hash
    ).first()
    
    if existing and existing.last_output_json:
        return existing.last_output_json  # Cache'den dön
    
    # LLM çağrısı (transaction dışında)
    llm_response = await call_llm_with_validation(prompt, Schema)
    
    # Tek transaction'da her şeyi yaz
    with db.begin():
        # Entity'leri oluştur
        # Step'i güncelle
        # LLM log yaz
        pass
```

### Kural 2.4: LLM Retry Log Korelasyonu

```python
correlation_id = str(uuid4())
for attempt in range(1, MAX_RETRIES + 1):
    log = LLMCallLog(
        correlation_id=correlation_id,
        attempt_number=attempt,
        ...
    )
```

---

## 3. Soft Delete ve Query Kuralları

### Kural 3.1: Tüm query'lerde soft delete filtresi ZORUNLU

```python
# ❌ YANLIŞ
db.query(Epic).filter(Epic.project_id == project_id).all()

# ✅ DOĞRU
db.query(Epic).filter(
    Epic.project_id == project_id,
    Epic.is_deleted == False
).all()

# Veya ORM event ile otomatik
@event.listens_for(Session, "do_orm_execute")
def _add_soft_delete_filter(execute_state):
    if execute_state.is_select:
        execute_state.statement = execute_state.statement.where(
            execute_state.mapper.class_.is_deleted == False
        )
```

---

## 4. Spec Lock Mekanizması

### Kural 4.1: Planned durumda spec endpoint'leri 403

```python
SPEC_ENDPOINTS = [
    "/projects/{id}/objectives",
    "/projects/{id}/tech-stacks", 
    "/projects/{id}/features",
    "/projects/{id}/architecture",
    "/projects/{id}/dod",
    "/projects/{id}/nfr",
    "/projects/{id}/risks",
    "/projects/{id}/epics",
]

async def spec_lock_middleware(request: Request, call_next):
    if request.method in ["GET", "HEAD", "OPTIONS"]:
        return await call_next(request)
    
    project = db.query(Project).get(project_id)
    if project.status == "planned":
        return JSONResponse(
            status_code=403,
            content={
                "error": "spec_locked",
                "message": "Proje kilitli. Clone yapın.",
                "hint": f"POST /projects/{project_id}/clone"
            }
        )
```

### Kural 4.2: Stale vs Lock önceliği

```
Project.status == "planned" → 403 (lock)
Project.status != "planned" → stale kontrolü yapılabilir

Planned durumda stale flag'i SET EDİLMEZ.
```

---

## 5. Planning Detail Level Kontrolü

```python
TASK_ENDPOINTS = [
    "/sprints/{id}/tasks/generate-skeleton",
    "/sprints/{id}/tasks/refine",
    "/sprints/{id}/tasks/audit",
]

async def detail_level_middleware(request: Request, call_next):
    if project.planning_detail_level == "low":
        return JSONResponse(
            status_code=400,
            content={
                "error": "detail_level_low",
                "message": "planning_detail_level='high' olmalı"
            }
        )
```

---

## 6. Epic/Sprint Point Hesaplamaları

### Kural 6.1: Task done → Epic completed_points güncelle

```python
def update_task_status(task_id: int, new_status: str, db: Session):
    task = db.query(Task).get(task_id)
    old_status = task.status
    task.status = new_status
    
    if old_status != "done" and new_status == "done":
        if task.epic_id:
            epic = db.query(Epic).get(task.epic_id)
            epic.completed_points = db.query(func.sum(Task.estimate_points)).filter(
                Task.epic_id == task.epic_id,
                Task.status == "done",
                Task.is_deleted == False
            ).scalar() or 0
```

---

## 7. DoD/NFR Tamamlama Önerileri

```python
def check_completion_suggestions(completed_task: Task, db: Session) -> List[dict]:
    suggestions = []
    
    for dod_id in completed_task.related_dod_ids or []:
        dod = db.query(DoDItem).get(dod_id)
        if dod.implementation_status == "done":
            continue
        
        related_tasks = db.query(Task).filter(
            Task.related_dod_ids.contains([dod_id]),
            Task.is_deleted == False
        ).all()
        
        if all(t.status == "done" for t in related_tasks) and related_tasks:
            suggestions.append({
                "type": "dod",
                "id": dod_id,
                "message": "Tüm task'lar tamamlandı. Onaylayın?"
            })
    
    return suggestions
```

---

## 8. Timezone ve Tarih Kuralları

```python
from datetime import datetime, timezone

class TimestampMixin:
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, onupdate=lambda: datetime.now(timezone.utc))

class BaseSchema(BaseModel):
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z" if v else None
        }
```

---

## 9. Enum/Field Drift Önleme

```python
# shared/enums.py - TEK KAYNAK

class ProjectStatus(str, Enum):
    DRAFT = "draft"
    SPEC_IN_PROGRESS = "spec_in_progress"
    READY_FOR_PLANNING = "ready_for_planning"
    PLANNED = "planned"

class StepStatus(str, Enum):
    NOT_STARTED = "not_started"
    DRAFT = "draft"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    STALE = "stale"

class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

# Model, Pydantic, LLM prompt hep buradan alsın
```

---

## 10. Task Bağımlılık Çözümleme

```python
def resolve_task_dependencies(refined_tasks: List[dict], db: Session):
    index_to_id = {}
    
    # İlk pass: Task'ları oluştur
    for idx, task_data in enumerate(refined_tasks):
        task = Task(**task_data, depends_on_task_ids=[])
        db.add(task)
        db.flush()
        index_to_id[idx] = task.id
    
    # İkinci pass: Bağımlılıkları çözümle
    for idx, task_data in enumerate(refined_tasks):
        depends_on_indices = task_data.get("depends_on_indices", [])
        depends_on_ids = [index_to_id[i] for i in depends_on_indices]
        tasks[idx].depends_on_task_ids = depends_on_ids
    
    # Döngü kontrolü
    if has_circular_dependency(tasks):
        raise ValueError("Circular dependency")

def has_circular_dependency(tasks) -> bool:
    # Kahn's algorithm ile topolojik sıralama
    # processed != len(tasks) ise döngü var
    pass
```

---

## 11. LLM Adapter Policy

```python
class LLMAdapter:
    def call(self, prompt: str) -> str:
        prompt = self._validate_input(prompt)       # Size/charset check
        prompt = self._mask_secrets(prompt)         # API key, JWT mask
        prompt = self._add_turkish_instruction(prompt)
        return self._do_call(prompt)

    def _validate_input(self, prompt: str) -> str:
        # Max 8K karakter, ASCII + temel UTF-8 kontrolü, binary içerik bloklanır
        if len(prompt) > 8000:
            raise ValueError("Prompt too long")
        if not prompt.encode("utf-8", "ignore").decode("utf-8", "ignore"):
            raise ValueError("Invalid charset")
        if b"\x00" in prompt.encode("utf-8"):
            raise ValueError("Binary-like content detected")
        return prompt
    
    def _add_turkish_instruction(self, prompt: str) -> str:
        return """
LANGUAGE RULE (CRITICAL):
- You MUST produce ALL output in TURKISH
""" + prompt
    
    def _mask_secrets(self, text: str) -> str:
        patterns = [
            (r'api[_-]?key\s*[=:]\s*[\w-]+', 'API_KEY=[MASKED]'),
            (r'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', '[JWT]'),
        ]
        for pattern, repl in patterns:
            text = re.sub(pattern, repl, text, flags=re.I)
        return text
```

---

## 12. Export Kaynağı ve Snapshot İlişkisi

```python
def export_markdown(project_id: int, db: Session) -> str:
    project = db.query(Project).get(project_id)
    
    if not project.current_snapshot_id:
        raise ValueError("Export için snapshot gerekli")
    
    snapshot = db.query(ProjectSpecSnapshot).get(project.current_snapshot_id)
    
    # Snapshot'taki ID'lerden entity'leri çek
    objective = db.get(ProjectObjective, snapshot.objective_id)
    features = db.query(Feature).filter(Feature.id.in_(snapshot.included_feature_ids)).all()
    # ...
    
    return f"""# {project.name}
**Versiyon:** {snapshot.spec_version}
**Tarih:** {snapshot.created_at}
...
"""
```

---

## 13. Import Pipeline ve Snapshot Uyumu

```
1. ImportSession oluştur (status=pending)
2. Ham tarama → ImportedAsset
3. Kullanıcı onayı (hangi klasörler dahil)
4. Chunk + LLM özetleme → ImportedSummary
5. build_spec_from_summaries → Entity'ler (origin="imported")
6. Kullanıcı spec onayı
7. ProjectSpecSnapshot oluştur
8. Project.current_snapshot_id = snapshot.id
9. Project.status = ready_for_planning
```

---

## 14. Gap Analizi Veri Akışı

```python
def generate_gap_analysis(project_id: int, db: Session):
    # Input: implementation_status alanları
    epics = db.query(Epic).filter(...).all()
    dod_items = db.query(DoDItem).filter(...).all()
    nfr_items = db.query(NFRItem).filter(...).all()
    
    incomplete = [e for e in epics if e.implementation_status != "done"]
    missing_dod = [d for d in dod_items if d.implementation_status != "done"]
    
    # LLM'den yorum al
    llm_response = call_llm(...)
    
    # Tarihçeli kaydet (her seferinde yeni kayıt)
    result = GapAnalysisResult(
        project_id=project_id,
        incomplete_epic_ids=[e.id for e in incomplete],
        ...
    )
    db.add(result)
```

---

## 15. Sprint Kapasite Yönetimi

```python
# Sprint modeline eklenen alan
capacity_hint: int = Column(Integer, nullable=True)

def audit_sprint_capacity(sprint_id: int, db: Session):
    total = db.query(func.sum(Task.estimate_points)).filter(
        Task.sprint_id == sprint_id
    ).scalar() or 0
    
    sprint = db.query(Sprint).get(sprint_id)
    if sprint.capacity_hint and total > sprint.capacity_hint:
        return {
            "over_capacity": True,
            "severity": "high" if total > sprint.capacity_hint * 1.2 else "medium"
        }
```

---

## 16. Task Pipeline Tetikleme Kuralları

```
planning_detail_level = "high" iken:

1. SprintPlan approve → Task OTOMATİK ÜRETİLMEZ
2. Kullanıcı manuel tetikler:
   POST /sprints/{id}/tasks/generate-skeleton  → Pass 1
   POST /sprints/{id}/tasks/refine             → Pass 2
   POST /sprints/{id}/tasks/audit              → Pass 3

3. Sprint status geçişleri:
   planned → in_progress: Manuel "Sprint Başlat"
   in_progress → completed: Tüm task done + kullanıcı onay
```

---

## 17. Comment vs Human Notes Ayrımı

```python
# Comment entity yeterli, ayrı alan YOK
class Comment(Base):
    entity_type: str  # project, epic, sprint, task, dod, nfr
    entity_id: int
    text: str

# KURAL: Comment'ler LLM'e ASLA girmez
def build_prompt(epic: Epic, db: Session) -> str:
    return f"Epic: {epic.name}\n{epic.description}"
    # Comment dahil DEĞİL
```

---

## 18. State Machine Kuralları (ProjectStep)

```
not_started → draft (generate çağrıldı)
draft → awaiting_approval (LLM başarılı)
awaiting_approval → approved (kullanıcı onayladı)
awaiting_approval → draft (regenerate)
approved → stale (bağımlı değişti, VE status != planned)

YASAK: approved → draft (immutable)
YASAK: planned durumda herhangi bir geçiş (403)

LLM hata/yetmezlik:
- generate çağrısı başarısız olursa status draft'ta kalır; partial entity yazılmaz.
- Retry sınırı dolduğunda kullanıcıya hata dönülür, DB'de yeni kayıt oluşmaz.
```

---

## 19. CI/CD Test Gereksinimleri

```yaml
tests:
  unit:
    - Schema validation
    - Enum consistency
    - Soft delete filter
    - Hash determinism
    
  integration:
    - Golden LLM tests
    - State machine
    - Stale trigger
    - Spec lock
    
  e2e:
    - Full spec flow
    - Task pipeline
    - Export + clone

required_checks:
  - coverage > 90%
  - all tests pass
```

---

## 20. Sprint Başlangıç Checklist

```markdown
## Her Sprint Başında Kontrol

### Veri Modeli
- [ ] Yeni entity'lerde soft delete var mı?
- [ ] Audit alanları (created_by vb.) var mı?
- [ ] Enum'lar shared/enums.py'den mi?
- [ ] Migration oluşturuldu mu?

### LLM
- [ ] Pydantic input/output şemaları var mı?
- [ ] Golden fixture'lar hazır mı?
- [ ] Türkçe zorunluluğu prompt'ta var mı?
- [ ] LLM input limitleri (max 8K, UTF-8) adapter seviyesinde enforce ediliyor mu?

### API
- [ ] Soft delete filter middleware'de mi?
- [ ] Spec lock kontrolü var mı?
- [ ] Transaction boundary'ler doğru mu?

### Test
- [ ] Unit test coverage > 90%?
- [ ] Integration testler geçiyor mu?
- [ ] E2E smoke test var mı?
- [ ] Export'un snapshot'tan beslendiği ve cache/stale akışının çalıştığı testle doğrulandı mı?
- [ ] Coverage > %90 mı? Pipeline'da zorunlu mu?

### Sprint 0 / Omurga
- [ ] shared/enums ve shared/schemas paketleri çıkarıldı mı?
- [ ] LLM adapter + validation + cache/stale + spec lock middleware omurga olarak kuruldu mu?
- [ ] tests/llm/golden/ dizin yapısı açıldı mı?
- [ ] İlk migration + soft delete filter + timezone encoder uygulandı mı?
```

---

**Doküman Sonu**
