from spacetrack import SpaceTrackClient
import pandas as pd
import json
from datetime import datetime

st = SpaceTrackClient('bradenrbailey02@gmail.com', 'Uscuscusc9777!!!')

constellations = [
    '~~YAOGAN~~', '~~BEIDOU~~', '~~GAOFEN~~', '~~QIANFAN~~',
    '~~FENGYUN~~', '~~HAIYANG~~', '~~JILIN~~', '~~TIANHUI~~',
    '~~GLONASS~~', '~~COSMOS~~', '~~KANOPUS~~', '~~RESURS~~',
    '~~KWANGMYONGSONG~~', '~~MALLIGYONG~~'
]

all_dfs = []

for name in constellations:
    try:
        data = st.gp(object_name=name, format='json')
        satellites = json.loads(data)
        df = pd.DataFrame(satellites)
        if not df.empty:
            df['CONSTELLATION'] = name.replace('~~', '')
            all_dfs.append(df)
            print(f"Pulled {len(df)} for {name}")
    except Exception as e:
        print(f"Error on {name}: {e}")

if all_dfs:
    master = pd.concat(all_dfs, ignore_index=True)
    master.to_csv('MASTER_ALL_SPACE_OBJECTS.csv', index=False)
    print(f"Saved master with {len(master)} objects")

    # Commentary
    notes = []
    notes.append(f"Patriot Orbit Update — {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n")

    # Chinese
    china = master[master['CONSTELLATION'].isin(['YAOGAN', 'BEIDOU', 'GAOFEN', 'QIANFAN', 'FENGYUN', 'HAIYANG', 'JILIN', 'TIANHUI'])]
    notes.append(f"Chinese Activity: {len(china)} objects tracked.")
    if not china.empty:
        recent = china[china['EPOCH'] > '2026-11-20']
        notes.append(f"- {len(recent)} have fresh epochs in the last few days.")
        yaogan = china[china['CONSTELLATION'] == 'YAOGAN']
        notes.append(f"- Yaogan: {len(yaogan)} objects (includes known debris and triplets).")
        notes.append("")

    # Russian
    russia = master[master['CONSTELLATION'].isin(['GLONASS', 'COSMOS', 'KANOPUS', 'RESURS'])]
    notes.append(f"Russian Activity: {len(russia)} objects tracked.")
    if not russia.empty:
        notes.append(f"- Includes GLONASS navigation and COSMOS reconnaissance satellites.")
        notes.append("")

    # North Korea
    nk = master[master['CONSTELLATION'].isin(['KWANGMYONGSONG', 'MALLIGYONG'])]
    notes.append(f"North Korean Activity: {len(nk)} objects tracked.")
    if not nk.empty:
        notes.append("- Limited public TLE coverage on known launches.")
        notes.append("")

    notes.append(f"Total objects in master file: {len(master)}")

    with open('AUTO_NOTES.txt', 'w') as f:
        f.write('\n'.join(notes))

    print("AUTO_NOTES.txt updated")
else:
    print("No data pulled")
