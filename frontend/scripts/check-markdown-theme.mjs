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
  markdownLayout: read('src/composables/useMarkdownLayout.ts'),
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

function expectCount(name, content, pattern, expected, message) {
  const actual = content.match(pattern)?.length ?? 0
  if (actual !== expected) {
    failures.push(`${name} ${message}，期望 ${expected} 处，实际 ${actual} 处`)
  }
}

expectNotIncludes('markdown.ts', files.markdown, 'highlight.js/styles/github')
expectIncludes('markdown.ts', files.markdown, 'markdown-code-block')
expectIncludes('markdown.ts', files.markdown, 'markdown-code-toolbar')
expectIncludes('markdown.ts', files.markdown, 'markdown-code-copy')
expectIncludes('markdown.ts', files.markdown, 'data-code')
expectIncludes('markdown.ts', files.markdown, 'language-')
expectIncludes('markdown.ts', files.markdown, 'data-lc-file-path')

expectIncludes('useMarkdownTheme.ts', files.markdownTheme, 'MARKDOWN_THEME_OPTIONS')
expectIncludes('useMarkdownTheme.ts', files.markdownTheme, 'lc-agent:markdown-theme')
expectIncludes('useMarkdownTheme.ts', files.markdownTheme, 'document.documentElement.dataset.mdTheme')
expectIncludes('useMarkdownTheme.ts', files.markdownTheme, 'Mist Blue')
expectIncludes('useMarkdownTheme.ts', files.markdownTheme, 'Sage')
expectIncludes('useMarkdownTheme.ts', files.markdownTheme, 'Graphite')
expectIncludes('useMarkdownTheme.ts', files.markdownTheme, 'Warm Gray')
expectIncludes('useMarkdownTheme.ts', files.markdownTheme, 'Rosewood')
expectIncludes('useMarkdownTheme.ts', files.markdownTheme, 'Paper')
expectIncludes('useMarkdownTheme.ts', files.markdownTheme, 'Sepia')
expectIncludes('useMarkdownTheme.ts', files.markdownTheme, 'Slate')
expectIncludes('useMarkdownTheme.ts', files.markdownTheme, 'Ocean Ink')
expectIncludes('useMarkdownTheme.ts', files.markdownTheme, 'Night Ink')
expectIncludes('useMarkdownTheme.ts', files.markdownTheme, "'graphite'")
expectIncludes('useMarkdownTheme.ts', files.markdownTheme, "'ocean-ink'")
expectIncludes('useMarkdownTheme.ts', files.markdownTheme, "DEFAULT_THEME: MarkdownThemeId = 'graphite'")
expectNotIncludes('useMarkdownTheme.ts', files.markdownTheme, 'Aurora Blast')
expectNotIncludes('useMarkdownTheme.ts', files.markdownTheme, 'Neon Future')
expectNotIncludes('useMarkdownTheme.ts', files.markdownTheme, "'aurora'")
expectNotIncludes('useMarkdownTheme.ts', files.markdownTheme, "'solar'")

