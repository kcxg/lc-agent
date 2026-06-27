import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = dirname(dirname(fileURLToPath(import.meta.url)))
const read = path => readFileSync(join(root, path), 'utf8')

const files = {
  http: read('src/api/http.ts'),
  router: read('src/router/index.ts'),
  authStore: read('src/stores/auth.ts'),
  loginView: read('src/views/LoginView.vue'),
  app: read('src/App.vue'),
  header: read('src/components/layout/AppHeader.vue'),
}

const failures = []
function expectIncludes(name, content, expected) {
  if (!content.includes(expected)) failures.push(`${name} 缺少: ${expected}`)
}
function expectMatch(name, content, pattern, message) {
  if (!pattern.test(content)) failures.push(`${name} ${message}`)
}

expectIncludes('http.ts', files.http, "credentials: 'same-origin'")
expectIncludes('http.ts', files.http, 'login:')
expectIncludes('http.ts', files.http, 'logout:')
expectIncludes('http.ts', files.http, 'getAuthState:')
expectIncludes('router/index.ts', files.router, "path: '/login'")
expectIncludes('router/index.ts', files.router, 'beforeEach')
expectIncludes('auth.ts', files.authStore, "defineStore('auth'")
expectIncludes('auth.ts', files.authStore, 'async function refreshAuth()')
expectIncludes('auth.ts', files.authStore, 'async function login(')
expectIncludes('auth.ts', files.authStore, 'async function logout()')
expectMatch('LoginView.vue', files.loginView, /<el-form[\s\S]*@submit\.prevent=/, '应使用表单提交登录')
expectIncludes('App.vue', files.app, 'useAuthStore')
expectIncludes('App.vue', files.app, 'authStore.authenticated')
expectIncludes('App.vue', files.app, 'async function handleLogout()')
expectIncludes('AppHeader.vue', files.header, 'logout: []')
expectIncludes('AppHeader.vue', files.header, '@click="$emit(\'logout\')"')

if (failures.length > 0) {
  console.error('认证前端契约测试失败:')
  for (const failure of failures) console.error(`- ${failure}`)
  process.exit(1)
}
console.log('认证前端契约测试通过')
