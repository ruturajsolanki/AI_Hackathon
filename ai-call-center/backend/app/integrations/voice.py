"""
Voice Service

Abstraction for voice handling including Speech-to-Text (STT) and
Text-to-Speech (TTS) operations. Designed for easy replacement with
real telephony providers.

This module provides:
- Abstract interfaces for STT and TTS
- Simulated implementations for development/testing
- Voice service facade for unified access
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# Voice Models
# -----------------------------------------------------------------------------

class AudioFormat(str, Enum):
    """Supported audio formats."""
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"
    PCM = "pcm"
    WEBM = "webm"


class VoiceGender(str, Enum):
    """Voice gender options for TTS."""
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"


class Language(str, Enum):
    """Supported languages."""
    EN_US = "en-US"
    EN_GB = "en-GB"
    ES_ES = "es-ES"
    FR_FR = "fr-FR"
    DE_DE = "de-DE"


class AudioInput(BaseModel):
    """
    Represents audio input for STT processing.
    
    In production, audio_data would contain actual audio bytes.
    For simulation, we use simulated_text as a stand-in.
    """
    input_id: UUID = Field(default_factory=uuid4)
    audio_format: AudioFormat = Field(default=AudioFormat.WAV)
    sample_rate: int = Field(default=16000)
    language: Language = Field(default=Language.EN_US)
    
    # In production: actual audio bytes
    audio_data: Optional[bytes] = Field(default=None, exclude=True)
    
    # For simulation: text that "would have been spoken"
    simulated_text: Optional[str] = Field(default=None)
    
    # Metadata
    duration_seconds: Optional[float] = Field(default=None)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TranscriptionResult(BaseModel):
    """Result of STT processing."""
    transcription_id: UUID = Field(default_factory=uuid4)
    input_id: UUID = Field(description="Reference to original audio input")
    
    # Transcription
    text: str = Field(description="Transcribed text")
    confidence: float = Field(ge=0.0, le=1.0, description="Transcription confidence")
    
    # Alternatives (if available)
    alternatives: List[str] = Field(default_factory=list)
    
    # Timing
    processing_time_ms: int = Field(default=0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Status
    is_final: bool = Field(default=True)
    is_partial: bool = Field(default=False)


class SpeechRequest(BaseModel):
    """Request for TTS processing."""
    request_id: UUID = Field(default_factory=uuid4)
    
    # Content
    text: str = Field(description="Text to synthesize")
    
    # Voice settings
    language: Language = Field(default=Language.EN_US)
    voice_gender: VoiceGender = Field(default=VoiceGender.NEUTRAL)
    voice_name: Optional[str] = Field(default=None)
    
    # Audio settings
    output_format: AudioFormat = Field(default=AudioFormat.WAV)
    sample_rate: int = Field(default=22050)
    speaking_rate: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=0.0, ge=-10.0, le=10.0)
    
    # Metadata
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SpeechResult(BaseModel):
    """Result of TTS processing."""
    result_id: UUID = Field(default_factory=uuid4)
    request_id: UUID = Field(description="Reference to original request")
    
    # In production: actual audio bytes
    audio_data: Optional[bytes] = Field(default=None, exclude=True)
    
    # For simulation: metadata about what would be generated
    audio_format: AudioFormat
    sample_rate: int
    duration_seconds: float
    
    # Original text
    original_text: str
    
    # Processing
    processing_time_ms: int = Field(default=0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Status
    success: bool = Field(default=True)
    error: Optional[str] = Field(default=None)


# -----------------------------------------------------------------------------
# Abstract Interfaces
# -----------------------------------------------------------------------------

class STTProvider(ABC):
    """
    Abstract interface for Speech-to-Text providers.
    
    Implement this interface to integrate with real STT services
    like Google Speech, AWS Transcribe, Azure Speech, etc.
    """
    
    @abstractmethod
    async def transcribe(
        self,
        audio_input: AudioInput,
    ) -> TranscriptionResult:
        """
        Transcribe audio to text.
        
        Args:
            audio_input: Audio data to transcribe.
            
        Returns:
            TranscriptionResult with transcribed text and confidence.
        """
        pass
    
    @abstractmethod
    async def transcribe_stream(
        self,
        audio_chunks: list,
        language: Language = Language.EN_US,
    ) -> TranscriptionResult:
        """
        Transcribe streaming audio.
        
        Args:
            audio_chunks: List of audio data chunks.
            language: Target language for transcription.
            
        Returns:
            TranscriptionResult with final transcription.
        """
        pass
    
    @abstractmethod
    def get_supported_languages(self) -> List[Language]:
        """Get list of supported languages."""
        pass


class TTSProvider(ABC):
    """
    Abstract interface for Text-to-Speech providers.
    
    Implement this interface to integrate with real TTS services
    like Google TTS, AWS Polly, Azure Speech, etc.
    """
    
    @abstractmethod
    async def synthesize(
        self,
        request: SpeechRequest,
    ) -> SpeechResult:
        """
        Synthesize speech from text.
        
        Args:
            request: Speech synthesis request.
            
        Returns:
            SpeechResult with audio data.
        """
        pass
    
    @abstractmethod
    def get_available_voices(
        self,
        language: Optional[Language] = None,
    ) -> List[dict]:
        """
        Get available voices.
        
        Args:
            language: Optional filter by language.
            
        Returns:
            List of voice configurations.
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[AudioFormat]:
        """Get list of supported audio formats."""
        pass


