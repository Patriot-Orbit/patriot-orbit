from spacetrack import SpaceTrackClient
import pandas as pd
import json

# Replace with your Space-Track email and password
import os
email = os.getenv('SPACETRACK_EMAIL')
password = os.getenv('SPACETRACK_PASSWORD')
st = SpaceTrackClient(email, password)

# Change this to any constellation: YAOGAN, QIANFAN, BEIDOU, FENGYUN, GLONASS, etc.
constellation = 'YAOGAN'

data = st.gp(object_name=f'~~{constellation}~~', format='json')
satellites = json.loads(data)

df = pd.DataFrame(satellites)
print(df[['OBJECT_NAME', 'NORAD_CAT_ID', 'EPOCH', 'INCLINATION', 'MEAN_MOTION']].head(20))

filename = f'{constellation.lower()}_current.csv'
df.to_csv(filename, index=False)
print(f"Saved {len(df)} objects to {filename}")
