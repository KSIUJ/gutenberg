# Changelog
The changes below are formatted according to [keep a changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]
- ...

## [4.0.0-rc0] - 2025-10-10 [Release candidate]
### Added
- Create documentation and host it using mdbook [#97]
- Created official Docker and Docker Compose configuration [#91]
- Host documentation next to the webapp in Docker [#120]
- Add N-up and booklet options to the print settings [#115] [#122]

### Changed
- Migrate to the uv package manager [#80]
- Rewritten the web UI to use Nuxt4 and PrimeVue [#86]
- Modified REST API and error messages [#107] [#114]
- Changed OpenID Connect backend and settings format [#109]
    - The client needs to be configured again
    - The names of the groups synced from Keycloak roles have changed.
  
  Please see the [OpenID Connect chapter] in the Gutenberg docs for more information.

## Previous releases
This document only keeps track of changes made since 2025-07-24.
The previous non-dependency commit was made on [2022-08-26](https://github.com/KSIUJ/gutenberg/commit/9bb5d09e1ca69756a5930d3be214f52598e40797)

[unreleased]: https://github.com/KSIUJ/gutenberg/compare/v4.0.0-rc0...HEAD
[4.0.0-rc0]: https://github.com/KSIUJ/gutenberg/releases/tag/v4.0.0-rc0

[#80]: https://github.com/KSIUJ/gutenberg/pull/80
[#86]: https://github.com/KSIUJ/gutenberg/pull/86
[#91]: https://github.com/KSIUJ/gutenberg/pull/91
[#97]: https://github.com/KSIUJ/gutenberg/pull/97
[#107]: https://github.com/KSIUJ/gutenberg/pull/107
[#109]: https://github.com/KSIUJ/gutenberg/pull/109
[#114]: https://github.com/KSIUJ/gutenberg/pull/114
[#115]: https://github.com/KSIUJ/gutenberg/pull/115
[#120]: https://github.com/KSIUJ/gutenberg/pull/120
[#122]: https://github.com/KSIUJ/gutenberg/pull/122

[OpenID Connect chapter]: https://ksiuj.github.io/gutenberg/admin/openid-connect.html
