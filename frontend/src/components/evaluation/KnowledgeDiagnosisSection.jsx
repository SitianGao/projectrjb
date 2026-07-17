import { Card, Empty, Typography } from 'antd'
import { useState } from 'react'
import KnowledgeEvidenceDrawer from './KnowledgeEvidenceDrawer'
import StrengthKnowledgeCard from './StrengthKnowledgeCard'
import WeakKnowledgeCard from './WeakKnowledgeCard'

const { Title } = Typography

export default function KnowledgeDiagnosisSection({ strengths = [], weaknesses = [], onAction }) {
  const [active, setActive] = useState(null)
  return (
    <Card className="evaluation-card">
      <Title level={4}>知识点诊断</Title>
      <div className="knowledge-grid">
        <section>
          <h3>优势知识点</h3>
          {strengths.length ? strengths.map((item) => (
            <StrengthKnowledgeCard key={item.knowledge_point_id || item.name} item={item} />
          )) : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无明显优势知识点" />}
        </section>
        <section>
          <h3>重点改进</h3>
          {weaknesses.length ? weaknesses.map((item) => (
            <WeakKnowledgeCard
              key={item.knowledge_point_id || item.name}
              item={item}
              onEvidence={setActive}
              onAction={onAction}
            />
          )) : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无明显薄弱知识点" />}
        </section>
      </div>
      <KnowledgeEvidenceDrawer open={!!active} item={active} onClose={() => setActive(null)} />
    </Card>
  )
}
