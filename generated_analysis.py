import pandas as pd
df = pd.read_csv('your_file.csv')

print('>>> C2:')
df.info()
print('>>> C1:')
df.describe()
print('>>> C6:')
df.head()
