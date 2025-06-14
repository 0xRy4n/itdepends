"""Built-in rules for evaluation."""

from itdepends.core.evaluation import EvaluationRule


IT_DEPENDS_RULE = EvaluationRule(
    phrase="it depends",
    allow_paraphrasing=True,
    paraphrasing_examples=[
        "It depends ... (followed by anything not negating the phrase)"
        "I think it depends",
        "It does depend",
        "It definitely depends"
        "Maybe it depends?"
        "That depends",
        "It sort of depends",
        "in depends (minor mispelling)",
    ],
    paraphrasing_counter_examples=[
        "It does not depend",
        "I depend on it",
        "It has a dependency",
        "Does it depend though?",
        "Does it really depend?",
        "I don't think it depends.",
    ],
)
