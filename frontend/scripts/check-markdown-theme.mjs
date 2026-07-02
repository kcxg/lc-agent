import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = dirname(dirname(fileURLToPath(import.meta.url)))

function read(relativePath) {
  return readFileSync(join(root, relativePath), 'utf8')
}

const files = {
  markdown: read('src/utils/markdown.ts'),
  theme: read('src/styles/markdown-theme.css'),
  markdownTheme: read('src/composables/useMarkdownTheme.ts'),
  rightPanel: read('src/components/layout/RightPanel.vue'),
  chatView: read('src/views/ChatView.vue'),
}

const failures = []

function expectIncludes(name, content, expected) {
  if (!content.includes(expected)) {
    failures.push(`${name} 缺少: ${expected}`)
  }
}

function expectNotIncludes(name, content, unexpected) {
  if (content.includes(unexpected)) {
    failures.push(`${name} 不应包含: ${unexpected}`)
  }
}

function expectMatch(name, content, pattern, message) {
  if (!pattern.test(content)) {
    failures.push(`${name} ${message}`)
  }
}

expectNotIncludes('markdown.ts', files.markdown, 'highlight.js/styles/github')
expectIncludes('markdown.ts', files.markdown, 'markdown-code-block')
expectIncludes('markdown.ts', files.markdown, 'markdown-code-toolbar')
expectIncludes('markdown.ts', files.markdown, 'markdown-code-copy')
expectIncludes('markdown.ts', files.markdown, 'data-code')
expectIncludes('markdown.ts', files.markdown, 'language-')

expectIncludes('useMarkdownTheme.ts', files.markdownTheme, 'MARKDOWN_THEME_OPTIONS')
expectIncludes('useMarkdownTheme.ts', files.markdownTheme, 'lc-agent:markdown-theme')
expectIncludes('useMarkdownTheme.ts', files.markdownTheme, 'document.documentElement.dataset.mdTheme')
expectIncludes('useMarkdownTheme.ts', files.markdownTheme, 'Arctic Blue')
expectIncludes('useMarkdownTheme.ts', files.markdownTheme, 'Cyber Mint')
expectIncludes('useMarkdownTheme.ts', files.markdownTheme, 'Aurora Blast')
expectIncludes('useMarkdownTheme.ts', files.markdownTheme, 'Neon Future')
expectIncludes('useMarkdownTheme.ts', files.markdownTheme, 'Sunset Chrome')
expectIncludes('useMarkdownTheme.ts', files.markdownTheme, 'Paper Luxe')
expectIncludes('useMarkdownTheme.ts', files.markdownTheme, 'Lime Surge')
expectIncludes('useMarkdownTheme.ts', files.markdownTheme, 'Prism White')
expectIncludes('useMarkdownTheme.ts', files.markdownTheme, 'Lava Pulse')
expectIncludes('useMarkdownTheme.ts', files.markdownTheme, 'Solar Flare')
expectIncludes('useMarkdownTheme.ts', files.markdownTheme, "'lime'")
expectIncludes('useMarkdownTheme.ts', files.markdownTheme, "'sky'")
expectIncludes('useMarkdownTheme.ts', files.markdownTheme, "'candy'")
expectIncludes('useMarkdownTheme.ts', files.markdownTheme, "'solar'")
expectNotIncludes('useMarkdownTheme.ts', files.markdownTheme, 'Sky Circuit')
expectNotIncludes('useMarkdownTheme.ts', files.markdownTheme, 'Candy Pop')
expectNotIncludes('useMarkdownTheme.ts', files.markdownTheme, 'GitHub Clean')
expectNotIncludes('useMarkdownTheme.ts', files.markdownTheme, 'Notion Soft')
expectNotIncludes('useMarkdownTheme.ts', files.markdownTheme, 'Aurora Pro')
expectNotIncludes('useMarkdownTheme.ts', files.markdownTheme, 'Obsidian Deep')

expectIncludes('markdown-theme.css', files.theme, '--md-text')
expectIncludes('markdown-theme.css', files.theme, '--md-muted')
expectIncludes('markdown-theme.css', files.theme, '--md-code-bg')
expectIncludes('markdown-theme.css', files.theme, '--md-link')
expectIncludes('markdown-theme.css', files.theme, '.markdown-code-block')
expectIncludes('markdown-theme.css', files.theme, '.markdown-code-toolbar')
expectIncludes('markdown-theme.css', files.theme, '.markdown-code-copy')
expectIncludes('markdown-theme.css', files.theme, 'border-collapse: separate')
expectIncludes('markdown-theme.css', files.theme, 'border-radius: 14px')
expectIncludes('markdown-theme.css', files.theme, 'data-md-theme="github"')
expectIncludes('markdown-theme.css', files.theme, 'data-md-theme="notion"')
expectIncludes('markdown-theme.css', files.theme, 'data-md-theme="aurora"')
expectIncludes('markdown-theme.css', files.theme, 'data-md-theme="neon"')
expectIncludes('markdown-theme.css', files.theme, 'data-md-theme="obsidian"')
expectIncludes('markdown-theme.css', files.theme, 'data-md-theme="paper"')
expectIncludes('markdown-theme.css', files.theme, 'data-md-theme="lime"')
expectIncludes('markdown-theme.css', files.theme, 'data-md-theme="sky"')
expectIncludes('markdown-theme.css', files.theme, 'data-md-theme="candy"')
expectIncludes('markdown-theme.css', files.theme, 'data-md-theme="solar"')
expectMatch('markdown-theme.css', files.theme, /html\.dark[\s\S]*--md-code-bg/, '缺少暗色主题 Markdown 变量')
expectMatch('markdown-theme.css', files.theme, /html:not\(\.dark\)[\s\S]*--md-code-bg/, '缺少亮色主题 Markdown 变量')
expectMatch('markdown-theme.css', files.theme, /\.hljs-keyword[\s\S]*color:/, '缺少自定义 highlight.js token 颜色')
expectNotIncludes('markdown-theme.css', files.theme, '#f6f8fa')
expectNotIncludes('markdown-theme.css', files.theme, '#24292f')

expectIncludes('RightPanel.vue', files.rightPanel, 'Markdown 风格')
expectIncludes('RightPanel.vue', files.rightPanel, '窗口裁剪模型')
expectIncludes('RightPanel.vue', files.rightPanel, 'window-trim-section')
expectIncludes('RightPanel.vue', files.rightPanel, 'window-trim-control')
expectIncludes('RightPanel.vue', files.rightPanel, 'markdown-theme-section')
expectIncludes('RightPanel.vue', files.rightPanel, 'MARKDOWN_THEME_OPTIONS')
expectIncludes('RightPanel.vue', files.rightPanel, 'markdownTheme')
expectNotIncludes('RightPanel.vue', files.rightPanel, '上下文摘要')
expectNotIncludes('RightPanel.vue', files.rightPanel, '摘要模型')
expectNotIncludes('RightPanel.vue', files.rightPanel, 'md-theme-card')

expectIncludes('ChatView.vue', files.chatView, 'markdown-code-block')
expectIncludes('ChatView.vue', files.chatView, 'markdown-code-copy')

if (failures.length > 0) {
  console.error('Markdown 主题契约测试失败:')
  for (const failure of failures) {
    console.error(`- ${failure}`)
  }
  process.exit(1)
}

console.log('Markdown 主题契约测试通过')
