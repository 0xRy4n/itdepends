import soundcard as sc
import numpy as np
import threading
import time
from typing import Tuple
from dataclasses import dataclass


@dataclass
class AudioConfig:
    """Audio configuration."""

    sample_rate: int = 24000
    channels: int = 1
    block_size: int = 1024
    dtype: str = "float32"
    mic_volume: float = 0.8  # Microphone mixing ratio
    system_volume: float = 0.8  # System audio mixing ratio
    chunk_size: int = 1024
    capture_duration_seconds: float = 0.5  # Duration of each capture chunk in seconds


def record_device_to_memory(
    device, duration_seconds: float, sample_rate: int
) -> Tuple[np.ndarray, bool]:
    """
    Record from a single device and return audio data in memory.

    Args:
        device: Audio device to record from
        duration_seconds: Recording duration in seconds
        sample_rate: Sample rate for recording

    Returns:
        Tuple of (audio_data, success_flag)
    """
    try:
        # Record audio
        data = device.record(
            numframes=int(duration_seconds * sample_rate), samplerate=sample_rate
        )

        # Convert to mono and normalize
        if data is not None and len(data) > 0:
            # Ensure mono
            if data.ndim > 1:
                data = data[:, 0]  # Take left channel

            # Convert to float32 in range [-1, 1]
            if data.dtype != np.float32:
                data = data.astype(np.float32)

            return data, True
        else:
            return np.array([]), False

    except Exception:
        return np.array([]), False


def normalize_audio_level(
    audio_data: np.ndarray, target_rms: float = 0.15
) -> np.ndarray:
    """
    Normalize audio level to prevent clipping during mixing.

    Args:
        audio_data: Input audio data
        target_rms: Target RMS level (default: 0.15 for good headroom)

    Returns:
        Normalized audio data
    """
    if len(audio_data) == 0:
        return audio_data

    # Calculate RMS (Root Mean Square)
    rms = np.sqrt(np.mean(audio_data**2))

    if rms > 0:
        # Normalize to target RMS level
        normalization_factor = target_rms / rms

        # Apply gentle compression to prevent over-normalization
        if normalization_factor > 2.0:
            normalization_factor = 2.0 + (normalization_factor - 2.0) * 0.3

        normalized_audio = audio_data * normalization_factor

        # Apply soft limiting to prevent clipping
        normalized_audio = np.tanh(normalized_audio * 0.9) * 0.8

        return normalized_audio
    else:
        return audio_data


def apply_crossfade(
    audio: np.ndarray, sample_rate: int, fade_duration_ms: float = 10.0
) -> np.ndarray:
    """
    Apply crossfade at the beginning and end to prevent pops and clicks.

    Args:
        audio: Audio array
        sample_rate: Sample rate in Hz
        fade_duration_ms: Fade duration in milliseconds

    Returns:
        Audio with crossfade applied
    """
    if len(audio) == 0:
        return audio

    fade_samples = int(fade_duration_ms * sample_rate / 1000)

    if len(audio) <= 2 * fade_samples:
        fade_samples = len(audio) // 4

    if fade_samples <= 0:
        return audio

    faded_audio = audio.copy()

    # Fade in (start)
    fade_in = np.linspace(0, 1, fade_samples)
    faded_audio[:fade_samples] *= fade_in

    # Fade out (end)
    fade_out = np.linspace(1, 0, fade_samples)
    faded_audio[-fade_samples:] *= fade_out

    return faded_audio


def mix_audio_streams(
    mic_audio: np.ndarray,
    system_audio: np.ndarray,
    mic_ratio: float = 0.7,
    system_ratio: float = 0.5,
) -> np.ndarray:
    """
    Mix microphone and system audio with proper balancing and artifact prevention.

    Args:
        mic_audio: Microphone audio data
        system_audio: System audio data
        mic_ratio: Mixing ratio for microphone (0.0 to 1.0)
        system_ratio: Mixing ratio for system audio (0.0 to 1.0)

    Returns:
        Mixed audio data
    """
    # Handle empty arrays
    if len(mic_audio) == 0 and len(system_audio) == 0:
        return np.array([])
    elif len(mic_audio) == 0:
        return system_audio * system_ratio
    elif len(system_audio) == 0:
        return mic_audio * mic_ratio

    # Align lengths by padding with silence
    max_length = max(len(mic_audio), len(system_audio))

    if len(mic_audio) < max_length:
        mic_audio = np.pad(mic_audio, (0, max_length - len(mic_audio)), "constant")

    if len(system_audio) < max_length:
        system_audio = np.pad(
            system_audio, (0, max_length - len(system_audio)), "constant"
        )

    # Mix the streams
    mixed_audio = (mic_audio * mic_ratio) + (system_audio * system_ratio)

    # Apply gentle compression to handle peaks
    mixed_audio = np.tanh(mixed_audio * 0.8) * 0.85

    # Final normalization to prevent clipping while maintaining dynamics
    peak = np.max(np.abs(mixed_audio))
    if peak > 0.95:
        mixed_audio = mixed_audio * (0.95 / peak)

    return mixed_audio


