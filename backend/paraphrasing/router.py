from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict
from .service import paraphrase

router = APIRouter()

class ParaphraseRequest(BaseModel):
    text: str = Field(..., min_length=3)
    model_name: str = Field("t5", description="t5 | bart | custom HF repo")
    level: str = Field("balanced", description="conservative | balanced | creative")
    num_return_sequences: int = Field(1)
    max_new_tokens: int = Field(50)

class ParaphraseResponse(BaseModel):
    paraphrases: list[str]
    model_name: str
    level: str
    generation_params: dict

@router.post("/generate", response_model=ParaphraseResponse)
def paraphrase_endpoint(req: ParaphraseRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Empty text.")

    try:
        outputs, params = paraphrase(
            text=req.text,
            level=req.level,
            num_return_sequences=req.num_return_sequences,
            max_new_tokens=req.max_new_tokens,
            model_name=req.model_name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return ParaphraseResponse(
        paraphrases=outputs,
        model_name=req.model_name,
        level=req.level,
        generation_params=params
    )