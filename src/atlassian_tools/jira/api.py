import httpx


def _base_url(domain: str) -> str:
    return f"https://{domain}.atlassian.net/rest/api/3"


def _client(email: str, api_token: str) -> httpx.Client:
    return httpx.Client(auth=(email, api_token), timeout=15)


def _raise_api_error(resp: httpx.Response) -> None:
    try:
        body = resp.json()
        detail = body.get("message") or body.get("errorMessages", [resp.text])[0]
    except Exception:
        detail = resp.text
    raise RuntimeError(f"Jira API error {resp.status_code}: {detail}")


def verify_credentials(email: str, api_token: str, domain: str) -> dict:
    with _client(email, api_token) as client:
        resp = client.get(f"{_base_url(domain)}/myself")
    if resp.status_code == 200:
        return resp.json()
    _raise_api_error(resp)


def list_assigned_issues(email: str, api_token: str, domain: str, max_results: int = 50) -> list[dict]:
    """Return issues assigned to the current user, ordered by last update."""
    params = {
        "jql": "assignee = currentUser() ORDER BY updated DESC",
        "maxResults": max_results,
        "fields": "summary,status,priority,issuetype,updated",
    }
    with _client(email, api_token) as client:
        resp = client.get(f"{_base_url(domain)}/search", params=params)
    if resp.status_code == 200:
        return resp.json().get("issues", [])
    _raise_api_error(resp)
