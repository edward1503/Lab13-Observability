import asyncio
import json
import re
from pathlib import Path
from types import SimpleNamespace

from fastapi.responses import Response
from structlog.contextvars import bind_contextvars, clear_contextvars

from app.agent import AgentResult
from app.main import chat
from app.middleware import CorrelationIdMiddleware
from app.pii import hash_user_id
from app.schemas import ChatRequest
import app.logging_config as logging_config
import app.main as main_module


def test_correlation_id_middleware_generates_and_propagates_headers() -> None:
    middleware = CorrelationIdMiddleware(app=lambda scope, receive, send: None)
    request = SimpleNamespace(headers={}, state=SimpleNamespace())

    async def call_next(_: object) -> Response:
        return Response(content="ok")

    response = asyncio.run(middleware.dispatch(request, call_next))

    assert re.fullmatch(r"req-[0-9a-f]{8}", request.state.correlation_id)
    assert response.headers["x-request-id"] == request.state.correlation_id
    assert float(response.headers["x-response-time-ms"]) >= 0


def test_chat_logs_include_member_a_context(tmp_path: Path, monkeypatch) -> None:
    log_path = tmp_path / "logs.jsonl"
    logging_config.LOG_PATH = log_path
    clear_contextvars()
    bind_contextvars(correlation_id="req-abc12345")
    monkeypatch.setenv("APP_ENV", "test")

    class StubAgent:
        model = "stub-model"

        def run(self, **_: object) -> AgentResult:
            return AgentResult(
                answer="Stub answer",
                latency_ms=42,
                tokens_in=10,
                tokens_out=20,
                cost_usd=0.001,
                quality_score=0.9,
            )

    monkeypatch.setattr(main_module, "agent", StubAgent())
    request = SimpleNamespace(state=SimpleNamespace(correlation_id="req-abc12345"))
    body = ChatRequest(
        user_id="u_member_a",
        session_id="s_demo_01",
        feature="qa",
        message="hello there",
    )

    response = asyncio.run(chat(request, body))

    records = [
        json.loads(line)
        for line in log_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    api_records = [record for record in records if record.get("service") == "api"]

    assert response.correlation_id == "req-abc12345"
    assert len(api_records) == 2
    for record in api_records:
        assert record["correlation_id"] == "req-abc12345"
        assert record["user_id_hash"] == hash_user_id("u_member_a")
        assert record["session_id"] == "s_demo_01"
        assert record["feature"] == "qa"
        assert record["model"] == "stub-model"
        assert record["env"] == "test"

    clear_contextvars()
