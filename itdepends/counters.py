from itdepends.core.counter import CounterConfig
from itdepends.rules import IT_DEPENDS_RULE

IT_DEPENDS_COUNTER = CounterConfig(
    name="it_depends",
    rule=IT_DEPENDS_RULE,
    description="Tracks the number of times the phrase 'it depends' is said.",
)