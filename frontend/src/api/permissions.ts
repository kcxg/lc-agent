const BASE = '/api/permissions'

export interface PermissionsConfig {
  version: number
  tool_allowlist: string[]
}

export async function getPermissions(): Promise<PermissionsConfig> {
  const resp = await fetch(BASE)
  return resp.json()
}

export async function allowTool(toolName: string): Promise<PermissionsConfig> {
  const resp = await fetch(`${BASE}/allow`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tool_name: toolName }),
  })
  return resp.json()
}

export async function removeTool(toolName: string): Promise<PermissionsConfig> {
  const resp = await fetch(`${BASE}/remove`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tool_name: toolName }),
  })
  return resp.json()
}

export async function setPermissions(tools: string[]): Promise<PermissionsConfig> {
  const resp = await fetch(BASE, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tool_allowlist: tools }),
  })
  return resp.json()
}
