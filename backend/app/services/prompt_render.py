import re

from app.core.exceptions import AppError
from app.models.llm import PromptTemplate

VARIABLE_RE = re.compile(r"{{\s*([a-zA-Z0-9_]+)\s*}}")


class PromptRenderService:
    def render(self, template: PromptTemplate, variables: dict) -> list[dict[str, str]]:
        missing = [name for name in template.variables if name not in variables]
        if missing:
            raise AppError(f"Prompt 变量缺失: {', '.join(missing)}")

        def replace(match: re.Match[str]) -> str:
            name = match.group(1)
            value = variables.get(name, "")
            if isinstance(value, list | dict):
                return str(value)
            return str(value)

        return [
            {"role": "system", "content": VARIABLE_RE.sub(replace, template.system_prompt)},
            {"role": "user", "content": VARIABLE_RE.sub(replace, template.user_prompt)},
        ]
