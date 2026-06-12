/**
 * 学习路径 Mock 数据 — 规划阶段使用
 */

// 知识点标签
export const SKILL_TAGS = {
  algebra: { label: '代数', color: '#1677ff' },
  geometry: { label: '几何', color: '#52c41a' },
  function: { label: '函数', color: '#722ed1' },
  statistics: { label: '统计', color: '#fa8c16' },
  calculus: { label: '微积分', color: '#eb2f96' },
  trig: { label: '三角', color: '#13c2c2' },
}

// 资源类型
export const RESOURCE_TYPES = {
  video: { label: '视频', icon: '📺' },
  article: { label: '文章', icon: '📄' },
  exercise: { label: '练习', icon: '✏️' },
  quiz: { label: '测验', icon: '📝' },
  project: { label: '项目', icon: '🔨' },
}

// 学习路径列表
export const mockPaths = [
  {
    id: 'path-001',
    title: '二次函数专项提升',
    subject: '数学',
    grade: '高中一年级',
    createdAt: '2026-06-01T08:00:00Z',
    updatedAt: '2026-06-10T15:30:00Z',
    totalNodes: 6,
    completedNodes: 3,
    totalDuration: '12h',
    spentDuration: '5h',
    overallProgress: 50,
    nodes: [
      {
        id: 'n1',
        title: '二次函数图像与性质',
        description: '掌握 y=ax²+bx+c 的标准形式，理解开口方向、对称轴、顶点坐标',
        status: 'completed',
        duration: '2h',
        skillTags: ['函数', '代数'],
        resources: [
          { type: 'video', title: '二次函数图像动画演示', url: '#', duration: '15min' },
          { type: 'exercise', title: '图像识别练习（20题）', url: '#', duration: '30min' },
        ],
        completedAt: '2026-06-02T14:00:00Z',
        score: 92,
      },
      {
        id: 'n2',
        title: '配方法与顶点式',
        description: '学会用配方法将一般式化为顶点式 y=a(x-h)²+k',
        status: 'completed',
        duration: '2.5h',
        skillTags: ['代数', '函数'],
        resources: [
          { type: 'video', title: '配方法步骤详解', url: '#', duration: '20min' },
          { type: 'article', title: '配方法技巧总结', url: '#', duration: '10min' },
          { type: 'exercise', title: '配方法专项练习（30题）', url: '#', duration: '45min' },
        ],
        completedAt: '2026-06-04T16:00:00Z',
        score: 85,
      },
      {
        id: 'n3',
        title: '二次函数与方程',
        description: '理解二次函数图像与一元二次方程根的关系，掌握判别式法',
        status: 'completed',
        duration: '2h',
        skillTags: ['函数', '代数'],
        resources: [
          { type: 'video', title: '函数与方程的关系', url: '#', duration: '18min' },
          { type: 'quiz', title: '函数与方程单元测验', url: '#', duration: '30min' },
        ],
        completedAt: '2026-06-07T10:00:00Z',
        score: 78,
      },
      {
        id: 'n4',
        title: '二次不等式求解',
        description: '利用二次函数图像解一元二次不等式，掌握区间表示法',
        status: 'in_progress',
        duration: '2.5h',
        skillTags: ['函数', '代数'],
        resources: [
          { type: 'video', title: '二次不等式图像解法', url: '#', duration: '22min' },
          { type: 'exercise', title: '不等式求解练习（25题）', url: '#', duration: '40min' },
          { type: 'article', title: '常见不等式解题模板', url: '#', duration: '12min' },
        ],
        completedAt: null,
        score: null,
      },
      {
        id: 'n5',
        title: '函数综合应用题',
        description: '综合运用二次函数知识，解决实际应用问题（最值、面积、利润等）',
        status: 'pending',
        duration: '3h',
        skillTags: ['函数', '几何'],
        resources: [
          { type: 'video', title: '应用题解题思路', url: '#', duration: '25min' },
          { type: 'project', title: '综合应用项目：设计最优方案', url: '#', duration: '1.5h' },
          { type: 'exercise', title: '综合应用题精选（15题）', url: '#', duration: '1h' },
        ],
        completedAt: null,
        score: null,
      },
      {
        id: 'n6',
        title: '章节综合测验',
        description: '完成二次函数全章测试，检验综合掌握程度',
        status: 'locked',
        duration: '1.5h',
        skillTags: ['函数', '代数', '几何'],
        resources: [
          { type: 'quiz', title: '二次函数综合测评', url: '#', duration: '1.5h' },
        ],
        completedAt: null,
        score: null,
      },
    ],
  },
  {
    id: 'path-002',
    title: '三角函数入门',
    subject: '数学',
    grade: '高中一年级',
    createdAt: '2026-06-08T10:00:00Z',
    updatedAt: '2026-06-10T12:00:00Z',
    totalNodes: 4,
    completedNodes: 1,
    totalDuration: '8h',
    spentDuration: '1.5h',
    overallProgress: 25,
    nodes: [
      {
        id: 't1',
        title: '角度与弧度制',
        description: '理解角度与弧度的概念及互化方法',
        status: 'completed',
        duration: '1.5h',
        skillTags: ['三角'],
        resources: [
          { type: 'video', title: '弧度制引入', url: '#', duration: '15min' },
          { type: 'exercise', title: '角度弧度互化练习', url: '#', duration: '25min' },
        ],
        completedAt: '2026-06-09T10:00:00Z',
        score: 88,
      },
      {
        id: 't2',
        title: '任意角三角函数定义',
        description: '掌握单位圆定义法，理解各象限符号规律',
        status: 'in_progress',
        duration: '2h',
        skillTags: ['三角', '函数'],
        resources: [
          { type: 'video', title: '单位圆与三角函数', url: '#', duration: '20min' },
          { type: 'article', title: '三角函数定义总结图', url: '#', duration: '8min' },
        ],
        completedAt: null,
        score: null,
      },
      {
        id: 't3',
        title: '三角函数图像',
        description: '绘制正弦、余弦、正切函数图像，理解周期性',
        status: 'pending',
        duration: '2.5h',
        skillTags: ['三角', '函数'],
        resources: [
          { type: 'video', title: '三角函数图像绘制', url: '#', duration: '22min' },
          { type: 'exercise', title: '图像绘制练习（20题）', url: '#', duration: '40min' },
        ],
        completedAt: null,
        score: null,
      },
      {
        id: 't4',
        title: '三角函数公式与应用',
        description: '掌握同角关系、诱导公式，解决三角恒等变换问题',
        status: 'locked',
        duration: '2h',
        skillTags: ['三角', '代数'],
        resources: [
          { type: 'video', title: '三角公式推导', url: '#', duration: '25min' },
          { type: 'quiz', title: '三角公式综合测试', url: '#', duration: '40min' },
        ],
        completedAt: null,
        score: null,
      },
    ],
  },
]

// 统计数据
export const mockStats = {
  totalPaths: 2,
  activePath: '二次函数专项提升',
  totalNodesCompleted: 4,
  totalNodesAll: 10,
  totalStudyTime: '6.5h',
  avgScore: 86,
  weeklyGoal: { completed: 4, total: 5 },
  streak: 5, // 连续学习天数
}

// 科目列表
export const subjects = [
  { key: 'math', label: '数学', icon: '📐', color: '#1677ff' },
  { key: 'physics', label: '物理', icon: '⚡', color: '#52c41a' },
  { key: 'chemistry', label: '化学', icon: '🧪', color: '#722ed1' },
  { key: 'english', label: '英语', icon: '📖', color: '#fa8c16' },
]
