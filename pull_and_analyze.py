from spacetrack import SpaceTrackClient
import pandas as pd
import json
import os
import time
import requests
from datetime import datetime

# Prefer secrets in GitHub Actions; falls back to the values below for local runs
IDENTITY = os.getenv('SPACETRACK_USER', 'bradenrbailey02@gmail.com')
PASSWORD = os.getenv('SPACETRACK_PASS', 'Uscuscusc9777!!!')

# CelesTrak requires a descriptive User-Agent
CELESTRAK_HEADERS = {
    'User-Agent': 'PatriotOrbit/1.0 (hourly public TLE fallback; +https://patriotorbit.com)'
}

constellations = [
    '~~YAOGAN~~', '~~BEIDOU~~', '~~GAOFEN~~', '~~QIANFAN~~',
    '~~FENGYUN~~', '~~HAIYANG~~', '~~JILIN~~', '~~TIANHUI~~',
    '~~GLONASS~~', '~~COSMOS~~', '~~KANOPUS~~', '~~RESURS~~',
    '~~KWANGMYONGSONG~~', '~~MALLIGYONG~~',
    '~~NOOR~~', '~~KHAYYAM~~', '~~SAFIR~~'
]

WATCHLIST_NORADS = [
    # '25544',
    # '63230',
]

country_map = {
    'YAOGAN': 'PRC', 'BEIDOU': 'PRC', 'GAOFEN': 'PRC', 'QIANFAN': 'PRC',
    'FENGYUN': 'PRC', 'HAIYANG': 'PRC', 'JILIN': 'PRC', 'TIANHUI': 'PRC',
    'GLONASS': 'CIS', 'COSMOS': 'CIS', 'KANOPUS': 'CIS', 'RESURS': 'CIS',
    'KWANGMYONGSONG': 'NKOR', 'MALLIGYONG': 'NKOR',
    'NOOR': 'IRAN', 'KHAYYAM': 'IRAN', 'SAFIR': 'IRAN'
}

ALLOWED_COUNTRIES = {'PRC', 'CIS', 'NKOR', 'IRAN'}

def rate_limit_sleep():
    time.sleep(3)

def fetch_celestrak_json(name):
    """Public CelesTrak GP JSON fallback. NAME is without the ~~ markers."""
    clean = name.replace('~~', '')
    url = 'https://celestrak.org/NORAD/elements/gp.php'
    params = {'NAME': clean, 'FORMAT': 'json'}
    r = requests.get(url, params=params, headers=CELESTRAK_HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list):
        return []
    return data

def fetch_celestrak_tle(name):
    """Return list of (name, line1, line2) from CelesTrak TLE format."""
    clean = name.replace('~~', '')
    url = 'https://celestrak.org/NORAD/elements/gp.php'
    params = {'NAME': clean, 'FORMAT': 'tle'}
    r = requests.get(url, params=params, headers=CELESTRAK_HEADERS, timeout=30)
    r.raise_for_status()
    lines = [ln.strip() for ln in r.text.splitlines() if ln.strip()]
    results = []
    i = 0
    while i + 2 < len(lines):
        if lines[i+1].startswith('1 ') and lines[i+2].startswith('2 '):
            results.append((lines[i], lines[i+1], lines[i+2]))
            i += 3
        else:
            i += 1
    return results

prev_file = 'previous_snapshot.csv'
previous = None
if os.path.exists(prev_file):
    try:
        previous = pd.read_csv(prev_file)
        if 'NORAD_CAT_ID' in previous.columns:
            previous['NORAD_CAT_ID'] = previous['NORAD_CAT_ID'].astype(str)
    except Exception:
        previous = None

all_dfs = []
watchlist_data = []

print("Starting hourly-compliant pull (Space-Track with CelesTrak fallback)...")

# Try Space-Track client once; if credentials fail we stay on CelesTrak
st = None
try:
    st = SpaceTrackClient(IDENTITY, PASSWORD)
    # Quick health check
    st.gp(norad_cat_id='25544', format='json')
    print("Space-Track connection OK")
except Exception as e:
    print(f"Space-Track unavailable ({e}). Using CelesTrak fallback for this run.")
    st = None

for name in constellations:
    clean_name = name.replace('~~', '')
    df = None
    source = None

    # Prefer Space-Track
    if st is not None:
        try:
            data = st.gp(
                object_name=name,
                format='json',
                epoch='%3Enow-10',
                decay_date='null-val'
            )
            satellites = json.loads(data)
            df = pd.DataFrame(satellites)
            source = 'Space-Track'
        except Exception as e:
            print(f"Space-Track error on {clean_name}: {e}")

    # Fallback to CelesTrak
    if df is None or df.empty:
        try:
            sats = fetch_celestrak_json(name)
            if sats:
                df = pd.DataFrame(sats)
                source = 'CelesTrak'
            rate_limit_sleep()
        except Exception as e:
            print(f"CelesTrak error on {clean_name}: {e}")

    if df is not None and not df.empty:
        df['CONSTELLATION'] = clean_name
        df['COUNTRY_CODE'] = country_map.get(clean_name, 'UNK')
        df = df[df['COUNTRY_CODE'].isin(ALLOWED_COUNTRIES)]
        if not df.empty:
            if 'NORAD_CAT_ID' in df.columns:
                df['NORAD_CAT_ID'] = df['NORAD_CAT_ID'].astype(str)
            all_dfs.append(df)
            print(f"Pulled {len(df)} for {clean_name} via {source}")

    rate_limit_sleep()

