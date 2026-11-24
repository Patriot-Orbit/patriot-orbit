# Patriot Orbit

Automated open-source space domain awareness tool that pulls public TLE data and generates daily commentary on Chinese, Russian, North Korean, and Iranian satellite activity.

## What It Does

- Pulls live orbital data from Space-Track for major constellations
- Combines everything into one master file: `MASTER_ALL_SPACE_OBJECTS.csv`
- Generates a readable summary in `AUTO_NOTES.txt` focused on:
  - Chinese satellites (Yaogan, Beidou, Gaofen, etc.)
  - Russian satellites
  - North Korean objects
  - Iranian satellites
- Runs automatically every 15-20 minutes via GitHub Actions

## Files

- `pull_and_analyze.py` — main script that pulls data and writes notes
- `MASTER_ALL_SPACE_OBJECTS.csv` — full combined dataset
- `AUTO_NOTES.txt` — latest commentary
- `.github/workflows/` — automation

## How to Run Locally

```bash
pip install -r requirements.txt
python3 pull_and_analyze.py
