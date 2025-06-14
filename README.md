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

2. **Start speaking!** The app will:
   - Listen to your microphone
   - Transcribe speech in real-time
   - Count occurrences of configured phrases
   - Generate HTML counter displays

3. **Access your counters:**
   - HTML files are created in the `web/` directory
   - Each counter gets its own HTML file (e.g., `web/it_depends.html`)
   - Files auto-refresh every second

## 🎮 OBS Integration

### Adding Counters to OBS

1. **Add Browser Source:**
   - In OBS, add a new "Browser" source
   - Set URL to the full path of your HTML file:
     ```
     file:///path/to/your/project/web/it_depends.html
     ```

2. **Recommended Settings:**
   - Width: 600px
   - Height: 100px
   - ✅ Shutdown source when not visible
   - ✅ Refresh browser when scene becomes active

3. **Positioning:**
   - Counters have transparent backgrounds
   - Designed to be horizontal overlays
   - Position anywhere on your stream layout

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

## 🎨 Counter Styling

The HTML counters feature:
- **Futuristic design** with Orbitron font
- **Animated particles** and glowing effects
- **Color scheme:** Dark blue (`#141d2b`) with neon green (`#9fef00`) accents
- **Responsive layout** that works on any screen size
- **Update animations** that flash when counters increment

### Customizing Appearance

To modify the styling, edit `itdepends/core/html_writer.py` and update the CSS in the `generate_counter_html` method.

## 🔧 Troubleshooting

### Common Issues

**"No audio input detected"**
- Check your microphone permissions
- Ensure your microphone is set as the default recording device

**"OpenAI API error"**
- Verify your API key is correct in the `.env` file
- Check your OpenAI account has sufficient credits

**"Counter not updating"**
- The phrase detection is intelligent but may miss variations
- Try adding paraphrasing examples to your rules
- Check the console logs for transcription output

### Debug Mode

Run with debug logging to see transcription output:
```bash
python main.py
```

The console will show:
- Real-time transcription text
- When phrases are detected
- Counter increment events
- HTML file generation

## 📁 Project Structure

```
itdepends/
├── itdepends/
│   ├── core/
│   │   ├── counter.py      # Counter management
│   │   ├── evaluation.py   # AI-powered phrase detection
│   │   ├── html_writer.py  # HTML counter generation
│   │   └── transcribe.py   # Real-time transcription
│   ├── app.py              # Main application
│   ├── counters.py         # Counter configurations
│   └── settings.py         # Environment configuration
├── web/                    # Generated HTML files
├── main.py                 # Entry point
└── README.md              # This file
```

## 🤝 Contributing

Feel free to submit issues and enhancement requests! Some ideas:
- Additional counter themes
- Discord integration
- Webhook support for external services
- Sound effects on counter increments

## 📄 License

This project is open source. See the license file for details.

---

**Happy streaming!** 🎉
