"""HTML file writer for counter display pages."""

import os
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime


class HTMLWriter:
    """Writes HTML files for counter displays.

    Attributes:
        output_dir: Directory where HTML files will be written
    """

    def __init__(self, output_dir: str = "web") -> None:
        """Initialize the HTML writer.

        Args:
            output_dir: Directory to write HTML files to
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def generate_counter_html(
        self, counter_name: str, counter_value: int, description: Optional[str] = None
    ) -> str:
        """Generate HTML content for a counter display.

        Args:
            counter_name: Name of the counter
            counter_value: Current value of the counter
            description: Optional description of what the counter tracks

        Returns:
            HTML content as a string
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        title = counter_name.replace("_", " ").title()
        
        # Create dynamic content based on description
        if description:
            display_text = description.replace("Tracks the number of times", "").replace("is said.", "").strip()
            if display_text.startswith("the phrase"):
                display_text = display_text.replace("the phrase", "").strip().strip("'\"")
            display_text = display_text.capitalize() if display_text else title
        else:
            display_text = title

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} Counter</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
        
        body {{
            font-family: 'Orbitron', 'Segoe UI', monospace;
            background: transparent;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            color: #c0c0c0;
            overflow: hidden;
        }}
        
        .counter-container {{
            background: linear-gradient(135deg, #141d2b 0%, #1a2332 50%, #141d2b 100%);
            border-radius: 12px;
            padding: 16px 32px;
            text-align: center;
            box-shadow: 
                0 0 20px rgba(159, 239, 0, 0.3),
                0 8px 32px rgba(0, 0, 0, 0.7),
                inset 0 1px 0 rgba(159, 239, 0, 0.1);
            border: 2px solid #9fef00;
            display: flex;
            align-items: center;
            gap: 20px;
            min-width: 350px;
            max-width: 700px;
            position: relative;
            overflow: hidden;
        }}
        
        .counter-container::before {{
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(159, 239, 0, 0.1), transparent);
            animation: shimmer 10s infinite;
        }}
        
        .counter-container::after {{
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(159, 239, 0, 0.03) 0%, transparent 70%);
            animation: rotate 10s linear infinite;
            pointer-events: none;
        }}
        
        .counter-label {{
            font-size: 1.6em;
            font-weight: 700;
            color: #9fef00;
            white-space: nowrap;
            text-shadow: 
                0 0 10px rgba(159, 239, 0, 0.5),
                0 0 20px rgba(159, 239, 0, 0.3),
                0 2px 4px rgba(0, 0, 0, 0.5);
            letter-spacing: 1px;
            position: relative;
            z-index: 2;
            text-transform: uppercase;
        }}
        
        .counter-separator {{
            font-size: 2em;
            color: #9fef00;
            opacity: 0.8;
            text-shadow: 0 0 5px rgba(159, 239, 0, 0.5);
            animation: pulse-separator 10s ease-in-out infinite;
            position: relative;
            z-index: 2;
        }}
        
        .counter-value {{
            font-size: 3.2em;
            font-weight: 900;
            color: #9fef00;
            text-shadow: 
                0 0 15px rgba(159, 239, 0, 0.8),
                0 0 30px rgba(159, 239, 0, 0.4),
                0 4px 8px rgba(0, 0, 0, 0.7);
            min-width: 80px;
            position: relative;
            z-index: 2;
            transition: all 0.3s ease;
        }}
        
        .counter-value::before {{
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 120%;
            height: 120%;
            background: radial-gradient(circle, rgba(159, 239, 0, 0.1) 0%, transparent 70%);
            border-radius: 50%;
            z-index: -1;
            animation: value-glow 3s ease-in-out infinite alternate;
        }}
        
        .particles {{
            position: absolute;
            width: 100%;
            height: 100%;
            overflow: hidden;
            pointer-events: none;
            z-index: 1;
        }}
        
        .particle {{
            position: absolute;
            width: 2px;
            height: 2px;
            background: #9fef00;
            border-radius: 50%;
            opacity: 0;
            animation: float 4s linear infinite;
        }}
        
        @keyframes shimmer {{
            0% {{ left: -100%; }}
            100% {{ left: 100%; }}
        }}
        
        @keyframes rotate {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(360deg); }}
        }}
        
        @keyframes pulse-separator {{
            0%, 100% {{ opacity: 0.8; transform: scale(1); }}
            50% {{ opacity: 1; transform: scale(1.1); }}
        }}
        
        @keyframes value-glow {{
            0% {{ opacity: 0.3; transform: translate(-50%, -50%) scale(1); }}
            100% {{ opacity: 0.6; transform: translate(-50%, -50%) scale(1.2); }}
        }}
        
        @keyframes float {{
            0% {{
                opacity: 0;
                transform: translateY(100%) translateX(var(--random-x)) scale(0);
            }}
            10% {{
                opacity: 1;
                transform: translateY(90%) translateX(var(--random-x)) scale(1);
            }}
            90% {{
                opacity: 1;
                transform: translateY(10%) translateX(var(--random-x)) scale(1);
            }}
            100% {{
                opacity: 0;
                transform: translateY(0%) translateX(var(--random-x)) scale(0);
            }}
        }}
        
        @keyframes counter-update {{
            0% {{ transform: scale(1); }}
            50% {{ 
                transform: scale(1.2);
                text-shadow: 
                    0 0 25px rgba(159, 239, 0, 1),
                    0 0 50px rgba(159, 239, 0, 0.6),
                    0 4px 8px rgba(0, 0, 0, 0.7);
            }}
            100% {{ transform: scale(1); }}
        }}
        
        .counter-value.updated {{
            animation: counter-update 0.6s ease-out;
        }}
        
        .counter-container.updated {{
            animation: container-flash 0.6s ease-out;
        }}
        
        @keyframes container-flash {{
            0% {{ border-color: #9fef00; }}
            50% {{ 
                border-color: #9fef00;
                box-shadow: 
                    0 0 30px rgba(159, 239, 0, 0.8),
                    0 0 60px rgba(159, 239, 0, 0.4),
                    0 8px 32px rgba(0, 0, 0, 0.7);
            }}
            100% {{ border-color: #9fef00; }}
        }}
    </style>
    <meta http-equiv="refresh" content="1">
</head>
<body>
    <div class="counter-container" id="counter-container">
        <div class="particles" id="particles"></div>
        <div class="counter-label">{display_text}</div>
        <div class="counter-separator">:</div>
        <div class="counter-value" id="counter-value">{counter_value}</div>
    </div>
    <script>
        // Particle system
        function createParticle() {{
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.style.left = Math.random() * 100 + '%';
            particle.style.setProperty('--random-x', (Math.random() - 0.5) * 100 + 'px');
            particle.style.animationDelay = Math.random() * 2 + 's';
            document.getElementById('particles').appendChild(particle);
            
            setTimeout(() => {{
                particle.remove();
            }}, 4000);
        }}
        
        // Create particles periodically
        setInterval(createParticle, 500);
        
        // Counter update animation
        const counterValue = document.getElementById('counter-value');
        const counterContainer = document.getElementById('counter-container');
        const currentValue = parseInt(counterValue.textContent);
        const lastValue = localStorage.getItem('lastCounterValue');
        
        if (lastValue && parseInt(lastValue) !== currentValue) {{
            counterValue.classList.add('updated');
            counterContainer.classList.add('updated');
            
            // Create burst of particles on update
            for (let i = 0; i < 5; i++) {{
                setTimeout(createParticle, i * 100);
            }}
            
            setTimeout(() => {{
                counterValue.classList.remove('updated');
                counterContainer.classList.remove('updated');
            }}, 600);
        }}
        
        localStorage.setItem('lastCounterValue', currentValue.toString());
    </script>
</body>
</html>"""
        return html_content

    def write_counter_file(
        self, counter_name: str, counter_value: int, description: Optional[str] = None
    ) -> Path:
        """Write an HTML file for a counter.

        Args:
            counter_name: Name of the counter
            counter_value: Current value of the counter
            description: Optional description of what the counter tracks

        Returns:
            Path to the created HTML file
        """
        html_content = self.generate_counter_html(
            counter_name, counter_value, description
        )
        file_path = self.output_dir / f"{counter_name}.html"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return file_path

    def write_all_counters(
        self, counters: Dict[str, int], descriptions: Optional[Dict[str, str]] = None
    ) -> None:
        """Write HTML files for all counters.

        Args:
            counters: Dictionary mapping counter names to their values
            descriptions: Optional dictionary mapping counter names to descriptions
        """
        descriptions = descriptions or {}

        for counter_name, counter_value in counters.items():
            description = descriptions.get(counter_name)
            self.write_counter_file(counter_name, counter_value, description)
