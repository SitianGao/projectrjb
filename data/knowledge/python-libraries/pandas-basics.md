# Pandas Basics

Pandas provides two primary data structures:
- **Series**: labeled 1D array (like a column in a spreadsheet).
- **DataFrame**: labeled 2D table (like a spreadsheet with named columns).

Import convention: `import pandas as pd`

## Creating DataFrames

```python
import pandas as pd

# From a dict of lists (keys = column names)
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35],
    'score': [85.5, 92.3, 78.0]
})

# From a list of dicts (each dict = one row)
df = pd.DataFrame([
    {'name': 'Alice', 'age': 25},
    {'name': 'Bob', 'age': 30}
])

# From CSV / Excel / JSON
df = pd.read_csv('data.csv')
df = pd.read_csv('data.csv', sep=';', encoding='utf-8', skiprows=2, nrows=1000)
df = pd.read_csv('data.csv', usecols=['name', 'age'], dtype={'age': 'int32'})
df = pd.read_excel('data.xlsx', sheet_name='Sheet1')
df = pd.read_json('data.json', orient='records')
```

## Basic Exploration

```python
df.head(10)         # First 10 rows (default 5)
df.tail(3)          # Last 3 rows
df.info()           # Column names, dtypes, non-null counts, memory usage
df.describe()       # count, mean, std, min, 25%, 50%, 75%, max (numeric cols)
df.describe(include='object')  # For string columns: count, unique, top, freq
df.shape            # (rows, cols) tuple
df.columns          # Index of column names
df.dtypes           # Data type of each column
df.nunique()        # Number of unique values per column
```

## Selecting Data

```python
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie', 'Diana'],
    'age': [25, 30, 35, 28],
    'score': [85.5, 92.3, 78.0, 88.2],
    'city': ['NY', 'LA', 'NY', 'SF']
})

# By column name
df['name']              # Returns a Series
df[['name', 'score']]   # Returns a DataFrame with two columns

# By position: .iloc (integer-location based)
df.iloc[0]              # First row as Series
df.iloc[1:3]            # Rows 1-2
df.iloc[:, 1:3]         # All rows, columns 1-2

# By label: .loc
df = df.set_index('name')   # Now index is the 'name' column
df.loc['Alice']             # Row where index = 'Alice'
df.loc['Alice', 'score']    # Single cell
df.loc['Alice':'Charlie']   # Slice by label (inclusive!)

# Conditional filtering
df[df['age'] > 28]                              # Filter rows
df[(df['age'] > 25) & (df['city'] == 'NY')]     # Combine with &, |, ~
df[df['name'].str.contains('A', case=False)]     # String matching
df.query('age > 25 and city == "NY"')            # SQL-like syntax
```

## Handling Missing Values

```python
df = pd.DataFrame({
    'A': [1, 2, None, 4],
    'B': [5, None, None, 8],
    'C': ['x', 'y', None, 'z']
})

df.isnull()          # Boolean mask of missing values
df.isnull().sum()    # Count of missing values per column

df.dropna()                    # Drop rows with ANY NaN
df.dropna(axis=1)              # Drop columns with ANY NaN
df.dropna(thresh=2)            # Keep rows with at least 2 non-NaN values
df.dropna(subset=['B'])        # Drop rows where B is NaN

df.fillna(0)                   # Fill all NaN with 0
df.fillna({'A': 0, 'B': 99})   # Fill each column with a different value
df.fillna(method='ffill')      # Forward fill (use last valid value)
df.fillna(df.mean())           # Fill numeric NaN with column mean
```

## Sorting

```python
df = pd.DataFrame({'name': ['C', 'A', 'B'], 'score': [85, 92, 78]})

df.sort_values('score')                  # Ascending by score
df.sort_values('score', ascending=False) # Descending
df.sort_values(['name', 'score'], ascending=[True, False])  # Multi-column
df.sort_index()                          # Sort by row index
df.reset_index(drop=True)                # Reset index to 0,1,2,... (drop old index)
```

## Group Operations

