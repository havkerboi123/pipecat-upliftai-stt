#
# Copyright (c) 2024-2026, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Uplift AI speech-to-text service implementation.

This module provides integration with Uplift AI's Scribe API for speech-to-text
transcription, optimized for Urdu language with domain-specific optimization support.
"""

import os
from typing import AsyncGenerator, Optional

from loguru import logger
from pydantic import BaseModel

from pipecat.frames.frames import ErrorFrame, Frame, TranscriptionFrame
from pipecat.services.stt_service import SegmentedSTTService
from pipecat.transcriptions.language import Language, resolve_language
from pipecat.utils.time import time_now_iso8601
from pipecat.utils.tracing.service_decorators import traced_stt

try:
    import httpx
except ModuleNotFoundError as e:
    logger.error(f"Exception: {e}")
    logger.error(
        "In order to use Uplift AI, you need to `pip install httpx`. Also, set `UPLIFT_API_KEY` environment variable."
    )
    raise Exception(f"Missing module: {e}")


class UpliftAISTTService(SegmentedSTTService):
    """Speech-to-text service using Uplift AI's Scribe API.

    This service uses Uplift AI's Scribe API to perform speech-to-text transcription
    optimized for Urdu language with optional domain-specific optimization.

    Note:
        The API is currently in beta. Features and pricing may change. ( According to UpliftAI docs )

    Pricing:
        - scribe: 40 credits per minute (full accuracy)
        - scribe-mini: 20 credits per minute (cost-effective, 50% cheaper)
    """

    class InputParams(BaseModel):
        """Configuration parameters for Uplift AI's Scribe API.

        Attributes:
            model: AI model to use. Options: 'scribe' (full accuracy, 40 credits/min)
                   or 'scribe-mini' (cost-effective, 20 credits/min). Defaults to 'scribe'.
            language:Currently only Urdu is supported so defaults to language UR.
            domain: Optional domain-specific optimization. Options: 'phone-commerce'
                    (e-commerce conversations) or 'farming' (agricultural terminology).
                    Defaults to None.
        """

        model: str = "scribe"
        language: str = "ur"
        domain: Optional[str] = None

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: str = "https://api.upliftai.org/v1",
        sample_rate: Optional[int] = None,
        model: str = "scribe",
        domain: Optional[str] = None,
        params: Optional[InputParams] = None,
        **kwargs,
    ):
        """Initialize the UpliftSTTService with API key and parameters.

        Args:
            api_key: Uplift AI API key. 
            base_url: Base URL for Uplift AI API. Defaults to 'https://api.upliftai.org/v1'.
            sample_rate: Audio sample rate in Hz. If not provided, uses the pipeline's rate.
            model: AI model to use. Options: 'scribe' or 'scribe-mini'. Defaults to 'scribe'.
            domain: Optional domain-specific optimization. Options: 'phone-commerce' or 'farming'.
            params: Configuration parameters (alternative to using direct parameters).
            **kwargs: Additional arguments passed to SegmentedSTTService.

        Raises:
            ValueError: If api_key is not provided and UPLIFT_API_KEY environment
                        variable is not set.
        """
        super().__init__(
            sample_rate=sample_rate,
            **kwargs,
        )

        # If params provided, use those; otherwise use direct parameters
        if params:
            model = params.model
            domain = params.domain

        
        if model not in ["scribe", "scribe-mini"]:
            raise ValueError(f"Invalid model: {model}. Must be 'scribe' or 'scribe-mini'")

        # Validating domain if provided
        if domain and domain not in ["phone-commerce", "farming"]:
            raise ValueError(
                f"Invalid domain: {domain}. Must be 'phone-commerce' or 'farming'"
            )

        #api key
        self._api_key = api_key or os.getenv("UPLIFT_API_KEY")
        if not self._api_key:
            raise ValueError(
                "UPLIFT_API_KEY must be provided either through api_key parameter or environment variable"
            )

        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            timeout=30.0,
            headers={"Authorization": f"Bearer {self._api_key}"},
        )

        self._settings = {
            "model": model,
            "language": "ur"
        }

        # Adding domain to settings if provided
        if domain:
            self._settings["domain"] = domain

        # Storing model name for metrics
        self.set_model_name(model)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - close HTTP client."""
        await self._client.aclose()

    async def close(self):
        """Close the HTTP client connection."""
        await self._client.aclose()

    def can_generate_metrics(self) -> bool:
        """Check if the service can generate processing metrics.

        Returns:
            True, as Uplift AI STT service supports metrics generation.
        """
        return True

    

    async def set_model(self, model: str):
        """Set the STT model.

        Args:
            model: The model name to use for transcription.
                   Must be 'scribe' or 'scribe-mini'.

        Raises:
            ValueError: If the model is not valid.
        """
        if model not in ["scribe", "scribe-mini"]:
            raise ValueError(f"Invalid model: {model}. Must be 'scribe' or 'scribe-mini'")

        await super().set_model(model)
        self._settings["model"] = model
        logger.info(f"Switching STT model to: [{model}]")

    async def set_domain(self, domain: Optional[str]):
        """Set the domain-specific optimization.

        Args:
            domain: Domain optimization to use. Options: 'phone-commerce' or 'farming'.
                    Set to None to disable domain optimization.

        Raises:
            ValueError: If the domain is not valid.
        """
        if domain and domain not in ["phone-commerce", "farming"]:
            raise ValueError(f"Invalid domain: {domain}. Must be 'phone-commerce' or 'farming'")

        if domain:
            self._settings["domain"] = domain
            logger.info(f"Setting STT domain optimization to: [{domain}]")
        else:
            self._settings.pop("domain", None)
            logger.info("Disabled STT domain optimization")

    @traced_stt
    async def _handle_transcription(
        self, transcript: str, is_final: bool, language: Optional[str] = None
    ):
        """Handle a transcription result with tracing.

        Args:
            transcript: The transcribed text.
            is_final: Whether this is a final transcription.
            language: The language of the transcription.
        """
        await self.stop_processing_metrics()

    async def run_stt(self, audio: bytes) -> AsyncGenerator[Frame, None]:
        """Transcribes an audio segment using Uplift AI's Scribe API.

        Args:
            audio: Raw audio bytes in WAV format (already converted by base class).

        Yields:
            Frame: TranscriptionFrame containing the transcribed text, or ErrorFrame on failure.

        Note:
            The audio is already in WAV format from the SegmentedSTTService.
            Only non-empty transcriptions are yielded.
            Maximum file size is 25MB.
        """
        try:
            await self.start_processing_metrics()

            #max size check
            max_size = 25 * 1024 * 1024  
            if len(audio) > max_size:
                error_msg = f"Audio file too large: {len(audio)} bytes (max: {max_size} bytes)"
                logger.error(error_msg)
                yield ErrorFrame(error=error_msg)
                return

            # multipart form data
            files = {"file": ("audio.wav", audio, "audio/wav")}
            data = {
                "model": self._settings["model"],
                "language": self._settings["language"],
            }

            #domain if present
            if "domain" in self._settings:
                data["domain"] = self._settings["domain"]

            #API request
            url = f"{self._base_url}/transcribe/speech-to-text"
            response = await self._client.post(url, files=files, data=data)

            #response handling
            response.raise_for_status()
            result = response.json()

            if result and "transcript" in result:
                text = result["transcript"].strip()
                if text:  
                    await self._handle_transcription(
                        text, True, self._settings["language"]
                    )
                    logger.debug(f"Transcription: [{text}]")
                    yield TranscriptionFrame(
                        text,
                        self._user_id,
                        time_now_iso8601(),
                        Language(self._settings["language"]),
                        result=result,
                    )
                else:
                    logger.warning("Received empty transcription from Uplift AI API")
            else:
                logger.warning(f"Unexpected response format from Uplift AI: {result}")

        except httpx.HTTPStatusError as e:
            error_msg = f"Uplift AI API error: {e.response.status_code} - {e.response.text}"
            logger.error(error_msg)
            yield ErrorFrame(error=error_msg)
        except httpx.RequestError as e:
            error_msg = f"Request error: {str(e)}"
            logger.error(error_msg)
            yield ErrorFrame(error=error_msg)
        except Exception as e:
            error_msg = f"Unknown error occurred: {e}"
            logger.error(error_msg)
            yield ErrorFrame(error=error_msg)