from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.scoring.app.domain.summary import build_score_summary
from services.scoring.app.tasks.suggest_scores import suggest_subjective_reviews


class SubjectiveAnswerPayload(BaseModel):
    question_title: str
    answer_text: str
    rubric_text: str
    max_score: int


class SuggestReviewRequest(BaseModel):
    objective_score: int = 0
    coding_score: int = 0
    risk_summary: dict = Field(default_factory=dict)
    subjective_answers: list[SubjectiveAnswerPayload] = Field(default_factory=list)


router = APIRouter(prefix="/internal/scoring/reviews", tags=["scoring-reviews"])


@router.post("/suggest")
async def suggest_reviews(request: SuggestReviewRequest) -> dict:
    suggestions = suggest_subjective_reviews(
        [item.model_dump() for item in request.subjective_answers]
    )
    subjective_score = sum(item["suggested_score"] for item in suggestions)
    summary = build_score_summary(
        objective_score=request.objective_score,
        subjective_score=subjective_score,
        coding_score=request.coding_score,
        risk_summary=request.risk_summary,
    )
    return {"suggestions": suggestions, "summary": summary}
