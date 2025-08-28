import sys

import pandas as pd

df = pd.read_csv(sys.argv[1])

print('>>> C2:')
df.info()

print('>>> C1:')
df.describe()

print('>>> C6:')
df.head()
