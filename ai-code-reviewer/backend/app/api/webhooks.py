from __future__ import annotations

import json
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PullRequestReview, Repository, ReviewComment
from app.db.session import get_db
from app.github.webhook_validator import verify_github_signature
from app.core.review_engine import run_review

logger = logging.getLogger(__name__)
router = APIRouter()

_HANDLED_ACTIONS = {"opened", "synchronize", "reopened"}


@router.post("/github")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    body = await verify_github_signature(request)
    event = request.headers.get("X-GitHub-Event", "")
    if event != "pull_request":
        return {"ignored": True}

    payload = json.loads(body)
    action = payload.get("action", "")
    if action not in _HANDLED_ACTIONS:
        return {"ignored": True}

    pr_data = payload["pull_request"]
    repo_data = payload["repository"]

    repo = await _get_or_create_repo(db, repo_data["full_name"])
    review = PullRequestReview(
        repo_id=repo.id,
        pr_number=pr_data["number"],
        pr_title=pr_data["title"],
        author=pr_data["user"]["login"],
        status="pending",
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)

    background_tasks.add_task(
        _process_review,
        review_id=review.id,
        repo_full_name=repo_data["full_name"],
        pr_number=pr_data["number"],
        head_sha=pr_data["head"]["sha"],
        diff_url=pr_data["diff_url"],
    )

    return {"status": "accepted", "review_id": review.id}


async def _get_or_create_repo(db: AsyncSession, full_name: str) -> Repository:
    from sqlalchemy import select

    result = await db.execute(
        select(Repository).where(Repository.github_repo_full_name == full_name)
    )
    repo = result.scalar_one_or_none()
    if repo is None:
        repo = Repository(github_repo_full_name=full_name)
        db.add(repo)
        await db.commit()
        await db.refresh(repo)
    return repo


async def _process_review(
    review_id: int,
    repo_full_name: str,
    pr_number: int,
    head_sha: str,
    diff_url: str,
) -> None:
    import httpx
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(diff_url)
                unified_diff = resp.text

            results = await run_review(repo_full_name, pr_number, head_sha, unified_diff)

            comments = [
                ReviewComment(
                    review_id=review_id,
                    file_path=r.file_path if hasattr(r, "file_path") else "",
                    line_number=r.line,
                    category=r.category,
                    severity=r.severity,
                    comment=r.comment,
                    suggestion=r.suggestion or "",
                )
                for r in results
            ]
            db.add_all(comments)

            from sqlalchemy import update
            from app.db.models import PullRequestReview as PRR

            await db.execute(
                update(PRR).where(PRR.id == review_id).values(status="completed")
            )
            await db.commit()
        except Exception as exc:
            logger.error("Review %s failed: %s", review_id, exc)
            from sqlalchemy import update
            from app.db.models import PullRequestReview as PRR

            await db.execute(
                update(PRR).where(PRR.id == review_id).values(status="failed")
            )
            await db.commit()
