import json

import pytest

from paper_stat_critic.adapters.claude_cli import parse_cli_output
from paper_stat_critic.ports import LLMError


def test_structured_output_is_returned():
    stdout = json.dumps({"is_error": False, "structured_output": {"a": 1}})
    assert parse_cli_output(stdout) == {"a": 1}


@pytest.mark.parametrize(
    "stdout",
    [
        "not json",
        json.dumps({"is_error": True, "result": "rate limited"}),
        json.dumps({"is_error": False, "result": "plain text"}),
    ],
)
def test_bad_output_raises(stdout):
    with pytest.raises(LLMError):
        parse_cli_output(stdout)
