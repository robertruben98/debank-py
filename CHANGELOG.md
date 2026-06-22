# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0]

### Added

- Initial release.
- Synchronous `DeBankClient` and asynchronous `AsyncDeBankClient` for the DeBank
  Cloud Pro API, built on `httpx` and `pydantic` v2.
- Authentication via the configurable `AccessKey` header.
- User endpoints: total balance, chain balance, used chain list, token list /
  all-chain token list, single token, NFT list / all-chain NFT list, complex and
  simple protocol lists (per-chain and all-chain), single protocol, history list
  and all-chain history list, token authorized list, and total net curve.
- Chain endpoints: chain list and single chain.
- Token endpoints: single token, list-by-ids and historical price.
- Automatic retry with exponential backoff on HTTP 429 and 5xx responses,
  honoring `Retry-After`.
- Typed exception hierarchy (`DeBankError`, `DeBankAPIError`,
  `DeBankRateLimitError`).
- `py.typed` marker for full type-checking support.

[Unreleased]: https://github.com/robertruben98/debank-py/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/robertruben98/debank-py/releases/tag/v0.1.0