# -----------------------------------------------------------------------------
# Simulated Implementations
# -----------------------------------------------------------------------------

class SimulatedSTTProvider(STTProvider):
    """
    Simulated STT provider for development and testing.
    
    Uses simulated_text from AudioInput or generates placeholder text.
    """
    
    def __init__(self, default_confidence: float = 0.95):
        """
        Initialize simulated STT.
        
        Args:
            default_confidence: Default confidence score for transcriptions.
        """
        self._default_confidence = default_confidence
        self._supported_languages = list(Language)
    
    async def transcribe(
        self,
        audio_input: AudioInput,
    ) -> TranscriptionResult:
        """Simulate transcription from audio."""
        # Use simulated text if provided
        if audio_input.simulated_text:
            text = audio_input.simulated_text
            confidence = self._default_confidence
        else:
            # Generate placeholder based on duration
            duration = audio_input.duration_seconds or 2.0
            word_count = int(duration * 2.5)  # ~2.5 words per second
            text = f"[Simulated transcription: {word_count} words from {duration:.1f}s audio]"
            confidence = 0.85
        
        return TranscriptionResult(
            input_id=audio_input.input_id,
            text=text,
            confidence=confidence,
            alternatives=[],
            processing_time_ms=int((audio_input.duration_seconds or 1.0) * 100),
            is_final=True,
            is_partial=False,
        )
    
    async def transcribe_stream(
        self,
        audio_chunks: list,
        language: Language = Language.EN_US,
    ) -> TranscriptionResult:
        """Simulate streaming transcription."""
        # Combine chunks and simulate
        total_chunks = len(audio_chunks)
        simulated_duration = total_chunks * 0.5  # Assume 0.5s per chunk
        
        return TranscriptionResult(
            input_id=uuid4(),
            text=f"[Streamed transcription from {total_chunks} chunks]",
            confidence=self._default_confidence,
            alternatives=[],
            processing_time_ms=int(simulated_duration * 50),
            is_final=True,
            is_partial=False,
        )
    
    def get_supported_languages(self) -> List[Language]:
        """Return all languages as supported in simulation."""
        return self._supported_languages


class SimulatedTTSProvider(TTSProvider):
    """
    Simulated TTS provider for development and testing.
    
    Generates metadata about what audio would be produced
    without actual audio synthesis.
    """
    
    def __init__(self, words_per_minute: float = 150.0):
        """
        Initialize simulated TTS.
        
        Args:
            words_per_minute: Speaking rate for duration estimation.
        """
        self._wpm = words_per_minute
        self._voices = self._create_simulated_voices()
    
    def _create_simulated_voices(self) -> List[dict]:
        """Create list of simulated voice configurations."""
        voices = []
        for lang in Language:
            for gender in VoiceGender:
                voices.append({
                    "name": f"Simulated-{lang.value}-{gender.value}",
                    "language": lang,
                    "gender": gender,
                    "description": f"Simulated {gender.value} voice for {lang.value}",
                })
        return voices
    
    async def synthesize(
        self,
        request: SpeechRequest,
    ) -> SpeechResult:
        """Simulate speech synthesis."""
        # Estimate duration based on text length
        word_count = len(request.text.split())
        base_duration = (word_count / self._wpm) * 60  # Convert to seconds
        
        # Adjust for speaking rate
        duration = base_duration / request.speaking_rate
        
        # Simulate processing time (faster than real-time)
        processing_time = int(duration * 50)  # 50ms per second of audio
        
        return SpeechResult(
            request_id=request.request_id,
            audio_data=None,  # No actual audio in simulation
            audio_format=request.output_format,
            sample_rate=request.sample_rate,
            duration_seconds=round(duration, 2),
            original_text=request.text,
            processing_time_ms=processing_time,
            success=True,
        )
    
    def get_available_voices(
        self,
        language: Optional[Language] = None,
    ) -> List[dict]:
        """Get available simulated voices."""
        if language is None:
            return self._voices
        return [v for v in self._voices if v["language"] == language]
    
    def get_supported_formats(self) -> List[AudioFormat]:
        """Return all formats as supported in simulation."""
        return list(AudioFormat)