class AudioCapture:
    """Audio capture with dual-stream recording and mixing."""

    def __init__(self, config: AudioConfig, transcriber=None):
        """Initialize audio capture."""
        self.config = config
        self._transcriber = transcriber
        self._running = False

        self._default_speaker = None
        self._default_mic = None
        self._system_mic = None

        # Mixed audio buffer for transcriber
        self._mixed_buffer = bytearray()
        self._mixed_buffer_lock = threading.Lock()

        self._initialize_devices()

        # Start continuous capture thread
        self._capture_thread = None

    def _initialize_devices(self):
        """Initialize audio devices."""
        # Get default devices
        self._default_speaker = sc.default_speaker()
        self._default_mic = sc.default_microphone()

        # Find system audio loopback
        mics = sc.all_microphones(include_loopback=True)
        self._system_mic = None

        for mic in mics:
            try:
                if mic.name == self._default_speaker.name:
                    self._system_mic = mic
                    break
            except Exception:
                continue

    def _record_and_mix_chunk(self):
        """Record and mix a chunk from both audio sources."""
        # Shared variables for thread communication
        mic_audio_result = [None, False]
        system_audio_result = [None, False]

        def record_mic():
            audio_data, success = record_device_to_memory(
                self._default_mic,
                self.config.capture_duration_seconds,
                self.config.sample_rate,
            )
            mic_audio_result[0] = audio_data
            mic_audio_result[1] = success

        def record_system():
            audio_data, success = record_device_to_memory(
                self._system_mic,
                self.config.capture_duration_seconds,
                self.config.sample_rate,
            )
            system_audio_result[0] = audio_data
            system_audio_result[1] = success

        # Create threads for simultaneous recording
        mic_thread = threading.Thread(target=record_mic)
        system_thread = threading.Thread(target=record_system)

        # Start both recordings
        mic_thread.start()
        system_thread.start()

        # Wait for both to complete
        mic_thread.join()
        system_thread.join()

        # Get the recorded audio data
        mic_audio, mic_success = mic_audio_result
        system_audio, system_success = system_audio_result

        if not mic_success and not system_success:
            return None

        # Apply crossfade to individual audio streams
        if mic_success and len(mic_audio) > 0:
            mic_audio = apply_crossfade(mic_audio, self.config.sample_rate)

        if system_success and len(system_audio) > 0:
            system_audio = apply_crossfade(system_audio, self.config.sample_rate)

        # Mix the audio streams
        mixed_audio = mix_audio_streams(
            mic_audio if mic_success else np.array([]),
            system_audio if system_success else np.array([]),
            mic_ratio=self.config.mic_volume,
            system_ratio=self.config.system_volume,
        )

        if len(mixed_audio) > 0:
            # Apply final crossfade for clean start/end
            mixed_audio = apply_crossfade(
                mixed_audio, self.config.sample_rate, fade_duration_ms=5.0
            )
            return mixed_audio
        else:
            return None

    def _continuous_capture(self):
        """Continuous capture loop."""
        while self._running:
            try:
                # Record and mix a chunk
                mixed_audio = self._record_and_mix_chunk()

                if mixed_audio is not None and len(mixed_audio) > 0:
                    # Convert to int16 bytes for transcriber
                    mixed_int16 = (mixed_audio * 32767).astype(np.int16)
                    mixed_bytes = mixed_int16.tobytes()

                    # Send to transcriber
                    self._send_mixed_audio_data(mixed_bytes)

            except Exception:
                if self._running:
                    time.sleep(0.1)

    def _send_mixed_audio_data(self, audio_bytes: bytes):
        """Send mixed audio data to transcriber."""
        # Use timeout lock to prevent deadlocks
        try:
            if self._mixed_buffer_lock.acquire(timeout=0.1):
                try:
                    self._mixed_buffer.extend(audio_bytes)

                    # Send chunks when buffer is large enough
                    while len(self._mixed_buffer) >= self.config.chunk_size:
                        chunk = bytes(self._mixed_buffer[: self.config.chunk_size])
                        self._mixed_buffer = self._mixed_buffer[
                            self.config.chunk_size :
                        ]

                        if self._transcriber and hasattr(
                            self._transcriber, "_process_audio_bytes"
                        ):
                            try:
                                self._transcriber._process_audio_bytes(chunk)
                            except Exception:
                                pass
                finally:
                    self._mixed_buffer_lock.release()
        except Exception:
            pass

    def start(self) -> None:
        """Start audio capture."""
        if not self._running:
            self._running = True

            # Start continuous capture thread
            try:
                self._capture_thread = threading.Thread(
                    target=self._continuous_capture, daemon=True
                )
                self._capture_thread.start()
            except Exception:
                self._running = False

    def stop(self) -> None:
        """Stop audio capture."""
        self._running = False

        # Wait for capture thread to finish
        if self._capture_thread and self._capture_thread.is_alive():
            self._capture_thread.join(timeout=2.0)

    def __del__(self):
        """Cleanup."""
        self.stop()
