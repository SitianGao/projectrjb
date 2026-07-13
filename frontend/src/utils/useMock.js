/**
 * Mock 数据开关
 *
 * 通过环境变量 VITE_USE_MOCK 控制是否使用本地 Mock 数据。
 * - true（默认）: 后端不可用时自动降级到 Mock 数据
 * - false         : 必须走真实接口，失败即报错
 *
 * 用法:
 *   import { shouldUseMock } from '../utils/useMock'
 *   if (shouldUseMock()) { return mockData }
 */
export function shouldUseMock() {
  return import.meta.env.VITE_USE_MOCK === 'true'
}
