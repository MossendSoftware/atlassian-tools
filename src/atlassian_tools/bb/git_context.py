import re
import subprocess
from dataclasses import dataclass


@dataclass
class GitContext:
    workspace: str
    repo_slug: str
    current_branch: str
    default_branch: str


def _run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def _parse_remote_url(url: str) -> tuple[str, str]:
    # SSH:   git@bitbucket.org:workspace/repo.git
    # HTTPS: https://bitbucket.org/workspace/repo.git
    ssh = re.match(r"git@bitbucket\.org:([^/]+)/(.+?)(?:\.git)?$", url)
    if ssh:
        return ssh.group(1), ssh.group(2)
    https = re.match(r"https?://(?:[^@]+@)?bitbucket\.org/([^/]+)/(.+?)(?:\.git)?$", url)
    if https:
        return https.group(1), https.group(2)
    raise ValueError(f"Cannot parse Bitbucket remote URL: {url}")


def _detect_default_branch() -> str:
    try:
        ref = _run(["git", "symbolic-ref", "refs/remotes/origin/HEAD"])
        return ref.split("/")[-1]
    except RuntimeError:
        for candidate in ("main", "master", "develop"):
            try:
                _run(["git", "rev-parse", "--verify", f"origin/{candidate}"])
                return candidate
            except RuntimeError:
                continue
    return "main"


def get_git_context() -> GitContext:
    try:
        remote_url = _run(["git", "remote", "get-url", "origin"])
    except RuntimeError:
        raise RuntimeError("No 'origin' remote found. Is this a git repository?")

    workspace, repo_slug = _parse_remote_url(remote_url)
    current_branch = _run(["git", "branch", "--show-current"])

    if not current_branch:
        raise RuntimeError("Not on a branch (detached HEAD).")

    default_branch = _detect_default_branch()
    return GitContext(workspace, repo_slug, current_branch, default_branch)


def branch_name_to_title(branch: str) -> str:
    name = re.sub(r"^(feat|fix|chore|docs|refactor|test|hotfix)/", "", branch)
    name = re.sub(r"[-_]", " ", name)
    return name.capitalize()
