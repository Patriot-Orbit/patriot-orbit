# Patriot Orbit

Open-source space intelligence project focused on tracking and analyzing satellite constellations using public TLE data from Space-Track.

## Current Features
- Pulls live orbital data for Chinese, Russian and other constellations (Yaogan, Qianfan, Beidou, Fengyun, Glonass, etc.)
- Exports clean CSV files for analysis
- Manual pattern tracking (debris, triplets, fresh epochs)

## How to Run
1. Install dependencies: `pip install spacetrack pandas`
2. Edit `pull_satellites.py` with your Space-Track credentials
3. Change the constellation name and run: `python3 pull_satellites.py`

## Goal
Build a simple open-source tool for space domain awareness, with future plans for AI-powered analysis and visualization.
