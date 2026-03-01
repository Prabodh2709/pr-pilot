from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PullRequestReview, Repository, ReviewComment
from app.db.session import get_db

router = APIRouter()


@router.get("/repos")
async def list_repos(db: AsyncSession = Depends(get_db)) -> list[dict]:
    result = await db.execute(select(Repository).order_by(Repository.installed_at.desc()))
    repos = result.scalars().all()
    return [
        {"id": r.id, "full_name": r.github_repo_full_name, "installed_at": r.installed_at}
        for r in repos
    ]


@router.get("/repos/{repo_name}/reviews")
async def list_reviews(
    repo_name: str,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
) -> dict:
    repo = await _get_repo(db, repo_name)
    offset = (page - 1) * page_size

    total_result = await db.execute(
        select(func.count()).where(PullRequestReview.repo_id == repo.id)
    )
    total = total_result.scalar_one()

    result = await db.execute(
        select(PullRequestReview)
        .where(PullRequestReview.repo_id == repo.id)
        .order_by(PullRequestReview.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    reviews = result.scalars().all()

    items = []
    for rev in reviews:
        count_result = await db.execute(
            select(func.count()).where(ReviewComment.review_id == rev.id)
        )
        issue_count = count_result.scalar_one()
        items.append(
            {
                "id": rev.id,
                "pr_number": rev.pr_number,
                "pr_title": rev.pr_title,
                "author": rev.author,
                "status": rev.status,
                "created_at": rev.created_at,
                "issue_count": issue_count,
            }
        )

    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.get("/repos/{repo_name}/metrics")
async def get_metrics(repo_name: str, db: AsyncSession = Depends(get_db)) -> dict:
    repo = await _get_repo(db, repo_name)

    review_ids_result = await db.execute(
        select(PullRequestReview.id).where(PullRequestReview.repo_id == repo.id)
    )
    review_ids = [row[0] for row in review_ids_result.all()]

    if not review_ids:
        return {"by_category": {}, "by_severity": {}, "total": 0}

    cat_result = await db.execute(
        select(ReviewComment.category, func.count())
        .where(ReviewComment.review_id.in_(review_ids))
        .group_by(ReviewComment.category)
    )
    by_category = {row[0]: row[1] for row in cat_result.all()}

    sev_result = await db.execute(
        select(ReviewComment.severity, func.count())
        .where(ReviewComment.review_id.in_(review_ids))
        .group_by(ReviewComment.severity)
    )
    by_severity = {row[0]: row[1] for row in sev_result.all()}

    total_result = await db.execute(
        select(func.count()).where(ReviewComment.review_id.in_(review_ids))
    )
    total = total_result.scalar_one()

    return {"by_category": by_category, "by_severity": by_severity, "total": total}


@router.get("/reviews/{review_id}")
async def get_review(review_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(
        select(PullRequestReview).where(PullRequestReview.id == review_id)
    )
    review = result.scalar_one_or_none()
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")

    comments_result = await db.execute(
        select(ReviewComment).where(ReviewComment.review_id == review_id)
    )
    comments = comments_result.scalars().all()

    return {
        "id": review.id,
        "pr_number": review.pr_number,
        "pr_title": review.pr_title,
        "author": review.author,
        "status": review.status,
        "created_at": review.created_at,
        "comments": [
            {
                "id": c.id,
                "file_path": c.file_path,
                "line_number": c.line_number,
                "category": c.category,
                "severity": c.severity,
                "comment": c.comment,
                "suggestion": c.suggestion,
            }
            for c in comments
        ],
    }


async def _get_repo(db: AsyncSession, full_name: str) -> Repository:
    result = await db.execute(
        select(Repository).where(Repository.github_repo_full_name == full_name)
    )
    repo = result.scalar_one_or_none()
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo
