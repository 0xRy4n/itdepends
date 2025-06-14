"""Counter management system for pattern matching and tracking."""

import re
from typing import Dict, Callable, Optional
from dataclasses import dataclass, field
from itdepends.core.evaluation import EvaluationRule, Evaluator
from loguru import logger


@dataclass
class CounterConfig:
    """Configuration for a single counter.

    Attributes:
        name: The name of the counter
        rule: The rule to evaluate against the text
        description: Optional description of what this counter tracks
        callback: Optional callback function called when counter increments
    """

    name: str
    rule: EvaluationRule
    description: str
    callback: Callable[[str, int], None] = None


@dataclass
class CounterManager:
    """Manages multiple counters with pattern matching.

    Attributes:
        counters: Dictionary mapping counter names to their current values
        configs: Dictionary mapping counter names to their configurations
        callbacks: Optional callbacks to execute when counters are incremented
    """
    def __init__(self):
        self.evaluator = Evaluator()
        self.configs: Dict[str, CounterConfig] = {}
        self.counters: Dict[str, int] = {}
        self.callbacks: Dict[str, Callable[[str, int], None]] = {}

    def add_counter(
        self,
        config: CounterConfig,
    ) -> None:
        """Add a new counter with its rule.

        Args:
            name: Name of the counter
            rule: The rule to evaluate against the text
        """
        self.configs[config.name] = config
        self.counters[config.name] = 0

        if config.callback:
            self.callbacks[config.name] = config.callback

    def process_text(self, text: str) -> Dict[str, int]:
        """Process text against all counter patterns and update counters.

        Args:
            text: Text to process against all patterns

        Returns:
            Dictionary of counters that were incremented and their new values
        """
        incremented = {}

        for name, config in self.configs.items():
            evaluation = self.evaluator.evaluate(text, config.rule)
            logger.debug(f"Evaluation for {name}: {evaluation.match}")
            if evaluation.match:
                self.counters[name] += 1
                incremented[name] = self.counters[name]

                # Execute callback if defined
                if name in self.callbacks:
                    self.callbacks[name](name, self.counters[name])

        return incremented

    def get_counter(self, name: str) -> int:
        """Get the current value of a counter.

        Args:
            name: Name of the counter

        Returns:
            Current counter value (0 if counter doesn't exist)
        """
        return self.counters.get(name, 0)

    def get_all_counters(self) -> Dict[str, int]:
        """Get all current counter values.

        Returns:
            Dictionary mapping counter names to their current values
        """
        return self.counters.copy()

    def reset_counter(self, name: str) -> None:
        """Reset a specific counter to 0.

        Args:
            name: Name of the counter to reset
        """
        if name in self.counters:
            self.counters[name] = 0

    def reset_all_counters(self) -> None:
        """Reset all counters to 0."""
        for name in self.counters:
            self.counters[name] = 0
