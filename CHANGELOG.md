# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Platinum Sprint: CI/CD workflow, standardized badge row, ADR documentation
- Initial CHANGELOG following Keep a Changelog format

## [1.0.1] - 2026-10-06

Housekeeping release. No code behaviour changes.

### Changed

- Repository cleaned: third-party and personal material removed from the
  repository and its history (a third-party manuscript and its derived
  analysis outputs, third-party PDFs, and chat-log dumps).
- Provenance notices added: per-corpus provenance in the README and a new
  `corpus/NOTICE.md` recording the licence terms of the bundled corpus texts.
- Packaging scoped to an explicit allow-list of project data, so the wheel
  and sdist ship only framework code, domain/schema files, notebook
  templates and the MET4MORFOSES sample project.
- The v1.0.0 release and tag were withdrawn and are superseded by this
  release.

## [0.1.0] - 2026-02-11

### Added

- Initial public release as part of the organvm eight-organ system
- Core project structure and documentation
- README with portfolio-quality documentation

[Unreleased]: https://github.com/organvm-i-theoria/linguistic-atomization-framework/compare/v0.1.0...HEAD
[1.0.1]: https://github.com/4444J99/linguistic-atomization-framework/releases/tag/v1.0.1
[0.1.0]: https://github.com/organvm-i-theoria/linguistic-atomization-framework/releases/tag/v0.1.0
