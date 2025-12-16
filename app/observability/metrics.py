from prometheus_client import Counter, Gauge, Histogram, generate_latest

api_requests_total = Counter(
    "masper_api_requests_total",
    "API requests toplam sayısı",
    ["path", "method", "status"],
)

api_request_duration_seconds = Histogram(
    "masper_api_request_duration_seconds",
    "API request süreleri",
    ["path", "method"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)

jobs_total = Counter(
    "masper_jobs_total",
    "Job tamamlanma sayısı",
    ["type", "status"],
)

jobs_in_progress = Gauge(
    "masper_jobs_in_progress",
    "Şu an çalışan job sayısı",
    ["type"],
)

llm_calls_total = Counter(
    "masper_llm_calls_total",
    "LLM çağrı sayısı",
    ["intent", "outcome"],
)


def render_metrics() -> bytes:
    return generate_latest()