# Watchlist (optional NORAD list) – try Space-Track, then CelesTrak
if WATCHLIST_NORADS:
    try:
        if st is not None:
            data = st.gp(
                norad_cat_id=','.join(WATCHLIST_NORADS),
                format='json',
                epoch='%3Enow-10',
                decay_date='null-val'
            )
            sats = json.loads(data)
            for s in sats:
                watchlist_data.append({
                    'norad': str(s.get('NORAD_CAT_ID', '')),
                    'name': s.get('OBJECT_NAME', ''),
                    'tle_line1': s.get('TLE_LINE1', ''),
                    'tle_line2': s.get('TLE_LINE2', ''),
                    'epoch': s.get('EPOCH', ''),
                    'inclination': s.get('INCLINATION', ''),
                })
            print(f"Pulled {len(watchlist_data)} watchlist objects via Space-Track")
        else:
            raise Exception("skip")
    except Exception:
        # CelesTrak fallback for watchlist: use TLE format so we have line1/line2
        try:
            for norad in WATCHLIST_NORADS:
                url = 'https://celestrak.org/NORAD/elements/gp.php'
                r = requests.get(url, params={'CATNR': norad, 'FORMAT': 'tle'},
                                 headers=CELESTRAK_HEADERS, timeout=30)
                r.raise_for_status()
                lines = [ln.strip() for ln in r.text.splitlines() if ln.strip()]
                if len(lines) >= 3 and lines[1].startswith('1 ') and lines[2].startswith('2 '):
                    watchlist_data.append({
                        'norad': norad,
                        'name': lines[0],
                        'tle_line1': lines[1],
                        'tle_line2': lines[2],
                        'epoch': '',
                        'inclination': '',
                    })
            print(f"Pulled {len(watchlist_data)} watchlist objects via CelesTrak")
        except Exception as e:
            print(f"Watchlist CelesTrak error: {e}")

with open('watchlist_tles.json', 'w') as f:
    json.dump(watchlist_data, f, indent=2)

notes = []
now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
notes.append(f"Patriot Orbit Update — {now_str}\n")

if all_dfs:
    master = pd.concat(all_dfs, ignore_index=True)
    master = master[master['COUNTRY_CODE'].isin(ALLOWED_COUNTRIES)]

    for col in ['INCLINATION', 'MEAN_MOTION', 'SEMIMAJOR_AXIS']:
        if col in master.columns:
            master[col] = pd.to_numeric(master[col], errors='coerce')

    changes = []
    if previous is not None and not previous.empty and 'NORAD_CAT_ID' in previous.columns:
        for col in ['INCLINATION', 'MEAN_MOTION', 'SEMIMAJOR_AXIS']:
            if col in previous.columns:
                previous[col] = pd.to_numeric(previous[col], errors='coerce')

        merged = master.merge(
            previous[['NORAD_CAT_ID', 'INCLINATION', 'MEAN_MOTION', 'SEMIMAJOR_AXIS']],
            on='NORAD_CAT_ID',
            how='left',
            suffixes=('', '_prev')
        )

        if 'INCLINATION_prev' in merged.columns:
            inc_change = merged[(merged['INCLINATION'] - merged['INCLINATION_prev']).abs() > 0.05]
            for _, row in inc_change.iterrows():
                if pd.notna(row['INCLINATION']) and pd.notna(row['INCLINATION_prev']):
                    changes.append(f"- {row['OBJECT_NAME']} (NORAD {row['NORAD_CAT_ID']}): Inclination shifted {row['INCLINATION_prev']:.2f}° → {row['INCLINATION']:.2f}°")

        if 'MEAN_MOTION_prev' in merged.columns:
            mm_change = merged[(merged['MEAN_MOTION'] - merged['MEAN_MOTION_prev']).abs() > 0.001]
            for _, row in mm_change.iterrows():
                if pd.notna(row['MEAN_MOTION']) and pd.notna(row['MEAN_MOTION_prev']):
                    changes.append(f"- {row['OBJECT_NAME']} (NORAD {row['NORAD_CAT_ID']}): Mean motion shifted {row['MEAN_MOTION_prev']:.4f} → {row['MEAN_MOTION']:.4f}")

    master.to_csv(prev_file, index=False)
    master.to_csv('MASTER_ALL_SPACE_OBJECTS.csv', index=False)
    print(f"Saved master with {len(master)} objects")

    if changes:
        notes.append("Significant Orbital Changes Detected:")
        notes.extend(changes[:15])
        if len(changes) > 15:
            notes.append(f"- ...and {len(changes) - 15} more changes")
        notes.append("")
    else:
        notes.append("No significant orbital changes detected this run.\n")

    china = master[master['COUNTRY_CODE'] == 'PRC']
    notes.append(f"Chinese Activity: {len(china)} objects tracked.")
    if not china.empty:
        yaogan = china[china['CONSTELLATION'] == 'YAOGAN']
        notes.append(f"- Yaogan: {len(yaogan)} objects (includes known debris and triplets).")
        notes.append("")

    russia = master[master['COUNTRY_CODE'] == 'CIS']
    notes.append(f"Russian Activity: {len(russia)} objects tracked.")
    if not russia.empty:
        notes.append("- Includes GLONASS navigation and COSMOS reconnaissance satellites.")
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
else:
    notes.append("No data pulled this run (both Space-Track and CelesTrak failed).")

with open('AUTO_NOTES.txt', 'w') as f:
    f.write('\n'.join(notes))

print("Done.")
