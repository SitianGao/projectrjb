/**
 * Playwright 脚本 —— 截图前端应用关键页面
 *
 * 用法: npx playwright test --config=... 或直接 node capture.mjs
 * 更简单的方式: 直接用 playwright 的 chromium 启动器
 */
import { chromium } from 'playwright';
import { mkdirSync } from 'fs';

const BASE = 'http://localhost:5174';
const OUT = 'd:/projectrjb/screenshots';
mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  locale: 'zh-CN',
});

const page = await context.newPage();

// ==== 1. 仪表盘首页 ====
console.log('1. 仪表盘首页...');
await page.goto(BASE + '/', { waitUntil: 'networkidle' });
await page.waitForTimeout(1000);
await page.screenshot({ path: OUT + '/01-home.png', fullPage: false });
console.log('   ✓ 01-home.png');

// ==== 2. 学生画像页（空白状态） ====
console.log('2. 学生画像页...');
await page.goto(BASE + '/profile', { waitUntil: 'networkidle' });
await page.waitForTimeout(1000);
await page.screenshot({ path: OUT + '/02-profile-empty.png', fullPage: false });
console.log('   ✓ 02-profile-empty.png');

// ==== 3. 发送对话消息 ====
console.log('3. 发送对话消息...');
const inputArea = page.locator('textarea').first();
await inputArea.waitFor({ timeout: 5000 });
await inputArea.fill('你好，我是大二计算机专业的学生，Python基础还可以，数学不太好，微积分和概率论都比较薄弱。平时喜欢看B站视频学习，对NLP和计算机视觉很感兴趣。');
await page.waitForTimeout(300);

// 点击发送按钮
const sendBtn = page.locator('button').filter({ has: page.locator('.anticon-send, [data-icon="send"]') }).first();
// or find by type
const sendButton = page.locator('button[type="primary"]').last();
await sendButton.click();
console.log('   消息已发送，等待响应...');

// 等待响应（SSE流式返回）
await page.waitForTimeout(5000);
await page.screenshot({ path: OUT + '/03-profile-chat.png', fullPage: false });
console.log('   ✓ 03-profile-chat.png');

// ==== 4. 学习路径页 ====
console.log('4. 学习路径页...');
await page.goto(BASE + '/learning-path', { waitUntil: 'networkidle' });
await page.waitForTimeout(1000);
await page.screenshot({ path: OUT + '/04-learning-path.png', fullPage: false });
console.log('   ✓ 04-learning-path.png');

// ==== 5. 学习资源页 ====
console.log('5. 学习资源页...');
await page.goto(BASE + '/resources', { waitUntil: 'networkidle' });
await page.waitForTimeout(1000);
await page.screenshot({ path: OUT + '/05-resources.png', fullPage: false });
console.log('   ✓ 05-resources.png');

// ==== 6. 智能辅导页 ====
console.log('6. 智能辅导页...');
await page.goto(BASE + '/tutor', { waitUntil: 'networkidle' });
await page.waitForTimeout(1000);
await page.screenshot({ path: OUT + '/06-tutor.png', fullPage: false });
console.log('   ✓ 06-tutor.png');

// ==== 7. 学习评估页 ====
console.log('7. 学习评估页...');
await page.goto(BASE + '/evaluate', { waitUntil: 'networkidle' });
await page.waitForTimeout(1000);
await page.screenshot({ path: OUT + '/07-evaluate.png', fullPage: false });
console.log('   ✓ 07-evaluate.png');

await browser.close();
console.log('\n所有截图已保存到 ' + OUT);
