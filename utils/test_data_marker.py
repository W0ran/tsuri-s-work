import json
import uuid
from pathlib import Path

TEST_MARKER_PREFIX = "QA-AUTOTEST-"

# Тестовые копии заявок (test-submit) обрабатываются экспертной очередью
# асинхронно и небыстро (уже видимые эксперту test-заявки на стенде имеют
# возраст ~10 дней) — синхронный тест не может дождаться этого в рамках
# одного прогона. Проверка "видно ли эксперту" вынесена в отдельный,
# самостоятельно пропускающий себя тест, который читает этот лог заявок,
# отправленных на предыдущих прогонах.
_PENDING_LOG_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "_stored_xss_pending.jsonl"


def make_test_application_name(base_name: str = "Тестовый препарат") -> str:
    """Название заявки с уникальным маркером — по нему отличаем свои
    тестовые заявки от реальных/чужих в общей очереди эксперта."""
    unique_suffix = uuid.uuid4().hex[:8]
    return f"{TEST_MARKER_PREFIX}{unique_suffix} {base_name}"


def record_pending_submission(app_id: str, marker_name: str, payload: str) -> None:
    """Запоминает отправленную test-submit заявку с XSS-маркером, чтобы
    отложенный тест мог позже проверить её в очереди эксперта."""
    _PENDING_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {"app_id": app_id, "marker_name": marker_name, "payload": payload}
    with _PENDING_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_pending_submissions() -> list[dict]:
    if not _PENDING_LOG_PATH.exists():
        return []
    entries = []
    for line in _PENDING_LOG_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            entries.append(json.loads(line))
    return entries
