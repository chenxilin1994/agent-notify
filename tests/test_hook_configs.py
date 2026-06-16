import json
from pathlib import Path


def test_hook_configs_point_at_shared_entrypoint():
    claude = json.loads(Path.home().joinpath(".claude/settings.json").read_text(encoding="utf-8"))
    codex = json.loads(Path.home().joinpath(".codex/hooks.json").read_text(encoding="utf-8"))
    expected = str(Path.home().joinpath(".local/share/agent-notify/bin/notify-hook.sh"))
    assert claude["autoUpdate"] is False
    assert claude["model"] == "glm-5"
    assert "env" in claude
    assert "enabledPlugins" in claude
    assert claude["hooks"]["Stop"][0]["hooks"][0]["command"] == expected
    assert codex["hooks"]["Stop"][0]["hooks"][0]["command"] == expected
