# Changelog

All notable changes to this project are listed here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-20

### Added

- Upcoming close passes tab: asteroids and comets passing near Earth, with a chart and a table.
- Past close passes tab: the same for past dates, up to a year at a time.
- Impact risk tab: every object on NASA's Sentry list, highest risk first.
- Fireballs tab: space rocks that burned up in the sky, on a world map.
- Distances in Moon distances, km, and miles.
- Sizes from measured diameters, or a size range from brightness.
- A rough "If it hit" guide by size.
- Filters for distance, number of days, and potentially hazardous asteroids only, plus sorting by closest or biggest.
- Clicking a dot on the chart shows that object's details below it.
- NASA/JPL calls with retries and backoff, request-ID logging, an API version check, and hour-long caching.
- Tests with 100% coverage, a browser test that clicks the chart, and a daily live check of the NASA/JPL APIs on GitHub.

[1.0.0]: https://github.com/datalogicpro/asteroid-watch/releases/tag/v1.0.0
