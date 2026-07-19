# Pandas基础

Pandas提供两种主要的数据结构：
- **Series**：带标签的一维数组（类似于电子表格中的一列）。
- **DataFrame**：带标签的二维表格（类似于带有命名列的电子表格）。

导入约定：`import pandas as pd`

## 创建DataFrame

```python
import pandas as pd

# 从字典的列表创建（键 = 列名）
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35],
    'score': [85.5, 92.3, 78.0]
})

# 从列表的字典创建（每个字典 = 一行）
df = pd.DataFrame([
    {'name': 'Alice', 'age': 25},
    {'name': 'Bob', 'age': 30}
])

# 从CSV / Excel / JSON读取
df = pd.read_csv('data.csv')
df = pd.read_csv('data.csv', sep=';', encoding='utf-8', skiprows=2, nrows=1000)
df = pd.read_csv('data.csv', usecols=['name', 'age'], dtype={'age': 'int32'})
df = pd.read_excel('data.xlsx', sheet_name='Sheet1')
df = pd.read_json('data.json', orient='records')
```

## 基本探索

```python
df.head(10)         # 前10行（默认5行）
df.tail(3)          # 最后3行
df.info()           # 列名、数据类型、非空计数、内存使用
df.describe()       # 计数、均值、标准差、最小值、25%、50%、75%、最大值（数值列）
df.describe(include='object')  # 字符串列：计数、唯一值、最频繁值、频率
df.shape            # (行数, 列数) 元组
df.columns          # 列名索引
df.dtypes           # 每列的数据类型
df.nunique()        # 每列唯一值的数量
```

## 数据选择

```python
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie', 'Diana'],
    'age': [25, 30, 35, 28],
    'score': [85.5, 92.3, 78.0, 88.2],
    'city': ['NY', 'LA', 'NY', 'SF']
})

# 按列名选择
df['name']              # 返回 Series
df[['name', 'score']]   # 返回包含两列的 DataFrame

# 按位置选择：.iloc（基于整数位置）
df.iloc[0]              # 第一行，返回 Series
df.iloc[1:3]            # 第1-2行
df.iloc[:, 1:3]         # 所有行，第1-2列

# 按标签选择：.loc
df = df.set_index('name')   # 现在索引是 'name' 列
df.loc['Alice']             # 索引为 'Alice' 的行
df.loc['Alice', 'score']    # 单个单元格
df.loc['Alice':'Charlie']   # 按标签切片（包含右边界！）

# 条件筛选
df[df['age'] > 28]                              # 筛选行
df[(df['age'] > 25) & (df['city'] == 'NY')]     # 使用 &、|、~ 组合条件
df[df['name'].str.contains('A', case=False)]     # 字符串匹配
df.query('age > 25 and city == "NY"')            # 类似SQL的语法
```

## 处理缺失值

```python
df = pd.DataFrame({
    'A': [1, 2, None, 4],
    'B': [5, None, None, 8],
    'C': ['x', 'y', None, 'z']
})

df.isnull()          # 缺失值的布尔掩码
df.isnull().sum()    # 每列缺失值计数

df.dropna()                    # 删除包含任何NaN的行
df.dropna(axis=1)              # 删除包含任何NaN的列
df.dropna(thresh=2)            # 保留至少有2个非NaN值的行
df.dropna(subset=['B'])        # 删除B列为NaN的行

df.fillna(0)                   # 将所有NaN填充为0
df.fillna({'A': 0, 'B': 99})   # 每列用不同的值填充
df.fillna(method='ffill')      # 前向填充（使用上一个有效值）
df.fillna(df.mean())           # 用每列的均值填充数值型NaN
```

## 排序

```python
df = pd.DataFrame({'name': ['C', 'A', 'B'], 'score': [85, 92, 78]})

df.sort_values('score')                  # 按score升序排列
df.sort_values('score', ascending=False) # 降序排列
df.sort_values(['name', 'score'], ascending=[True, False])  # 多列排序
df.sort_index()                          # 按行索引排序
df.reset_index(drop=True)                # 重置索引为0,1,2,...（丢弃旧索引）
```

