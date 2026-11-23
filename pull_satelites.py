from spacetrack import SpaceTrackClient
import pandas as pd
import json

# Replace with your Space-Track email and password
st = SpaceTrackClient('YOUR_EMAIL', 'YOUR_PASSWORD')

# Change this to any constellation: YAOGAN, QIANFAN, BEIDOU, FENGYUN, GLONASS, etc.
constellation = 'YAOGAN'

data = st.gp(object_name=f'~~{constellation}~~', format='json')
satellites = json.loads(data)

df = pd.DataFrame(satellites)
print(df[['OBJECT_NAME', 'NORAD_CAT_ID', 'EPOCH', 'INCLINATION', 'MEAN_MOTION']].head(20))

filename = f'{constellation.lower()}_current.csv'
df.to_csv(filename, index=False)
print(f"Saved {len(df)} objects to {filename}")
