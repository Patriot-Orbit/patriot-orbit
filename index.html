#!/usr/bin/env python3
"""
Patriot Orbit — Full Automated Space Domain Awareness Updater
Pulls public GP/TLE data for adversary constellations (PRC, CIS, NKOR, IRAN),
detects significant orbital changes, generates detailed AUTO_NOTES.txt,
and maintains MASTER_ALL_SPACE_OBJECTS.csv + previous_snapshot.csv.

Primary source: Space-Track.org (with credentials)
Fallback: CelesTrak public GP endpoints

Designed to run on a schedule via GitHub Actions.
"""

import os
import sys
import time
import json
import requests
import pandas as pd
from datetime import datetime
from spacetrack import SpaceTrackClient

# =============================================================================
# CONFIGURATION
# =============================================================================
IDENTITY = os.getenv('SPACETRACK_USER', 'bradenrbailey02@gmail.com')
PASSWORD = os.getenv('SPACETRACK_PASS', 'Uscuscusc9777!!!')

CELESTRAK_HEADERS = {
    'User-Agent': 'PatriotOrbit/1.0 (public TLE/GP fallback; +https://patriotorbit.com)'
}

CONSTELLATIONS = [
    '~~YAOGAN~~', '~~BEIDOU~~', '~~GAOFEN~~', '~~QIANFAN~~',
    '~~FENGYUN~~', '~~HAIYANG~~', '~~JILIN~~', '~~TIANHUI~~',
    '~~GLONASS~~', '~~COSMOS~~', '~~KANOPUS~~', '~~RESURS~~',
    '~~KWANGMYONGSONG~~', '~~MALLIGYONG~~',
    '~~NOOR~~', '~~KHAYYAM~~', '~~SAFIR~~'
]

WATCHLIST_NORADS = [
    # Add specific NORAD IDs here if desired
    # '25544',
    # '63230',
]

COUNTRY_MAP = {
    'YAOGAN': 'PRC', 'BEIDOU': 'PRC', 'GAOFEN': 'PRC', 'QIANFAN': 'PRC',
    'FENGYUN': 'PRC', 'HAIYANG': 'PRC', 'JILIN': 'PRC', 'TIANHUI': 'PRC',
    'GLONASS': 'CIS', 'COSMOS': 'CIS', 'KANOPUS': 'CIS', 'RESURS': 'CIS',
    'KWANGMYONGSONG': 'NKOR', 'MALLIGYONG': 'NKOR',
    'NOOR': 'IRAN', 'KHAYYAM': 'IRAN', 'SAFIR': 'IRAN'
}

ALLOWED_COUNTRIES = {'PRC', 'CIS', 'NKOR', 'IRAN'}

PREV_SNAPSHOT = 'previous_snapshot.csv'
MASTER_CSV = 'MASTER_ALL_SPACE_OBJECTS.csv'
NOTES_FILE = 'AUTO_NOTES.txt'
WATCHLIST_JSON = 'watchlist_tles.json'
HTML_SNIPPET = 'major_movements_snippet.html'

INCLINATION_THRESHOLD = 0.05
MEAN_MOTION_THRESHOLD = 0.001

# =============================================================================
# UTILITIES
# =============================================================================
def rate_limit_sleep(seconds=3.0):
    """Respect rate limits on both Space-Track and CelesTrak."""
    time.sleep(seconds)

def safe_numeric(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """Convert listed columns to numeric where they exist."""
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def log(msg: str):
    """Simple timestamped log line."""
    ts = datetime.utcnow().strftime('%H:%M:%S')
    print(f"[{ts}] {msg}")

# =============================================================================
# DATA FETCHERS
# =============================================================================
def fetch_celestrak_json(name: str) -> list:
    """Fetch GP JSON from CelesTrak for a constellation name (without ~~)."""
    clean = name.replace('~~', '')
    url = 'https://celestrak.org/NORAD/elements/gp.php'
    params = {'NAME': clean, 'FORMAT': 'json'}
    try:
        r = requests.get(url, params=params, headers=CELESTRAK_HEADERS, timeout=60)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list):
            return data
        return []
    except Exception as e:
        log(f"CelesTrak JSON failed for {clean}: {e}")
        return []

def fetch_celestrak_tle_by_norad(norad: str) -> tuple:
    """Return (name, line1, line2) or (None, None, None)."""
    url = 'https://celestrak.org/NORAD/elements/gp.php'
    try:
        r = requests.get(url, params={'CATNR': norad, 'FORMAT': 'tle'},
                         headers=CELESTRAK_HEADERS, timeout=30)
        r.raise_for_status()
        lines = [ln.strip() for ln in r.text.splitlines() if ln.strip()]
        if len(lines) >= 3 and lines[1].startswith('1 ') and lines[2].startswith('2 '):
            return lines[0], lines[1], lines[2]
    except Exception as e:
        log(f"CelesTrak TLE failed for NORAD {norad}: {e}")
    return None, None, None

