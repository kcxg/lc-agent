// 文件类型徽标映射：按后缀/文件名给出「短标签 + 品牌色」。
// 徽标风格参考编辑器图标主题（Seti 一类），零依赖且能覆盖任意后缀。

export interface FileTypeMeta {
  /** 徽标内文字，1–5 个字符 */
  label: string
  /** 品牌色，用于文字色与底色推导 */
  color: string
}

const DEFAULT_COLOR = '#8f8f8f'

// 无扩展名或需整体识别的文件
const SPECIAL_FILES: Record<string, FileTypeMeta> = {
  '.gitignore': { label: 'GIT', color: '#f14e32' },
  '.gitattributes': { label: 'GIT', color: '#f14e32' },
  '.gitmodules': { label: 'GIT', color: '#f14e32' },
  '.dockerignore': { label: 'DKR', color: '#2496ed' },
  '.editorconfig': { label: 'EDC', color: '#8f8f8f' },
  'dockerfile': { label: 'DKR', color: '#2496ed' },
  'makefile': { label: 'MAKE', color: '#b45309' },
  'license': { label: 'LIC', color: '#d4a017' },
  'procfile': { label: 'PRC', color: '#6a4c93' },
}

const EXT_META: Record<string, FileTypeMeta> = {
  // 脚本与语言
  py: { label: 'PY', color: '#4b8bbe' },
  pyi: { label: 'PY', color: '#4b8bbe' },
  ipynb: { label: 'IPYNB', color: '#f37626' },
  ts: { label: 'TS', color: '#3178c6' },
  tsx: { label: 'TSX', color: '#3178c6' },
  js: { label: 'JS', color: '#e8c547' },
  mjs: { label: 'JS', color: '#e8c547' },
  cjs: { label: 'JS', color: '#e8c547' },
  jsx: { label: 'JSX', color: '#61dafb' },
  vue: { label: 'VUE', color: '#41b883' },
  java: { label: 'JAVA', color: '#e76f00' },
  kt: { label: 'KT', color: '#a97bff' },
  kts: { label: 'KT', color: '#a97bff' },
  scala: { label: 'SCALA', color: '#c22d40' },
  go: { label: 'GO', color: '#00add8' },
  rs: { label: 'RS', color: '#dea584' },
  rb: { label: 'RB', color: '#cc342d' },
  php: { label: 'PHP', color: '#8892bf' },
  cs: { label: 'C#', color: '#9b4f96' },
  c: { label: 'C', color: '#599eff' },
  h: { label: 'H', color: '#599eff' },
  cpp: { label: 'C++', color: '#f34b7d' },
  cc: { label: 'C++', color: '#f34b7d' },
  cxx: { label: 'C++', color: '#f34b7d' },
  hpp: { label: 'H++', color: '#f34b7d' },
  swift: { label: 'SWIFT', color: '#f05138' },
  dart: { label: 'DART', color: '#00b4ab' },
  lua: { label: 'LUA', color: '#4b6fbf' },
  r: { label: 'R', color: '#276dc3' },
  m: { label: 'OBJ', color: '#438eff' },

  // 标记与样式
  md: { label: 'MD', color: '#519aba' },
  markdown: { label: 'MD', color: '#519aba' },
  rst: { label: 'RST', color: '#519aba' },
  html: { label: 'HTML', color: '#e44d26' },
  htm: { label: 'HTML', color: '#e44d26' },
  css: { label: 'CSS', color: '#519aba' },
  scss: { label: 'SCSS', color: '#c6538c' },
  sass: { label: 'SASS', color: '#c6538c' },
  less: { label: 'LESS', color: '#519aba' },
  xml: { label: 'XML', color: '#8dc149' },

  // 配置与数据
  json: { label: 'JSON', color: '#cbcb41' },
  jsonc: { label: 'JSON', color: '#cbcb41' },
  json5: { label: 'JSON', color: '#cbcb41' },
  yml: { label: 'YML', color: '#cb6b16' },
  yaml: { label: 'YML', color: '#cb6b16' },
  toml: { label: 'TOML', color: '#9c6b4e' },
  ini: { label: 'INI', color: '#8f8f8f' },
  conf: { label: 'CONF', color: '#8f8f8f' },
  cfg: { label: 'CFG', color: '#8f8f8f' },
  env: { label: 'ENV', color: '#8f8f8f' },
  properties: { label: 'PRP', color: '#8f8f8f' },
  csv: { label: 'CSV', color: '#89a832' },
  tsv: { label: 'TSV', color: '#89a832' },
  db: { label: 'DB', color: '#e38c00' },
  sqlite: { label: 'DB', color: '#e38c00' },
  sql: { label: 'SQL', color: '#e38c00' },

  // 脚本与命令行
  sh: { label: 'SH', color: '#89e051' },
  bash: { label: 'BASH', color: '#89e051' },
  zsh: { label: 'ZSH', color: '#89e051' },
  ps1: { label: 'PS1', color: '#4b7fc4' },
  bat: { label: 'BAT', color: '#8aa832' },
  cmd: { label: 'CMD', color: '#8aa832' },

  // 资源与二进制
  png: { label: 'IMG', color: '#a074c4' },
  jpg: { label: 'IMG', color: '#a074c4' },
  jpeg: { label: 'IMG', color: '#a074c4' },
  gif: { label: 'IMG', color: '#a074c4' },
  webp: { label: 'IMG', color: '#a074c4' },
  bmp: { label: 'IMG', color: '#a074c4' },
  ico: { label: 'IMG', color: '#a074c4' },
  svg: { label: 'SVG', color: '#d9a03c' },
  pdf: { label: 'PDF', color: '#d9534f' },
  zip: { label: 'ZIP', color: '#af8c00' },
  tar: { label: 'TAR', color: '#af8c00' },
  gz: { label: 'GZ', color: '#af8c00' },
  rar: { label: 'RAR', color: '#af8c00' },
  '7z': { label: '7Z', color: '#af8c00' },
  whl: { label: 'WHL', color: '#4b8bbe' },
  exe: { label: 'EXE', color: '#8f8f8f' },
  dll: { label: 'DLL', color: '#8f8f8f' },

  // 文本与日志
  txt: { label: 'TXT', color: '#8f8f8f' },
  log: { label: 'LOG', color: '#8f8f8f' },
  out: { label: 'OUT', color: '#8f8f8f' },
  err: { label: 'ERR', color: '#d9534f' },
  lock: { label: 'LOCK', color: '#8f8f8f' },
  pid: { label: 'PID', color: '#8f8f8f' },
}

/** 取小写文件名（不含目录） */
function baseName(name: string): string {
  const normalized = name.replace(/\\/g, '/')
  const idx = normalized.lastIndexOf('/')
  return (idx === -1 ? normalized : normalized.slice(idx + 1)).toLowerCase()
}

/**
 * 由文件名推导徽标元信息。
 * 未知后缀回退为「后缀大写」，无后缀回退为文件名首字母缩写。
 */
export function fileTypeMeta(name: string): FileTypeMeta {
  const base = baseName(name)
  if (!base) return { label: '?', color: DEFAULT_COLOR }

  const special = SPECIAL_FILES[base]
  if (special) return special

  const dot = base.lastIndexOf('.')
  // dot <= 0 覆盖「无扩展名」与「点开头的隐藏文件」
  if (dot <= 0 || dot === base.length - 1) {
    return { label: base.replace(/^\./, '').slice(0, 3).toUpperCase() || '?', color: DEFAULT_COLOR }
  }

  const ext = base.slice(dot + 1)
  return EXT_META[ext] || { label: ext.slice(0, 5).toUpperCase(), color: DEFAULT_COLOR }
}
