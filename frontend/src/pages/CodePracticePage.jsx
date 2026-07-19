import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Layout, List, Tag, Space, Typography, Button, Input, Select,
  Empty, message, Spin,
} from 'antd'
import {
  SearchOutlined, SendOutlined, ReloadOutlined,
  CheckCircleFilled, RightOutlined, LeftOutlined,
} from '@ant-design/icons'
import ProblemPanel from '../components/ProblemPanel'
import CodeEditor from '../components/CodeEditor'
import JudgeResult from '../components/JudgeResult'
import { getProblems, getProblemDetail, submitCode } from '../api/judge'
import { useAuth } from '../contexts/AuthContext'
import LoadingSkeleton from '../components/LoadingSkeleton'
import { invalidateHomeDashboard } from '../utils/dashboardEvents'

const { Sider, Content } = Layout
const { Text } = Typography

const DIFFICULTY_OPTIONS = [
  { label: '全部难度', value: '' },
  { label: '简单', value: '简单' },
  { label: '中等', value: '中等' },
  { label: '困难', value: '困难' },
]

const LANGUAGE_STARTER = {
  c: '#include <stdio.h>\n\nint main() {\n    // 在此编写代码\n    return 0;\n}\n',
  cpp: '#include <iostream>\nusing namespace std;\n\nint main() {\n    // 在此编写代码\n    return 0;\n}\n',
  java: 'import java.util.*;\n\npublic class Main {\n    public static void main(String[] args) {\n        // 在此编写代码\n    }\n}\n',
  python: '# 在此编写代码\n',
}

