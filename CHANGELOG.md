# Changelog
All notable changes to the Uplift STT integration for Pipecat.

## [1.0.0] - 2026-02-24
### Added
- Initial release of Uplift STT integration for Pipecat
- Support for Urdu language transcription via Uplift AI's Scribe API
- Two model options: `scribe` (40 credits/min) and `scribe-mini` (20 credits/min)
- Domain-specific optimization support: `phone-commerce` and `farming`
- Comprehensive error handling including file size validation (25MB limit) and HTTP error handling
- Processing metrics support
- Full Pipecat pipeline integration via `SegmentedSTTService`
- Async HTTP client with Bearer token authentication

## [Unreleased]
### Planned
- Additional language support beyond Urdu