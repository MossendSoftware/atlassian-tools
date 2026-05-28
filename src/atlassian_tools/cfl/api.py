import httpx


def _normalize_domain(domain: str) -> str:
    domain = domain.strip().rstrip("/")
    if domain.endswith(".atlassian.net"):
        domain = domain[: -len(".atlassian.net")]
    return domain


def _base_url(domain: str) -> str:
    return f"https://{_normalize_domain(domain)}.atlassian.net/wiki/rest/api"


def _client(email: str, api_token: str) -> httpx.Client:
    return httpx.Client(auth=(email, api_token), timeout=15)


def _raise_api_error(resp: httpx.Response) -> None:
    try:
        body = resp.json()
        detail = body.get("message") or body.get("reason", resp.text)
    except Exception:
        detail = resp.text
    raise RuntimeError(f"Confluence API error {resp.status_code}: {detail}")


def verify_credentials(email: str, api_token: str, domain: str) -> dict:
    """Verify credentials by fetching the current user from the Confluence API."""
    with _client(email, api_token) as client:
        resp = client.get(
            f"{_base_url(domain)}/user/current"
        )
    if resp.status_code == 200:
        return resp.json()
    _raise_api_error(resp)
