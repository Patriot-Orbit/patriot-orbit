import os
import pandas as pd
from spacetrack import SpaceTrackClient
import json
from datetime import datetime, timezone

user = os.getenv('SPACETRACK_USER')
password = os.getenv('SPACETRACK_PASS')
if not user or not password:
    raise ValueError("Missing credentials")

st = SpaceTrackClient(user, password)

targets = [
    ('~~YAOGAN~~', 'yaogan'),
    ('~~QIANFAN~~', 'qianfan'),
    ('~~BEIDOU~~', 'beidou'),
    ('~~GAOFEN~~', 'gaofen'),
    ('~~FENGYUN~~', 'fengyun'),
    ('~~GUOWANG~~', 'guowang'),
    ('~~HAIYANG~~', 'haiyang'),
    ('~~JILIN~~', 'jilin'),
    ('~~TIANHUI~~', 'tianhui'),
    ('~~YUNHAI~~', 'yunhai'),
    ('~~GLONASS~~', 'glonass'),
    ('~~COSMOS~~', 'cosmos'),
    ('~~METEOR~~', 'meteor'),
    ('~~RESURS~~', 'resurs'),
    ('~~MALLIGYONG~~', 'malligyong'),
    ('~~KWANGMYONGSONG~~', 'kwangmyongsong'),
]

dfs = []
for query, source in targets:
    try:
        print(f"Pulling {source}...")
        data = st.gp(object_name=query, format='json')
        sats = json.loads(data)
        if sats:
            df = pd.DataFrame(sats)
            df['SOURCE'] = source
            dfs.append(df)
            print(f"  {len(df)} objects")
    except Exception as e:
        print(f"  Skipped {source}: {e}")

if not dfs:
    raise SystemExit("No data pulled")

master = pd.concat(dfs, ignore_index=True)
master['EPOCH'] = pd.to_datetime(master['EPOCH'], errors='coerce', utc=True)
now = datetime.now(timezone.utc)
master = master[master['EPOCH'] <= now + pd.Timedelta(hours=6)]
master = master.drop_duplicates(subset=['NORAD_CAT_ID'], keep='last')
master['hours_old'] = (now - master['EPOCH']).dt.total_seconds() / 3600

master.to_csv('MASTER_ALL_SPACE_OBJECTS.csv', index=False)
print(f"Master saved: {len(master)} unique objects")

# Automatic commentary
notes = []
notes.append(f"Patriot Orbit Auto-Analysis — {now.strftime('%Y-%m-%d %H:%M UTC')}")
notes.append(f"Total unique objects: {len(master)}")

chinese_sources = ['yaogan', 'qianfan', 'beidou', 'gaofen', 'fengyun', 'guowang', 'haiyang', 'jilin', 'tianhui', 'yunhai']
chinese = master[master['SOURCE'].isin(chinese_sources)]
fresh_chinese = chinese[chinese['hours_old'] <= 48]
notes.append(f"\nCHINESE: {len(chinese)} objects, {len(fresh_chinese)} fresh (48h)")
if len(fresh_chinese) > 0:
    top = fresh_chinese.sort_values('hours_old').head(5)
    notes.append("Recent Chinese activity:")
    for _, row in top.iterrows():
        notes.append(f"  - {row['OBJECT_NAME']} ({row['NORAD_CAT_ID']}) | {row['SOURCE']} | {row['hours_old']:.1f}h old")

russian_sources = ['glonass', 'cosmos', 'meteor', 'resurs']
russian = master[master['SOURCE'].isin(russian_sources)]
fresh_russian = russian[russian['hours_old'] <= 48]
notes.append(f"\nRUSSIAN: {len(russian)} objects, {len(fresh_russian)} fresh (48h)")

nk = master[master['SOURCE'].isin(['malligyong', 'kwangmyongsong'])]
notes.append(f"\nNORTH KOREAN: {len(nk)} objects tracked")
if len(nk) > 0:
    for _, row in nk.iterrows():
        notes.append(f"  - {row['OBJECT_NAME']} ({row['NORAD_CAT_ID']})")

debris = master[master['OBJECT_NAME'].str.contains('DEB', case=False, na=False)]
notes.append(f"\nDebris objects: {len(debris)}")

with open('AUTO_NOTES.txt', 'w') as f:
    f.write('\n'.join(notes))
print("Notes written to AUTO_NOTES.txt")
