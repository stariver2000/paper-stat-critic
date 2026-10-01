"""paper-stat-critic: critical statistical review of research papers."""

from paper_stat_critic.pipeline import (
    Adapters,
    ReviewConfig,
    RunResult,
    StageName,
    build_adapters,
    run_pipeline,
)

__all__ = ["Adapters", "ReviewConfig", "RunResult", "StageName", "build_adapters", "run_pipeline"]
