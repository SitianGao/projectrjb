import { useRef, useState, useCallback, useEffect } from 'react'
import gsap from 'gsap'

// 4 个几何角色定义
const CHARS = [
  { id: 'purple', fill: '#A78BFA', stroke: '#7C5CCF', rx: 4,  label: '紫' },
  { id: 'black',  fill: '#4A4A5A', stroke: '#2D2D3A', rx: 4,  label: '黑' },
  { id: 'orange', fill: '#FBA97C', stroke: '#D4783C', rx: 20, label: '橙' },
  { id: 'yellow', fill: '#FCD34D', stroke: '#D4A020', rx: 18, label: '黄' },
]

// 每个角色的布局位置（在 300x300 画布中，带堆叠重叠）
const LAYOUT = [
  { x: 10,  y: 20,  w: 105, h: 120 }, // 紫色 — 左上
  { x: 165, y: 15,  w: 105, h: 125 }, // 黑色 — 右上
  { x: 55,  y: 145, w: 100, h: 115 }, // 橙色 — 左下（叠入上方）
  { x: 140, y: 135, w: 105, h: 120 }, // 黄色 — 右下（叠入上方）
]

// 每个角色眼睛在其自身坐标系中的位置
function eyePos(charW, charH) {
  return {
    left:  { cx: charW * 0.32, cy: charH * 0.35 },
    right: { cx: charW * 0.68, cy: charH * 0.35 },
    r: Math.min(charW, charH) * 0.14,
  }
}

// ====== 单个几何角色 SVG ======
function GeoChar({ ch, layout, mouse, groupRect }) {
  const { x, y, w, h } = layout
  const eyeRefs = useRef([null, null])
  const [pupils, setPupils] = useState({ lx: 0, ly: 0, rx: 0, ry: 0 })
  const blinkRef = useRef(null)
  const frameRef = useRef(null)
  const targetRef = useRef({ lx: 0, ly: 0, rx: 0, ry: 0 })

  const ep = eyePos(w, h)
  const eyeR = ep.r
  const pupilR = eyeR * 0.55
  const maxShift = eyeR - pupilR - 1

  // 鼠标追踪
  useEffect(() => {
    let raf
    const track = () => {
      if (!groupRect) { raf = requestAnimationFrame(track); return }
      const mx = mouse.x - groupRect.left
      const my = mouse.y - groupRect.top

      // 该角色中心在画布中的像素位置
      const scaleX = groupRect.width / 300
      const scaleY = groupRect.height / 300
      const charCX = (x + w / 2) * scaleX
      const charCY = (y + h / 2) * scaleY

      // 左眼
      const lex = charCX + (ep.left.cx - w / 2) * scaleX
      const ley = charCY + (ep.left.cy - h / 2) * scaleY
      const ldx = mx - lex
      const ldy = my - ley
      const ld = Math.sqrt(ldx * ldx + ldy * ldy) || 1
      const lr = Math.min(maxShift * scaleX, ld) / ld
      targetRef.current.lx = ldx * lr / scaleX
      targetRef.current.ly = ldy * lr / scaleY

      // 右眼
      const rex = charCX + (ep.right.cx - w / 2) * scaleX
      const rey = charCY + (ep.right.cy - h / 2) * scaleY
      const rdx = mx - rex
      const rdy = my - rey
      const rd = Math.sqrt(rdx * rdx + rdy * rdy) || 1
      const rr = Math.min(maxShift * scaleX, rd) / rd
      targetRef.current.rx = rdx * rr / scaleX
      targetRef.current.ry = rdy * rr / scaleY

      // 平滑
      const e = 0.25
      setPupils(p => ({
        lx: p.lx + (targetRef.current.lx - p.lx) * e,
        ly: p.ly + (targetRef.current.ly - p.ly) * e,
        rx: p.rx + (targetRef.current.rx - p.rx) * e,
        ry: p.ry + (targetRef.current.ry - p.ry) * e,
      }))

      raf = requestAnimationFrame(track)
    }
    raf = requestAnimationFrame(track)
    return () => cancelAnimationFrame(raf)
  }, [mouse, groupRect, x, y, w, h, maxShift])

  // 随机眨眼
  useEffect(() => {
    const schedule = () => {
      const delay = 2500 + Math.random() * 5000
      blinkRef.current = setTimeout(() => {
        const el = eyeRefs.current.filter(Boolean)
        if (el.length) {
          gsap.to(el, { scaleY: 0.1, duration: 0.05, yoyo: true, repeat: 1, onComplete: schedule })
        } else schedule()
      }, delay)
    }
    schedule()
    return () => clearTimeout(blinkRef.current)
  }, [])

  return (
    <g>
      {/* 身体 */}
      <rect
        x={x} y={y} width={w} height={h} rx={ch.rx} ry={ch.rx}
        fill={ch.fill} stroke={ch.stroke} strokeWidth="3"
      />

      {/* 左眼白 */}
      <g ref={el => eyeRefs.current[0] = el}>
        <circle cx={x + ep.left.cx} cy={y + ep.left.cy} r={eyeR} fill="#fff" />
      </g>
      {/* 右眼白 */}
      <g ref={el => eyeRefs.current[1] = el}>
        <circle cx={x + ep.right.cx} cy={y + ep.right.cy} r={eyeR} fill="#fff" />
      </g>

      {/* 左瞳孔 */}
      <circle
        cx={x + ep.left.cx + pupils.lx} cy={y + ep.left.cy + pupils.ly}
        r={pupilR} fill="#1a1a2e"
      />
      <circle
        cx={x + ep.left.cx + pupils.lx + pupilR * 0.3}
        cy={y + ep.left.cy + pupils.ly - pupilR * 0.3}
        r={pupilR * 0.3} fill="#fff"
      />

      {/* 右瞳孔 */}
      <circle
        cx={x + ep.right.cx + pupils.rx} cy={y + ep.right.cy + pupils.ry}
        r={pupilR} fill="#1a1a2e"
      />
      <circle
        cx={x + ep.right.cx + pupils.rx + pupilR * 0.3}
        cy={y + ep.right.cy + pupils.ry - pupilR * 0.3}
        r={pupilR * 0.3} fill="#fff"
      />

      {/* 腮红 */}
      <ellipse cx={x + w * 0.15} cy={y + h * 0.48} rx={w * 0.08} ry={h * 0.04} fill="#F9A4C8" opacity="0.5" />
      <ellipse cx={x + w * 0.85} cy={y + h * 0.48} rx={w * 0.08} ry={h * 0.04} fill="#F9A4C8" opacity="0.5" />

      {/* 嘴巴 */}
      <path
        d={`M ${x + w * 0.4} ${y + h * 0.55} Q ${x + w * 0.5} ${y + h * 0.65} ${x + w * 0.6} ${y + h * 0.55}`}
        stroke="#E8888A" strokeWidth="2.5" fill="none" strokeLinecap="round"
      />
    </g>
  )
}