## 分组操作

```python
df = pd.DataFrame({
    'department': ['Sales', 'Sales', 'Engineering', 'Engineering'],
    'employee': ['A', 'B', 'C', 'D'],
    'salary': [50000, 60000, 80000, 75000]
})

# 聚合
df.groupby('department')['salary'].mean()     # 每个部门的平均工资
df.groupby('department').agg({
    'salary': ['mean', 'min', 'max', 'count'],
    'employee': 'count'
})

# 变换（返回与输入相同的形状 -- 非常适合归一化）
df['salary_norm'] = df.groupby('department')['salary'].transform(
    lambda x: (x - x.mean()) / x.std()
)

# 筛选分组
df.groupby('department').filter(lambda g: g['salary'].mean() > 60000)
```

## 合并DataFrame

```python
left = pd.DataFrame({'id': [1, 2, 3], 'name': ['A', 'B', 'C']})
right = pd.DataFrame({'id': [1, 2, 4], 'score': [85, 90, 78]})

# SQL风格的连接
pd.merge(left, right, on='id', how='inner')   # 仅匹配的键
pd.merge(left, right, on='id', how='left')    # 保留左侧所有键
pd.merge(left, right, on='id', how='right')   # 保留右侧所有键
pd.merge(left, right, on='id', how='outer')   # 保留两表所有键

# 拼接（堆叠行或列）
pd.concat([left, left], axis=0, ignore_index=True)  # 堆叠行
pd.concat([left, right], axis=1)                    # 并排堆叠列
```

## Apply与Map

```python
df = pd.DataFrame({'a': [1, 2, 3], 'b': [10, 20, 30]})

# DataFrame的apply：对每列（axis=0）或每行（axis=1）执行函数
df.apply(np.sum, axis=0)           # 每列的和
df.apply(lambda row: row['a'] + row['b'], axis=1)  # 逐行计算

# Series的map：逐元素映射
df['a'].map({1: 'one', 2: 'two', 3: 'three'})

# DataFrame的applymap：对每个单元格逐元素操作
df.applymap(lambda x: x * 2)
```

## 日期时间处理

```python
df = pd.DataFrame({'date_str': ['2024-01-15', '2024-02-20', '2024-03-10']})

df['date'] = pd.to_datetime(df['date_str'])
df['year']   = df['date'].dt.year
df['month']  = df['date'].dt.month
df['weekday'] = df['date'].dt.day_name()   # 'Monday', 'Tuesday', ...
df['quarter'] = df['date'].dt.quarter

# 日期范围与重采样（用于时间序列）
dates = pd.date_range('2024-01-01', periods=12, freq='ME')  # 月末
```

## 数据透视表

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

## 导出

```python
df.to_csv('output.csv', index=False, encoding='utf-8-sig')
df.to_excel('output.xlsx', sheet_name='Results', index=False)
df.to_json('output.json', orient='records', force_ascii=False)
df.to_sql('table_name', engine, if_exists='replace')  # 需要SQLAlchemy
```

## 实际小型示例：学生成绩分析

```python
grades = pd.DataFrame({
    'student': ['张三', '李四', '王五', '赵六', '张三', '李四'],
    'subject': ['数学', '数学', '数学', '数学', '英语', '英语'],
    'score': [85, 92, 78, 88, 90, 85]
})

# 每个学生的平均分
avg_per_student = grades.groupby('student')['score'].mean()   # 赵六=88, 张三=87.5, ...

# 每门科目的最高分学生
top = grades.loc[grades.groupby('subject')['score'].idxmax()]

# 透视表：学生 vs 科目
pivot = grades.pivot_table(values='score', index='student',
                           columns='subject', fill_value=0)
```
