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

export function renderMarkdown(text: string): string {
  return md.render(text)
}
