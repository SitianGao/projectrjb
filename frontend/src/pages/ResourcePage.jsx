<<<<<<< Updated upstream
import { useState, useRef } from 'react'
import { Typography, Input, Select, Button, Empty, Row, Col, message, Modal } from 'antd'
import {
  SearchOutlined, ThunderboltOutlined, FileTextOutlined,
  EditOutlined, CodeOutlined, ReloadOutlined,
=======
import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Typography, Input, Select, Button, Empty, Row, Col, Space, Tabs,
  Tag, Card, Skeleton, Result, Dropdown, message, Modal,
} from 'antd'
import {
  SearchOutlined, ThunderboltOutlined, FileTextOutlined,
  EditOutlined, CodeOutlined, FilePptOutlined, SoundOutlined,
  BranchesOutlined, DownloadOutlined, StarOutlined, StarFilled,
  MoreOutlined, ClockCircleOutlined, CheckCircleOutlined,
  BookOutlined, ReloadOutlined, FilterOutlined, InboxOutlined,
>>>>>>> Stashed changes
} from '@ant-design/icons'
import MarkdownRenderer from '../components/MarkdownRenderer'
<<<<<<< Updated upstream
import ProgressBar from '../components/ProgressBar'
import { useTaskStatus } from '../hooks/useTaskStatus'
import { generateResources, getTaskStatus } from '../api/resource'
import { shouldUseMock } from '../utils/useMock'
=======
import ResourceGenerateDrawer from '../components/ResourceGenerateDrawer'
import { useResources } from '../hooks/useResources'
import { useAuth } from '../contexts/AuthContext'
import { normalizeTitle, getResourceStats } from '../utils/resourceNormalizer'
>>>>>>> Stashed changes

const { Text, Title, Paragraph } = Typography

const TYPE_CONFIG = {
  document: { icon: <FileTextOutlined />, color: 'blue', label: '讲义' },
  exercise: { icon: <EditOutlined />, color: 'green', label: '练习题' },
  code: { icon: <CodeOutlined />, color: 'red', label: '代码' },
  mindmap: { icon: <BranchesOutlined />, color: 'purple', label: '思维导图' },
  ppt: { icon: <FilePptOutlined />, color: 'magenta', label: 'PPT' },
  audio: { icon: <SoundOutlined />, color: 'geekblue', label: '音频' },
  reading: { icon: <BookOutlined />, color: 'cyan', label: '阅读' },
}

<<<<<<< Updated upstream
const TYPE_OPTIONS = [
  { value: 'document', label: '文档' },
  { value: 'exercise', label: '练习题' },
  { value: 'code', label: '代码' },
]

const TYPE_ICONS = {
  document: <FileTextOutlined />,
  exercise: <EditOutlined />,
  code: <CodeOutlined />,
}

