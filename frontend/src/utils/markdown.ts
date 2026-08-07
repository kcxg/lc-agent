import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js/lib/core'
// 按需注册常用语言，避免全量引入 ~190 种语言（节省 ~100KB gzipped）
import javascript from 'highlight.js/lib/languages/javascript'
import typescript from 'highlight.js/lib/languages/typescript'
import python from 'highlight.js/lib/languages/python'
import bash from 'highlight.js/lib/languages/bash'
import json from 'highlight.js/lib/languages/json'
import yaml from 'highlight.js/lib/languages/yaml'
import xml from 'highlight.js/lib/languages/xml'
import sql from 'highlight.js/lib/languages/sql'
import markdown from 'highlight.js/lib/languages/markdown'
import css from 'highlight.js/lib/languages/css'
import shell from 'highlight.js/lib/languages/shell'
import ini from 'highlight.js/lib/languages/ini'

hljs.registerLanguage('javascript', javascript)
hljs.registerLanguage('js', javascript)
hljs.registerLanguage('typescript', typescript)
hljs.registerLanguage('ts', typescript)
hljs.registerLanguage('python', python)
hljs.registerLanguage('py', python)
hljs.registerLanguage('bash', bash)
hljs.registerLanguage('sh', bash)
hljs.registerLanguage('shell', shell)
hljs.registerLanguage('json', json)
hljs.registerLanguage('yaml', yaml)
hljs.registerLanguage('yml', yaml)
hljs.registerLanguage('xml', xml)
hljs.registerLanguage('html', xml)
hljs.registerLanguage('sql', sql)
hljs.registerLanguage('markdown', markdown)
hljs.registerLanguage('md', markdown)
hljs.registerLanguage('css', css)
hljs.registerLanguage('ini', ini)
hljs.registerLanguage('toml', ini)
hljs.registerLanguage('env', bash)

function escapeAttr(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

function normalizeLanguage(lang: string): string {
  return lang.trim().split(/\s+/)[0]?.toLowerCase() || ''
}

function renderCodeBlock(source: string, lang: string): string {
  const language = normalizeLanguage(lang)
  const knownLanguage = language && hljs.getLanguage(language)
  const highlighted = knownLanguage
    ? hljs.highlight(source, { language }).value
    : md.utils.escapeHtml(source)
  const label = language || 'text'
  const languageClass = language ? ` language-${escapeAttr(language)}` : ''
  const encodedSource = escapeAttr(encodeURIComponent(source))

  return [
    `<div class="markdown-code-block" data-language="${escapeAttr(label)}">`,
    '<div class="markdown-code-toolbar">',
    '<span class="markdown-code-window" aria-hidden="true"><i></i><i></i><i></i></span>',
    `<span class="markdown-code-language">${escapeAttr(label)}</span>`,
    `<button class="markdown-code-expand" type="button" data-code="${encodedSource}" data-lang="${escapeAttr(label)}" aria-label="展开源码">⛶</button>`,
    `<button class="markdown-code-copy" type="button" data-code="${encodedSource}" aria-label="复制代码">复制</button>`,
    '</div>',
    `<pre class="hljs"><code class="hljs${languageClass}">${highlighted}</code></pre>`,
    '</div>',
  ].join('')
}

const md: MarkdownIt = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true,
  highlight(str: string, lang: string): string {
    try {
      return renderCodeBlock(str, lang)
    } catch {
      return renderCodeBlock(str, '')
    }
  },
})

const defaultLinkOpen =
  md.renderer.rules.link_open ||
  ((tokens, idx, options, _env, self) => self.renderToken(tokens, idx, options))

function getProjectMarkdownLinkPath(tokens: any[], idx: number, href: string): string | null {
  const token = tokens[idx]
  const explicitPath = href.split(/[?#]/, 1)[0]

  if (
    explicitPath
    && !/^[a-z][a-z0-9+.-]*:/i.test(explicitPath)
    && !explicitPath.startsWith('/')
    && !explicitPath.startsWith('\\')
    && /\.md(?:own)?$/i.test(explicitPath)
  ) {
    return explicitPath
  }

  if (token.markup !== 'linkify') return null

  const label = tokens[idx + 1]?.content?.trim()
  if (!label || !/\.md(?:own)?$/i.test(label)) return null

  try {
    const parsed = new URL(href)
    if (
      parsed.protocol === 'http:'
      && parsed.pathname === '/'
      && !parsed.search
      && !parsed.hash
      && parsed.hostname.toLowerCase() === label.toLowerCase()
    ) {
      return label
    }
  } catch {
    return null
  }

  return null
}

md.renderer.rules.link_open = (tokens, idx, options, env, self) => {
  const href = tokens[idx].attrGet('href') || ''
  const projectFilePath = getProjectMarkdownLinkPath(tokens, idx, href)

  if (projectFilePath) {
    tokens[idx].attrSet('href', '#')
    tokens[idx].attrSet('data-lc-file-path', projectFilePath)
    tokens[idx].attrSet('title', `在应用内预览 ${projectFilePath}`)
    return defaultLinkOpen(tokens, idx, options, env, self)
  }

  let isExternal = false
  if (/^https?:\/\//i.test(href) || href.startsWith('//')) {
    try {
      const base = globalThis.location?.origin
      isExternal = !base || new URL(href, base).origin !== base
    } catch {
      isExternal = true
    }
  }

  if (isExternal) {
    tokens[idx].attrSet('target', '_blank')
    tokens[idx].attrSet('rel', 'noopener noreferrer')
  }

  return defaultLinkOpen(tokens, idx, options, env, self)
}

export function renderMarkdown(text: string): string {
  return md.render(text)
}
