# Matplotlib Basics

## Architecture

Matplotlib's three-layer structure:
- **Figure**: The top-level container (the whole canvas).
- **Axes**: The actual plotting area (a figure can have multiple Axes via subplots).
- **Artist**: Everything visible on the canvas (lines, text, ticks, labels).

Import convention: `import matplotlib.pyplot as plt`

## Basic Plot Types

```python
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 100)
y = np.sin(x)

# Line plot
plt.plot(x, y, label='sin(x)')
plt.plot(x, np.cos(x), label='cos(x)', linestyle='--')
plt.legend()
plt.show()

# Scatter plot
x_pts = np.random.rand(50)
y_pts = np.random.rand(50)
sizes = np.random.randint(20, 200, 50)
colors = np.random.rand(50)
plt.scatter(x_pts, y_pts, s=sizes, c=colors, alpha=0.6, cmap='viridis')
plt.colorbar()   # Show color scale
plt.show()

# Bar chart
categories = ['A', 'B', 'C', 'D']
values = [23, 45, 56, 78]
plt.bar(categories, values, color=['#2196F3', '#4CAF50', '#FF9800', '#F44336'])
plt.xlabel('Category')
plt.ylabel('Value')
plt.title('Bar Chart Example')
plt.show()

# Histogram
data = np.random.randn(1000)
plt.hist(data, bins=30, alpha=0.7, edgecolor='black')
plt.axvline(data.mean(), color='red', linestyle='dashed', linewidth=2, label=f'Mean={data.mean():.2f}')
plt.legend()
plt.show()

# Box plot
data = [np.random.randn(100), np.random.randn(100) + 2, np.random.randn(100) - 1]
plt.boxplot(data, labels=['Group 1', 'Group 2', 'Group 3'])
plt.ylabel('Value')
plt.show()

# Pie chart
sizes = [30, 25, 20, 15, 10]
labels = ['数学', '英语', '物理', '化学', '生物']
explode = (0.05, 0, 0, 0, 0)  # Slightly pull out the first slice
plt.pie(sizes, labels=labels, explode=explode, autopct='%1.1f%%',
        shadow=True, startangle=90)
plt.axis('equal')  # Ensure the pie is circular
plt.show()
```

## Figure and Subplots

```python
# Single figure with multiple subplots
fig, axes = plt.subplots(2, 2, figsize=(10, 8))
# axes is a 2x2 array of Axes objects
axes[0, 0].plot(x, np.sin(x)); axes[0, 0].set_title('Sine')
axes[0, 1].plot(x, np.cos(x)); axes[0, 1].set_title('Cosine')
axes[1, 0].scatter(np.random.rand(20), np.random.rand(20)); axes[1, 0].set_title('Scatter')
axes[1, 1].hist(np.random.randn(500), bins=30); axes[1, 1].set_title('Histogram')
plt.tight_layout()  # Adjust spacing between subplots
plt.show()

# Shared axes (useful for comparing data ranges)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
ax1.plot([1, 2, 3], [10, 20, 30])
ax2.plot([1, 2, 3], [5, 15, 25])
plt.show()

# Different subplot layouts
plt.subplot(2, 1, 1)  # 2 rows, 1 col, position 1
plt.plot([1, 2, 3], [1, 4, 9])
plt.subplot(2, 1, 2)  # 2 rows, 1 col, position 2
plt.plot([1, 2, 3], [1, 2, 3])
plt.show()
```

## Customization

```python
plt.figure(figsize=(8, 5))

# Colors, markers, and line styles
plt.plot(x, y, color='#2196F3', marker='o', markersize=4,
         linestyle='-', linewidth=2, label='Data', alpha=0.8)
# color: hex string, named color, or RGB tuple
# marker options: '.', 'o', 's', '^', 'v', 'd', '*', 'x'
# linestyle: '-', '--', '-.', ':'

# Labels and title
plt.xlabel('X Axis Label', fontsize=12, fontweight='bold')
plt.ylabel('Y Axis Label', fontsize=12)
plt.title('Customized Plot', fontsize=14, fontweight='bold', pad=15)

# Grid and legend
plt.grid(True, alpha=0.3, linestyle='--')
plt.legend(loc='upper right', fontsize=10, framealpha=0.9)

# Axis control
plt.xlim(0, 10)
plt.ylim(-1.5, 1.5)
plt.xticks([0, 2, 4, 6, 8, 10], ['0', '2', '4', '6', '8', '10'])
plt.xscale('log')  # Switch to logarithmic scale

plt.tight_layout()
plt.show()
```

