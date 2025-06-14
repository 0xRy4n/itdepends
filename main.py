"""Main entry point - defines patterns and runs the transcription counter app."""

from itdepends.app import TranscriptionCounterApp
from itdepends.counters import IT_DEPENDS_COUNTER


if __name__ == "__main__":
    app = TranscriptionCounterApp()
    app.setup_counters(IT_DEPENDS_COUNTER)
    app.run()


