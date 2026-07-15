/**
 * 附件处理工具：图片压缩、文本文件读取、content blocks 构造
 */

export interface ContentBlock {
  type: 'text' | 'image_url'
  text?: string
  image_url?: { url: string }
}

export interface Attachment {
  id: string
  type: 'image' | 'text_file'
  name: string
  // image 专属
  dataUrl?: string
  // text_file 专属
  textContent?: string
}

/** 支持的文本文件扩展名白名单 */
export const TEXT_EXTENSIONS = [
  'txt', 'md', 'markdown', 'json', 'yaml', 'yml', 'csv', 'log', 'xml', 'html', 'htm',
  'js', 'ts', 'jsx', 'tsx', 'py', 'go', 'rs', 'java', 'c', 'cpp', 'h', 'hpp', 'sh', 'sql',
  'css', 'scss', 'less', 'vue', 'toml', 'ini', 'conf',
]

/** 扩展名到代码块语言的映射 */
const EXT_TO_LANG: Record<string, string> = {
  js: 'javascript', ts: 'typescript', jsx: 'jsx', tsx: 'tsx',
  py: 'python', go: 'go', rs: 'rust', java: 'java',
  c: 'c', cpp: 'cpp', h: 'c', hpp: 'cpp',
  sh: 'bash', sql: 'sql', css: 'css', scss: 'scss',
  less: 'less', vue: 'vue', html: 'html', htm: 'html',
  xml: 'xml', json: 'json', yaml: 'yaml', yml: 'yaml',
  toml: 'toml', ini: 'ini', conf: 'ini',
  md: 'markdown', markdown: 'markdown',
}

/** 图片上限（软提示） */
export const MAX_IMAGE_COUNT = 9

/** 图片压缩最长边 */
const MAX_IMAGE_EDGE = 1280

/** 生成简单 uuid */
function genId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
}

/** 获取文件扩展名（小写，无点） */
export function getExtension(filename: string): string {
  const parts = filename.split('.')
  return parts.length > 1 ? parts.pop()!.toLowerCase() : ''
}

/** 判断文件是否为图片 */
export function isImageFile(file: File): boolean {
  return file.type.startsWith('image/')
}

/** 判断文件是否为白名单文本文件 */
export function isTextFile(file: File): boolean {
  const ext = getExtension(file.name)
  return TEXT_EXTENSIONS.includes(ext)
}

/** 压缩图片：最长边 1280，保留原格式 */
export async function compressImage(file: File): Promise<string> {
  const bitmap = await createImageBitmap(file)
  let { width, height } = bitmap
  if (width > MAX_IMAGE_EDGE || height > MAX_IMAGE_EDGE) {
    const ratio = Math.min(MAX_IMAGE_EDGE / width, MAX_IMAGE_EDGE / height)
    width = Math.round(width * ratio)
    height = Math.round(height * ratio)
  }
  const canvas = new OffscreenCanvas(width, height)
  const ctx = canvas.getContext('bitmaprenderer')
  if (!ctx) throw new Error('Canvas 2D context unavailable')
  ctx.transferFromImageBitmap(bitmap)
  // 保留原格式：png 输出 png，jpeg 输出 jpeg
  const blob = await canvas.convertToBlob({ type: file.type, quality: 0.8 })
  return await blobToDataURL(blob)
}

function blobToDataURL(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = () => reject(new Error('Failed to read blob as data URL'))
    reader.readAsDataURL(blob)
  })
}

/** 读取文本文件内容 */
export function readTextFile(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = () => reject(new Error(`Failed to read ${file.name}`))
    reader.readAsText(file, 'utf-8')
  })
}

/** 把 File 转为 Attachment */
export async function fileToAttachment(file: File): Promise<Attachment | null> {
  if (isImageFile(file)) {
    try {
      const dataUrl = await compressImage(file)
      return {
        id: genId(),
        type: 'image',
        name: file.name || `image-${Date.now()}.png`,
        dataUrl,
      }
    } catch (e) {
      console.error('Image compression failed:', e)
      return null
    }
  }
  if (isTextFile(file)) {
    try {
      const textContent = await readTextFile(file)
      return {
        id: genId(),
        type: 'text_file',
        name: file.name,
        textContent,
      }
    } catch (e) {
      console.error('Text file read failed:', e)
      return null
    }
  }
  return null
}

/** 批量处理文件 */
export async function filesToAttachments(files: File[]): Promise<{ attachments: Attachment[]; rejected: string[] }> {
  const attachments: Attachment[] = []
  const rejected: string[] = []
  for (const file of files) {
    const att = await fileToAttachment(file)
    if (att) {
      attachments.push(att)
    } else {
      rejected.push(file.name)
    }
  }
  return { attachments, rejected }
}

/** 从剪贴板 items 提取图片文件（只取图片，忽略文本） */
export function imageFilesFromClipboard(items: DataTransferItemList): File[] {
  const files: File[] = []
  for (let i = 0; i < items.length; i++) {
    const item = items[i]
    if (item.kind === 'file' && item.type.startsWith('image/')) {
      const file = item.getAsFile()
      if (file) files.push(file)
    }
  }
  return files
}

/** 构造 content blocks list */
export function buildContentBlocks(text: string, attachments: Attachment[]): ContentBlock[] {
  const blocks: ContentBlock[] = []
  const trimmed = text.trim()
  if (trimmed) {
    blocks.push({ type: 'text', text: trimmed })
  }
  for (const att of attachments) {
    if (att.type === 'image' && att.dataUrl) {
      blocks.push({ type: 'image_url', image_url: { url: att.dataUrl } })
    } else if (att.type === 'text_file' && att.textContent !== undefined) {
      const ext = getExtension(att.name)
      const lang = EXT_TO_LANG[ext] || ''
      blocks.push({
        type: 'text',
        text: `📎 \`${att.name}\`:\n\`\`\`${lang}\n${att.textContent}\n\`\`\``,
      })
    }
  }
  return blocks
}

/** 统计图片数量 */
export function countImages(attachments: Attachment[]): number {
  return attachments.filter(a => a.type === 'image').length
}
