/**
 * Resource title normalization and legacy content format detection.
 */
const TYPE_TITLES = {
  document: '核心讲义',
  exercise: '专项练习',
  mindmap: '知识导图',
  ppt: '教学课件',
  video_script: '视频脚本',
  case: '案例分析',
  project: '项目任务',
  code: '代码示例',
  reading: '拓展阅读',
  audio: '音频讲解',
}

/**
 * Clean up resource title: remove type suffix and apply proper naming.
 */
export function normalizeTitle(title, type, topic) {
  if (!title) return topic ? `${topic} ${TYPE_TITLES[type] || '学习资源'}` : '学习资源'

  let cleaned = String(title)
  // Remove "- type" suffix patterns
  cleaned = cleaned.replace(/\s*[-–—]\s*(document|exercise|mindmap|ppt|code|reading|audio|quiz)\s*$/i, '')
  // Remove type label in brackets
  cleaned = cleaned.replace(/\s*[\[(](document|exercise|mindmap|ppt|code|reading|audio|quiz)[\])]\s*$/i, '')

  if (cleaned.length < 3 && topic) {
    return `${topic} ${TYPE_TITLES[type] || '学习资源'}`
  }
  return cleaned.trim()
}

/**
 * Get resource stats for card display.
 */
export function getResourceStats(resource) {
  const type = resource?.type
  const content = resource?.content

  if (!content) return null

  // Already structured content
  if (typeof content === 'object') {
    switch (type) {
      case 'document':
        return { label: `${content.sections?.length || 0} 章节`, icon: '📄' }
      case 'exercise':
        return { label: `${content.questions?.length || 0} 道题`, icon: '✏️' }
      case 'mindmap':
        return { label: `${countNodes(content.root)} 个节点`, icon: '🧠' }
      case 'ppt':
        return { label: `${content.slides?.length || 0} 张幻灯片`, icon: '📊' }
      default:
        return null
    }
  }

  // Legacy string content
  if (typeof content === 'string') {
    switch (type) {
      case 'document':
        return { label: `约 ${Math.ceil(content.length / 500)} 分钟阅读`, icon: '📄' }
      case 'exercise': {
        const qCount = (content.match(/"question"/g) || []).length || (content.match(/#+\s*题目/g) || []).length
        return { label: qCount > 0 ? `${qCount} 道题` : '练习', icon: '✏️' }
      }
      case 'mindmap':
        return { label: `${(content.match(/^- /gm) || []).length} 个分支`, icon: '🧠' }
      default:
        return null
    }
  }

  return null
}

function countNodes(node) {
  if (!node) return 0
  let count = 1
  if (Array.isArray(node.children)) {
    node.children.forEach((c) => { count += countNodes(c) })
  }
  return count
}

/**
 * Detect if content is valid structured JSON matching the expected schema.
 */
export function detectContentFormat(resource) {
  const content = resource?.content
  if (!content) return 'empty'

  if (typeof content === 'object') return 'structured'

  if (typeof content === 'string') {
    const trimmed = content.trim()
    // Is it JSON?
    if (trimmed.startsWith('[') || trimmed.startsWith('{')) {
      try {
        JSON.parse(trimmed)
        return 'json_string'
      } catch { /* fall through */ }
    }
    // Is it Markdown?
    if (trimmed.startsWith('#') || trimmed.includes('##') || trimmed.includes('```')) {
      return 'markdown'
    }
    return 'plain_text'
  }

  return 'unknown'
}

/**
 * Try to extract structured data from legacy formats.
 */
export function normalizeLegacyContent(resource) {
  const type = resource?.type
  const content = resource?.content

  if (!content) return null

  // Already structured
  if (typeof content === 'object') return content

  // Try JSON parse
  if (typeof content === 'string') {
    const trimmed = content.trim()
    if (trimmed.startsWith('[') || trimmed.startsWith('{')) {
      try {
        const parsed = JSON.parse(trimmed)
        if (type === 'exercise') {
          // Convert old exercise format
          if (Array.isArray(parsed)) {
            return {
              instructions: '',
              questions: parsed.map((q, i) => ({
                id: q.id || `q-${i + 1}`,
                type: q.type || 'single_choice',
                stem: q.question || q.stem || '',
                options: Array.isArray(q.options)
                  ? q.options.map((o, oi) => ({
                    key: typeof o === 'string' ? String.fromCharCode(65 + oi) : (o.key || String.fromCharCode(65 + oi)),
                    text: typeof o === 'string' ? o : (o.content || o.text || ''),
                  }))
                  : [],
                correct_answer: Array.isArray(q.answer) ? q.answer : [q.answer || q.correct_answer || ''],
                explanation: q.explanation || '',
                difficulty: q.difficulty || 'medium',
              })),
            }
          }
          if (parsed.questions) return parsed
        }
        if (type === 'mindmap') {
          if (Array.isArray(parsed)) {
            return {
              root: { id: 'root', label: resource.topic || '知识点', children: parsed.map((n) => ({ id: n.id || `n-${Math.random()}`, label: n.label || n.title || n, children: n.children || [] })) },
            }
          }
          if (parsed.root) return parsed
        }
        if (type === 'document') {
          if (parsed.sections) return parsed
          // Treat as raw document sections from parsed content
          return {
            learning_objectives: [],
            sections: [{ heading: resource.title || '', paragraphs: [trimmed], examples: [], key_points: [] }],
            summary: '', common_mistakes: [],
          }
        }
        return parsed
      } catch { /* not valid JSON */ }
    }

    // Markdown or plain text — treat as document
    if (type === 'document' || type === 'reading' || !type) {
      return {
        learning_objectives: [],
        sections: [{ heading: resource.title || '', paragraphs: [trimmed], examples: [], key_points: [] }],
        summary: '', common_mistakes: [],
      }
    }
  }

  return content
}
