/**
 * 学习评估仪表盘 —— 数据接入层
 *
 * 真实接口：GET /api/evaluate/assessment-dashboard
 * 当接口失败时回退到 MOCK_DATA，保证页面可用（便于离线/后端异常时调试）。
 */

import client from '../api/client'

const MOCK_DATA = {
  overview: {
    overall_mastery: 72,
    mastery_change: 6,
    stage_completion: 67,
    completion_change: 12,
    latest_score: 78,
    score_change: 9,
    weak_knowledge_count: 3,
    weak_change: -1,
  },
  knowledge_mastery: [
    { name: '数学基础', mastery: 72 },
    { name: '梯度计算', mastery: 58 },
    { name: '神经网络', mastery: 81 },
    { name: 'CNN', mastery: 65 },
    { name: '模型训练', mastery: 76 },
    { name: '代码实践', mastery: 54 },
  ],
  diagnosis: {
    strengths: [
      { name: '神经网络基本结构', mastery: 86 },
      { name: '激活函数', mastery: 82 },
      { name: '损失函数', mastery: 79 },
    ],
    weaknesses: [
      { name: '多元函数梯度', mastery: 48, reason: '多次混淆梯度方向与负梯度方向' },
      { name: '反向传播链式法则', mastery: 53, reason: '公式理解不稳定，步骤易出错' },
      { name: '代码实现', mastery: 54, reason: '对框架 API 熟练度不足' },
    ],
  },
  trend: {
    labels: ['第1次', '第2次', '第3次', '第4次', '第5次'],
    score_series: [62, 68, 71, 75, 78],
    mastery_series: [55, 60, 63, 68, 72],
    completion_series: [20, 35, 48, 59, 67],
  },
  error_distribution: [
    { name: '概念理解错误', value: 35 },
    { name: '公式使用错误', value: 28 },
    { name: '计算错误', value: 20 },
    { name: '代码实现错误', value: 17 },
  ],
  weak_points: [
    {
      knowledge_point_id: 'kp_gradient_direction',
      name: '梯度方向判断',
      mastery: 48,
      evidence: [
        '最近5道相关题目答错3道',
        '两次将梯度方向理解为下降最快方向',
      ],
      reason: '对梯度几何意义理解不足',
      suggestions: [
        '重新学习"梯度与等高线"讲义',
        '完成梯度方向专项练习',
        '通过图示方式再次理解梯度方向',
      ],
      actions: {
        review_resource_id: 'resource_102',
        exercise_task_id: 'task_203',
      },
    },
    {
      knowledge_point_id: 'kp_chain_rule',
      name: '反向传播链式法则',
      mastery: 53,
      evidence: [
        '链式法则复合函数求导步骤出错',
        '两次测验中该知识点得分低于 60',
      ],
      reason: '公式理解不稳定，复合函数分解步骤易出错',
      suggestions: [
        '复习链式法则基本原理',
        '完成反向传播推导专项练习',
        '观看链式法则动画演示',
      ],
      actions: {
        review_resource_id: 'resource_108',
        exercise_task_id: 'task_210',
      },
    },
    {
      knowledge_point_id: 'kp_framework_api',
      name: '框架 API 使用',
      mastery: 54,
      evidence: [
        '代码题中 3 次因 API 用法错误导致运行失败',
        '对 PyTorch 张量操作不熟练',
      ],
      reason: '对深度学习框架 API 熟练度不足',
      suggestions: [
        '重新学习 PyTorch 张量基础操作',
        '完成框架 API 速查练习',
        '在代码实验环境中多加练习',
      ],
      actions: {
        review_resource_id: 'resource_115',
        exercise_task_id: 'task_218',
      },
    },
  ],
  improvement_plan: [
    { day: '今天', title: '重新学习梯度的几何意义', duration: '15分钟', type: 'learn' },
    { day: '今天', title: '复习链式法则基本原理', duration: '10分钟', type: 'learn' },
    { day: '明天', title: '完成梯度方向专项练习', duration: '10分钟', type: 'practice' },
    { day: '明天', title: '完成反向传播推导练习', duration: '15分钟', type: 'practice' },
    { day: '后天', title: '进行一次梯度基础小测', duration: '20分钟', type: 'test' },
    { day: '大后天', title: 'PyTorch 张量操作实战', duration: '20分钟', type: 'practice' },
  ],
}

/**
 * 获取学习评估仪表盘数据
 * @param {object} params - { courseId, scope, studentId }
 * @returns {Promise<object>}
 */
export async function fetchAssessmentDashboard(params = {}) {
  const { courseId, scope, studentId } = params
  try {
    return await client.get('/evaluate/assessment-dashboard', {
      params: {
        student_id: studentId,
        course_id: courseId,
        scope,
      },
    })
  } catch (err) {
    // 后端异常时回退到 Mock 数据，保证页面可渲染
    // eslint-disable-next-line no-console
    console.warn('[assessment] 接口失败，回退到 Mock 数据：', err?.message || err)
    return { ...MOCK_DATA }
  }
}

export default MOCK_DATA
