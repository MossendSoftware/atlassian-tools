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


def list_pull_requests(
    email: str,
    api_token: str,
    workspace: str,
    repo_slug: str,
    max_results: int = 50,
) -> list[dict]:
    params = {"state": "OPEN", "pagelen": max_results}
    with _client(email, api_token) as client:
        resp = client.get(
            f"{BASE_URL}/repositories/{workspace}/{repo_slug}/pullrequests",
            params=params,
        )
    if resp.status_code == 200:
        return resp.json().get("values", [])
    _raise_api_error(resp)


def get_pull_request(
    email: str,
    api_token: str,
    workspace: str,
    repo_slug: str,
    pr_id: int,
) -> dict:
    with _client(email, api_token) as client:
        resp = client.get(
            f"{BASE_URL}/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}"
        )
    if resp.status_code == 200:
        return resp.json()
    _raise_api_error(resp)


def merge_pull_request(
    email: str,
    api_token: str,
    workspace: str,
    repo_slug: str,
    pr_id: int,
    message: str | None = None,
    close_source_branch: bool = False,
) -> dict:
    payload = {"type": "pullrequest", "close_source_branch": close_source_branch}
    if message:
        payload["message"] = message
    with _client(email, api_token) as client:
        resp = client.post(
            f"{BASE_URL}/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}/merge",
            json=payload,
        )
    if resp.status_code == 200:
        return resp.json()
    _raise_api_error(resp)


def approve_pull_request(
    email: str,
    api_token: str,
    workspace: str,
    repo_slug: str,
    pr_id: int,
) -> dict:
    with _client(email, api_token) as client:
        resp = client.post(
            f"{BASE_URL}/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}/approve"
        )
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
    close_source_branch: bool = False,
) -> dict:
    payload = {
        "title": title,
        "description": description,
        "source": {"branch": {"name": source_branch}},
        "destination": {"branch": {"name": destination_branch}},
        "close_source_branch": close_source_branch,
    }
    with _client(email, api_token) as client:
        resp = client.post(
            f"{BASE_URL}/repositories/{workspace}/{repo_slug}/pullrequests",
            json=payload,
        )
    if resp.status_code == 201:
        return resp.json()
    _raise_api_error(resp)
