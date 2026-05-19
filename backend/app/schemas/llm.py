from pydantic import BaseModel, Field

from app.schemas.common import TimestampMixin


class LLMProviderCreate(BaseModel):
    name: str
    provider_type: str = "openai_compatible"
    base_url: str
    api_key: str = ""
    timeout_seconds: int = 60
    status: str = "enabled"


class LLMProviderUpdate(LLMProviderCreate):
    id: str
    api_key: str | None = None


class LLMModelCreate(BaseModel):
    provider_id: str
    model_name: str
    display_name: str
    usage_type: str = "content_generation"
    context_window: int = 128000
    max_output_tokens: int = 4096
    temperature: float = 0.7
    input_token_price: float = 0.0
    output_token_price: float = 0.0
    status: str = "enabled"


class LLMModelUpdate(LLMModelCreate):
    id: str


class PromptTemplateCreate(BaseModel):
    scene: str
    version: int = 1
    name: str
    system_prompt: str
    user_prompt: str
    variables: list[str] = Field(default_factory=list)
    output_schema: dict = Field(default_factory=dict)
    status: str = "draft"


class PromptTemplateUpdate(PromptTemplateCreate):
    id: str


class PromptTemplatePublish(BaseModel):
    id: str


class PromptStreamTestRequest(BaseModel):
    prompt_template_id: str
    model_id: str
    variables: dict = Field(default_factory=dict)


class LLMCallRetryRequest(BaseModel):
    id: str


class LLMProviderOut(TimestampMixin):
    name: str
    provider_type: str
    base_url: str
    api_key: str | None
    timeout_seconds: int
    status: str