```python
df = pd.DataFrame({
    'department': ['Sales', 'Sales', 'Engineering', 'Engineering'],
    'employee': ['A', 'B', 'C', 'D'],
    'salary': [50000, 60000, 80000, 75000]
})

# Aggregation
df.groupby('department')['salary'].mean()     # Average salary per dept
df.groupby('department').agg({
    'salary': ['mean', 'min', 'max', 'count'],
    'employee': 'count'
})

# Transform (returns same shape as input -- great for normalization)
df['salary_norm'] = df.groupby('department')['salary'].transform(
    lambda x: (x - x.mean()) / x.std()
)

# Filter groups
df.groupby('department').filter(lambda g: g['salary'].mean() > 60000)
```

## Merging DataFrames

```python
left = pd.DataFrame({'id': [1, 2, 3], 'name': ['A', 'B', 'C']})
right = pd.DataFrame({'id': [1, 2, 4], 'score': [85, 90, 78]})

# SQL-style joins
pd.merge(left, right, on='id', how='inner')   # Only matching keys
pd.merge(left, right, on='id', how='left')    # All left keys
pd.merge(left, right, on='id', how='right')   # All right keys
pd.merge(left, right, on='id', how='outer')   # All keys from both

# Concatenation (stack rows or columns)
pd.concat([left, left], axis=0, ignore_index=True)  # Stack rows
pd.concat([left, right], axis=1)                    # Stack columns side by side
```

## Apply and Map

```python
df = pd.DataFrame({'a': [1, 2, 3], 'b': [10, 20, 30]})

# apply on DataFrame: runs function on each column (axis=0) or row (axis=1)
df.apply(np.sum, axis=0)           # Sum of each column
df.apply(lambda row: row['a'] + row['b'], axis=1)  # Row-wise

# map on Series: element-wise mapping
df['a'].map({1: 'one', 2: 'two', 3: 'three'})

# applymap on DataFrame: element-wise on every cell
df.applymap(lambda x: x * 2)
```

## DateTime Handling

```python
df = pd.DataFrame({'date_str': ['2024-01-15', '2024-02-20', '2024-03-10']})

df['date'] = pd.to_datetime(df['date_str'])
df['year']   = df['date'].dt.year
df['month']  = df['date'].dt.month
df['weekday'] = df['date'].dt.day_name()   # 'Monday', 'Tuesday', ...
df['quarter'] = df['date'].dt.quarter

# Date ranges and resampling (for time series)
dates = pd.date_range('2024-01-01', periods=12, freq='ME')  # Month-end
```

## Pivot Tables

```python
df = pd.DataFrame({
    'date':   ['Mon','Mon','Tue','Tue','Wed','Wed'],
    'region': ['East','West','East','West','East','West'],
    'sales':  [100, 150, 200, 180, 130, 160]
})

pivot = pd.pivot_table(df, values='sales', index='date',
                       columns='region', aggfunc='sum', fill_value=0)
# region  East  West
# date
# Mon      100   150
# Tue      200   180
# Wed      130   160
```

## Exporting

```python
df.to_csv('output.csv', index=False, encoding='utf-8-sig')
df.to_excel('output.xlsx', sheet_name='Results', index=False)
df.to_json('output.json', orient='records', force_ascii=False)
df.to_sql('table_name', engine, if_exists='replace')  # Requires SQLAlchemy
```

## Real Mini-Example: Student Grade Analysis

```python
grades = pd.DataFrame({
    'student': ['张三', '李四', '王五', '赵六', '张三', '李四'],
    'subject': ['数学', '数学', '数学', '数学', '英语', '英语'],
    'score': [85, 92, 78, 88, 90, 85]
})

# Average score per student
avg_per_student = grades.groupby('student')['score'].mean()   # 赵六=88, 张三=87.5, ...

# Top student in each subject
top = grades.loc[grades.groupby('subject')['score'].idxmax()]

# Pivot: students vs subjects
pivot = grades.pivot_table(values='score', index='student',
                           columns='subject', fill_value=0)
```
