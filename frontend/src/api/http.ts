const BASE_URL = '/api'

const AUTH_PATHS = ['/auth/me', '/auth/login', '/auth/logout']
type UnauthorizedHandler = (path: string) => void | Promise<void>
let unauthorizedHandler: UnauthorizedHandler | undefined

export class ApiError extends Error {
  status: number

  constructor(response: Response) {
    super(`API error: ${response.status} ${response.statusText}`)
    this.name = 'ApiError'
    this.status = response.status
  }
}

export function setUnauthorizedHandler(handler: UnauthorizedHandler) {
  unauthorizedHandler = handler
}

async function handleUnauthorized(path: string) {
  if (AUTH_PATHS.includes(path)) return
  await unauthorizedHandler?.(path)
}

export async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!response.ok) {
    if (response.status === 401) {
      await handleUnauthorized(path)
    }
    throw new ApiError(response)
  }
  if (response.status === 204) return undefined as T
  return response.json()
}

export const api = {
  health: () => fetchApi<{ status: string; version: string; app_name?: string }>('/health'),
  getAuthState: () => fetchApi<{ authenticated: boolean; username: string }>('/auth/me'),
  login: (data: { username: string; password: string }) =>
    fetchApi<{ authenticated: boolean; username: string }>('/auth/login', { method: 'POST', body: JSON.stringify(data) }),
  logout: () => fetchApi<{ authenticated: boolean }>('/auth/logout', { method: 'POST' }),

  getTools: () => fetchApi<{ name: string; group: string; group_description: string; description: string }[]>('/tools'),
  getToolGroups: () => fetchApi<{ id: string; description: string; tools: { name: string; description: string }[]; enabled: boolean }[]>('/tools/groups'),
  toggleToolGroup: (groupId: string) => fetchApi<{ id: string; enabled: boolean }>(`/tools/groups/${groupId}/toggle`, { method: 'POST' }),

  getModels: () => fetchApi<{ id: string; provider: string; base_url: string; context_limit: number }[]>('/models'),

  getMcpServers: () => fetchApi<any[]>('/mcp'),
  toggleMcpServer: (name: string) => fetchApi<{ name: string; enabled: boolean }>(`/mcp/${name}/toggle`, { method: 'POST' }),
  getSkills: () => fetchApi<any[]>('/skills'),
  getSkillDetail: (name: string) => fetchApi<any>(`/skills/${name}`),
  toggleSkill: (name: string) => fetchApi<{ name: string; enabled: boolean }>(`/skills/${name}/toggle`, { method: 'POST' }),

  getAgents: () => fetchApi<any[]>('/agents'),
  createAgent: (data: object) => fetchApi<any>('/agents', { method: 'POST', body: JSON.stringify(data) }),
  updateAgent: (id: string, data: object) => fetchApi<any>(`/agents/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteAgent: (id: string) => fetchApi<void>(`/agents/${id}`, { method: 'DELETE' }),
  activateAgent: (id: string) => fetchApi<any>(`/agents/${id}/activate`, { method: 'POST' }),

  getSessions: () => fetchApi<any[]>('/sessions'),
  createSession: (data: { title?: string; agent_id?: string; model?: string }) =>
    fetchApi<{ id: string; title: string }>('/sessions', { method: 'POST', body: JSON.stringify(data) }),
  updateSession: (id: string, data: { title?: string; model?: string; is_pinned?: boolean }) =>
    fetchApi<any>(`/sessions/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteSession: (id: string) =>
    fetchApi<void>(`/sessions/${id}`, { method: 'DELETE' }),
  getSessionMessages: (id: string) =>
    fetchApi<any[]>(`/sessions/${id}/messages`),
}
