"""Real-time audio transcription using OpenAI's Realtime Transcription Sessions API."""

import numpy as np
import time
import threading
import asyncio
import websockets
import json
import base64
import requests
import warnings

from threading import Lock
from collections import deque
from typing import Optional, Tuple, List, Deque, Dict, Any, Callable

from ..settings import OPENAI_API_KEY, TRANSCRIPTION_SESSIONS_URL, REALTIME_WS_URL, TRANSCRIPTION_MODEL
from .audio_capture import AudioCapture, AudioConfig

SAMPLERATE = 24000  # OpenAI Realtime API requires 24kHz
MAX_CHUNKS = 1000


class RealtimeTranscriber:
    """Real-time transcriber using OpenAI's Transcription Sessions API."""

    def __init__(self, callback: Callable[[str], None] = None):
        """Initialize the Realtime Transcriber."""
        self._full_transcript = ""
        self._chunks: Deque[Tuple[str, float]] = deque(maxlen=MAX_CHUNKS)
        self._lock = Lock()
        self._running = False
        self._websocket = None
        self._loop = None
        self._thread: Optional[threading.Thread] = None
        self._session_data: Optional[Dict[str, Any]] = None
        self._client_secret: Optional[str] = None
        self._processing_start_time: Optional[float] = None
        self._callback = callback
        # Dual audio capture setup - microphone and system audio at full volume
        self._audio_capture = AudioCapture(
            AudioConfig(
                sample_rate=SAMPLERATE,
                channels=1,
                block_size=512,
                dtype="float32",
                mic_volume=1.0,  # Full microphone volume
                system_volume=1.0,  # Full system audio volume
            ),
            transcriber=self,
        )

        # Suppress warnings
        warnings.filterwarnings("ignore", category=UserWarning, module="soundcard")

    def _create_transcription_session(self) -> bool:
        """Create a transcription session and get ephemeral client secret."""
        try:
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            }

            # Start with empty payload as shown in OpenAI spec example
            payload = {}

            response = requests.post(
                TRANSCRIPTION_SESSIONS_URL, headers=headers, json=payload
            )
            response.raise_for_status()

            self._session_data = response.json()
            self._client_secret = self._session_data.get("client_secret", {}).get(
                "value"
            )

            if not self._client_secret:
                return False

            return True

        except Exception as e:
            return False

    def _update_transcript(self, new_text: str) -> None:
        """Update both the full transcript and chunks with new text."""
        if not new_text or new_text.isspace():
            return

        with self._lock:
            # Add to chunks with timestamp
            self._chunks.append((new_text, time.time()))

            # Update full transcript
            if self._full_transcript:
                self._full_transcript += " " + new_text
            else:
                self._full_transcript = new_text

            if self._callback:
                self._callback(new_text)

    def _process_audio_bytes(self, audio_bytes: bytes) -> None:
        """Process raw audio bytes and send to WebSocket."""
        if not self._websocket or not self._running:
            return

        try:
            # Encode to base64
            audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

            # Send audio data to WebSocket
            message = {"type": "input_audio_buffer.append", "audio": audio_base64}

            # Send immediately
            if self._loop and not self._loop.is_closed():
                asyncio.run_coroutine_threadsafe(
                    self._send_message(message), self._loop
                )

        except Exception as e:
            pass  # Keep running even if there are errors

    def _process_audio_block(self, audio_data: np.ndarray) -> None:
        """Process a block of audio data and send to WebSocket."""
        if not self._websocket or not self._running:
            return

        try:
            # Ensure audio is in the correct range
            audio_data = np.clip(audio_data, -1.0, 1.0)

            # Convert to int16 PCM format with little-endian byte order (as required by OpenAI)
            audio_int16 = (audio_data * 32767).astype(
                "<i2"
            )  # '<i2' = little-endian int16
            audio_bytes = audio_int16.tobytes()

            # Encode to base64
            audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

            # Send audio data to WebSocket
            message = {"type": "input_audio_buffer.append", "audio": audio_base64}

            # Send immediately
            if self._loop and not self._loop.is_closed():
                asyncio.run_coroutine_threadsafe(
                    self._send_message(message), self._loop
                )

        except Exception as e:
            pass  # Keep running even if there are errors

    async def _send_message(self, message: dict) -> None:
        """Send a message to the WebSocket."""
        if self._websocket:
            try:
                await self._websocket.send(json.dumps(message))
            except Exception as e:
                pass  # Suppress error messages

    async def _initialize_transcription_session(self) -> None:
        """Initialize the transcription session over WebSocket."""
        if not self._session_data:
            return

        # Configure for very responsive VAD with short silence threshold
        session_update = {
            "type": "transcription_session.update",
            "session": {
                "input_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": TRANSCRIPTION_MODEL,
                    "language": "en",  # Explicitly set English
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.3,  # Balanced threshold - not too sensitive
                    "prefix_padding_ms": 300,  # Standard padding to capture start of speech
                    "silence_duration_ms": 100,  # Allow complete thoughts - not too short
                },
            },
        }

        await self._websocket.send(json.dumps(session_update))

    async def _handle_message(self, message: str) -> None:
        """Handle incoming WebSocket messages from transcription session."""
        try:
            data = json.loads(message)
            event_type = data.get("type", "")

            if event_type == "input_audio_buffer.speech_stopped":
                # Auto-commit when speech stops
                commit_message = {"type": "input_audio_buffer.commit"}
                await self._send_message(commit_message)
            elif event_type == "input_audio_buffer.committed":
                self._processing_start_time = (
                    time.time()
                )  # Track when processing started

            # Handle transcription events - only print actual transcription
            elif event_type == "conversation.item.input_audio_transcription.completed":
                transcript = data.get("transcript", "").strip()
                if transcript:
                    # Add proper spacing and newline for completed transcriptions
                    print(f"\nTranscript: {transcript}")
                    self._update_transcript(transcript)
                self._processing_start_time = None  # Clear processing timer

            elif event_type == "conversation.item.input_audio_transcription.delta":
                delta = data.get("delta", "").strip()
                if delta:
                    print(delta, end="", flush=True)

            elif event_type == "conversation.item.input_audio_transcription.failed":
                error = data.get("error", {})
                print(f"\n[Transcription failed: {error}]")
                self._processing_start_time = None  # Clear processing timer

        except Exception as e:
            pass  # Keep running silently

    async def _check_processing_timeout(self) -> None:
        """Check if transcription processing has timed out and recover."""
        while self._running:
            if (
                self._processing_start_time
                and time.time() - self._processing_start_time > 5.0
            ):  # 5 second timeout
                print("\n[Timeout - retrying...]", flush=True)
                self._processing_start_time = None

                # Try to clear the audio buffer and restart
                try:
                    clear_message = {"type": "input_audio_buffer.clear"}
                    await self._send_message(clear_message)
                except:
                    pass

            await asyncio.sleep(1)  # Check every second

    async def _websocket_handler(self) -> None:
        """Main WebSocket connection handler for transcription sessions."""
        try:
            headers = {
                "Authorization": f"Bearer {self._client_secret}",
                "OpenAI-Beta": "realtime=v1",
            }

            async with websockets.connect(
                REALTIME_WS_URL,
                additional_headers=headers,
                ping_interval=20,
                ping_timeout=10,
            ) as websocket:
                self._websocket = websocket

                # Initialize transcription session
                await self._initialize_transcription_session()

                # Start audio capture
                self._audio_capture.start()

                # Start timeout checker
                timeout_task = asyncio.create_task(self._check_processing_timeout())

                try:
                    # Listen for messages
                    async for message in websocket:
                        await self._handle_message(message)
                finally:
                    timeout_task.cancel()

        except Exception as e:
            pass  # Keep running silently
        finally:
            self._websocket = None
            self._audio_capture.stop()

    def _run_event_loop(self) -> None:
        """Run the asyncio event loop in a separate thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        try:
            self._loop.run_until_complete(self._websocket_handler())
        except Exception as e:
            print(f"Event loop error: {e}")
        finally:
            self._loop.close()

    def start(self) -> None:
        """Start the transcription process."""
        if not self._running:
            # Create the transcription session
            if not self._create_transcription_session():
                return

            self._running = True
            self._thread = threading.Thread(target=self._run_event_loop, daemon=True)
            self._thread.start()

    def stop(self) -> None:
        """Stop the transcription process."""

        self._running = False

        # Stop audio capture first
        if hasattr(self, "_audio_capture"):
            self._audio_capture.stop()

        if self._websocket:
            # Schedule close in the event loop if it exists and is running
            if self._loop and not self._loop.is_closed():
                try:
                    asyncio.run_coroutine_threadsafe(
                        self._websocket.close(), self._loop
                    )
                except Exception:
                    pass  # Ignore errors during shutdown

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
            self._thread = None

        # Clear session data
        self._session_data = None
        self._client_secret = None
        self._loop = None

    def manual_commit(self) -> None:
        """Manually commit the audio buffer to trigger transcription."""
        if self._websocket and self._loop and not self._loop.is_closed():
            commit_message = {"type": "input_audio_buffer.commit"}
            asyncio.run_coroutine_threadsafe(
                self._send_message(commit_message), self._loop
            )

    def get_full_transcript(self) -> str:
        """Get the complete transcript."""
        with self._lock:
            return self._full_transcript

    def get_chunks(self) -> List[Tuple[str, float]]:
        """Get all transcript chunks with timestamps."""
        with self._lock:
            return list(self._chunks)

    def get_recent_chunks(self, seconds: float = 60.0) -> List[Tuple[str, float]]:
        """Get transcript chunks from the last N seconds."""
        with self._lock:
            cutoff_time = time.time() - seconds
            return [(text, ts) for text, ts in self._chunks if ts >= cutoff_time]


# Create a global instance
transcriber = RealtimeTranscriber()

# Don't auto-start - let main.py control it
