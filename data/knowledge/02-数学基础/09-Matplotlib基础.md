# Matplotlib基础

## 架构

Matplotlib的三层结构：
- **Figure**：顶层容器（整个画布）。
- **Axes**：实际绘图区域（一个figure可以通过子图包含多个axes）。
- **Artist**：画布上所有可见的元素（线条、文本、刻度、标签）。

导入约定：`import matplotlib.pyplot as plt`

## 基本图表类型

```python
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 100)
y = np.sin(x)

# 折线图
plt.plot(x, y, label='sin(x)')
plt.plot(x, np.cos(x), label='cos(x)', linestyle='--')
plt.legend()
plt.show()

# 散点图
x_pts = np.random.rand(50)
y_pts = np.random.rand(50)
sizes = np.random.randint(20, 200, 50)
colors = np.random.rand(50)
plt.scatter(x_pts, y_pts, s=sizes, c=colors, alpha=0.6, cmap='viridis')
plt.colorbar()   # 显示颜色刻度
plt.show()

# 柱状图
categories = ['A', 'B', 'C', 'D']
values = [23, 45, 56, 78]
plt.bar(categories, values, color=['#2196F3', '#4CAF50', '#FF9800', '#F44336'])
plt.xlabel('Category')
plt.ylabel('Value')
plt.title('Bar Chart Example')
plt.show()

# 直方图
data = np.random.randn(1000)
plt.hist(data, bins=30, alpha=0.7, edgecolor='black')
plt.axvline(data.mean(), color='red', linestyle='dashed', linewidth=2, label=f'Mean={data.mean():.2f}')
plt.legend()
plt.show()

# 箱线图
data = [np.random.randn(100), np.random.randn(100) + 2, np.random.randn(100) - 1]
plt.boxplot(data, labels=['Group 1', 'Group 2', 'Group 3'])
plt.ylabel('Value')
plt.show()

# 饼图
sizes = [30, 25, 20, 15, 10]
labels = ['数学', '英语', '物理', '化学', '生物']
explode = (0.05, 0, 0, 0, 0)  # 稍微突出第一块
plt.pie(sizes, labels=labels, explode=explode, autopct='%1.1f%%',
        shadow=True, startangle=90)
plt.axis('equal')  # 确保饼图为正圆形
plt.show()
```

## Figure与子图

```python
# 单个figure包含多个子图
fig, axes = plt.subplots(2, 2, figsize=(10, 8))
# axes 是一个 2x2 的 Axes 对象数组
axes[0, 0].plot(x, np.sin(x)); axes[0, 0].set_title('Sine')
axes[0, 1].plot(x, np.cos(x)); axes[0, 1].set_title('Cosine')
axes[1, 0].scatter(np.random.rand(20), np.random.rand(20)); axes[1, 0].set_title('Scatter')
axes[1, 1].hist(np.random.randn(500), bins=30); axes[1, 1].set_title('Histogram')
plt.tight_layout()  # 调整子图之间的间距
plt.show()

# 共享坐标轴（适用于比较数据范围）
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
ax1.plot([1, 2, 3], [10, 20, 30])
ax2.plot([1, 2, 3], [5, 15, 25])
plt.show()

# 不同的子图布局
plt.subplot(2, 1, 1)  # 2行1列，位置1
plt.plot([1, 2, 3], [1, 4, 9])
plt.subplot(2, 1, 2)  # 2行1列，位置2
plt.plot([1, 2, 3], [1, 2, 3])
plt.show()
```

## 自定义

```python
plt.figure(figsize=(8, 5))

# 颜色、标记和线型
plt.plot(x, y, color='#2196F3', marker='o', markersize=4,
         linestyle='-', linewidth=2, label='Data', alpha=0.8)
# color：十六进制字符串、颜色名称或RGB元组
# marker选项：'.', 'o', 's', '^', 'v', 'd', '*', 'x'
# linestyle：'-', '--', '-.', ':'

# 标签与标题
plt.xlabel('X Axis Label', fontsize=12, fontweight='bold')
plt.ylabel('Y Axis Label', fontsize=12)
plt.title('Customized Plot', fontsize=14, fontweight='bold', pad=15)

# 网格与图例
plt.grid(True, alpha=0.3, linestyle='--')
plt.legend(loc='upper right', fontsize=10, framealpha=0.9)

# 坐标轴控制
plt.xlim(0, 10)
plt.ylim(-1.5, 1.5)
plt.xticks([0, 2, 4, 6, 8, 10], ['0', '2', '4', '6', '8', '10'])
plt.xscale('log')  # 切换到对数刻度

plt.tight_layout()
plt.show()
```

