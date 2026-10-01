"""Reads and writes stage artifacts under runs/<paper_id>/.

Each artifact is wrapped as {"stage", "cache_key", "data"} so a later run
can tell whether the stored output was produced from the same inputs.
"""

import json
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter

from paper_stat_critic.pipeline.registry import ARTIFACT_FILES, StageName


class RunStore:
    def __init__(self, runs_dir: Path, paper_id: str) -> None:
        self.run_dir = runs_dir / paper_id

    def path(self, stage: StageName) -> Path:
        return self.run_dir / ARTIFACT_FILES[stage]

    def load[T](self, stage: StageName, type_: type[T], cache_key: str) -> T | None:
        """Return the stored output if it was made with `cache_key`, else None."""
        path = self.path(stage)
        if not path.exists():
            return None
        envelope = json.loads(path.read_text(encoding="utf-8"))
        if envelope.get("cache_key") != cache_key:
            return None
        return TypeAdapter(type_).validate_python(envelope["data"])

    def save(self, stage: StageName, value: Any, type_: type, cache_key: str) -> Path:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        data = TypeAdapter(type_).dump_python(value, mode="json")
        envelope = {"stage": stage.value, "cache_key": cache_key, "data": data}
        path = self.path(stage)
        text = json.dumps(envelope, ensure_ascii=False, indent=2)
        path.write_text(text + "\n", encoding="utf-8")
        return path
