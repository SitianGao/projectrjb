import { Component } from 'react'
import { Button, Result, Space, Typography } from 'antd'

const { Text } = Typography

export default class PageErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { error: null }
  }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    if (import.meta.env.DEV) {
      console.error('[PageErrorBoundary]', error, info)
    }
  }

  render() {
    if (!this.state.error) return this.props.children
    const isDev = import.meta.env.DEV
    return (
      <div style={{ minHeight: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 48, background: 'var(--bg-page)' }}>
        <Result
          status="error"
          title="页面加载失败"
          subTitle="请返回我的课程，或重新加载当前页面。"
          extra={(
            <Space>
              <Button type="primary" onClick={() => { window.location.href = '/courses' }}>
                返回我的课程
              </Button>
              <Button onClick={() => window.location.reload()}>
                重新加载
              </Button>
            </Space>
          )}
        >
          {isDev && (
            <Text type="secondary">
              {this.state.error?.message || 'UNKNOWN_PAGE_ERROR'}
            </Text>
          )}
        </Result>
      </div>
    )
  }
}
