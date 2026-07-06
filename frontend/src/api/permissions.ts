import { fetchApi } from './http'

export interface PermissionsConfig {
  version: number
  tool_allowlist: string[]
}

export async function getPermissions(): Promise<PermissionsConfig> {
  return fetchApi<PermissionsConfig>('/permissions')
}

export async function allowTool(toolName: string): Promise<PermissionsConfig> {
  return fetchApi<PermissionsConfig>('/permissions/allow', {
    method: 'POST',
    body: JSON.stringify({ tool_name: toolName }),
  })
}

export async function removeTool(toolName: string): Promise<PermissionsConfig> {
  return fetchApi<PermissionsConfig>('/permissions/remove', {
    method: 'POST',
    body: JSON.stringify({ tool_name: toolName }),
  })
}

export async function setPermissions(tools: string[]): Promise<PermissionsConfig> {
  return fetchApi<PermissionsConfig>('/permissions', {
    method: 'PUT',
    body: JSON.stringify({ tool_allowlist: tools }),
  })
}