/** 模拟生成资源（页面初始展示用） */
function generateMockResources(topic, difficulty, types) {
  const diffLabel = DIFFICULTY_OPTIONS.find((d) => d.value === difficulty)?.label || '中级'

  const templates = {
    document: {
      title: `${topic} — 知识点详解`,
      description: `${topic}核心概念梳理与知识框架`,
      content: `# 📖 ${topic} 知识点详解

> **难度等级**：${diffLabel}　|　**预计阅读**：15 分钟　|　**标签**：#${topic} #基础

---

## 1. 概述

本文系统梳理 **${topic}** 的核心知识点，涵盖从基础定义到实际应用的完整链路。

---

## 2. 核心概念

### 2.1 基础定义

| 术语 | 定义 | 示例 |
|:---|:---|:---|
| 变量 | 可变化的量，用字母表示 | \`x, y, t\` |
| 常量 | 固定不变的数值 | \`π ≈ 3.14159\` |
| 函数 | 变量之间的映射关系 | \`f(x) = x²\` |

### 2.2 重要性质

- **封闭性**：集合内任意两个元素运算结果仍在集合内
- **结合律**：\`(a + b) + c = a + (b + c)\`
- **分配律**：\`a × (b + c) = a × b + a × c\`

### 2.3 核心定理

> 💡 **核心定理**：若函数 \`f(x)\` 在区间 \`[a, b]\` 上连续，在 \`(a, b)\` 内可导，则存在一点 \`ξ ∈ (a, b)\` 使得 \`f'(ξ) = (f(b) - f(a)) / (b - a)\`。

---

## 3. 知识体系

| 模块 | 内容概要 | 重要程度 | 掌握要求 |
|:---|:---|:---:|:---|
| 基础理论 | 定义、公理、定理推导 | ⭐⭐⭐ | 熟练掌握 |
| 公式推导 | 常用公式的推导与应用 | ⭐⭐⭐ | 理解并记忆 |
| 计算技巧 | 快速计算方法汇总 | ⭐⭐ | 灵活运用 |
| 实际应用 | 工程与生活中的案例 | ⭐⭐ | 了解即可 |
| 拓展阅读 | 高等数学中的延伸 | ⭐ | 选学 |

---

## 4. 学习路线

\`\`\`mermaid
graph LR
    A[基础概念] --> B[公式推导]
    B --> C[典型例题]
    C --> D[综合练习]
    D --> E[实际应用]
\`\`\`

---

## 5. 常见误区

- [ ] ~~死记硬背公式而不理解推导过程~~
- [x] 先理解原理，再通过练习巩固记忆
- [ ] ~~只看例题不动手演算~~
- [x] 独立完成至少 3 道同类题目

---

## 6. 参考资源

- [MDN Web Docs](https://developer.mozilla.org/) — 前端技术文档
- [Khan Academy](https://www.khanacademy.org/) — 免费公开课

---

> 🎯 **学习建议**：每天投入 30 分钟，坚持一周即可掌握本章核心内容。`,
    },
    exercise: {
      title: `${topic} — 专项练习`,
      description: `${topic}精选练习题，巩固知识`,
      content: `# ✍️ ${topic} 专项练习

> **难度等级**：${diffLabel}　|　**题量**：3 道　|　**建议用时**：30 分钟

---

## 题目一 · 基础计算

已知函数 \`f(x) = x² + 2x + 1\`，请回答以下问题：

1. 求 \`f(x)\` 的最小值
2. 求取得最小值时 \`x\` 的值
3. 画出函数图像的草图（描述对称轴和开口方向）

### 💡 解题提示

| 方法 | 步骤 | 难度 |
|:---|:---|:---:|
| **配方法** | \`f(x) = (x+1)² + 0\` | 简单 |
| **求导法** | 令 \`f'(x) = 0\` 即 \`2x + 2 = 0\` | 中等 |
| **公式法** | 顶点公式 \`x = -b/(2a)\` | 简单 |

---

## 题目二 · 实际应用

> 📦 某商品定价 **100 元** 时月销量 **200 件**。市场调研表明：**每降价 1 元，销量增加 10 件**；每提价 1 元，销量减少 8 件。成本为每件 40 元。

1. 建立利润 \`P(x)\` 关于调价幅度 \`x\` 的函数（\`x > 0\` 表示降价）
2. 求利润最大时的定价
3. 最大利润是多少？

### 📝 答题模板

\`\`\`text
解：
已知：原价 = 100，成本 = 40，降价 x 元
销量 = 200 + 10x
利润 = (售价 - 成本) × 销量
     = (100 - x - 40) × (200 + 10x)
     = (60 - x)(200 + 10x)
     = ...
\`\`\`

---

## 题目三 · 代码验证

用你熟悉的编程语言验证题目二的结论：

\`\`\`python
def max_profit():
    """计算最大利润及对应定价"""
    best_price = 100
    max_p = 0

    for price in range(50, 150):
        diff = 100 - price
        sales = 200 + (10 if diff > 0 else -8) * abs(diff)
        profit = (price - 40) * sales
        if profit > max_p:
            max_p = profit
            best_price = price

    return best_price, max_p

if __name__ == '__main__':
    price, profit = max_profit()
    print(f"最优定价: {price} 元")
    print(f"最大利润: {profit} 元")
\`\`\`

---

## 📋 参考答案

| 题目 | 答案 | 分值 |
|:---|:---|:---:|
| 题目一 (1) | \`f(x)ₘᵢₙ = 0\` | 5 分 |
| 题目一 (2) | \`x = -1\` | 5 分 |
| 题目二 (2) | 定价 **60 元** | 10 分 |
| 题目二 (3) | 最大利润 **4000 元** | 5 分 |

> ✅ 全部答对？恭喜你已掌握 ${topic} 的核心计算！`,
    },
    code: {
      title: `${topic} — 代码实现`,
      description: `${topic}相关算法的代码实现`,
      content: `# 💻 ${topic} 代码实现

> **语言**：Python / JavaScript / SQL　|　**难度**：${diffLabel}

---

## 1. Python 实现

### 1.1 核心算法

\`\`\`python
from typing import List


def solve(input_data: List[int]) -> int:
    """
    ${topic} 核心算法

    Args:
        input_data: 输入整数列表

    Returns:
        计算结果（平方和）
    """
    result = 0
    for i in range(len(input_data)):
        result += input_data[i] ** 2
    return result


if __name__ == '__main__':
    test_data = [1, 2, 3, 4, 5]
    print(f"输入: {test_data}")
    print(f"输出: {solve(test_data)}")
\`\`\`

### 1.2 一行写法（函数式）

\`\`\`python
solve = lambda arr: sum(x ** 2 for x in arr)

# 测试
print(solve([1, 2, 3]))  # 输出: 14
print(solve([10, 20, 30]))  # 输出: 1400
\`\`\`

---

## 2. JavaScript 实现

\`\`\`javascript
/**
 * ${topic} 核心算法
 * @param {number[]} arr - 输入数组
 * @returns {number} 平方和
 */
function solve(arr) {
  return arr.reduce((sum, x) => sum + x ** 2, 0);
}

// 测试用例
console.log(solve([1, 2, 3]));       // 14
console.log(solve([10, 20, 30]));    // 1400
console.log(solve([]));              // 0
\`\`\`

---

## 3. 复杂度分析

| 指标 | 大 O 表示 | 说明 |
|:---|:---:|:---|
| ⏱ 时间复杂度 | \`O(n)\` | 需要遍历一次数组 |
| 📦 空间复杂度 | \`O(1)\` | 仅使用常量额外空间 |
| 🔁 稳定性 | ✅ 稳定 | 无副作用，幂等操作 |

---

## 4. 边界测试

\`\`\`python
import pytest


def test_empty():
    """空数组应返回 0"""
    assert solve([]) == 0


def test_single():
    """单元素数组"""
    assert solve([5]) == 25


def test_negative():
    """负数平方后为正"""
    assert solve([-1, -2, -3]) == 14


def test_large():
    """大数值测试"""
    assert solve([1000, 2000]) == 5_000_000
\`\`\`

---

## 5. SQL 示例

\`\`\`sql
-- 统计每位学生的成绩平方和
SELECT
    student_id,
    SUM(score * score) AS score_square_sum
FROM exam_results
WHERE exam_date >= '2025-01-01'
GROUP BY student_id
HAVING SUM(score * score) > 10000
ORDER BY score_square_sum DESC
LIMIT 10;
\`\`\`

---

> 🔗 完整代码仓库：[GitHub - ${topic} Examples](https://github.com/example)`,
    },
  }

  return types.map((t) => ({
    id: `${t}-${Date.now()}`,
    type: t,
    title: templates[t]?.title || `${topic} — 资源`,
    description: templates[t]?.description || '',
    content: templates[t]?.content || '',
    tags: [topic, diffLabel],
    createdAt: new Date(),
  }))
}

