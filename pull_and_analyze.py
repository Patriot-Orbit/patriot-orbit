from spacetrack import SpaceTrackClient
import pandas as pd
import json
from datetime import datetime
import os

st = SpaceTrackClient('bradenrbailey02@gmail.com', 'Uscuscusc9777!!!')

constellations = [
    '~~YAOGAN~~', '~~BEIDOU~~', '~~GAOFEN~~', '~~QIANFAN~~',
    '~~FENGYUN~~', '~~HAIYANG~~', '~~JILIN~~', '~~TIANHUI~~',
    '~~GLONASS~~', '~~COSMOS~~', '~~KANOPUS~~', '~~RESURS~~',
    '~~KWANGMYONGSONG~~', '~~MALLIGYONG~~',
    '~~NOOR~~', '~~KHAYYAM~~', '~~SAFIR~~'
]

country_map = {
    'YAOGAN': 'PRC', 'BEIDOU': 'PRC', 'GAOFEN': 'PRC', 'QIANFAN': 'PRC',
    'FENGYUN': 'PRC', 'HAIYANG': 'PRC', 'JILIN': 'PRC', 'TIANHUI': 'PRC',
    'GLONASS': 'CIS', 'COSMOS': 'CIS', 'KANOPUS': 'CIS', 'RESURS': 'CIS',
    'KWANGMYONGSONG': 'NKOR', 'MALLIGYONG': 'NKOR',
    'NOOR': 'IRAN', 'KHAYYAM': 'IRAN', 'SAFIR': 'IRAN'
}

ALLOWED_COUNTRIES = {'PRC', 'CIS', 'NKOR', 'IRAN'}

# Load previous snapshot if it exists
prev_file = 'previous_snapshot.csv'
previous = None
if os.path.exists(prev_file):
    try:
        previous = pd.read_csv(prev_file)
    except:
        previous = None

all_dfs = []

for name in constellations:
    try:
        data = st.gp(object_name=name, format='json')
        satellites = json.loads(data)
        df = pd.DataFrame(satellites)
        if not df.empty:
            clean_name = name.replace('~~', '')
            df['CONSTELLATION'] = clean_name
            df['COUNTRY_CODE'] = country_map.get(clean_name, 'UNK')
            df = df[df['COUNTRY_CODE'].isin(ALLOWED_COUNTRIES)]
            if not df.empty:
                all_dfs.append(df)
                print(f"Pulled {len(df)} for {name}")
    except Exception as e:
        print(f"Error on {name}: {e}")

if all_dfs:
    master = pd.concat(all_dfs, ignore_index=True)
    master = master[master['COUNTRY_CODE'].isin(ALLOWED_COUNTRIES)]

    # Convert numeric columns for comparison
    for col in ['INCLINATION', 'MEAN_MOTION', 'SEMIMAJOR_AXIS']:
        if col in master.columns:
            master[col] = pd.to_numeric(master[col], errors='coerce')

    # Maneuver / change detection
    changes = []
    if previous is not None and not previous.empty:
        for col in ['INCLINATION', 'MEAN_MOTION', 'SEMIMAJOR_AXIS']:
            if col in previous.columns:
                previous[col] = pd.to_numeric(previous[col], errors='coerce')

        merged = master.merge(
            previous[['NORAD_CAT_ID', 'INCLINATION', 'MEAN_MOTION', 'SEMIMAJOR_AXIS']],
            on='NORAD_CAT_ID',
            how='left',
            suffixes=('', '_prev')
        )

        # Flag significant changes
        # Inclination change > 0.05 deg
        if 'INCLINATION_prev' in merged.columns:
            inc_change = merged[(merged['INCLINATION'] - merged['INCLINATION_prev']).abs() > 0.05]
            for _, row in inc_change.iterrows():
                changes.append(f"- {row['OBJECT_NAME']} (NORAD {row['NORAD_CAT_ID']}): Inclination shifted {row['INCLINATION_prev']:.2f}° → {row['INCLINATION']:.2f}°")

        # Mean motion change > 0.001 rev/day (rough altitude proxy)
        if 'MEAN_MOTION_prev' in merged.columns:
            mm_change = merged[(merged['MEAN_MOTION'] - merged['MEAN_MOTION_prev']).abs() > 0.001]
            for _, row in mm_change.iterrows():
                changes.append(f"- {row['OBJECT_NAME']} (NORAD {row['NORAD_CAT_ID']}): Mean motion shifted {row['MEAN_MOTION_prev']:.4f} → {row['MEAN_MOTION']:.4f}")

    # Save current as next previous
    master.to_csv(prev_file, index=False)
    master.to_csv('MASTER_ALL_SPACE_OBJECTS.csv', index=False)
    print(f"Saved master with {len(master)} objects")

    # Build notes
    notes = []
    notes.append(f"Patriot Orbit Update — {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n")

    if changes:
        notes.append("Significant Orbital Changes Detected:")
        notes.extend(changes[:15])  # Limit to top 15 to keep notes readable
        if len(changes) > 15:
            notes.append(f"- ...and {len(changes) - 15} more changes")
        notes.append("")

    china = master[master['COUNTRY_CODE'] == 'PRC']
    notes.append(f"Chinese Activity: {len(china)} objects tracked.")
    if not china.empty:
        recent = china[china['EPOCH'] > '2026-11-20']
        notes.append(f"- {len(recent)} have fresh epochs in the last few days.")
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

    with open('AUTO_NOTES.txt', 'w') as f:
        f.write('\n'.join(notes))

    print("AUTO_NOTES.txt updated")
else:
    print("No data pulled")
