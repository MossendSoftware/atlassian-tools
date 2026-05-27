import httpx

BASE_URL = "https://api.bitbucket.org/2.0"


def _client(email: str, api_token: str) -> httpx.Client:
    return httpx.Client(auth=(email, api_token), timeout=15)


def _raise_api_error(resp: httpx.Response) -> None:
    try:
        detail = resp.json().get("error", {}).get("message", resp.text)
    except Exception:
        detail = resp.text
    raise RuntimeError(f"Bitbucket API error {resp.status_code}: {detail}")


def verify_credentials(email: str, api_token: str) -> dict:
    with _client(email, api_token) as client:
        resp = client.get(f"{BASE_URL}/user")
    if resp.status_code == 200:
        return resp.json()
    _raise_api_error(resp)


def create_pull_request(
    email: str,
    api_token: str,
    workspace: str,
    repo_slug: str,
    title: str,
    description: str,
    source_branch: str,
    destination_branch: str,
) -> dict:
    payload = {
        "title": title,
        "description": description,
        "source": {"branch": {"name": source_branch}},
        "destination": {"branch": {"name": destination_branch}},
    }
    with _client(email, api_token) as client:
        resp = client.post(
            f"{BASE_URL}/repositories/{workspace}/{repo_slug}/pullrequests",
            json=payload,
        )
    if resp.status_code == 201:
        return resp.json()
    _raise_api_error(resp)