# -----------------------------------------------------------------------------
# Voice Service Facade
# -----------------------------------------------------------------------------

@dataclass
class VoiceService:
    """
    Unified facade for voice operations.
    
    Provides a simple interface for:
    - Converting speech to text (STT)
    - Converting text to speech (TTS)
    - Handling both audio and text input
    
    Designed to be initialized with any STT/TTS provider
    implementing the abstract interfaces.
    """
    
    stt_provider: STTProvider
    tts_provider: TTSProvider
    
    async def process_audio_input(
        self,
        audio_input: AudioInput,
    ) -> TranscriptionResult:
        """
        Process audio input and return transcription.
        
        Args:
            audio_input: Audio data to process.
            
        Returns:
            TranscriptionResult with transcribed text.
        """
        return await self.stt_provider.transcribe(audio_input)
    
    async def process_text_input(
        self,
        text: str,
        language: Language = Language.EN_US,
    ) -> TranscriptionResult:
        """
        Process text input (passthrough for unified interface).
        
        Args:
            text: Text input.
            language: Language of the text.
            
        Returns:
            TranscriptionResult with the text as transcription.
        """
        # For text input, just wrap in TranscriptionResult
        return TranscriptionResult(
            input_id=uuid4(),
            text=text,
            confidence=1.0,  # Perfect confidence for text
            alternatives=[],
            processing_time_ms=0,
            is_final=True,
            is_partial=False,
        )
    
    async def generate_audio_response(
        self,
        text: str,
        language: Language = Language.EN_US,
        voice_gender: VoiceGender = VoiceGender.NEUTRAL,
        output_format: AudioFormat = AudioFormat.WAV,
    ) -> SpeechResult:
        """
        Generate audio response from text.
        
        Args:
            text: Text to synthesize.
            language: Output language.
            voice_gender: Preferred voice gender.
            output_format: Desired audio format.
            
        Returns:
            SpeechResult with audio data.
        """
        request = SpeechRequest(
            text=text,
            language=language,
            voice_gender=voice_gender,
            output_format=output_format,
        )
        return await self.tts_provider.synthesize(request)
    
    async def transcribe_and_respond(
        self,
        audio_input: AudioInput,
        response_text: str,
        voice_gender: VoiceGender = VoiceGender.NEUTRAL,
    ) -> tuple[TranscriptionResult, SpeechResult]:
        """
        Full voice round-trip: transcribe input and generate response.
        
        Args:
            audio_input: Audio to transcribe.
            response_text: Text response to synthesize.
            voice_gender: Voice for response.
            
        Returns:
            Tuple of (TranscriptionResult, SpeechResult).
        """
        # Transcribe input
        transcription = await self.process_audio_input(audio_input)
        
        # Generate response audio
        speech = await self.generate_audio_response(
            text=response_text,
            language=audio_input.language,
            voice_gender=voice_gender,
        )
        
        return transcription, speech
    
    def get_supported_languages(self) -> List[Language]:
        """Get languages supported by both STT and TTS."""
        stt_langs = set(self.stt_provider.get_supported_languages())
        tts_langs = {v["language"] for v in self.tts_provider.get_available_voices()}
        return list(stt_langs & tts_langs)
    
    def get_available_voices(
        self,
        language: Optional[Language] = None,
    ) -> List[dict]:
        """Get available TTS voices."""
        return self.tts_provider.get_available_voices(language)


class SimulatedVoiceService(VoiceService):
    """
    Pre-configured VoiceService with simulated providers.
    
    Use for development and testing without real telephony.
    """
    
    def __init__(
        self,
        default_confidence: float = 0.95,
        words_per_minute: float = 150.0,
    ):
        """
        Initialize with simulated providers.
        
        Args:
            default_confidence: STT confidence level.
            words_per_minute: TTS speaking rate.
        """
        super().__init__(
            stt_provider=SimulatedSTTProvider(default_confidence),
            tts_provider=SimulatedTTSProvider(words_per_minute),
        )
