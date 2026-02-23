# UpliftAI STT Integration for Pipecat

This repository provides an integration of [Uplift AI's](https://upliftai.org) Speech-to-Text (STT) service with the [Pipecat](https://github.com/pipecat-ai/pipecat) framework.

## About

Uplift AI provides high-quality speech-to-text transcription optimized for Urdu language with domain-specific optimization support. This integration enables seamless use of Uplift's STT capabilities within Pipecat pipelines.

**Integration Type:** This is a **SegmentedSTTService** integration (HTTP-based service), using the Uplift API endpoint: `https://api.upliftai.org/v1/transcribe/speech-to-text`

**Company Attribution:** This integration was developed by havkerboi123 as a personal contribution to enable Uplift STT within the Pipecat framework.

## Features

- ✅ Urdu language transcription via Uplift AI's Scribe API
- ✅ Two model options: `scribe` and `scribe-mini`
- ✅ Domain-specific optimization (`phone-commerce`, `farming`)
- ✅ Async/await support
- ✅ Comprehensive error handling (including 25MB file size limit)
- ✅ Metrics and usage tracking
- ✅ Dynamic model and domain switching
- ✅ Session management with httpx

## Installation

### Install from GitHub
```bash
# With pip
pip install git+https://github.com/havkerboi123/pipecat-upliftai-stt.git

# With uv (recommended - faster)
uv pip install git+https://github.com/havkerboi123/pipecat-upliftai-stt.git
```

> **Note:** PyPI package will be published after community review and approval.

### Development Installation
```bash
# Clone the repository
git clone https://github.com/havkerboi123/pipecat-upliftai-stt.git
cd pipecat-upliftai-stt

# Install in editable mode
uv pip install -e .
# or with pip
pip install -e .
```

## Prerequisites

- Python 3.8 or higher
- UpliftAI API key ([Get yours here](https://platform.upliftai.org/studio/api-keys))

## Getting Your API Key

1. Sign up at [Uplift AI](https://upliftai.org)
2. Go to [API Keys](https://platform.upliftai.org/studio/api-keys)
3. Generate an API key (format: `sk_api_...`)

## Usage

### Usage with Pipecat Pipeline

`UpliftAISTTService` integrates Uplift's speech-to-text into a Pipecat pipeline, converting user audio into text for downstream processing.
```python
import os
from pipecat.pipeline.pipeline import Pipeline
from pipecat_upliftai import UpliftAISTTService

stt = UpliftAISTTService(
    api_key=os.getenv("UPLIFT_API_KEY"),
    model="scribe",
    domain="phone-commerce",  # optional
)

pipeline = Pipeline([
    transport.input(),               # audio/user input
    stt,                             # Uplift STT transcription
    context_aggregator.user(),       # add user text to context
    llm,                             # LLM generates response
    tts,                             # text to speech synthesis
    transport.output(),              # stream audio back to user
    context_aggregator.assistant(),  # store assistant response
])
```

See [`example.py`](example.py) for a complete working example.

### Available Models

| Model | Credits | Description |
|-------|---------|-------------|
| `scribe` | 40 credits/min | Full accuracy |
| `scribe-mini` | 20 credits/min | Cost-effective, 50% cheaper |

### Available Domains (Optional)

| Domain | Description |
|--------|-------------|
| `phone-commerce` | Optimized for e-commerce conversations |
| `farming` | Optimized for agricultural terminology |

### Dynamic Model & Domain Switching
```python
# Change model during runtime
await stt.set_model("scribe-mini")

# Change domain optimization
await stt.set_domain("farming")

# Disable domain optimization
await stt.set_domain(None)
```

## Running the Example

1. Install dependencies:
```bash
   uv sync
   # or
   pip install -r requirements.txt
```

2. Set up your environment:
```bash
   cp .env.example .env
   # Edit .env and add your API keys
```

3. Run the example:
```bash
   python example.py
   # or with uv
   uv run python example.py
```

## Configuration Options

### Constructor Parameters
```python
UpliftAISTTService(
    api_key: str,          # Required: Your Uplift API key
    base_url: str,         # Optional: API endpoint (default: "https://api.upliftai.org/v1")
    model: str,            # Optional: Model to use (default: "scribe")
    domain: str,           # Optional: Domain optimization (default: None)
    sample_rate: int,      # Optional: Audio sample rate in Hz
    params: InputParams,   # Optional: Alternative parameter configuration
)
```

### Input Parameters

Use the `InputParams` class for advanced configuration:
```python
params = UpliftAISTTService.InputParams(
    model="scribe-mini",
    domain="phone-commerce",
)

stt = UpliftAISTTService(
    api_key=api_key,
    params=params,
)
```

## Error Handling

The service includes comprehensive error handling:
```python
from pipecat.frames.frames import ErrorFrame

async for frame in stt.run_stt(audio_bytes):
    if isinstance(frame, ErrorFrame):
        print(f"STT Error: {frame.error}")
    else:
        # Process transcription frame
        pass
```

## Limitations

- Maximum audio file size: 25MB per request
- Currently only Urdu (`ur`) language is supported
- Rate limits apply based on your Uplift API plan

## Compatibility

- **Pipecat Version:** Tested with Pipecat v0.0.86 and later
- **Python Version:** 3.8+
- **Dependencies:**
  - `pipecat-ai >= 0.0.86`
  - `httpx >= 0.24.0`
  - `loguru >= 0.7.0`

## Support

- **Issues:** [GitHub Issues](https://github.com/havkerboi123/pipecat-uplift-stt/issues)
- **Uplift AI Documentation:** [https://upliftai.org/docs](https://upliftai.org/docs)
- **Pipecat Documentation:** [https://docs.pipecat.ai](https://docs.pipecat.ai)

## License

This project is licensed under the BSD 2-Clause License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.

## Acknowledgments

- Thanks to the [Pipecat](https://github.com/pipecat-ai/pipecat) team for the excellent framework
- Thanks to [Uplift AI](https://upliftai.org) for providing high-quality STT services