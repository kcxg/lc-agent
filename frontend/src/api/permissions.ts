const BASE = '/api/permissions'

export interface PermissionsConfig {
  version: number
  tool_allowlist: string[]
}

async function checkedJson<T>(resp: Response): Promise<T> {
  if (!resp.ok) {
    throw new Error(`Permissions API error: ${resp.status} ${resp.statusText}`)
  }
  return resp.json()
}

export async function getPermissions(): Promise<PermissionsConfig> {
  const resp = await fetch(BASE)
  return checkedJson(resp)
}

export async function allowTool(toolName: string): Promise<PermissionsConfig> {
  const resp = await fetch(`${BASE}/allow`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tool_name: toolName }),
  })
  return checkedJson(resp)
}

export async function removeTool(toolName: string): Promise<PermissionsConfig> {
  const resp = await fetch(`${BASE}/remove`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tool_name: toolName }),
  })
  return checkedJson(resp)
}

export async function setPermissions(tools: string[]): Promise<PermissionsConfig> {
  const resp = await fetch(BASE, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tool_allowlist: tools }),
  })
  return checkedJson(resp)
}
