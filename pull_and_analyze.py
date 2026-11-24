from spacetrack import SpaceTrackClient
import pandas as pd
import json
from datetime import datetime

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
            all_dfs.append(df)
            print(f"Pulled {len(df)} for {name}")
    except Exception as e:
        print(f"Error on {name}: {e}")

if all_dfs:
    master = pd.concat(all_dfs, ignore_index=True)
    master.to_csv('MASTER_ALL_SPACE_OBJECTS.csv', index=False)
    print(f"Saved master with {len(master)} objects")

    notes = []
    notes.append(f"Patriot Orbit Update — {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n")

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
        notes.append("- Limited public TLE coverage on known launches.")
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
