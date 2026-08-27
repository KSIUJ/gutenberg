# Changelog
The changes below are formatted according to [keep a changelog].

See also [Creating new releases] for instructions on how to create a new release.

## [Unreleased]
### Added
- Added REST API endpoints for print previews [#178]
- Added configurable printer display order in the Django admin panel. [#181]
- Added configuration environment variables used when Gutenberg is deployed behind a reverse proxy:
  - `GUTENBERG_TRUST_X_FORWARDED_HOST`, `GUTENBERG_TRUST_X_FORWARDED_PROTO` and `GUTENBERG_TRUST_X_REAL_IP` [#175]
  - `GUTENBERG_TRUSTED_PROXY_IPS` [#190]
- Docker Images are now published in the GitHub Container Registry [#199]
- Added automatic CUPS printer capability configuration when selecting a printer in the Django admin panel [#200]
- Added 4 test print buttons to the Printer admin page. Buttons: one-sided grayscale, one-sided colored,two-sided grayscale, two-sided colored [#196]
- Added a web UI for print preview REST API added in [#178] , [#210]

### Changed
- Modified nginx Docker image config to correctly pass the `X-Forwarded-Host` header [#175]
- Changed the filenames and structure of nginx configuration files [#175], [#190]
- Changed print jobs to be created when the first file is uploaded, not only when clicking Print, so preview can be shown before printing [#210]
- Enhanced the IPP configuration page UI in the webapp [#206]

### Fixed
- Fixed canceled CUPS job being incorrectly marked as completed [#179]
  Fixed backend Docker container startup crashes (permission denied) by ensuring the `gutenberg-docker` home directory is explicitly created with proper ownership [#206]

### Tests
- Added new edge-case tests for page size ratio orientations, booklet odd-page imposition,
  disabled fit-to-page scaling, isolated temporary directories via `pytest` fixtures,
  and overlapping/unusual order input validators [#194]
- Migrated printing processing tests from `unittest` to `pytest`, parameterized test cases,
  and removed redundant `sys.modules` Django mocking [#194]

## [4.0.0] - 2026-07-13
### Added
- Created documentation and host it using mdbook [#97]
- Created official Docker and Docker Compose configuration [#91]
- Host documentation next to the webapp in Docker [#120]
- Added N-up and booklet options to the print settings [#115] [#122]
- Added Django cache configuration in the example setting files [#130]
- Added autocomplete for CUPS printer names in Django Admin [#127]

### Changed
- Migrated to the uv package manager [#80]
- Rewritten the web UI to use Nuxt4 and PrimeVue [#86]
- Modified REST API and error messages [#107] [#114]
- Changed OpenID Connect backend and settings format [#109]
    - The client needs to be configured again
    - The names of the groups synced from Keycloak roles have changed.

  Please see the [OpenID Connect chapter] in the Gutenberg docs for more information.
- Use LibreOffice's CLI directly instead of using `unoconv` [#130]
- Changed the layout of `/webapp/.output` in webapp builds [#170]
- Replaced calls to deprecated `convert` ImageMagick command with calls to `magick` [#172]

## Previous releases
This document only keeps track of changes made after 2025-07-24.
The previous significant commit was made on [2022-08-26](https://github.com/KSIUJ/gutenberg/commit/9bb5d09e1ca69756a5930d3be214f52598e40797)

[unreleased]: https://github.com/KSIUJ/gutenberg/compare/v4.0.0...HEAD
[4.0.0]: https://github.com/KSIUJ/gutenberg/releases/tag/v4.0.0

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
[#127]: https://github.com/KSIUJ/gutenberg/pull/127
[#130]: https://github.com/KSIUJ/gutenberg/pull/130
[#170]: https://github.com/KSIUJ/gutenberg/pull/170
[#172]: https://github.com/KSIUJ/gutenberg/pull/172
[#175]: https://github.com/KSIUJ/gutenberg/pull/175
[#179]: https://github.com/KSIUJ/gutenberg/pull/179
[#181]: https://github.com/KSIUJ/gutenberg/pull/181
[#178]: https://github.com/KSIUJ/gutenberg/pull/178
[#190]: https://github.com/KSIUJ/gutenberg/pull/190
[#194]: https://github.com/KSIUJ/gutenberg/pull/194
[#196]: https://github.com/KSIUJ/gutenberg/pull/196
[#199]: https://github.com/KSIUJ/gutenberg/pull/199
[#200]: https://github.com/KSIUJ/gutenberg/pull/200
[#206]: https://github.com/KSIUJ/gutenberg/pull/206
[#210]: https://github.com/KSIUJ/gutenberg/pull/210

[keep a changelog]: https://keepachangelog.com/en/1.1.0/
[OpenID Connect chapter]: https://ksiuj.github.io/gutenberg/admin/openid-connect.html
[Creating new releases]: https://ksiuj.github.io/gutenberg/internals/creating-new-releases.html
