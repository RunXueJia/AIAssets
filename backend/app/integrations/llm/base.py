from collections.abc import AsyncIterator


class LLMProviderClient:
    async def stream_chat(self, payload: dict) -> AsyncIterator[str]:
        raise NotImplementedError