expectIncludes('useMarkdownLayout.ts', files.markdownLayout, "'github-docs'")
expectIncludes('useMarkdownLayout.ts', files.markdownLayout, "'notion-editorial'")
expectIncludes('useMarkdownLayout.ts', files.markdownLayout, "'obsidian-reading'")
expectIncludes('useMarkdownLayout.ts', files.markdownLayout, "'typora-paper'")
expectIncludes('useMarkdownLayout.ts', files.markdownLayout, "'gitbook-guides'")
expectIncludes('useMarkdownLayout.ts', files.markdownLayout, "'vitepress-technical'")
expectIncludes('useMarkdownLayout.ts', files.markdownLayout, "'docusaurus-docs'")
expectIncludes('useMarkdownLayout.ts', files.markdownLayout, "'hackmd-collaboration'")
expectIncludes('useMarkdownLayout.ts', files.markdownLayout, "'stackedit-focus'")
expectIncludes('useMarkdownLayout.ts', files.markdownLayout, "'joplin-notes'")
expectIncludes('useMarkdownLayout.ts', files.markdownLayout, 'GitHub Docs')
expectIncludes('useMarkdownLayout.ts', files.markdownLayout, 'Notion Editorial')
expectIncludes('useMarkdownLayout.ts', files.markdownLayout, 'Obsidian Reading')
expectIncludes('useMarkdownLayout.ts', files.markdownLayout, 'Typora Paper')
expectIncludes('useMarkdownLayout.ts', files.markdownLayout, 'GitBook Guides')
expectIncludes('useMarkdownLayout.ts', files.markdownLayout, 'VitePress Technical')
expectIncludes('useMarkdownLayout.ts', files.markdownLayout, 'Docusaurus Docs')
expectIncludes('useMarkdownLayout.ts', files.markdownLayout, 'HackMD Collaboration')
expectIncludes('useMarkdownLayout.ts', files.markdownLayout, 'StackEdit Focus')
expectIncludes('useMarkdownLayout.ts', files.markdownLayout, 'Joplin Notes')
expectIncludes('useMarkdownLayout.ts', files.markdownLayout, "'lc-agent:markdown-layout'")
expectIncludes('useMarkdownLayout.ts', files.markdownLayout, "DEFAULT_LAYOUT: MarkdownLayoutId = 'notion-editorial'")
expectIncludes('useMarkdownLayout.ts', files.markdownLayout, 'document.documentElement.dataset.mdLayout')

expectIncludes('markdown-theme.css', files.theme, '--md-text')
expectIncludes('markdown-theme.css', files.theme, '--md-muted')
expectIncludes('markdown-theme.css', files.theme, '--md-code-bg')
expectIncludes('markdown-theme.css', files.theme, '--md-link')
expectIncludes('markdown-theme.css', files.theme, '.markdown-code-block')
expectIncludes('markdown-theme.css', files.theme, '.markdown-code-toolbar')
expectIncludes('markdown-theme.css', files.theme, '.markdown-code-copy')
expectIncludes('markdown-theme.css', files.theme, '.answer-markdown')
expectIncludes('markdown-theme.css', files.theme, 'data-md-layout="github-docs"')
expectIncludes('markdown-theme.css', files.theme, 'data-md-layout="obsidian-reading"')
expectIncludes('markdown-theme.css', files.theme, 'data-md-layout="typora-paper"')
expectIncludes('markdown-theme.css', files.theme, 'data-md-layout="gitbook-guides"')
expectIncludes('markdown-theme.css', files.theme, 'data-md-layout="vitepress-technical"')
expectIncludes('markdown-theme.css', files.theme, 'data-md-layout="docusaurus-docs"')
expectIncludes('markdown-theme.css', files.theme, 'data-md-layout="hackmd-collaboration"')
expectIncludes('markdown-theme.css', files.theme, 'data-md-layout="stackedit-focus"')
expectIncludes('markdown-theme.css', files.theme, 'data-md-layout="joplin-notes"')
expectIncludes('markdown-theme.css', files.theme, 'max-width: 860px')
expectIncludes('markdown-theme.css', files.theme, 'max-width: 920px')
expectIncludes('markdown-theme.css', files.theme, 'font-family: Inter')
expectIncludes('markdown-theme.css', files.theme, '@media (max-width: 996px)')
expectIncludes('markdown-theme.css', files.theme, 'border-collapse: separate')
expectIncludes('markdown-theme.css', files.theme, 'border-radius: 14px')
expectIncludes('markdown-theme.css', files.theme, 'data-md-theme="mist-blue"')
expectIncludes('markdown-theme.css', files.theme, 'data-md-theme="sage"')
expectIncludes('markdown-theme.css', files.theme, 'data-md-theme="graphite"')
expectIncludes('markdown-theme.css', files.theme, 'data-md-theme="warm-gray"')
expectIncludes('markdown-theme.css', files.theme, 'data-md-theme="rosewood"')
expectIncludes('markdown-theme.css', files.theme, 'data-md-theme="paper"')
expectIncludes('markdown-theme.css', files.theme, 'data-md-theme="sepia"')
expectIncludes('markdown-theme.css', files.theme, 'data-md-theme="slate"')
expectIncludes('markdown-theme.css', files.theme, 'data-md-theme="ocean-ink"')
expectIncludes('markdown-theme.css', files.theme, 'data-md-theme="night-ink"')
expectNotIncludes('markdown-theme.css', files.theme, 'data-md-theme="aurora"')
expectNotIncludes('markdown-theme.css', files.theme, 'data-md-theme="solar"')
expectMatch('markdown-theme.css', files.theme, /html\.dark[\s\S]*--md-code-bg/, '缺少暗色主题 Markdown 变量')
expectMatch('markdown-theme.css', files.theme, /html:not\(\.dark\)[\s\S]*--md-code-bg/, '缺少亮色主题 Markdown 变量')
expectMatch('markdown-theme.css', files.theme, /\.hljs-keyword[\s\S]*color:/, '缺少自定义 highlight.js token 颜色')
expectNotIncludes('markdown-theme.css', files.theme, '#f6f8fa')
expectNotIncludes('markdown-theme.css', files.theme, '#24292f')

