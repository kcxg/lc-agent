import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = dirname(dirname(fileURLToPath(import.meta.url)))
const chatView = readFileSync(join(root, 'src/views/ChatView.vue'), 'utf8')
const main = readFileSync(join(root, 'src/main.ts'), 'utf8')
const failures = []

if (!chatView.includes('max-width:min(560px, calc(100vw - 64px))')) {
  failures.push('聊天错误提示必须将 560px 桌面上限限制在窄视口可用宽度内')
}

if (!main.includes("import 'element-plus/es/components/message/style/css'")) {
  failures.push('程序式 ElMessage 必须显式导入消息组件样式，避免提示按普通 div 排版')
}

if (failures.length > 0) {
  console.error('聊天错误提示布局契约测试失败:')
  for (const failure of failures) console.error(`- ${failure}`)
  process.exit(1)
}

console.log('聊天错误提示布局契约测试通过')
