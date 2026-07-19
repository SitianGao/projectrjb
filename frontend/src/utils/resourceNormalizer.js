/**
 * Resource normalization: titles, stats, legacy content parsing, display helpers.
 *
 * All display-facing values are derived here; raw internal IDs and JSON
 * are never leaked to the UI.
 */

const TYPE_LABELS = {
  document: '讲义', exercise: '练习题', mindmap: '思维导图',
  ppt: 'PPT课件', code: '代码', reading: '阅读',
  interactive_classroom: 'AI互动课堂',
}

const DIFFICULTY_LABELS = {
  '初级': '初级', '中级': '中级', '高级': '高级',
  beginner: '初级', medium: '中级', advanced: '高级',
  easy: '初级', hard: '高级',
}

const TRIGGER_LABELS = {
  learning_task: '为当前学习任务准备',
  evaluation: '根据近期学习诊断生成',
  wrong_book: '根据错题生成',
  tutor: '由 AI 学习助手整理',
  path_adjustment: '学习路径调整后新增',
  manual_workspace: '自主生成',
  curated_course: '课程预置',
}

const LEARNING_STATUS_LABELS = {
  not_started: '未开始',
  in_progress: '学习中',
  completed: '已完成',
}

/* ── Title ── */

export function normalizeTitle(title, type, topic) {
  if (!title) return topic ? `${topic} ${TYPE_LABELS[type] || '学习资源'}` : '学习资源'
  let cleaned = String(title)
    .replace(/\s*[-–—]\s*(document|exercise|mindmap|ppt|code|reading|audio|quiz)\s*$/i, '')
    .replace(/\s*(?:\[|\()(document|exercise|mindmap|ppt|code|reading|audio|quiz)(?:\]|\))\s*$/i, '')
  if (cleaned.length < 3 && topic) return `${topic} ${TYPE_LABELS[type] || '学习资源'}`
  return cleaned.trim()
}

export function typeLabel(type) { return TYPE_LABELS[type] || '资源' }
export function difficultyLabel(d) { return DIFFICULTY_LABELS[d] || d || '中级' }
export function learningStatusLabel(status) {
  return LEARNING_STATUS_LABELS[status] || '未开始'
}

function parseSourceRefs(resource) {
  const refs = resource?.source_refs || resource?.source_provenance?.sources || []
  if (Array.isArray(refs)) return refs
  if (typeof refs === 'string') {
    try {
      const parsed = JSON.parse(refs)
      return Array.isArray(parsed) ? parsed : []
    } catch {
      return []
    }
  }
  return []
}

export function getResourceSourceLabel(resource) {
  const source = resource?.generation_meta?.generation_source
    || resource?.generation_source
    || ''
  const trigger = resource?.trigger_source || resource?.generation_meta?.trigger_source
  const ragUsed = resource?.trigger_context?.rag_used === true
    || parseSourceRefs(resource).length > 0

  if (source === 'curated_seed' || trigger === 'curated_course') return '课程精选'
  if (['llm_generated', 'llm', 'agent'].includes(source) && ragUsed) return 'AI 个性化生成'
  if (['template_generated', 'knowledge_base', 'template'].includes(source) && ragUsed) return '知识库基础版'
  if (['template_generated', 'outline', 'template'].includes(source) && !ragUsed) return '基础提纲'
  return '历史资源'
}

export function getTriggerReasonLabel(resource) {
  const trigger = resource?.trigger_source || resource?.generation_meta?.trigger_source
  return TRIGGER_LABELS[trigger] || '历史学习资料'
}

export function getTriggerReasonDescription(resource) {
  const trigger = resource?.trigger_source || resource?.generation_meta?.trigger_source
  const context = resource?.trigger_context || {}
  const topic = context.knowledge_point || resource?.topic
  if (trigger === 'evaluation') return '根据你最近的学习诊断生成。'
  if (trigger === 'wrong_book') {
    return topic
      ? `根据你在${topic}相关题目中的错误生成。`
      : '根据你的近期错题生成。'
  }
  if (trigger === 'learning_task') return '为当前学习任务准备。'
  if (trigger === 'tutor') return '由 AI 学习助手根据本次对话整理。'
  if (trigger === 'path_adjustment') return '根据学习诊断调整路径后，为新增任务准备。'
  if (trigger === 'manual_workspace') return '由你在 AI 学习工作台中自主生成。'
  if (trigger === 'curated_course') return '由课程内容团队预先整理。'
  return '这是你之前学习过程中保存的资料。'
}

export function isTargetedResource(resource) {
  const trigger = resource?.trigger_source || resource?.generation_meta?.trigger_source
  return ['evaluation', 'wrong_book', 'tutor', 'path_adjustment'].includes(trigger)
}

/* ── Stats for cards ── */

function countNodes(node) {
  if (!node) return 0
  let count = 1
  if (Array.isArray(node.children)) node.children.forEach((c) => { count += countNodes(c) })
  return count
}