export default function CodePracticePage() {
  const { problemId: routeProblemId } = useParams()
  const navigate = useNavigate()
  const { studentId, activeCourse } = useAuth()

  // Problem list
  const [problems, setProblems] = useState([])
  const [problemsLoading, setProblemsLoading] = useState(true)
  const [searchText, setSearchText] = useState('')
  const [filterDifficulty, setFilterDifficulty] = useState('')

  // Current problem
  const [currentProblem, setCurrentProblem] = useState(null)
  const [problemLoading, setProblemLoading] = useState(false)

  // Code
  const [language, setLanguage] = useState('python')
  const [code, setCode] = useState(LANGUAGE_STARTER['python'])

  // Judge
  const [judging, setJudging] = useState(false)
  const [judgeResult, setJudgeResult] = useState(null)

  // Mobile sidebar
  const [sidebarOpen, setSidebarOpen] = useState(true)

  // Load problem list
  useEffect(() => {
    loadProblems()
  }, [filterDifficulty])

  // Load specific problem from route
  useEffect(() => {
    if (routeProblemId) {
      loadProblem(routeProblemId)
    }
  }, [routeProblemId])

  const loadProblems = useCallback(async () => {
    setProblemsLoading(true)
    try {
      const params = {}
      if (filterDifficulty) params.difficulty = filterDifficulty
      const data = await getProblems(params)
      setProblems(data.problems || [])
    } catch (err) {
      message.error('加载题库失败')
    } finally {
      setProblemsLoading(false)
    }
  }, [filterDifficulty])

  const loadProblem = useCallback(async (pid) => {
    setProblemLoading(true)
    setJudgeResult(null)
    try {
      const data = await getProblemDetail(pid)
      setCurrentProblem(data)
      setCode(LANGUAGE_STARTER[language] || LANGUAGE_STARTER['python'])
    } catch (err) {
      message.error('加载题目失败')
    } finally {
      setProblemLoading(false)
    }
  }, [language])

  const handleSelectProblem = (pid) => {
    navigate(`/code-practice/${pid}`, { replace: true })
  }

  const handleLanguageChange = (lang) => {
    setLanguage(lang)
    // Keep existing code unless it's empty/default
    const isDefault = Object.values(LANGUAGE_STARTER).some(
      (s) => code.trim() === s.trim()
    )
    if (isDefault || !code.trim()) {
      setCode(LANGUAGE_STARTER[lang] || '')
    }
  }

  const handleSubmit = useCallback(async () => {
    if (!code.trim()) {
      message.warning('请先编写代码')
      return
    }
    if (!currentProblem) {
      message.warning('请先选择题目')
      return
    }

    setJudging(true)
    setJudgeResult(null)
    try {
      const result = await submitCode({
        student_id: studentId,
        problem_id: currentProblem.id,
        language,
        code,
      })
      setJudgeResult(result)
      invalidateHomeDashboard(activeCourse?.id, 'code_submitted')
    } catch (err) {
      message.error(err?.message || '判题失败，请稍后重试')
    } finally {
      setJudging(false)
    }
  }, [activeCourse, code, currentProblem, language, studentId])

  const handleReset = () => {
    setCode(LANGUAGE_STARTER[language] || '')
    setJudgeResult(null)
  }

  // Filter problems locally
  const filteredProblems = problems.filter((p) => {
    if (searchText && !p.title.toLowerCase().includes(searchText.toLowerCase())) {
      return false
    }
    return true
  })

  return (
    <Layout style={{ height: '100%', background: 'transparent' }}>
      {/* Sidebar Toggle (mobile) */}
      <Button
        type="text"
        icon={sidebarOpen ? <LeftOutlined /> : <RightOutlined />}
        onClick={() => setSidebarOpen(!sidebarOpen)}
        style={{
          position: 'absolute', top: 8, left: sidebarOpen ? 260 : 0,
          zIndex: 10, transition: 'left 0.3s',
        }}
      />

      {/* Problem List Sidebar */}
      {sidebarOpen && (
        <Sider
          width={280}
          style={{
            background: 'var(--bg-card)',
            borderRight: '1px solid var(--border)',
            overflow: 'auto',
            padding: 16,
          }}
        >
          <Text strong style={{ fontSize: 16 }}>编程题库</Text>

          <Space direction="vertical" style={{ width: '100%', marginTop: 12 }} size={8}>
            <Input
              prefix={<SearchOutlined />}
              placeholder="搜索题目..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              allowClear
              size="small"
            />
            <Select
              size="small"
              style={{ width: '100%' }}
              options={DIFFICULTY_OPTIONS}
              value={filterDifficulty}
              onChange={setFilterDifficulty}
            />
          </Space>

          <div style={{ marginTop: 16 }}>
            {problemsLoading ? (
              <Spin style={{ display: 'block', textAlign: 'center', marginTop: 40 }} />
            ) : filteredProblems.length === 0 ? (
              <Empty description="暂无题目" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            ) : (
              <List
                size="small"
                dataSource={filteredProblems}
                renderItem={(p) => {
                  const isActive = currentProblem?.id === p.id
                  const diffColor = { '简单': 'success', '中等': 'warning', '困难': 'error' }[p.difficulty] || 'default'
                  return (
                    <div
                      onClick={() => handleSelectProblem(p.id)}
                      style={{
                        padding: '10px 12px',
                        marginBottom: 4,
                        borderRadius: 6,
                        cursor: 'pointer',
                        background: isActive ? 'var(--color-primary-bg, #e6f4ff)' : 'transparent',
                        border: isActive ? '1px solid var(--color-primary, #1677ff)' : '1px solid transparent',
                        transition: 'all 0.2s',
                      }}
                      onMouseEnter={(e) => {
                        if (!isActive) e.currentTarget.style.background = 'var(--bg-page)'
                      }}
                      onMouseLeave={(e) => {
                        if (!isActive) e.currentTarget.style.background = 'transparent'
                      }}
                    >
                      <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                        <Text
                          strong={isActive}
                          style={{ fontSize: 13, flex: 1 }}
                          ellipsis={{ tooltip: p.title }}
                        >
                          {p.title}
                        </Text>
                        <Tag color={diffColor} style={{ fontSize: 11 }}>{p.difficulty}</Tag>
                      </Space>
                    </div>
                  )
                }}
              />
            )}
          </div>
        </Sider>
      )}

      {/* Main Content */}
      <Content style={{ display: 'flex', flexDirection: 'column', padding: 16, overflow: 'auto' }}>
        {!currentProblem ? (
          <div style={{
            flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Empty description="请从左侧选择一道编程题开始练习" />
          </div>
        ) : (
          <>
            {/* Problem Description */}
            <div style={{ flex: '0 0 auto', marginBottom: 16 }}>
              <ProblemPanel problem={currentProblem} loading={problemLoading} />
            </div>

            {/* Code Editor */}
            <div style={{ flex: '0 0 auto', marginBottom: 16 }}>
              <CodeEditor
                language={language}
                onLanguageChange={handleLanguageChange}
                value={code}
                onChange={setCode}
                height={350}
              />
            </div>

            {/* Action Buttons */}
            <div style={{ flex: '0 0 auto', marginBottom: 16, display: 'flex', gap: 12 }}>
              <Button
                type="primary"
                size="large"
                icon={<SendOutlined />}
                onClick={handleSubmit}
                loading={judging}
              >
                提交代码
              </Button>
              <Button
                size="large"
                icon={<ReloadOutlined />}
                onClick={handleReset}
                disabled={judging}
              >
                重置代码
              </Button>
              <Text type="secondary" style={{ alignSelf: 'center', marginLeft: 'auto' }}>
                <Text strong>{language.toUpperCase()}</Text> 模式
              </Text>
            </div>

            {/* Judge Result */}
            <div style={{ flex: '0 0 auto' }}>
              {(judging || judgeResult) && (
                <JudgeResult result={judgeResult} loading={judging} />
              )}
            </div>
          </>
        )}
      </Content>
    </Layout>
  )
}
