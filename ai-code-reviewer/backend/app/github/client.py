from github import Github, GithubException

from app.config import settings

_gh = Github(settings.github_token)


def get_pull_request(repo_full_name: str, pr_number: int):
    repo = _gh.get_repo(repo_full_name)
    return repo.get_pull(pr_number)


def post_review_comment(
    repo_full_name: str,
    pr_number: int,
    commit_id: str,
    path: str,
    line: int,
    body: str,
) -> None:
    repo = _gh.get_repo(repo_full_name)
    pr = repo.get_pull(pr_number)
    commit = repo.get_commit(commit_id)
    try:
        pr.create_review_comment(body=body, commit=commit, path=path, line=line)
    except GithubException as exc:
        raise RuntimeError(f"Failed to post GitHub comment: {exc}") from exc


def get_file_content(repo_full_name: str, path: str, ref: str) -> list[str]:
    repo = _gh.get_repo(repo_full_name)
    contents = repo.get_contents(path, ref=ref)
    return contents.decoded_content.decode("utf-8").splitlines()
