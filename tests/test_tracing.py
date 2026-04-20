from app import tracing


def test_tracing_uses_installed_langfuse_observe() -> None:
    assert tracing.observe.__module__.startswith("langfuse")
