"""Path constants for the Chief of Staff skill."""

from pathlib import Path

CLAUDE_DIR = Path.home() / ".claude"
PROJECTS_DIR = CLAUDE_DIR / "projects"
SKILL_DIR = Path(__file__).parent
DATA_DIR = SKILL_DIR / "data"
DIGESTS_DIR = DATA_DIR / "claude-code-summaries"

# Codex sessions
CODEX_SESSIONS_DIR = Path.home() / ".codex" / "sessions"

# Day-tracker canonical session data
DAY_TRACKER_DAILY_DIR = Path.home() / "Documents" / "day-tracker" / "data" / "daily"

# External paths
PROJECTS_YAML = Path.home() / "Documents" / "Projects" / "projects.yaml"
