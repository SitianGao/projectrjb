import { Typography, Slider, Select, InputNumber, Button, Space, Tooltip } from 'antd'
import { SettingOutlined, UndoOutlined, InfoCircleOutlined } from '@ant-design/icons'

const { Text } = Typography

/**
 * 参数调节面板 — 让学生调整实验参数（学习率、batch size 等）。
 */
export default function ParameterPanel({
  parameters = [],
  values = {},
  onChange,
  onReset,
}) {
  if (!parameters || parameters.length === 0) return null

  const handleChange = (name, value) => {
    onChange?.({ ...values, [name]: value })
  }

  return (
    <div style={{
      border: '1px solid var(--border)',
      borderRadius: 8,
      padding: '10px 14px',
      background: 'var(--bg-card)',
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 10,
      }}>
        <Space size={6}>
          <SettingOutlined style={{ color: '#89b4fa' }} />
          <Text strong style={{ fontSize: 13 }}>实验参数</Text>
        </Space>
        <Tooltip title="恢复默认值">
          <Button
            type="text"
            size="small"
            icon={<UndoOutlined />}
            onClick={onReset}
          />
        </Tooltip>
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16 }}>
        {parameters.map((param) => (
          <ParameterControl
            key={param.name}
            param={param}
            value={values[param.name] ?? param.default_value}
            onChange={(val) => handleChange(param.name, val)}
          />
        ))}
      </div>
    </div>
  )
}

function ParameterControl({ param, value, onChange }) {
  const { name, label, default_value, allowed_values, explanation } = param

  // 如果有 allowed_values，使用 Select
  if (allowed_values && allowed_values.length > 0) {
    return (
      <div style={{ minWidth: 140, flex: '1 1 140px' }}>
        <Space size={4}>
          <Text style={{ fontSize: 12, color: '#666' }}>{label || name}</Text>
          {explanation && (
            <Tooltip title={explanation}>
              <InfoCircleOutlined style={{ fontSize: 11, color: '#999' }} />
            </Tooltip>
          )}
        </Space>
        <Select
          size="small"
          style={{ width: '100%', marginTop: 4 }}
          value={value}
          onChange={onChange}
          options={allowed_values.map((v) => ({
            label: String(v),
            value: v,
          }))}
        />
      </div>
    )
  }

  // 数值类型使用 Slider + InputNumber
  if (typeof default_value === 'number') {
    const isFloat = !Number.isInteger(default_value)
    const step = isFloat ? 0.001 : 1
    const min = isFloat ? 0.0001 : 0
    const max = isFloat ? 10.0 : 1000

    return (
      <div style={{ minWidth: 180, flex: '1 1 180px' }}>
        <Space size={4}>
          <Text style={{ fontSize: 12, color: '#666' }}>{label || name}</Text>
          {explanation && (
            <Tooltip title={explanation}>
              <InfoCircleOutlined style={{ fontSize: 11, color: '#999' }} />
            </Tooltip>
          )}
        </Space>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4 }}>
          <Slider
            style={{ flex: 1 }}
            min={min}
            max={max}
            step={step}
            value={value}
            onChange={onChange}
          />
          <InputNumber
            size="small"
            style={{ width: 70 }}
            min={min}
            max={max}
            step={step}
            value={value}
            onChange={onChange}
          />
        </div>
      </div>
    )
  }

  // 字符串类型使用普通输入
  return (
    <div style={{ minWidth: 140, flex: '1 1 140px' }}>
      <Space size={4}>
        <Text style={{ fontSize: 12, color: '#666' }}>{label || name}</Text>
        {explanation && (
          <Tooltip title={explanation}>
            <InfoCircleOutlined style={{ fontSize: 11, color: '#999' }} />
          </Tooltip>
        )}
      </Space>
      <input
        style={{
          width: '100%', marginTop: 4, padding: '4px 8px',
          border: '1px solid #d9d9d9', borderRadius: 6,
          fontSize: 13,
        }}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  )
}
