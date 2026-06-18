import { useState, useRef } from 'react'
import { Typography, Input, Select, Button, Empty, Row, Col, message, Modal } from 'antd'
import {
  SearchOutlined, ThunderboltOutlined, FileTextOutlined,
  EditOutlined, CodeOutlined, ReloadOutlined,
} from '@ant-design/icons'
import ResourceCard from '../components/ResourceCard'
import MarkdownRenderer from '../components/MarkdownRenderer'
import ProgressBar from '../components/ProgressBar'
import { useTaskStatus } from '../hooks/useTaskStatus'
import { generateResources, getTaskStatus } from '../api/resource'
import { shouldUseMock } from '../utils/useMock'

const USE_MOCK = shouldUseMock()

const { Text } = Typography

const DIFFICULTY_OPTIONS = [
  { value: 'beginner', label: '初级' },
  { value: 'intermediate', label: '中级' },
  { value: 'advanced', label: '高级' },
]

const DIFFICULTY_COLORS = {
  beginner: '#22c55e',
  intermediate: '#f59e0b',
  advanced: '#ef4444',
}

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
  const defaultTopic = '二次函数'
  const [topic, setTopic] = useState(defaultTopic)
  const [difficulty, setDifficulty] = useState('intermediate')
  const [selectedTypes, setSelectedTypes] = useState(['document', 'exercise', 'code'])
  const [detailResource, setDetailResource] = useState(null)

  // 页面初始 Mock 展示（仅在 VITE_USE_MOCK=true 时启用）
  const [initialResources] = useState(() =>
    USE_MOCK
      ? generateMockResources(defaultTopic, 'intermediate', ['document', 'exercise', 'code'])
      : [],
  )

  // Mock 轮询计数器：模拟渐进式任务进度
  const mockPollRef = useRef(0)

  // 异步任务轮询 — Mock 模式模拟完整生命周期，真实模式轮询后端
  const {
    status, result, error,
    progress, taskMessage,
    startPolling, reset,
  } = useTaskStatus(async (taskId) => {
    // ── Mock 路径：模拟 6 次轮询后完成任务 ──
    if (USE_MOCK) {
      mockPollRef.current += 1
      const count = mockPollRef.current

      if (count <= 2) {
        return { status: 'running', progress: count * 15, message: '看看你想学什么…' }
      }
      if (count <= 4) {
        return { status: 'running', progress: 30 + (count - 2) * 15, message: '整理相关资料中…' }
      }
      if (count <= 6) {
        return { status: 'running', progress: 60 + (count - 4) * 20, message: '最后润色一下…' }
      }
      // 完成任务：返回 Mock 资源
      const resources = generateMockResources(topic, difficulty, selectedTypes)
      return { status: 'completed', progress: 100, message: '好了，帮你准备了 ' + resources.length + ' 份资料', result: resources }
    }

    // ── 真实路径：轮询后端 ──
    const data = await getTaskStatus(taskId)
    return {
      status: data.status === 'done' ? 'completed' : data.status,
      result: data.result,
      error: data.error,
      progress: data.progress ?? 0,
      message: data.message ?? '',
    }
  })

  const isRunning = status === 'pending' || status === 'running'
  const isCompleted = status === 'completed'
  const isFailed = status === 'failed'

  /** 点击生成 — Mock 模式模拟异步任务，真实模式调后端接口 */
  async function handleGenerate() {
    if (!topic.trim()) {
      message.warning('请输入学习主题')
      return
    }
    if (selectedTypes.length === 0) {
      message.warning('请至少选择一种资源类型')
      return
    }

    try {
      if (USE_MOCK) {
        // Mock: 重置计数器，直接用虚拟 task_id 启动轮询
        mockPollRef.current = 0
        startPolling('mock-task-' + Date.now())
        return
      }

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
    })
  }

  return (
    <div style={{ maxWidth: 960, margin: '0 auto', padding: 24 }}>
      {/* ── 参数输入区 ── */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 10,
        marginBottom: 24,
      }}>
        <Input
          placeholder="输入学习主题，如：二次函数"
          prefix={<SearchOutlined style={{ color: '#8b5cf6' }} />}
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          onPressEnter={handleGenerate}
          style={{ flex: 1, minWidth: 180, borderRadius: 8 }}
          allowClear
          disabled={isRunning}
        />
        <Select
          value={difficulty}
          onChange={setDifficulty}
          style={{ width: 100, borderRadius: 8 }}
          popupMatchSelectWidth={false}
          disabled={isRunning}
        >
          {DIFFICULTY_OPTIONS.map((opt) => (
            <Select.Option key={opt.value} value={opt.value}
              label={
                <span style={{ color: DIFFICULTY_COLORS[opt.value], fontWeight: 500 }}>
                  {opt.label}
                </span>
              }
            >
              <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{
                  width: 8, height: 8, borderRadius: '50%',
                  background: DIFFICULTY_COLORS[opt.value],
                  flexShrink: 0,
                }} />
                <span>{opt.label}</span>
              </span>
            </Select.Option>
          ))}
        </Select>
        <Select
          mode="multiple"
          value={selectedTypes}
          onChange={setSelectedTypes}
          options={TYPE_OPTIONS}
          style={{ width: 130, borderRadius: 8 }}
          placeholder="资源类型"
          disabled={isRunning}
          optionRender={(option) => (
            <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ color: '#8b5cf6' }}>{TYPE_ICONS[option.value]}</span>
              <span>{option.label}</span>
            </span>
          )}
          tagRender={({ value, closable, onClose }) => (
            <span
              style={{ display: 'inline-flex', alignItems: 'center', color: '#8b5cf6', marginRight: 2 }}
              onMouseDown={(e) => { e.preventDefault(); e.stopPropagation() }}
            >
              {TYPE_ICONS[value]}
            </span>
          )}
        />
        <Button
          type="primary"
          icon={<ThunderboltOutlined />}
          onClick={handleGenerate}
          loading={isRunning}
          disabled={isRunning}
          style={{
            background: 'linear-gradient(135deg, #8b5cf6, #6366f1)',
            border: 'none',
            borderRadius: 8,
            minWidth: 120,
            flexShrink: 0,
          }}
        >
          {isRunning ? '生成中...' : '生成资源'}
        </Button>
      </div>

      {/* ── 生成进度区 ── */}
      {isRunning && (
        <div style={{
          background: '#fff', borderRadius: 12, padding: '24px 32px',
          border: '1px solid #f0f0f0',
        }}>
          <ProgressBar
            status={status}
            percent={progress}
            steps={buildSteps()}
            message={taskMessage || '准备中…'}
            error={error}
          />
        </div>
      )}

      {/* ── 失败区 ── */}
      {isFailed && (
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          justifyContent: 'center', minHeight: 320,
          background: '#fafafa', borderRadius: 12, gap: 16,
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
            minHeight: 320, background: '#fafafa', borderRadius: 12,
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
            minHeight: 320, background: '#fafafa', borderRadius: 12,
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
        width={800}
        style={{ top: 24 }}
        styles={{ body: { maxHeight: '70vh', overflow: 'auto', padding: '24px 32px' } }}
      >
        {detailResource && <MarkdownRenderer content={detailResource.content} />}
      </Modal>
    </div>
  )
}
