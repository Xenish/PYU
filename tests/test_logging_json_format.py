import json

from app.observability.logging import get_logger, set_context, clear_context, JsonFormatter
import logging


def test_json_formatter_includes_context():
    set_context(request_id="req-123", project_id=7, job_id=9, component="api")
    logger = get_logger("masper.test", component="api")
    record = logger.logger.makeRecord(  # type: ignore[attr-defined]
        logger.logger.name,
        logging.INFO,
        fn="",
        lno=0,
        msg="hello",
        args=(),
        exc_info=None,
        func=None,
        extra={"path": "/health"},
    )
    formatter = JsonFormatter()
    output = formatter.format(record)
    data = json.loads(output)
    assert data["request_id"] == "req-123"
    assert data["project_id"] == 7
    assert data["job_id"] == 9
    assert data["component"] == "api"
    assert data["path"] == "/health"
    clear_context()
