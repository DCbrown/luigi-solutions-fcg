"""Fetch a submitted repo and read it as text.

Hard rule, no exceptions: **submitted code is never executed.** No build, no
install, no import. We shallow-clone it, read the text files, and throw the clone
away. Every check downstream is static. See docs/quality.md Q5.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from fcg.models import Submission

# Guardrails. A submission that blows through these fails cleanly rather than
# hanging the app — docs/requirements.md R3.4.
CLONE_TIMEOUT_SECONDS = 30
MAX_FILES = 2_000
MAX_FILE_BYTES = 1_000_000

# Never worth reading, and they'd swamp the content checks — a vendored copy of
# React contains the word "form" rather a lot.
SKIP_DIRS = {
    ".git", "node_modules", "dist", "build", ".next", ".nuxt", ".svelte-kit",
    "venv", ".venv", "__pycache__", "vendor", ".cache", "out", "coverage",
}
TEXT_SUFFIXES = {
    ".html", ".htm", ".css", ".scss", ".sass", ".less", ".js", ".jsx", ".mjs",
    ".ts", ".tsx", ".vue", ".svelte", ".astro", ".json", ".md", ".txt", ".csv",
    ".py", ".rb", ".php", ".hbs", ".ejs", ".pug", ".njk",
}

_GITHUB_URL = re.compile(
    r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?$", re.IGNORECASE
)


class IngestError(Exception):
    """Something went wrong fetching the repo, with a message fit for a user."""


def normalise_url(repo_url: str) -> str:
    """Accept what people actually paste; reject what we can't clone.

    Tolerates a trailing slash, a `.git` suffix, and stray whitespace. Rejects SSH
    remotes and non-GitHub hosts, because we only promised GitHub (D4).
    """
    url = repo_url.strip().removesuffix(".git").rstrip("/")

    if url.startswith("git@github.com:"):
        raise IngestError(
            "That's an SSH remote. Paste the https:// URL from the browser bar instead."
        )
    if not _GITHUB_URL.match(url):
        raise IngestError(
            "That doesn't look like a GitHub repo URL. It should look like "
            "https://github.com/your-name/your-project"
        )
    return url


def fetch_repo(repo_url: str, project_id: str) -> Submission:
    """Shallow-clone a public GitHub repo and read its text files.

    Raises IngestError with a message that says what actually went wrong.
    """
    url = normalise_url(repo_url)
    tmp = Path(tempfile.mkdtemp(prefix="fcg-"))

    try:
        _clone(url, tmp)
        files = _read_text_files(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if not files:
        raise IngestError(
            "Cloned the repo, but found no source files in it. Is the code "
            "definitely pushed, and on the default branch?"
        )

    return Submission(project_id=project_id, repo_url=url, files=files)


def _clone(url: str, dest: Path) -> None:
    """Shallow clone, no history, no submodules, no code run."""
    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "--no-tags", url, str(dest)],
            capture_output=True,
            text=True,
            timeout=CLONE_TIMEOUT_SECONDS,
            check=False,
        )
    except FileNotFoundError:
        raise IngestError("git isn't installed on this machine, so I can't clone.") from None
    except subprocess.TimeoutExpired:
        raise IngestError(
            f"The clone took longer than {CLONE_TIMEOUT_SECONDS}s and I gave up. "
            "Is the repo very large, or the connection slow?"
        ) from None

    if result.returncode == 0:
        return

    # git's stderr is not a user-facing message. Translate the ones we expect.
    err = result.stderr.lower()
    if "not found" in err or "repository not found" in err:
        raise IngestError(
            "GitHub says that repo doesn't exist. If it's private, make it public "
            "— I can only read public repos."
        )
    if "authentication" in err or "permission denied" in err or "could not read" in err:
        raise IngestError("That repo is private. Make it public and try again.")
    if "could not resolve host" in err or "network" in err:
        raise IngestError("Couldn't reach GitHub. Is the network up?")

    raise IngestError(f"git couldn't clone that: {result.stderr.strip().splitlines()[-1]}")


def _read_text_files(root: Path) -> dict[str, str]:
    """Read the source out of the clone. Text only, capped, never executed."""
    files: dict[str, str] = {}

    for path in sorted(root.rglob("*")):
        if len(files) >= MAX_FILES:
            break
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if path.stat().st_size > MAX_FILE_BYTES:
            continue

        try:
            files[str(path.relative_to(root))] = path.read_text(
                encoding="utf-8", errors="replace"
            )
        except OSError:
            continue  # unreadable file is not a reason to fail the whole submission

    return files
