from pydantic import BaseModel, Field
from typing import List

# Request schema
class ParaphraseRequest(BaseModel):
    text: str = Field(..., min_length=3, description="Text to paraphrase")
    model_name: str = Field("bart", description="bart | t5 | custom HF model repo")
    level: str = Field("balanced", description="conservative | balanced | creative")
    num_return_sequences: int = Field(1, description="Number of paraphrases to generate")
    max_new_tokens: int = Field(96, description="Max tokens for generation")

# Response schema
class ParaphraseResponse(BaseModel):
    paraphrases: List[str]
    used_model: str
    level: str
    generation_params: dict
