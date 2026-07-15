#!/usr/bin/env python3
"""PreToolUse hook: deny Edit/Write/MultiEdit on generated/vendored paths.

Mirrors the "Files to Never Edit" list in the root CLAUDE.md. Reads the
hook's JSON payload from stdin and, for Edit/Write/MultiEdit calls, checks
tool_input.file_path against a fixed blocklist of path fragments.
"""

import json
import sys

PROTECTED_FRAGMENTS = (
    "apps/app-be/.venv/",
    "apps/app-be/dist/",
    "apps/app-be/uv.lock",
    "__pycache__/",
    "/coverage/",
    "/reports/",
    ".nx/cache/",
    "callback_data.yaml",
    "apps/app-be/src/app_be/data/",
)


def main() -> None:
    payload = json.load(sys.stdin)
    file_path = payload.get("tool_input", {}).get("file_path", "")
    normalized = file_path.replace("\\", "/")

    for fragment in PROTECTED_FRAGMENTS:
        if fragment in normalized:
            print(
                json.dumps(
                    {
                        "hookSpecificOutput": {
                            "hookEventName": "PreToolUse",
                            "permissionDecision": "deny",
                            "permissionDecisionReason": (
                                f"{file_path} is generated/vendored "
                                "(see CLAUDE.md > Files to Never Edit). "
                                "Use the corresponding nx/uv command instead."
                            ),
                        }
                    }
                )
            )
            return


if __name__ == "__main__":
    main()
