import os
from typing import List

import google.generativeai as genai

from bigbuild.utils.llm.provider.base import BaseProvider
from bigbuild.utils.llm.provider.request.google import make_auto_request


class GoogleProvider(BaseProvider):
    def __init__(self, model):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = model
        self.client = genai.GenerativeModel(model)

    def generate_reply(
        self, message, n=1, max_tokens=1024, temperature=0.0, system_msg=None
    ) -> List[str]:
        assert temperature != 0 or n == 1, "n must be 1 when temperature is 0"
        replies = make_auto_request(
            self.client,
            message,
            self.model,
            n=n,
            max_tokens=max_tokens,
            temperature=temperature,
            system_msg=system_msg,
        )

        if len(replies.candidates) != n:
            print(f"[WARNING] # replies = {len(replies.candidates)} != {n = }")

        ret_texts = []
        for candidate in replies.candidates:
            parts = candidate.content.parts
            if parts:
                ret_texts.append(parts[0].text)
            else:
                print("Empty response!")
                ret_texts.append("")
                print(f"{candidate.safety_ratings = }")

        return ret_texts + [""] * (n - len(ret_texts))

    def count_tokens(self, message: str) -> int:
        return len(self.client.tokenize(message))
