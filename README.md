# Asteroid Watch

[![Tests](https://github.com/datalogicpro/asteroid-watch/actions/workflows/tests.yml/badge.svg)](https://github.com/datalogicpro/asteroid-watch/actions/workflows/tests.yml)
[![NASA check](https://github.com/datalogicpro/asteroid-watch/actions/workflows/live.yml/badge.svg)](https://github.com/datalogicpro/asteroid-watch/actions/workflows/live.yml)

A live dashboard of asteroids and comets passing near Earth, the objects with a chance of hitting it, and the space rocks that burned up in the sky, using NASA/JPL data.

**Live demo:** https://datalogicpro-asteroid-watch.streamlit.app

## What it shows

The page has four tabs:

| Tab | What's in it |
|---|---|
| Upcoming close passes | Asteroids and comets passing near Earth in the coming days, on a chart and in a table |
| Past close passes | The same for any dates in the past, up to a year at a time |
| Impact risk | Every object on NASA's Sentry list with a chance of hitting Earth, highest risk first |
| Fireballs | Space rocks that burned up in the sky, on a world map |

On the close-pass tabs you can:

- choose how many days to look at, and how close the passes must be
- show only potentially hazardous asteroids (about 140 m or larger, with orbits that come close to Earth's)
- sort by closest or biggest
- click a dot on the chart to see that object's details in large text below it

## Reading the numbers

- **Moon distances.** Distances are shown in Moon distances, along with km and miles. 1 Moon distance is how far the Moon is from Earth: 384,399 km, or 238,855 miles. A pass at 0.5 Moon distances comes halfway to the Moon.
- **Size.** Most of these objects have never been measured. Their size is worked out from how bright they are, and since a dark surface reflects less light than a shiny one, the size is a range, like 2.9–6.4 m. When NASA has a measured size, that is shown instead.
- **If it hit.** A rough guide from size alone. Real effects also depend on speed, angle, and what the object is made of.

  | Size | If it hit |
  |---|---|
  | Under 10 m | Burns up high in the air |
  | 10–40 m | Air blast, like Chelyabinsk in 2013 |
  | 40–140 m | Could flatten a forest or city, like Tunguska in 1908 |
  | 140 m–1 km | Regional damage |
  | 1 km and up | Global effects |

- **Impact risk scales.** On the Palermo scale, below -2 is no concern and -2 to 0 is worth watching. On the Torino scale, 0 is no hazard and 10 is a certain collision with global effects; it only covers the next 100 years.

## Seeing one in a telescope

Most of these objects can't be seen with your eyes, binoculars, or a backyard telescope. They are small and very faint. For example, (2025 UK9), which passes inside the Moon's orbit on October 31, 2026, is only about 3 to 6 m across. At its brightest it is about magnitude 19; the faintest stars you can see with your eyes are about magnitude 6, and a bigger number means fainter.

They also move fast across the sky. Near its closest pass, (2025 UK9) crosses about 2.5° of sky an hour, about 5 times the width of the full Moon. Large observatories follow an object like this by moving the telescope along its predicted path, so the asteroid stays still in the picture while the stars turn into streaks.

To find where an object will be in the sky from any spot on Earth, use NASA/JPL's free Horizons system:

```
https://ssd.jpl.nasa.gov/horizons/app.html
```

1. **Target Body:** click **Edit** and type the object's name, like `2025 UK9`.
2. **Observer Location:** click **Edit** and pick an observatory or enter a location.
3. **Time Specification:** click **Edit** and set the start, the stop, and how often to show a position, like every 5 minutes.
4. **Table Settings:** click **Edit** to choose what the table shows. Useful choices:
   - **Apparent AZ & EL:** the compass direction and the height above the horizon, from that spot
   - **Rates; RA & DEC:** how fast the object moves across the sky
   - **Visual mag. & Surface Brght:** how bright it is
   - **Skip daylight:** leaves out times when the Sun is up
   - **Elevation cutoff:** leaves out times when the object is too low, for example below 20 degrees
   - **RTS flag:** shows only when the object rises, is highest in the sky, and sets
5. Click **Generate Ephemeris**.

The Minor Planet Center has a similar free tool that observatories also use:

```
https://minorplanetcenter.net/iau/MPEph/MPEph.html
```

For a newly found object, the predicted path can be off, so observers may need to search a wider area of sky.

## Times

- The dates on the close-pass tabs are in **TDB**, the time scale astronomers use for orbits. It runs about 1 minute ahead of UTC.
- Horizons tables are in **UTC**, also called world time.
- To change UTC to your local time, add or subtract your offset from UTC. Daylight saving time changes the offset by 1 hour.

  | Place | Offset from UTC | 18:00 UTC is |
  |---|---|---|
  | Los Angeles (summer) | −7 hours | 11:00 AM |
  | Los Angeles (winter) | −8 hours | 10:00 AM |
  | New York (summer) | −4 hours | 2:00 PM |
  | Honolulu (all year) | −10 hours | 8:00 AM |

- The date can change too. For example, October 31 at 03:00 UTC is still October 30 at 8:00 PM in Los Angeles.

## How to run

This project uses [uv](https://docs.astral.sh/uv/) and Python 3.13.

1. Install everything:

```
   uv sync
```

2. Start the dashboard:

```
   uv run streamlit run app.py
```

3. Open it in your browser:

```
   http://localhost:8501
```

No API key is needed.

## Tests

Run the tests:

```
uv run python -m pytest
```

- **Unit and page tests** check every part of the code with saved NASA/JPL replies, so they never call NASA. Coverage must stay at 100%.
- **A browser test** starts the real page in Chrome, clicks a dot on the chart, and checks that the details box shows the right object. It uses a small stand-in server that sends the saved replies. It needs Google Chrome installed.
- **A live NASA check** calls the real NASA/JPL APIs and reads each reply the same way the page does, so a changed field or a new API version is caught. It is left out of the normal run. GitHub runs it once a day, and you can run it by hand:

```
  uv run python -m pytest -m live --no-cov
```

## How it's built

- **Retries with backoff:** busy-server replies from NASA/JPL are retried after 1, 2, then 4 seconds.
- **Logging with request IDs:** every NASA/JPL call is logged with its own ID, so a failure can be traced.
- **API version check:** each reply's version is checked against the version the code was written for.
- **Caching:** each NASA/JPL reply is saved for an hour, so the page doesn't call NASA on every click.
- **Clear errors:** if NASA/JPL doesn't answer, that tab shows a message and the other tabs keep working.
- **Checks on every change:** GitHub Actions runs Ruff, mypy, pip-audit, and the tests on every pull request.
- **Up-to-date dependencies:** Dependabot opens pull requests for new library and GitHub Actions versions.
- **Pre-commit hooks:** formatting, linting, and type checks run before every commit.

## Project files

| File | What's in it |
|---|---|
| `app.py` | The page: tabs, sliders and other choices, and the calls to NASA/JPL |
| `charts.py` | The close-pass chart and the fireball map |
| `tables.py` | The table rows, sorting, and the details-box text |
| `space.py` | Turns NASA/JPL's replies into records with everyday units |
| `jpl.py` | Calls the NASA/JPL APIs, with retries and logging |
| `tests/` | The tests and the saved NASA/JPL replies they use |
| `.github/workflows/tests.yml` | Runs the checks and tests on GitHub |
| `.github/workflows/live.yml` | Runs the live NASA check once a day |

## Built with

Python, Streamlit, Plotly, requests, pytest, Playwright, Ruff, mypy, and uv.

## Data

Data: NASA/JPL Center for Near Earth Object Studies (CNEOS), through JPL's Solar System Dynamics APIs:

- [Close-Approach Data API](https://ssd-api.jpl.nasa.gov/doc/cad.html)
- [Sentry API](https://ssd-api.jpl.nasa.gov/doc/sentry.html)
- [Fireball API](https://ssd-api.jpl.nasa.gov/doc/fireball.html)

## License

MIT. See [LICENSE](LICENSE).

## Author

Bobby (datalogicpro)
