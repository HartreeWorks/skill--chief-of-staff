#!/bin/bash
# Open the most recent Chief of Staff daily briefing in the default Markdown viewer.
# Intended to run on the MacBook Pro at 8:00 AM weekdays via launchd.

BRIEFINGS_DIR="$HOME/.agents/skills/chief-of-staff/data/briefings"

latest=$(ls -1 "$BRIEFINGS_DIR"/*.md 2>/dev/null | sort | tail -1)

if [ -n "$latest" ]; then
    open "$latest"
fi
