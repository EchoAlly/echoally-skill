"""Compare the installed EchoAlly Skill with the public stable version."""

import http.client
import json
from pathlib import Path
import re
import sys
from urllib.request import urlopen


VERSION_URL = "https://raw.githubusercontent.com/iChunzhen/echoally-skill/main/skills/echoally/VERSION"
LOCAL_VERSION = Path(__file__).resolve().parents[1] / "VERSION"


def parse_version(text):
    version = text.strip()
    if not re.fullmatch(r"(?:0|[1-9][0-9]{0,5})(?:\.(?:0|[1-9][0-9]{0,5})){2}", version):
        raise ValueError("expected a stable MAJOR.MINOR.PATCH version")
    return tuple(map(int, version.split(".")))


def main():
    try:
        installed = parse_version(LOCAL_VERSION.read_text(encoding="ascii"))
        with urlopen(VERSION_URL, timeout=5) as response:
            latest = parse_version(response.read(64).decode("ascii"))
    except (OSError, ValueError, http.client.HTTPException) as error:
        print(f"EchoAlly Skill update check failed: {error}", file=sys.stderr)
        return 1

    print(json.dumps({
        "installed": ".".join(map(str, installed)),
        "latest": ".".join(map(str, latest)),
        "update_available": latest > installed,
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
