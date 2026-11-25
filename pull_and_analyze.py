from spacetrack import SpaceTrackClient
import pandas as pd
import json
import os
import time
from datetime import datetime

# Prefer secrets in GitHub Actions; falls back to the values below for local runs
IDENTITY = os.getenv('SPACETRACK_USER', 'bradenrbailey02@gmail.com')
PASSWORD = os.getenv('SPACETRACK_PASS', 'Uscuscusc9777!!!')

st = SpaceTrackClient(IDENTITY, PASSWORD)

constellations = [
    '~~YAOGAN~~', '~~BEIDOU~~', '~~GAOFEN~~', '~~QIANFAN~~',
    '~~FENGYUN~~', '~~HAIYANG~~', '~~JILIN~~', '~~TIANHUI~~',
    '~~GLONASS~~', '~~COSMOS~~', '~~KANOPUS~~', '~~RESURS~~',
    '~~KWANGMYONGSONG~~', '~~MALLIGYONG~~',
    '~~NOOR~~', '~~KHAYYAM~~', '~~SAFIR~~'
]

# Optional extra NORAD IDs for the frontend watchlist file
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

print("Starting hourly-compliant pull...")

for name in constellations:
    try:
        data = st.gp(
            object_name=name,
            format='json',
            epoch='%3Enow-10',
            decay_date='null-val'
        )
        satellites = json.loads(data)
        df = pd.DataFrame(satellites)
        if not df.empty:
            clean_name = name.replace('~~', '')
            df['CONSTELLATION'] = clean_name
            df['COUNTRY_CODE'] = country_map.get(clean_name, 'UNK')
            df = df[df['COUNTRY_CODE'].isin(ALLOWED_COUNTRIES)]
            if not df.empty:
                if 'NORAD_CAT_ID' in df.columns:
                    df['NORAD_CAT_ID'] = df['NORAD_CAT_ID'].astype(str)
                all_dfs.append(df)
                print(f"Pulled {len(df)} for {clean_name}")
        rate_limit_sleep()
    except Exception as e:
        print(f"Error on {name}: {e}")
        rate_limit_sleep()

if WATCHLIST_NORADS:
    try:
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
        print(f"Pulled {len(watchlist_data)} watchlist objects")
        rate_limit_sleep()
    except Exception as e:
        print(f"Watchlist pull error: {e}")

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
    notes.append("No new data pulled this run.\n")
    notes.append("Showing last successful pull if available:\n")

    if previous is not None and not previous.empty:
        china = previous[previous['COUNTRY_CODE'] == 'PRC'] if 'COUNTRY_CODE' in previous.columns else pd.DataFrame()
        russia = previous[previous['COUNTRY_CODE'] == 'CIS'] if 'COUNTRY_CODE' in previous.columns else pd.DataFrame()
        nk = previous[previous['COUNTRY_CODE'] == 'NKOR'] if 'COUNTRY_CODE' in previous.columns else pd.DataFrame()
        iran = previous[previous['COUNTRY_CODE'] == 'IRAN'] if 'COUNTRY_CODE' in previous.columns else pd.DataFrame()

        notes.append(f"Chinese Activity: {len(china)} objects tracked.")
        if not china.empty and 'CONSTELLATION' in china.columns:
            yaogan = china[china['CONSTELLATION'] == 'YAOGAN']
            notes.append(f"- Yaogan: {len(yaogan)} objects (includes known debris and triplets).")
        notes.append("")

        notes.append(f"Russian Activity: {len(russia)} objects tracked.")
        notes.append("- Includes GLONASS navigation and COSMOS reconnaissance satellites.")
        notes.append("")

        notes.append(f"North Korean Activity: {len(nk)} objects tracked.")
        notes.append("- Malligyong-1 remains the primary active object.")
        notes.append("")

        notes.append(f"Iranian Activity: {len(iran)} objects tracked.")
        notes.append("- Includes Noor military satellites and related objects.")
        notes.append("")

        notes.append(f"Total objects in master file: {len(previous)}")
    else:
        notes.append("No previous data available.")

with open('AUTO_NOTES.txt', 'w') as f:
    f.write('\n'.join(notes))

print("AUTO_NOTES.txt and watchlist_tles.json updated")
print("Done (hourly schedule).")
