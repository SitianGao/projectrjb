import { Button, Input, Typography } from 'antd'
import { useState } from 'react'

const { Paragraph } = Typography

export default function CodeDemoScene({ scene }) {
  const [code, setCode] = useState(scene.content?.code || '')
  const [output, setOutput] = useState('')
  return (
    <div className="code-demo-scene">
      <Paragraph>{scene.content?.explanation}</Paragraph>
      <Input.TextArea value={code} onChange={(event) => setCode(event.target.value)} rows={8} />
      <Button type="primary" onClick={() => setOutput('安全沙箱演示输出：参数逐步接近最优值 1.0')}>运行代码</Button>
      {output && <pre>{output}</pre>}
    </div>
  )
}
