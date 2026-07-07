import httpx


def _normalize_domain(domain: str) -> str:
    domain = domain.strip().rstrip("/")
    if domain.endswith(".atlassian.net"):
        domain = domain[: -len(".atlassian.net")]
    return domain


def _base_url(domain: str) -> str:
    return f"https://{_normalize_domain(domain)}.atlassian.net/rest/api/3"


def _client(email: str, api_token: str) -> httpx.Client:
    return httpx.Client(auth=(email, api_token), timeout=15)


def _raise_api_error(resp: httpx.Response) -> None:
    try:
        body = resp.json()
        detail = body.get("message") or body.get("errorMessages", [resp.text])[0]
    except Exception:
        detail = resp.text
    raise RuntimeError(f"Jira API error {resp.status_code}: {detail}")


def get_issue(email: str, api_token: str, domain: str, key: str) -> dict:
    fields = "summary,description,status,priority,issuetype,assignee,reporter,comment,attachment"
    with _client(email, api_token) as client:
        resp = client.get(f"{_base_url(domain)}/issue/{key}", params={"fields": fields})
    if resp.status_code == 200:
        return resp.json()
    _raise_api_error(resp)


def download_attachment(email: str, api_token: str, url: str) -> bytes:
    with _client(email, api_token) as client:
        resp = client.get(url)
    if resp.status_code == 200:
        return resp.content
    _raise_api_error(resp)


def verify_credentials(email: str, api_token: str, domain: str) -> dict:
    with _client(email, api_token) as client:
        resp = client.get(f"{_base_url(domain)}/myself")
    if resp.status_code == 200:
        return resp.json()
    _raise_api_error(resp)


def list_assigned_issues(
    email: str,
    api_token: str,
    domain: str,
    max_results: int = 50,
    statuses: list[str] | None = None,
) -> list[dict]:
    """Return issues assigned to the current user, ordered by last update."""
    jql = "assignee = currentUser()"
    if statuses:
        quoted = ", ".join(f'"{s}"' for s in statuses)
        jql += f" AND status in ({quoted})"
    jql += " ORDER BY updated DESC"
    params = {
        "jql": jql,
        "maxResults": max_results,
        "fields": "summary,status,priority,issuetype,updated",
    }
    with _client(email, api_token) as client:
        resp = client.get(f"{_base_url(domain)}/search/jql", params=params)
    if resp.status_code == 200:
        return resp.json().get("issues", [])
    _raise_api_error(resp)
