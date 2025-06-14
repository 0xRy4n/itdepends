from dataclasses import dataclass
from pydantic import BaseModel
from openai import Client
from itdepends.settings import OPENAI_API_KEY, EVALUATION_MODEL


@dataclass
class EvaluationRule:
    """
    The following is a rule for evaluating a piece of text.
    We want to answer "Does this text contain the phrase or minor variations of the phrase?"
    Text is from a transcription and may be slightly mistranscribed.

    phrase: The phrase we are looking for
    allow_paraphrasing: Whether to allow minor paraphrasing of the phrase.
    paraphrasing_examples: Non-exhaustive examples of acceptable paraphrases / variations
    paraphrasing_counter_examples: Examples of unacceptable paraphrasing.
    """

    phrase: str
    allow_paraphrasing: bool = False
    paraphrasing_examples: list[str] | None = None
    paraphrasing_counter_examples: list[str] | None = None


class BooleanResponse(BaseModel):
    """Evaluation if the text matches the rule."""

    match: bool


class Evaluator:
    def __init__(self, openai_api_key=OPENAI_API_KEY, model=EVALUATION_MODEL):
        self.client = Client(api_key=openai_api_key)
        self.model = model

    def evaluate(self, text: str, rule: EvaluationRule) -> BooleanResponse:
        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"Instructions: {rule.__doc__}, \n\n"
                        f"Rule: {rule.__dict__}\n\n"
                        f"Response Instructions: {BooleanResponse.__doc__}"
                    ),
                },
                {"role": "user", "content": text},
            ],
            temperature=0.0,
            response_format=BooleanResponse,
        )

        return response.choices[0].message.parsed
