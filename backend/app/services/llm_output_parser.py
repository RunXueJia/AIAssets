import json

from jsonschema import ValidationError, validate


class LLMOutputParser:
    def parse_json(self, raw_text: str) -> dict:
        text = raw_text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:]
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end >= start:
            text = text[start : end + 1]
        return json.loads(text)

    def validate(self, parsed: dict, schema: dict) -> tuple[bool, str | None]:
        if not schema:
            return True, None
        try:
            validate(instance=parsed, schema=schema)
            return True, None
        except ValidationError as exc:
            return False, exc.message