export function getResourceStats(resource) {
  const type = resource?.type
  let content = resource?.content
  if (!content) return null

  // Auto-parse double-serialized JSON strings
  if (typeof content === 'string') {
    try { content = JSON.parse(content) } catch { /* keep as string */ }
  }

  if (typeof content === 'object') {
    switch (type) {
      case 'document':
        return { label: `${content.sections?.length || 1} 章节`, icon: '📄', numeric: content.sections?.length || 1 }
      case 'exercise':
        return { label: `${content.questions?.length || 0} 道题`, icon: '✏️', numeric: content.questions?.length || 0, suffix: 'question_count' }
      case 'mindmap': {
        const nodes = countNodes(content.root)
        return { label: `${nodes} 个节点`, icon: '🧠', numeric: nodes }
      }
      case 'ppt': {
        // 优先使用星火 PPT API 的大纲格式
        if (content.outline?.length > 0) {
          return { label: `${content.outline.length} 章`, icon: '📊', numeric: content.outline.length }
        }
        return { label: `${content.slides?.length || 0} 张幻灯片`, icon: '📊', numeric: content.slides?.length || 0 }
      }
      case 'interactive_classroom':
        return { label: `${content.scenes?.length || content.summary ? '已' : '0'} 场景`, icon: '🎓', numeric: content.scenes?.length || 0 }
      case 'code':
        return { label: '代码案例', icon: '💻' }
      case 'reading':
        return { label: '拓展阅读', icon: '📖' }
      default:
        return { label: typeLabel(type), icon: '📦' }
    }
  }

  // String content
  if (typeof content === 'string') {
    switch (type) {
      case 'document':
        return { label: `约 ${Math.ceil(content.length / 500)} 分钟`, icon: '📄' }
      case 'exercise': {
        const qCount = (content.match(/"question"/g) || []).length || (content.match(/#+\s*题目/g) || []).length
        return { label: qCount > 0 ? `${qCount} 道题` : '练习', icon: '✏️', numeric: qCount }
      }
      case 'mindmap':
        return { label: `${(content.match(/^- /gm) || []).length} 个分支`, icon: '🧠' }
      default:
        return null
    }
  }
  return null
}

/* ── Content format detection ── */

export function detectContentFormat(resource) {
  const content = resource?.content
  if (!content) return 'empty'
  if (typeof content === 'object') return 'structured'
  if (typeof content === 'string') {
    const t = content.trim()
    if (t.startsWith('[') || t.startsWith('{')) {
      try { JSON.parse(t); return 'json_string' } catch { /* continue format detection */ }
    }
    if (t.startsWith('#') || t.includes('##') || t.includes('```')) return 'markdown'
    return 'plain_text'
  }
  return 'unknown'
}

/* ── Legacy content normalization ── */

export function normalizeLegacyContent(resource) {
  const type = resource?.type
  let content = resource?.content
  if (!content) return null
  if (typeof content === 'object') return content

  if (typeof content === 'string') {
    const trimmed = content.trim()
    // Try JSON parse first (handles double-serialized content)
    if (trimmed.startsWith('[') || trimmed.startsWith('{')) {
      try {
        const parsed = JSON.parse(trimmed)
        // If parsed is a string again (double-serialized), try one more time
        if (typeof parsed === 'string') {
          try { return JSON.parse(parsed) } catch { return parsed }
        }
        // Exercise normalization
        if (type === 'exercise') {
          if (Array.isArray(parsed)) {
            return { instructions: '', questions: parsed.map((q, i) => normalizeQuestion(q, i)) }
          }
          if (parsed.questions) return { ...parsed, questions: parsed.questions.map((q, i) => normalizeQuestion(q, i)) }
        }
        // Mindmap normalization
        if (type === 'mindmap') {
          if (Array.isArray(parsed)) {
            return { root: { id: 'root', label: resource.topic || '知识点', children: parsed.map(n => normalizeNode(n)) } }
          }
          if (parsed.root) return parsed
        }
        return parsed
      } catch { /* keep the original content */ }
    }
    // Plain text → document format
    if (type === 'document' || type === 'reading' || !type) {
      return { learning_objectives: [], sections: [{ heading: resource.title || '', paragraphs: [trimmed], examples: [], key_points: [] }], summary: '', common_mistakes: [] }
    }
  }
  return content
}

function normalizeQuestion(q, i) {
  return {
    id: q.id || `q-${i + 1}`,
    type: q.type || 'single_choice',
    stem: q.question || q.stem || '',
    options: Array.isArray(q.options) ? q.options.map((o, oi) => ({
      key: typeof o === 'string' ? String.fromCharCode(65 + oi) : (o.key || String.fromCharCode(65 + oi)),
      text: typeof o === 'string' ? o : (o.content || o.text || ''),
    })) : [],
    correct_answer: Array.isArray(q.answer) ? q.answer : [q.answer || q.correct_answer || ''],
    explanation: q.explanation || '',
    difficulty: q.difficulty || 'medium',
  }
}

function normalizeNode(n) {
  return {
    id: n.id || `n-${Math.random().toString(36).slice(2, 8)}`,
    label: n.label || n.title || String(n),
    children: (n.children || []).map(normalizeNode),
  }
}
