// Headless 截图：验证"当前课程页面"(StudyHomePage) 深色模式
const { chromium } = require('playwright')
const fs = require('fs')

const SHOTS = 'd:/git_projectrjb/projectrjb/shots'
fs.mkdirSync(SHOTS, { recursive: true })

async function login() {
  const resp = await fetch('http://localhost:8000/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: 'student', password: 'student123' }),
  })
  const body = await resp.json()
  if (!body.success) throw new Error('login failed: ' + JSON.stringify(body))
  return body.data
}

(async () => {
  const session = await login()
  const courseId = session.user.active_course?.id || session.user.courses?.[0]?.id
  console.log('courseId=', courseId)

  const browser = await chromium.launch()
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } })
  const page = await ctx.newPage()

  await page.goto('http://localhost:5173/login', { waitUntil: 'domcontentloaded' })
  await page.evaluate((s) => {
    localStorage.setItem('auth_token', s.token)
    localStorage.setItem('auth_user', JSON.stringify(s.user))
    localStorage.setItem('app-theme', 'dark')
  }, session)

  // 当前课程页面（会自动跳到 /learn/:taskId）
  await page.goto(`http://localhost:5173/course/${courseId}`, { waitUntil: 'domcontentloaded' })
  await page.waitForTimeout(3500)
  await page.screenshot({ path: `${SHOTS}/study-home-dark-before.png`, fullPage: true })
  console.log('shot: study-home-dark-before.png  url=', page.url())

  await browser.close()
  console.log('done')
})().catch((e) => { console.error(e); process.exit(1) })