/**
 * 学习资源页
 * - 接入 useTaskStatus 轮询异步任务进度
 * - 生成中显示 ProgressBar + 阶段文案，按钮禁用
 * - 完成后自动替换为资源卡片
 * - 失败时显示重试按钮
 */
export default function ResourcePage() {
  const [topic, setTopic] = useState('')
  const [difficulty, setDifficulty] = useState('intermediate')
  const [selectedTypes, setSelectedTypes] = useState(['document', 'exercise', 'code'])
  const [detailResource, setDetailResource] = useState(null)
=======
const DIFFICULTY_COLORS = { '初级': 'green', '中级': 'orange', '高级': 'red' }

export default function ResourcePage() {
  const navigate = useNavigate()
  const { courses } = useAuth()

  // ── Filters ──
  const [keyword, setKeyword] = useState('')
  const [filterCourse, setFilterCourse] = useState('')
  const [filterType, setFilterType] = useState('')
  const [filterDifficulty, setFilterDifficulty] = useState('')
  const [sortBy, setSortBy] = useState('recent')
  const [activeTab, setActiveTab] = useState('all')
>>>>>>> Stashed changes

  // ── Generate drawer ──
  const [genDrawerOpen, setGenDrawerOpen] = useState(false)
  const [genContext, setGenContext] = useState({ source: 'global' })

  // ── Favorites ──
  const [favorites, setFavorites] = useState(new Set())

  // ── Data ──
  const { data: resources, total, loading, error, reload } = useResources({
    courseId: filterCourse || undefined,
    type: filterType || undefined,
    difficulty: filterDifficulty || undefined,
    keyword: keyword || undefined,
    sort: sortBy,
  })

  const filtered = useMemo(() => {
    let list = resources
    if (activeTab === 'recent') {
      list = list.slice(0, 5)
    } else if (activeTab === 'favorites') {
      list = list.filter((r) => favorites.has(r.id))
    }
    return list
  }, [resources, activeTab, favorites])

  const tabItems = [
    { key: 'all', label: `全部资源 ${total}` },
    { key: 'recent', label: '最近生成' },
    { key: 'favorites', label: `我的收藏 ${favorites.size}` },
  ]

<<<<<<< Updated upstream
      const diffLabel = DIFFICULTY_OPTIONS.find((d) => d.value === difficulty)?.label || '中级'
      const data = await generateResources({
        student_id: 'demo-student-01',
        topic: topic.trim(),
        types: selectedTypes,
        difficulty: diffLabel,
      })

      if (data.task_id) {
        startPolling(data.task_id)
      } else {
        message.error('未获取到任务 ID')
      }
    } catch (err) {
      message.error('生成请求失败: ' + (err.message || '未知错误'))
    }
  }

  /** 失败后重试 */
  function handleRetry() {
    if (USE_MOCK) {
      mockPollRef.current = 0
      startPolling('mock-task-retry-' + Date.now())
      return
    }
    reset()
    handleGenerate()
  }

  /** 从 result 中提取资源列表 */
  const resultResources = (() => {
    if (!isCompleted || !result) return []
    if (Array.isArray(result)) return result
    return result.items || result.resources || []
  })()

  /** 根据进度百分比推演步骤状态 */
  function buildSteps() {
    const phaseLabels = [
      { key: 'understand', label: '了解主题' },
      { key: 'prepare', label: '准备资料' },
      { key: 'polish', label: '排版整理' },
    ]
    return phaseLabels.map((phase, i) => {
      const threshold = (i + 1) / phaseLabels.length * 100
      if (progress >= threshold || isCompleted) return { ...phase, status: 'finish' }
      if (progress >= i / phaseLabels.length * 100 && isRunning) return { ...phase, status: 'process' }
      return { ...phase, status: 'wait' }
=======
  const toggleFavorite = (id) => {
    setFavorites((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
>>>>>>> Stashed changes
    })
  }

  return (
    <div style={{ minHeight: '100%', background: '#F6F7FB', padding: '20px 24px 48px' }}>
      <div style={{ maxWidth: 1440, margin: '0 auto' }}>

        {/* ── Header ── */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16, marginBottom: 24 }}>
          <div>
            <Title level={3} style={{ margin: 0, color: '#111827' }}>资源中心</Title>
            <Text style={{ color: '#6B7280', fontSize: 14 }}>
              生成、管理并复用你的个性化学习资源
            </Text>
          </div>
          <Button type="primary" size="large" icon={<ThunderboltOutlined />}
            onClick={() => { setGenContext({ source: 'global' }); setGenDrawerOpen(true) }}
            style={{ borderRadius: 10, background: '#6C5CE7', borderColor: '#6C5CE7' }}>
            生成新资源
          </Button>
        </div>

        {/* ── Filter bar ── */}
        <Card style={{ borderRadius: 16, marginBottom: 20, border: '1px solid #E5E7EB' }}
          styles={{ body: { padding: '14px 20px' } }}>
          <Space size={12} wrap style={{ width: '100%' }}>
            <Input prefix={<SearchOutlined style={{ color: '#6C5CE7' }} />}
              placeholder="搜索资源名称、主题、知识点"
              value={keyword} onChange={(e) => setKeyword(e.target.value)}
              style={{ width: 260, borderRadius: 8 }} allowClear />
            <Select placeholder="全部课程" value={filterCourse} onChange={setFilterCourse}
              allowClear style={{ width: 140, borderRadius: 8 }}
              options={(courses || []).map((c) => ({ label: c.title, value: c.id }))} />
            <Select placeholder="全部类型" value={filterType} onChange={setFilterType}
              allowClear style={{ width: 120, borderRadius: 8 }}
              options={Object.entries(TYPE_CONFIG).map(([k, v]) => ({ label: v.label, value: k }))} />
            <Select placeholder="全部难度" value={filterDifficulty} onChange={setFilterDifficulty}
              allowClear style={{ width: 110, borderRadius: 8 }}
              options={[{ label: '初级', value: '初级' }, { label: '中级', value: '中级' }, { label: '高级', value: '高级' }]} />
            <Select value={sortBy} onChange={setSortBy} style={{ width: 130, borderRadius: 8 }}
              options={[
                { label: '最近生成', value: 'recent' },
                { label: '最近使用', value: 'used' },
                { label: '最多访问', value: 'views' },
                { label: '名称排序', value: 'name' },
              ]} />
            <Button icon={<ReloadOutlined />} onClick={reload} style={{ borderRadius: 8 }} />
          </Space>
        </Card>

        {/* ── Tabs ── */}
        <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems}
          style={{ marginBottom: 16 }} />

        {/* ── Content ── */}
        {loading ? (
          <Skeleton active paragraph={{ rows: 4 }} />
        ) : error ? (
          <Result status="error" title="资源加载失败" subTitle={error}
            extra={<Button type="primary" icon={<ReloadOutlined />} onClick={reload}>重试</Button>} />
        ) : filtered.length === 0 ? (
          <Card style={{ borderRadius: 16, textAlign: 'center', padding: 48, border: '1px solid #E5E7EB' }}>
            <InboxOutlined style={{ fontSize: 48, color: '#D1D5DB', marginBottom: 16 }} />
            <Title level={4} style={{ color: '#111827' }}>还没有学习资源</Title>
            <Paragraph style={{ color: '#6B7280', maxWidth: 460, margin: '0 auto 20px' }}>
              你可以选择一门课程和学习主题，生成讲义、练习题、PPT 或思维导图。
              生成的资源会自动保存到此处，并可关联到具体课程和阶段。
            </Paragraph>
            <Button type="primary" size="large" icon={<ThunderboltOutlined />}
              onClick={() => { setGenContext({ source: 'global' }); setGenDrawerOpen(true) }}
              style={{ borderRadius: 8, background: '#6C5CE7' }}>
              生成第一个资源
            </Button>
          </Card>
        ) : (
          <Row gutter={[16, 16]}>
            {filtered.map((res) => {
              const cfg = TYPE_CONFIG[res.type] || TYPE_CONFIG.document
              const isFav = favorites.has(res.id)
              return (
                <Col xs={24} sm={12} lg={8} xl={6} key={res.id}>
                  <Card
                    hoverable
                    style={{ borderRadius: 12, border: '1px solid #E5E7EB', height: '100%', minWidth: 0 }}
                    styles={{ body: { padding: '16px 18px' } }}
                    onClick={() => navigate(`/resources/${res.id}`)}
                  >
                    {/* Type + difficulty */}
                    <Space size={4} style={{ marginBottom: 8 }}>
                      <Tag icon={cfg.icon} color={cfg.color} style={{ borderRadius: 6, margin: 0 }}>{cfg.label}</Tag>
                      {res.difficulty && <Tag color={DIFFICULTY_COLORS[res.difficulty] || 'default'} style={{ borderRadius: 6, margin: 0 }}>{res.difficulty}</Tag>}
                      {res.stage_id && <Tag style={{ borderRadius: 6, margin: 0 }}>阶段{res.stage_id}</Tag>}
                    </Space>

                    {/* Title */}
                    <Text strong style={{ fontSize: 14, color: '#111827', display: 'block', marginBottom: 6 }}
                      ellipsis={{ rows: 2 }}>{normalizeTitle(res.title, res.type, res.topic)}</Text>
                    {/* Stats */}
                    {(() => { const s = getResourceStats(res); return s ? <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 6 }}>{s.icon} {s.label}</Text> : null })()}

                    {/* Summary */}
                    {res.description && (
                      <Paragraph type="secondary" style={{ fontSize: 12, marginBottom: 8 }}
                        ellipsis={{ rows: 2 }}>{res.description}</Paragraph>
                    )}

                    {/* Meta */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto' }}>
                      <Text type="secondary" style={{ fontSize: 11 }}>
                        {res.createdAt ? new Date(res.createdAt).toLocaleDateString('zh-CN') : ''}
                      </Text>
                      <Space size={4}>
                        <Button size="small" type="text" icon={isFav ? <StarFilled style={{ color: '#F59E0B' }} /> : <StarOutlined />}
                          onClick={(e) => { e.stopPropagation(); toggleFavorite(res.id) }} />
                        <Dropdown menu={{ items: [
                          { key: 'view', label: '查看详情', onClick: () => navigate(`/resources/${res.id}`) },
                          { key: 'regenerate', label: '重新生成', onClick: () => { setGenContext({ source: 'global', courseId: res.course_id, topic: res.topic }); setGenDrawerOpen(true) } },
                        ]}} trigger={['click']}>
                          <Button size="small" type="text" icon={<MoreOutlined />} onClick={(e) => e.stopPropagation()} />
                        </Dropdown>
                      </Space>
                    </div>
                  </Card>
                </Col>
              )
            })}
          </Row>
        )}
      </div>

      {/* ── Generate Drawer ── */}
      <ResourceGenerateDrawer
        visible={genDrawerOpen}
        onClose={() => setGenDrawerOpen(false)}
        onGenerated={() => { reload(); setGenDrawerOpen(false) }}
        context={genContext}
      />

<<<<<<< Updated upstream
      {/* ── 失败区 ── */}
      {isFailed && (
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          justifyContent: 'center', minHeight: 320,
          background: 'var(--surface-secondary)', borderRadius: 12, gap: 16,
        }}>
          <ProgressBar
            status="failed"
            percent={progress}
            message={taskMessage || '生成失败'}
            error={error}
          />
          <Button
            type="primary"
            icon={<ReloadOutlined />}
            onClick={handleRetry}
            style={{ borderRadius: 8 }}
          >
            重新生成
          </Button>
        </div>
      )}

      {/* ── 结果区 / 初始 Mock 展示 ── */}
      {!isRunning && !isFailed && (
        isCompleted && resultResources.length > 0 ? (
          <Row gutter={[16, 16]}>
            {resultResources.map((r) => (
              <Col key={r.id} xs={24} md={8}>
                <ResourceCard resource={r} onClick={(res) => setDetailResource(res)} />
              </Col>
            ))}
          </Row>
        ) : isCompleted && resultResources.length === 0 ? (
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            minHeight: 320, background: 'var(--surface-secondary)', borderRadius: 12,
          }}>
            <Empty description={<Text type="secondary">没有匹配的资源</Text>} image={Empty.PRESENTED_IMAGE_SIMPLE} />
          </div>
        ) : initialResources.length > 0 ? (
          <Row gutter={[16, 16]}>
            {initialResources.map((r) => (
              <Col key={r.id} xs={24} md={8}>
                <ResourceCard resource={r} onClick={(res) => setDetailResource(res)} />
              </Col>
            ))}
          </Row>
        ) : (
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            minHeight: 320, background: 'var(--surface-secondary)', borderRadius: 12,
          }}>
            <Empty description={<Text type="secondary">暂无资源，先输入主题生成</Text>} image={Empty.PRESENTED_IMAGE_SIMPLE} />
          </div>
        )
      )}

      {/* ── 详情弹窗 ── */}
      <Modal
        title={detailResource?.title}
        open={!!detailResource}
        onCancel={() => setDetailResource(null)}
        footer={null}
        width={960}
        style={{ top: 40 }}
        styles={{ body: { maxHeight: '80vh', overflow: 'auto', padding: '24px 32px' } }}
      >
        {detailResource && <MarkdownRenderer content={detailResource.content} />}
      </Modal>
=======
>>>>>>> Stashed changes
    </div>
  )
}
