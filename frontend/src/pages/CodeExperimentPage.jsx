import { useState, useEffect, useCallback, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Layout, Button, Space, Typography, message, Spin, Empty, List, Tag,
} from 'antd'
import {
  PlayCircleOutlined, ReloadOutlined, UndoOutlined,
  ExperimentOutlined, LeftOutlined, RightOutlined,
} from '@ant-design/icons'
import MonacoCodeEditor from '../components/MonacoCodeEditor'
import ExperimentGuide from '../components/experiment/ExperimentGuide'
import ParameterPanel from '../components/experiment/ParameterPanel'
import ExperimentResult from '../components/experiment/ExperimentResult'
import { CodeBlanks, ErrorDiagnosis } from '../components/experiment/CodeBlanks'
import { runExperiment } from '../api/experiment'
import { useAuth } from '../contexts/AuthContext'

const { Sider, Content } = Layout
const { Text, Title } = Typography

// 实验模式中文标签
const MODE_LABELS = {
  code_guide: '代码导读',
  param_experiment: '参数实验',
  code_completion: '代码补全',
  error_diagnosis: '错误诊断',
  mini_project: '小型项目',
}

/**
 * 交互式代码实验页面。
 * 左侧：实验指导 + 参数调节 | 右侧：代码编辑器 + 结果面板
 */