## 标注

```python
x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.plot(x, y)

# 简单文本
plt.text(5, 0, 'Center point', fontsize=12, ha='center',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# 带箭头的标注
plt.annotate('Peak', xy=(np.pi/2, 1.0),          # 箭头指向此处
             xytext=(np.pi/2 + 3, 0.8),           # 文本位于此处
             arrowprops=dict(arrowstyle='->', color='red', lw=1.5),
             fontsize=11, color='red')
plt.show()
```

## 保存图形

```python
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot([1, 2, 3], [1, 4, 9])

plt.savefig('plot.png', dpi=300, bbox_inches='tight')
# bbox_inches='tight' 移除多余的空白
# dpi=300 为打印提供高分辨率
# 支持的格式：png, jpg, pdf, svg

plt.savefig('plot.pdf', format='pdf', bbox_inches='tight')  # 矢量格式
```

## 样式表

```python
print(plt.style.available)  # 列出所有可用的样式
plt.style.use('seaborn-v0_8-darkgrid')      # 全局应用样式
# 试试：'ggplot', 'fivethirtyeight', 'seaborn-v0_8-whitegrid', 'dark_background'

# 恢复默认设置
plt.style.use('default')
```

## 中文字体处理

中文字符默认通常会显示为空白方块。以下是解决方法：

```python
import matplotlib.pyplot as plt

# 检查支持中文的可用字体
import matplotlib.font_manager as fm
chinese_fonts = [f.name for f in fm.fontManager.ttflist if any(
    keyword in f.name for keyword in ['SimHei', 'KaiTi', 'Microsoft YaHei', 'Noto Sans CJK']
)]
print(chinese_fonts)

# 方法1：全局设置
plt.rcParams['font.sans-serif'] = ['SimHei']  # 或 'Microsoft YaHei'、'WenQuanYi Micro Hei'
plt.rcParams['axes.unicode_minus'] = False    # 修复负号显示

# 方法2：为特定文本元素设置
plt.title('中文标题', fontfamily='SimHei')

# 方法3：直接使用字体文件
from matplotlib.font_manager import FontProperties
zh_font = FontProperties(fname='C:/Windows/Fonts/msyh.ttc', size=12)
plt.title('中文标题', fontproperties=zh_font)
```

## Seaborn快速参考

Seaborn构建在Matplotlib之上，提供高级统计可视化：

```python
import seaborn as sns
import pandas as pd

# 加载内置数据集
tips = sns.load_dataset('tips')

# 热力图（相关性矩阵）
corr = tips.corr(numeric_only=True)
sns.heatmap(corr, annot=True, cmap='coolwarm', center=0, fmt='.2f')
plt.title('Correlation Heatmap')
plt.show()

# 配对图（散点矩阵与分布）
sns.pairplot(tips, hue='day', diag_kind='hist')
plt.show()

# 分布图
sns.histplot(tips['total_bill'], kde=True, bins=30)  # kde=True添加密度曲线
plt.show()

# 按类别分组的箱线图
sns.boxplot(x='day', y='total_bill', data=tips, palette='Set2')
plt.show()

# 小提琴图（箱线图 + 密度）
sns.violinplot(x='day', y='total_bill', data=tips, inner='quartile')
plt.show()
```

## 常见可视化模式

```python
# 数据探索工作流与可视化
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# 1. 变量分布
axes[0, 0].hist(data, bins=30, color='steelblue', edgecolor='white', alpha=0.8)
axes[0, 0].set_title('Distribution'); axes[0, 0].set_xlabel('Value'); axes[0, 0].set_ylabel('Frequency')

# 2. 随时间变化的趋势
axes[0, 1].plot(dates, values, marker='o', linewidth=2, markersize=4)
axes[0, 1].set_title('Trend Over Time'); axes[0, 1].tick_params(axis='x', rotation=45)

# 3. 跨类别比较
axes[1, 0].bar(categories, group_a, label='Group A', alpha=0.8)
axes[1, 0].bar(categories, group_b, bottom=group_a, label='Group B', alpha=0.8)  # 堆叠
axes[1, 0].legend(); axes[1, 0].set_title('Category Comparison')

# 4. 两个变量之间的关系
axes[1, 1].scatter(x_var, y_var, alpha=0.6, edgecolors='white')
axes[1, 1].set_title('Relationship'); axes[1, 1].set_xlabel('X'); axes[1, 1].set_ylabel('Y')

plt.tight_layout()
plt.show()
```
