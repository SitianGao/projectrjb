import { Button, Result, Space } from 'antd'
import { ReloadOutlined, HomeOutlined } from '@ant-design/icons'

export default function GenerationErrorState({ title, subTitle, onRetry, onGoHome }) {
  return (
    <div
      style={{
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(160deg, #F6F7FB 0%, #EDE9FE 40%, #F6F7FB 100%)',
      }}
    >
      <Result
        status="error"
        title={title || '生成失败'}
        subTitle={subTitle || '请稍后重试'}
        extra={
          <Space>
            {onRetry && (
              <Button icon={<ReloadOutlined />} onClick={onRetry}>
                重试
              </Button>
            )}
            {onGoHome && (
              <Button
                type="primary"
                icon={<HomeOutlined />}
                onClick={onGoHome}
                style={{ borderRadius: 10 }}
              >
                返回首页
              </Button>
            )}
          </Space>
        }
      />
    </div>
  )
}
