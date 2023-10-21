# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.0] - 2023-10-21

**Fixed**

- Issue where non-API-required options prompt user for requisites/credentials.

**Changed**

- Env-vars now prefixed with `CLO_` instead of `OD_`.
- Auth env-vars no longer abbreviated.
- `--env` now defaults to `.clorc`, instead of `~/.clorc`.
- `--demo` now accepts the save path, as opposed to using `--out`.
- `--demo` now defaults to `.clorc`.

## [0.5.0] - 2023-10-16

**Added**

- Initial feature set.
- Added tests