// ====== 主组件 ======
export default function CharacterGroup({ userNameFocused = false, pwFocused = false, className = '' }) {
  const groupRef = useRef(null)
  const [mouse, setMouse] = useState({ x: 0, y: 0 })
  const [groupRect, setGroupRect] = useState(null)

  // 记录容器位置
  useEffect(() => {
    if (!groupRef.current) return
    const update = () => {
      if (groupRef.current) setGroupRect(groupRef.current.getBoundingClientRect())
    }
    update()
    window.addEventListener('resize', update)
    return () => window.removeEventListener('resize', update)
  }, [])

  const handleMouseMove = useCallback((e) => {
    setMouse({ x: e.clientX, y: e.clientY })
  }, [])

  const hint = pwFocused
    ? '🙈 输入密码...我们闭眼啦！'
    : userNameFocused
      ? '👥 输入用户名...我们在看着你！'
      : '👀 嘿！看这里 ~'

  return (
    <div className={`character-group ${className}`}>
      <div ref={groupRef} className="char-svg-wrap" onMouseMove={handleMouseMove}>
        <svg viewBox="0 0 300 300" width="100%" height="100%" style={{ overflow: 'visible' }}>
          {CHARS.map((ch, i) => (
            <GeoChar
              key={ch.id}
              ch={ch}
              layout={LAYOUT[i]}
              mouse={mouse}
              groupRect={groupRect}
            />
          ))}
        </svg>
      </div>

      <div className="char-group-hint">{hint}</div>
    </div>
  )
}
