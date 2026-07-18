// Headless 截图脚本：验证深色模式下资源中心 & 学习路径页
const { chromium } = require('playwright')
const fs = require('fs')

const SHOTS = 'd:/git_projectrjb/projectrjb/shots'
fs.mkdirSync(SHOTS, { recursive: true })

async function login() {
  const resp = await fetch('http://localhost:8000/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: 'demo_student', password: 'demo123' }),
  })
  const body = await resp.json()
  if (!body.success) throw new Error('login failed: ' + JSON.stringify(body))
  return body.data // { token, user }
}

(async () => {
  const session = await login()
  console.log('logged in as', session.user.username, 'student_id=', session.user.student_id)
  const courseId = session.user.active_course?.id || session.user.courses?.[0]?.id
  console.log('courseId=', courseId)

  const browser = await chromium.launch()
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } })
  const page = await ctx.newPage()

  // 先打开任意页建立 origin，注入登录态 + 深色主题
  await page.goto('http://localhost:5173/login', { waitUntil: 'domcontentloaded' })
  await page.evaluate((s) => {
    localStorage.setItem('auth_token', s.token)
    localStorage.setItem('auth_user', JSON.stringify(s.user))
    localStorage.setItem('app-theme', 'dark')
  }, session)

  // 资源中心
  await page.goto('http://localhost:5173/resources', { waitUntil: 'domcontentloaded' })
  await page.waitForTimeout(2500)
  await page.screenshot({ path: `${SHOTS}/resources-dark.png`, fullPage: true })
  console.log('shot: resources-dark.png')

  // 学习路径页（需先激活课程上下文）
  if (courseId) {
    await page.goto(`http://localhost:5173/course/${courseId}/path`, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(3000)
    await page.screenshot({ path: `${SHOTS}/learning-path-dark.png`, fullPage: true })
    console.log('shot: learning-path-dark.png')
  }

  await browser.close()
  console.log('done')
})().catch((e) => { console.error(e); process.exit(1) })