# =============================================================================
# LOAD PREVIOUS SNAPSHOT
# =============================================================================
def load_previous_snapshot() -> pd.DataFrame | None:
    if not os.path.exists(PREV_SNAPSHOT):
        log("No previous snapshot found.")
        return None
    try:
        df = pd.read_csv(PREV_SNAPSHOT)
        if 'NORAD_CAT_ID' in df.columns:
            df['NORAD_CAT_ID'] = df['NORAD_CAT_ID'].astype(str)
        df = safe_numeric(df, ['INCLINATION', 'MEAN_MOTION', 'SEMIMAJOR_AXIS'])
        log(f"Loaded previous snapshot: {len(df)} objects")
        return df
    except Exception as e:
        log(f"Failed to load previous snapshot: {e}")
        return None

previous = load_previous_snapshot()

# =============================================================================
# MAIN DATA PULL
# =============================================================================
all_dfs = []
watchlist_data = []
pull_stats = []

log("Starting hourly-compliant pull...")

# Initialize Space-Track client (or fall back)
st = None
try:
    st = SpaceTrackClient(IDENTITY, PASSWORD)
    # Quick health check
    _ = st.gp(norad_cat_id='25544', format='json')
    log("Space-Track connection successful")
except Exception as e:
    log(f"Space-Track unavailable ({e}). Falling back to CelesTrak for this run.")
    st = None

for raw_name in CONSTELLATIONS:
    clean_name = raw_name.replace('~~', '')
    df = None
    source = None
    start = time.time()

    # Prefer Space-Track
    if st is not None:
        try:
            data = st.gp(
                object_name=raw_name,
                format='json',
                epoch='%3Enow-10',
                decay_date='null-val'
            )
            sats = json.loads(data)
            if sats:
                df = pd.DataFrame(sats)
                source = 'Space-Track'
        except Exception as e:
            log(f"Space-Track error on {clean_name}: {e}")

    # CelesTrak fallback
    if df is None or df.empty:
        sats = fetch_celestrak_json(raw_name)
        if sats:
            df = pd.DataFrame(sats)
            source = 'CelesTrak'
        rate_limit_sleep(2.5)

    if df is not None and not df.empty:
        df['CONSTELLATION'] = clean_name
        df['COUNTRY_CODE'] = COUNTRY_MAP.get(clean_name, 'UNK')
        df = df[df['COUNTRY_CODE'].isin(ALLOWED_COUNTRIES)]
        if not df.empty:
            if 'NORAD_CAT_ID' in df.columns:
                df['NORAD_CAT_ID'] = df['NORAD_CAT_ID'].astype(str)
            all_dfs.append(df)
            elapsed = time.time() - start
            pull_stats.append((clean_name, len(df), source, elapsed))
            log(f"Pulled {len(df):>5}  {clean_name:<16}  via {source:<12}  ({elapsed:.1f}s)")

    rate_limit_sleep(1.5)

# =============================================================================
# WATCHLIST (optional specific NORADs)
# =============================================================================
if WATCHLIST_NORADS:
    log("Processing watchlist...")
    for norad in WATCHLIST_NORADS:
        entry = {
            'norad': norad,
            'name': '',
            'tle_line1': '',
            'tle_line2': '',
            'epoch': '',
            'inclination': ''
        }
        success = False
        if st is not None:
            try:
                data = st.gp(norad_cat_id=norad, format='json',
                              epoch='%3Enow-10', decay_date='null-val')
                sats = json.loads(data)
                if sats:
                    s = sats[0]
                    entry.update({
                        'name': s.get('OBJECT_NAME', ''),
                        'tle_line1': s.get('TLE_LINE1', ''),
                        'tle_line2': s.get('TLE_LINE2', ''),
                        'epoch': s.get('EPOCH', ''),
                        'inclination': str(s.get('INCLINATION', '')),
                    })
                    success = True
            except Exception as e:
                log(f"Watchlist Space-Track failed for {norad}: {e}")

        if not success:
            name, l1, l2 = fetch_celestrak_tle_by_norad(norad)
            if l1:
                entry.update({'name': name or '', 'tle_line1': l1, 'tle_line2': l2 or ''})
                success = True

        if success:
            watchlist_data.append(entry)
        rate_limit_sleep(1)

    log(f"Watchlist complete: {len(watchlist_data)} objects")

with open(WATCHLIST_JSON, 'w') as f:
    json.dump(watchlist_data, f, indent=2)

# =============================================================================
# CHANGE DETECTION + NOTES GENERATION
# =============================================================================
notes = []
now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
notes.append(f"Patriot Orbit Update — {now_str}")
notes.append("")

