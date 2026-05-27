# atlassian-tools

Fast, terminal-native CLIs for Atlassian products — **`bb`** (Bitbucket), **`jira`** (Jira), and **`cfl`** (Confluence). Run common Atlassian operations without leaving the terminal.

Built with [Click](https://click.palletsprojects.com/) and [Rich](https://github.com/Textualize/rich). One shared credential store; no third-party service involved.

## Requirements

- [uv](https://docs.astral.sh/uv/)

## Installation

```bash
git clone https://github.com/MossendSoftware/atlassian-tools
cd atlassian-tools
make install
```

This installs `bb`, `jira`, and `cfl` as isolated tools into `~/.local/bin`. If that directory is not on your `PATH`, run:

```bash
uv tool update-shell
```

then restart your shell.

## Authentication

All three CLIs share a single credential store at `~/.config/atlassian-tools/credentials.yaml` (mode `600`). You only need to log in once — credentials are reused by every tool.

### Creating an API token

**1.** Go to <https://id.atlassian.com/manage-profile/security/api-tokens> and click **Create API token with Scopes**.

![API Tokens page](docs/images/api-tokens-page.png)

**2.** Give the token a name (e.g. `atlassian-tools`) and set an expiry date (maximum 365 days).

![Name and expiry](docs/images/api-token-name.png)

**3.** Select the products you use (Bitbucket, Jira, Confluence) and grant Read + Write scopes.

**4.** Copy the token — it is only shown once.

### Logging in

Run the `auth login` command from any of the three CLIs — they all do the same thing:

```bash
bb auth login
# or: jira auth login
# or: cfl auth login
```

You will be prompted for:

| Prompt | Notes |
|---|---|
| Email | Your Atlassian account email |
| API token | The token you just created |
| Atlassian domain | Your site name, e.g. `mycompany` for `mycompany.atlassian.net` — required for jira/cfl, optional for bb-only users |

### Other auth commands

```bash
bb auth status    # show stored credentials
bb auth logout    # remove stored credentials
```

## Usage

### `bb` — Bitbucket

All `bb` commands must be run from inside a Bitbucket git repository (origin remote points to `bitbucket.org`).

#### `bb auth login`

Authenticate and save credentials (shared with jira and cfl).

#### `bb pr create`

Create a pull request from the current branch.

```bash
bb pr create
```

Reads workspace, repository slug, current branch, and default branch from git. You are prompted for:

| Prompt | Default |
|---|---|
| Title | Branch name converted to title case (prefix stripped) |
| Destination branch | Detected default branch (`main`, `master`, or `develop`) |
| Description | `$EDITOR` opens with a structured markdown template |

Comment lines (`<!-- ... -->`) are stripped from the description before submission. If the description is left empty, you are asked to confirm before the PR is created.

### `jira` — Jira

```bash
jira auth login    # authenticate (shared with bb and cfl)
jira auth status   # show stored credentials
```

More commands coming soon.

### `cfl` — Confluence

```bash
cfl auth login     # authenticate (shared with bb and jira)
cfl auth status    # show stored credentials
```

More commands coming soon.

## Command reference

| Command | Description |
|---|---|
| `bb auth login` | Authenticate with Atlassian (shared) |
| `bb auth status` | Show stored credentials |
| `bb auth logout` | Remove stored credentials |
| `bb pr create` | Create a PR from the current branch |
| `jira auth login` | Authenticate with Atlassian (shared) |
| `jira auth status` | Show stored credentials |
| `jira auth logout` | Remove stored credentials |
| `cfl auth login` | Authenticate with Atlassian (shared) |
| `cfl auth status` | Show stored credentials |
| `cfl auth logout` | Remove stored credentials |

## Development

### Setup

```bash
git clone https://github.com/MossendSoftware/atlassian-tools
cd atlassian-tools
make dev
```

### Project layout

```
src/atlassian_tools/
  shared/
    config.py              # Credential load/save (~/.config/atlassian-tools/)
    commands/
      auth.py              # Shared auth group (login, logout, status)
  bb/
    cli.py                 # bb entry point
    api.py                 # Bitbucket REST API client
    git_context.py         # Git remote parsing and branch detection
    commands/
      pr.py                # bb pr *
  jira/
    cli.py                 # jira entry point
    api.py                 # Jira REST API client
  cfl/
    cli.py                 # cfl entry point
    api.py                 # Confluence REST API client
```

### Running locally

```bash
uv run bb --help
uv run jira --help
uv run cfl --help
```

### Running tests

```bash
uv run pytest
```

### Contributing

1. Branch off `main` using a descriptive name: `feat/`, `fix/`, `chore/`, or `docs/` prefix.
2. Open a pull request against `main`. A member of the **Developers** group must approve it before it can be merged.
3. Keep commits focused; squash noise before opening the PR.

### Releasing

Releases follow [Semantic Versioning](https://semver.org/): `v{MAJOR}.{MINOR}.{PATCH}`.

| Change type | Version bump |
|---|---|
| Breaking changes | MAJOR |
| New backwards-compatible features | MINOR |
| Bug fixes, patches | PATCH |

Only members of the **Developers** group may create and push release tags:

```bash
git tag v1.2.3
git push origin v1.2.3
```

Tags must be pushed from a commit on `main`. The tag name must match `v*.*.*` exactly.

## License

[MIT](LICENSE)
