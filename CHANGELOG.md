# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

### Added
- QR authorization (Link Desktop Device) as a fallback when SMS/app codes don’t arrive.
- QR authorization support for accounts with 2FA (cloud password).
- `qrcode` dependency for QR rendering.

### Fixed
- Channel cloning now preserves message formatting entities (incl. custom/premium emoji where possible).
- Clone scripts now detect and report “no access / 0 messages” instead of reporting success with no copied content.

### Changed
- Improved `.gitignore` to prevent committing Telegram session files and OS junk.