if all_dfs:
    master = pd.concat(all_dfs, ignore_index=True)
    master = master[master['COUNTRY_CODE'].isin(ALLOWED_COUNTRIES)].copy()
    master = safe_numeric(master, ['INCLINATION', 'MEAN_MOTION', 'SEMIMAJOR_AXIS'])

    log(f"Master dataframe assembled: {len(master)} objects")

    changes = []
    if previous is not None and not previous.empty and 'NORAD_CAT_ID' in previous.columns:
        # Only use columns that actually exist in the previous snapshot
        prev_cols = ['NORAD_CAT_ID']
        for col in ['INCLINATION', 'MEAN_MOTION', 'SEMIMAJOR_AXIS']:
            if col in previous.columns:
                prev_cols.append(col)

        try:
            merged = master.merge(
                previous[prev_cols],
                on='NORAD_CAT_ID',
                how='left',
                suffixes=('', '_prev')
            )

            # Inclination shifts
            if 'INCLINATION_prev' in merged.columns:
                mask = (merged['INCLINATION'] - merged['INCLINATION_prev']).abs() > INCLINATION_THRESHOLD
                for _, row in merged[mask].iterrows():
                    if pd.notna(row['INCLINATION']) and pd.notna(row['INCLINATION_prev']):
                        changes.append(
                            f"- {row.get('OBJECT_NAME', 'UNK')} (NORAD {row['NORAD_CAT_ID']}): "
                            f"Inclination {row['INCLINATION_prev']:.2f}° → {row['INCLINATION']:.2f}°"
                        )

            # Mean motion shifts
            if 'MEAN_MOTION_prev' in merged.columns:
                mask = (merged['MEAN_MOTION'] - merged['MEAN_MOTION_prev']).abs() > MEAN_MOTION_THRESHOLD
                for _, row in merged[mask].iterrows():
                    if pd.notna(row['MEAN_MOTION']) and pd.notna(row['MEAN_MOTION_prev']):
                        changes.append(
                            f"- {row.get('OBJECT_NAME', 'UNK')} (NORAD {row['NORAD_CAT_ID']}): "
                            f"Mean motion {row['MEAN_MOTION_prev']:.4f} → {row['MEAN_MOTION']:.4f}"
                        )

            log(f"Change detection complete: {len(changes)} significant shifts found")
        except Exception as e:
            log(f"Change detection error (continuing): {e}")

    # Persist snapshots
    master.to_csv(PREV_SNAPSHOT, index=False)
    master.to_csv(MASTER_CSV, index=False)
    log(f"Saved {MASTER_CSV} and {PREV_SNAPSHOT}")

    # Build notes content
    if changes:
        notes.append("Significant Orbital Changes Detected:")
        notes.extend(changes[:25])
        if len(changes) > 25:
            notes.append(f"- ...and {len(changes) - 25} more changes")
        notes.append("")
    else:
        notes.append("No significant orbital changes detected this run.")
        notes.append("")

    # Country / constellation summaries
    china = master[master['COUNTRY_CODE'] == 'PRC']
    notes.append(f"Chinese Activity: {len(china)} objects tracked.")
    if not china.empty:
        yaogan = china[china['CONSTELLATION'] == 'YAOGAN']
        notes.append(f"- Yaogan: {len(yaogan)} objects (includes known debris and triplets).")
        for const in sorted(china['CONSTELLATION'].unique()):
            count = len(china[china['CONSTELLATION'] == const])
            if const != 'YAOGAN':
                notes.append(f"- {const}: {count} objects")
        notes.append("")

    russia = master[master['COUNTRY_CODE'] == 'CIS']
    notes.append(f"Russian Activity: {len(russia)} objects tracked.")
    if not russia.empty:
        notes.append("- Includes GLONASS navigation and COSMOS reconnaissance satellites.")
        for const in sorted(russia['CONSTELLATION'].unique()):
            count = len(russia[russia['CONSTELLATION'] == const])
            notes.append(f"- {const}: {count} objects")
        notes.append("")

    nk = master[master['COUNTRY_CODE'] == 'NKOR']
    notes.append(f"North Korean Activity: {len(nk)} objects tracked.")
    if not nk.empty:
        notes.append("- Malligyong-1 remains the primary active object.")
        notes.append("")

    iran = master[master['COUNTRY_CODE'] == 'IRAN']
    notes.append(f"Iranian Activity: {len(iran)} objects tracked.")
    if not iran.empty:
        notes.append("- Includes Noor military satellites and related objects.")
        notes.append("")

    notes.append(f"Total objects in master file: {len(master)}")
    notes.append("")
    notes.append("Pull statistics:")
    for name, count, source, elapsed in pull_stats:
        notes.append(f"  {name:<16} {count:>5} objects  ({source}, {elapsed:.1f}s)")

else:
    notes.append("No data pulled this run (both Space-Track and CelesTrak failed).")
    log("WARNING: No data retrieved from either source.")

# Write notes
with open(NOTES_FILE, 'w') as f:
    f.write('\n'.join(notes))
log(f"Wrote {NOTES_FILE}")

# Optional: simple HTML snippet for the site (major movements)
if changes:
    html_lines = ['<ul class="movements">']
    for c in changes[:15]:
        html_lines.append(f"  <li>{c[2:]}</li>")
    if len(changes) > 15:
        html_lines.append(f"  <li>...and {len(changes) - 15} more</li>")
    html_lines.append('</ul>')
    with open(HTML_SNIPPET, 'w') as f:
        f.write('\n'.join(html_lines))
    log(f"Wrote optional {HTML_SNIPPET}")

log("Run complete.")
