import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import duration from 'dayjs/plugin/duration'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.extend(duration)
dayjs.locale('zh-cn')

/**
 * 格式化日期时间
 * @param {string|Date} date - 日期
 * @param {string} fmt - 格式模板，默认 'YYYY-MM-DD HH:mm:ss'
 * @returns {string}
 */
export function formatDate(date, fmt = 'YYYY-MM-DD HH:mm:ss') {
  if (!date) return '--'
  return dayjs(date).format(fmt)
}

/**
 * 格式化为相对时间（如"3 小时前"）
 * @param {string|Date} date - 日期
 * @returns {string}
 */
export function formatRelativeTime(date) {
  if (!date) return '--'
  return dayjs(date).fromNow()
}

/**
 * 格式化持续时间（秒 → "1h 30m"）
 * @param {number} seconds - 秒数
 * @returns {string}
 */
export function formatDuration(seconds) {
  if (!seconds && seconds !== 0) return '--'
  const d = dayjs.duration(seconds, 'seconds')
  const h = Math.floor(d.asHours())
  const m = d.minutes()
  if (h > 0) return `${h}h ${m}m`
  if (m > 0) return `${m}m`
  return `${Math.floor(d.asSeconds())}s`
}

/**
 * 截断文本并添加省略号
 * @param {string} text - 原文本
 * @param {number} maxLen - 最大长度
 * @returns {string}
 */
export function truncateText(text, maxLen = 100) {
  if (!text) return ''
  if (text.length <= maxLen) return text
  return text.slice(0, maxLen) + '...'
}

/**
 * 格式化数字（添加千分位分隔符）
 * @param {number} num - 数字
 * @returns {string}
 */
export function formatNumber(num) {
  if (num == null) return '0'
  return num.toLocaleString('zh-CN')
}

/**
 * 格式化百分比
 * @param {number} value - 值（0-1 或 0-100）
 * @param {number} decimals - 小数位数
 * @returns {string}
 */
export function formatPercent(value, decimals = 1) {
  if (value == null) return '0%'
  const pct = value > 1 ? value : value * 100
  return pct.toFixed(decimals) + '%'
}

export { dayjs }
