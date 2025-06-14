# ItDepends - Real-time Speech Counter for Streaming

A wildly over-engineered bot that increments a counter (in the form of an OBS browser componenet) when you say "it depends". Or other stuff, I guess.

## 🚀 Quick Start

### Prerequisites

- Python 3.12 or higher
- OpenAI API key

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd itdepends
   ```

2. **Install dependencies:**
   ```bash
   pip install -e .
   ```

3. **Set up your environment:**
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

### Usage

1. **Start the application:**
   ```bash
   python main.py
   ```

2. **Start speaking or playing system audio** The app will:
   - Listen to your microphone / system audio
   - Transcribe speech in real-time
   - Count occurrences of configured phrases
   - Generate HTML counter displays

3. **Access your counters:**
   - HTML files are created in the `web/` directory
   - Each counter gets its own HTML file (e.g., `web/it_depends.html`)
   - Files auto-refresh every second


## ⚙️ Configuration

### Creating Custom Counters

Edit `itdepends/counters.py` to add your own counters:

```python
from itdepends.core.counter import CounterConfig
from itdepends.core.evaluation import EvaluationRule

# Create a custom counter
CUSTOM_COUNTER = CounterConfig(
    name="awesome_count",
    rule=EvaluationRule(
        phrase="that's awesome",
        allow_paraphrasing=True,
        paraphrasing_examples=["that's great", "that's amazing"],
        paraphrasing_counter_examples=["that's awful", "that's terrible"]
    ),
    description="Tracks positive reactions"
)
```

### Using Multiple Counters

In `main.py`, you can set up multiple counters:

```python
from itdepends.app import TranscriptionCounterApp
from itdepends.counters import IT_DEPENDS_COUNTER, CUSTOM_COUNTER

app = TranscriptionCounterApp()
app.setup_counters([IT_DEPENDS_COUNTER, CUSTOM_COUNTER])
app.run()
```

### Environment Variables

Create a `.env` file to customize:

```env
# Required
OPENAI_API_KEY=your_api_key_here

# Optional (with defaults)
EVALUATION_MODEL=gpt-4o
TRANSCRIPTION_MODEL=gpt-4o-transcribe
```
