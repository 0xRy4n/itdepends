"""Real-time transcription application with pattern-based counter tracking."""

import signal
import sys
import time
from typing import Dict, Callable

from loguru import logger
from .core.transcribe import RealtimeTranscriber
from .core.counter import CounterManager, CounterConfig
from .core.html_writer import HTMLWriter


class TranscriptionCounterApp:
    """Main application for real-time transcription with counter tracking.

    Attributes:
        counter_manager: Manages pattern-based counters
        html_writer: Writes HTML files for counter displays
        transcriber: Real-time audio transcriber
    """

    def __init__(self) -> None:
        """Initialize the transcription counter application."""
        logger.debug("Initializing TranscriptionCounterApp")
        self.counter_manager = CounterManager()
        self.html_writer = HTMLWriter()
        self.transcriber: RealtimeTranscriber = None

        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        logger.debug("Signal handler configured for graceful shutdown")

    def setup_counters(self, counter_configs: list[CounterConfig] | CounterConfig) -> None:
        """Set up counters with their patterns and configurations.

        Args:
            counter_configs: Dictionary mapping counter names to their configurations.
                           Each config should contain 'pattern' and optionally 'description'.
        """
        if isinstance(counter_configs, CounterConfig):
            counter_configs = [counter_configs]

        logger.info(f"Setting up {len(counter_configs)} counter(s)")
        for config in counter_configs:
            callback = self._create_counter_callback(config.name, config.description)
            config.callback = callback
            self.counter_manager.add_counter(config)
            
            # Write initial HTML file with 0 count
            logger.debug(f"Writing initial HTML file for counter '{config.name}'")
            self.html_writer.write_counter_file(config.name, 0, config.description)
            
            logger.debug(f"Configured counter '{config.name}' with pattern: {config.rule.phrase}")
        logger.info("All counters configured successfully")

    def _create_counter_callback(
        self, name: str, description: str = None
    ) -> Callable[[str, int], None]:
        """Create a callback function for a specific counter.

        Args:
            name: Name of the counter
            description: Optional description of the counter

        Returns:
            Callback function that handles counter updates
        """

        def callback(counter_name: str, counter_value: int) -> None:
            logger.success(f"{counter_name.replace('_', ' ').title()}: {counter_value}")
            logger.debug(f"Writing HTML file for counter '{counter_name}'")
            self.html_writer.write_counter_file(
                counter_name, counter_value, description
            )

        return callback

    def _transcription_callback(self, text: str) -> None:
        """Handle transcribed text by processing it through counter patterns.

        Args:
            text: Transcribed text to process
        """
        logger.debug(f"Processing transcribed text: {text[:50]}{'...' if len(text) > 50 else ''}")
        self.counter_manager.process_text(text)

    def _signal_handler(self, sig: int, frame) -> None:
        """Handle interrupt signals for graceful shutdown.

        Args:
            sig: Signal number
            frame: Current stack frame
        """
        logger.info("Shutdown signal received, stopping transcription...")
        if self.transcriber:
            self.transcriber.stop()
        logger.info("Application shutdown complete")
        sys.exit(0)

    def run(self) -> None:
        """Start the real-time transcription and counter tracking."""
        logger.info("Starting real-time transcription service")
        
        # Initialize transcriber with our callback
        self.transcriber = RealtimeTranscriber(self._transcription_callback)
        logger.debug("RealtimeTranscriber initialized")

        logger.info("Real-time Transcription:")
        logger.info("-" * 40)

        # Start transcription
        self.transcriber.start()
        logger.info("Transcription started successfully")
        logger.info("Listening for audio... Press Ctrl+C to stop")

        # Keep the main thread alive - transcript will appear continuously
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, shutting down...")
            self.transcriber.stop()
