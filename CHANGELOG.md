# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-04-06

### Security
- Add `validate_id()` input validation for all numeric ID parameters across all tool modules — rejects zero and negative values before they reach the API
- Add file upload validation in `create_attachment` — validates base64 encoding, enforces 10MB size limit, rejects path traversal in filenames
- Truncate API error response bodies in `APIError.__str__` to 200 characters to prevent leaking internal server details (full body remains on attribute for internal use)
- Acquire lock in `CircuitBreaker.failures` property to fix race condition with concurrent reads
- Clamp and round rate limiter token count after refill to prevent accumulated floating-point precision drift
- Make `UserContext.user_id` immutable after first set — rejects re-assignment and non-positive values
- Add ID validation and type coercion to `bulk_update_transactions` — safely handles string, zero, and negative transaction IDs

## [1.0.1] - 2024-01-15

### Added
- Documentation assets (screenshots for API key setup guide)
- PyPI package metadata and badge

### Changed
- Updated badge styling in README

## [1.0.0] - 2024-01-01

### Added
- Initial release with 43 MCP tools for PocketSmith API v2
- Async HTTP client with rate limiting (token bucket algorithm, 60 req/min)
- Retry with exponential backoff and jitter for transient errors
- Circuit breaker for fault tolerance
- Tool modules: accounts, transactions, categories, budgeting, events, institutions, attachments, labels, transaction accounts, users, utilities
- Pydantic models for API entities
- Comprehensive test suite with pytest-asyncio and respx
- Environment-based configuration with python-dotenv

[1.1.0]: https://github.com/ajanderson1/mcp_pocketsmith/compare/v1.0.1...v1.1.0
[1.0.1]: https://github.com/ajanderson1/mcp_pocketsmith/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/ajanderson1/mcp_pocketsmith/releases/tag/v1.0.0