expectIncludes('RightPanel.vue', files.rightPanel, 'Markdown 版式')
expectIncludes('RightPanel.vue', files.rightPanel, 'Markdown 色盘')
expectIncludes('RightPanel.vue', files.rightPanel, '窗口裁剪模型')
expectIncludes('RightPanel.vue', files.rightPanel, 'window-trim-section')
expectIncludes('RightPanel.vue', files.rightPanel, 'window-trim-control')
expectIncludes('RightPanel.vue', files.rightPanel, 'markdown-theme-section')
expectIncludes('RightPanel.vue', files.rightPanel, 'MARKDOWN_THEME_OPTIONS')
expectIncludes('RightPanel.vue', files.rightPanel, 'MARKDOWN_LAYOUT_OPTIONS')
expectIncludes('RightPanel.vue', files.rightPanel, 'markdownTheme')
expectIncludes('RightPanel.vue', files.rightPanel, 'markdownLayout')
expectIncludes('RightPanel.vue', files.rightPanel, 'useMarkdownLayout')
expectNotIncludes('RightPanel.vue', files.rightPanel, 'Markdown 风格')
expectNotIncludes('RightPanel.vue', files.rightPanel, '上下文摘要')
expectNotIncludes('RightPanel.vue', files.rightPanel, '摘要模型')
expectNotIncludes('RightPanel.vue', files.rightPanel, 'md-theme-card')

expectIncludes('ChatView.vue', files.chatView, 'markdown-code-block')
expectIncludes('ChatView.vue', files.chatView, 'markdown-code-copy')
expectIncludes('ChatView.vue', files.chatView, 'openProjectMarkdownFile')
expectIncludes('ChatView.vue', files.chatView, 'answer-markdown')
expectCount('ChatView.vue', files.chatView, /class="markdown-body answer-markdown"/g, 2, '最终回答样式作用域不正确')
expectIncludes('ChatView.vue', files.chatView, '.markdown-body:not(.answer-markdown) blockquote')
expectMatch('ChatView.vue', files.chatView, /v-if="item\.isSystem"[\s\S]*?class="markdown-body"/, '系统消息不应使用最终回答样式')
expectMatch('ChatView.vue', files.chatView, /seg\.type === 'thinking'[\s\S]*?class="markdown-body thinking-body"/, '思考过程不应使用最终回答样式')

if (failures.length > 0) {
  console.error('Markdown 主题契约测试失败:')
  for (const failure of failures) {
    console.error(`- ${failure}`)
  }
  process.exit(1)
}

console.log('Markdown 主题契约测试通过')