export default function CodeExperimentPage() {
  const { experimentId } = useParams()
  const navigate = useNavigate()
  const { studentId } = useAuth()

  // 实验数据（来自资源或直接传入）
  const [experiment, setExperiment] = useState(null)
  const [loading, setLoading] = useState(false)

  // 编辑器状态
  const [code, setCode] = useState('')
  const [currentStep, setCurrentStep] = useState(0)
  const [paramValues, setParamValues] = useState({})

  // 运行状态
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState(null)
  const [history, setHistory] = useState([])

  // AI 分析
  const [aiAnalysis, setAiAnalysis] = useState('')
  const [aiLoading, setAiLoading] = useState(false)

  // 侧边栏
  const [sidebarOpen, setSidebarOpen] = useState(true)

  // 从 URL 参数或 localStorage 加载实验数据
  useEffect(() => {
    if (experimentId) {
      loadExperiment(experimentId)
    } else {
      // 尝试从 localStorage 加载（从资源详情页跳转）
      const saved = localStorage.getItem('current_experiment')
      if (saved) {
        try {
          const data = JSON.parse(saved)
          initExperiment(data)
        } catch (e) {
          console.error('加载实验数据失败', e)
        }
      }
    }
  }, [experimentId])

  const loadExperiment = useCallback(async (id) => {
    setLoading(true)
    try {
      // 尝试从资源 API 加载
      const { getResource } = await import('../api/resource')
      const res = await getResource(id)
      const content = typeof res.content === 'string'
        ? (() => { try { return JSON.parse(res.content) } catch { return {} } })()
        : (res.content || {})
      initExperiment({ ...content, title: res.title || content.title })
    } catch (e) {
      console.error('加载实验失败', e)
      message.error('加载实验数据失败')
    } finally {
      setLoading(false)
    }
  }, [])

  const initExperiment = useCallback((data) => {
    setExperiment(data)
    // 设置初始代码
    const initialCode = data.starter_code || data.code || ''
    setCode(initialCode)
    // 初始化参数默认值
    const defaults = {}
    ;(data.editable_parameters || []).forEach((p) => {
      defaults[p.name] = p.default_value
    })
    setParamValues(defaults)
    setCurrentStep(0)
    setResult(null)
    setHistory([])
    setAiAnalysis('')
  }, [])

  // 参数变更时，同步更新代码中的参数值
  const handleParamChange = useCallback((newValues) => {
    setParamValues(newValues)
    // 在代码中替换参数值
    let newCode = code
    for (const [name, value] of Object.entries(newValues)) {
      const pattern = new RegExp(`(${name}\\s*=\\s*)([^\\s\\n#]+)`, 'g')
      newCode = newCode.replace(pattern, `$1${value}`)
    }
    setCode(newCode)
  }, [code])

  const handleResetParams = useCallback(() => {
    if (!experiment) return
    const defaults = {}
    ;(experiment.editable_parameters || []).forEach((p) => {
      defaults[p.name] = p.default_value
    })
    setParamValues(defaults)
    // 重置代码到初始值
    const initialCode = experiment.starter_code || experiment.code || ''
    setCode(initialCode)
  }, [experiment])

  const handleResetCode = useCallback(() => {
    if (!experiment) return
    const initialCode = experiment.starter_code || experiment.code || ''
    setCode(initialCode)
    setResult(null)
  }, [experiment])

  // 运行实验
  const handleRun = useCallback(async (codeToRun) => {
    const runCode = codeToRun || code
    if (!runCode.trim()) {
      message.warning('请先编写代码')
      return
    }

    setRunning(true)
    setResult(null)
    try {
      const res = await runExperiment({
        code: runCode,
        student_id: studentId,
        experiment_id: experimentId,
        parameters: paramValues,
      })
      setResult(res)
      // 记录历史
      setHistory((prev) => [...prev, {
        parameters: { ...paramValues },
        ...res,
      }])
      if (res.status === 'success') {
        message.success('实验运行完成')
      } else {
        message.warning(`实验运行状态: ${res.status}`)
      }
    } catch (e) {
      message.error(e?.message || '实验运行失败')
    } finally {
      setRunning(false)
    }
  }, [code, studentId, experimentId, paramValues])

  // AI 分析
  const handleAIAnalyze = useCallback(async () => {
    if (!result) return
    setAiLoading(true)
    try {
      const { askTutor } = await import('../api/tutor')
      const prompt = [
        '我正在做一个代码实验，请分析以下运行结果：',
        '',
        `实验：${experiment?.title || '未知'}`,
        `状态：${result.status}`,
        result.stdout ? `\n输出：\n${result.stdout.slice(0, 1000)}` : '',
        result.stderr ? `\n错误：\n${result.stderr.slice(0, 500)}` : '',
        result.metrics ? `\n指标：${JSON.stringify(result.metrics)}` : '',
        result.observations?.length ? `\n自动观察：${result.observations.join('；')}` : '',
        '',
        '请分析：1) 结果是否正常 2) 有什么改进空间 3) 相关知识点解释',
      ].filter(Boolean).join('\n')

      const res = await askTutor({
        question: prompt,
        student_id: studentId,
      })
      setAiAnalysis(res.answer || res.response || '分析完成')
    } catch (e) {
      setAiAnalysis('AI 分析暂时不可用，请稍后重试。')
    } finally {
      setAiLoading(false)
    }
  }, [result, experiment, studentId])

  // 根据实验模式决定右侧渲染内容
  const editorContent = useMemo(() => {
    if (!experiment) return null

    const mode = experiment.experiment_mode || 'code_guide'

    if (mode === 'code_completion' && experiment.blanks?.length > 0) {
      return (
        <CodeBlanks
          codeWithBlanks={experiment.starter_code || experiment.code || ''}
          blanks={experiment.blanks}
          onSubmit={(answers) => {
            // 将填空答案填入代码并运行
            let filledCode = experiment.starter_code || experiment.code || ''
            for (const [key, val] of Object.entries(answers)) {
              filledCode = filledCode.replace('______', val)
            }
            setCode(filledCode)
            handleRun(filledCode)
          }}
          showAnswers
        />
      )
    }

    if (mode === 'error_diagnosis' && experiment.buggy_code) {
      return (
        <ErrorDiagnosis
          buggyCode={experiment.buggy_code}
          bugDescription={experiment.bug_description}
          fixHint={experiment.fix_hint}
          onFix={(fixedCode) => {
            setCode(fixedCode)
            handleRun(fixedCode)
          }}
        />
      )
    }

    // 默认：Monaco 编辑器
    return (
      <MonacoCodeEditor
        value={code}
        onChange={setCode}
        height={380}
        title={MODE_LABELS[mode] || '代码编辑器'}
      />
    )
  }, [experiment, code, experiment?.experiment_mode, experiment?.blanks, experiment?.buggy_code])

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
        <Spin size="large" tip="加载实验数据..." />
      </div>
    )
  }

  if (!experiment) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
        <Empty description="未找到实验数据">
          <Button onClick={() => navigate('/resources')}>返回资源列表</Button>
        </Empty>
      </div>
    )
  }

  const canRun = !['code_completion', 'error_diagnosis'].includes(experiment.experiment_mode)

  return (
    <Layout style={{ height: '100%', background: 'transparent' }}>
      {/* Sidebar Toggle */}
      <Button
        type="text"
        icon={sidebarOpen ? <LeftOutlined /> : <RightOutlined />}
        onClick={() => setSidebarOpen(!sidebarOpen)}
        style={{
          position: 'absolute', top: 8, left: sidebarOpen ? 320 : 0,
          zIndex: 10, transition: 'left 0.3s',
        }}
      />

      {/* 左侧：实验指导 + 参数调节 */}
      {sidebarOpen && (
        <Sider
          width={320}
          style={{
            background: 'var(--bg-card)',
            borderRight: '1px solid var(--border)',
            overflow: 'auto',
            padding: 16,
          }}
        >
          <ExperimentGuide
            experiment={experiment}
            currentStep={currentStep}
            onStepChange={setCurrentStep}
          />

          {/* 参数调节面板 */}
          {experiment.editable_parameters?.length > 0 && (
            <div style={{ marginTop: 16 }}>
              <ParameterPanel
                parameters={experiment.editable_parameters}
                values={paramValues}
                onChange={handleParamChange}
                onReset={handleResetParams}
              />
            </div>
          )}
        </Sider>
      )}

      {/* 右侧：代码编辑器 + 结果 */}
      <Content style={{
        display: 'flex',
        flexDirection: 'column',
        padding: 16,
        overflow: 'auto',
        gap: 16,
      }}>
        {/* 代码编辑器区 */}
        <div style={{ flex: '0 0 auto' }}>
          {editorContent}
        </div>

        {/* 操作按钮 */}
        {canRun && (
          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            <Button
              type="primary"
              size="large"
              icon={<PlayCircleOutlined />}
              onClick={() => handleRun()}
              loading={running}
            >
              运行实验
            </Button>
            <Button
              size="large"
              icon={<ReloadOutlined />}
              onClick={handleResetCode}
              disabled={running}
            >
              重置代码
            </Button>
            {experiment.editable_parameters?.length > 0 && (
              <Button
                size="large"
                icon={<UndoOutlined />}
                onClick={handleResetParams}
                disabled={running}
              >
                恢复默认参数
              </Button>
            )}
            <Text type="secondary" style={{ marginLeft: 'auto' }}>
              <ExperimentOutlined /> {MODE_LABELS[experiment.experiment_mode] || '代码实验'}
            </Text>
          </div>
        )}

        {/* 实验结果 */}
        <ExperimentResult
          result={result}
          loading={running}
          history={history}
          aiAnalysis={aiAnalysis}
          aiLoading={aiLoading}
          onAIAnalyze={handleAIAnalyze}
        />
      </Content>
    </Layout>
  )
}