## Annotations

```python
x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.plot(x, y)

# Simple text
plt.text(5, 0, 'Center point', fontsize=12, ha='center',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Annotation with arrow
plt.annotate('Peak', xy=(np.pi/2, 1.0),          # Arrow points here
             xytext=(np.pi/2 + 3, 0.8),           # Text here
             arrowprops=dict(arrowstyle='->', color='red', lw=1.5),
             fontsize=11, color='red')
plt.show()
```

## Saving Figures

```python
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot([1, 2, 3], [1, 4, 9])

plt.savefig('plot.png', dpi=300, bbox_inches='tight')
# bbox_inches='tight' removes excess whitespace
# dpi=300 gives high resolution for print
# Supported formats: png, jpg, pdf, svg

plt.savefig('plot.pdf', format='pdf', bbox_inches='tight')  # Vector format
```

## Style Sheets

```python
print(plt.style.available)  # List all available styles
plt.style.use('seaborn-v0_8-darkgrid')      # Apply a style globally
# Try: 'ggplot', 'fivethirtyeight', 'seaborn-v0_8-whitegrid', 'dark_background'

# Reset to default
plt.style.use('default')
```

## Chinese Font Handling

Chinese characters often render as empty boxes by default. Here is how to fix it:

```python
import matplotlib.pyplot as plt

# Check available fonts that support Chinese
import matplotlib.font_manager as fm
chinese_fonts = [f.name for f in fm.fontManager.ttflist if any(
    keyword in f.name for keyword in ['SimHei', 'KaiTi', 'Microsoft YaHei', 'Noto Sans CJK']
)]
print(chinese_fonts)

# Method 1: Set globally
plt.rcParams['font.sans-serif'] = ['SimHei']  # or 'Microsoft YaHei', 'WenQuanYi Micro Hei'
plt.rcParams['axes.unicode_minus'] = False    # Fix minus sign display

# Method 2: Set for specific text elements
plt.title('中文标题', fontfamily='SimHei')

# Method 3: Use a font file directly
from matplotlib.font_manager import FontProperties
zh_font = FontProperties(fname='C:/Windows/Fonts/msyh.ttc', size=12)
plt.title('中文标题', fontproperties=zh_font)
```

## Seaborn Quick Reference

Seaborn is built on Matplotlib and provides high-level statistical visualizations:

```python
import seaborn as sns
import pandas as pd

# Load a built-in dataset
tips = sns.load_dataset('tips')

# Heatmap (correlation matrix)
corr = tips.corr(numeric_only=True)
sns.heatmap(corr, annot=True, cmap='coolwarm', center=0, fmt='.2f')
plt.title('Correlation Heatmap')
plt.show()

# Pair plot (scatter matrix with distributions)
sns.pairplot(tips, hue='day', diag_kind='hist')
plt.show()

# Distribution plot
sns.histplot(tips['total_bill'], kde=True, bins=30)  # kde=True adds density curve
plt.show()

# Box plot grouped by category
sns.boxplot(x='day', y='total_bill', data=tips, palette='Set2')
plt.show()

# Violin plot (boxplot + density)
sns.violinplot(x='day', y='total_bill', data=tips, inner='quartile')
plt.show()
```

## Common Visualization Pattern

```python
# Data analysis workflow with visualization
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# 1. Distribution of a variable
axes[0, 0].hist(data, bins=30, color='steelblue', edgecolor='white', alpha=0.8)
axes[0, 0].set_title('Distribution'); axes[0, 0].set_xlabel('Value'); axes[0, 0].set_ylabel('Frequency')

# 2. Trend over time
axes[0, 1].plot(dates, values, marker='o', linewidth=2, markersize=4)
axes[0, 1].set_title('Trend Over Time'); axes[0, 1].tick_params(axis='x', rotation=45)

# 3. Comparison across categories
axes[1, 0].bar(categories, group_a, label='Group A', alpha=0.8)
axes[1, 0].bar(categories, group_b, bottom=group_a, label='Group B', alpha=0.8)  # Stacked
axes[1, 0].legend(); axes[1, 0].set_title('Category Comparison')

# 4. Relationship between two variables
axes[1, 1].scatter(x_var, y_var, alpha=0.6, edgecolors='white')
axes[1, 1].set_title('Relationship'); axes[1, 1].set_xlabel('X'); axes[1, 1].set_ylabel('Y')

plt.tight_layout()
plt.show()
```
