const BASE_URL = '/api'

function getAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  const token = localStorage.getItem('token')
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

export async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: getAuthHeaders(),
    ...options,
  })
  if (response.status === 401) {
    localStorage.removeItem('token')
    window.dispatchEvent(new CustomEvent('auth:expired'))
    throw new Error('认证已过期，请重新登录')
  }
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`)
  }
  if (response.status === 204) return undefined as T
  return response.json()
}

export const api = {
  health: () => fetchApi<{ status: string; version: string; app_name?: string; config_loaded: boolean }>('/health'),

  getTools: () => fetchApi<{ name: string; group: string; group_description: string; description: string }[]>('/tools'),
  getToolGroups: () => fetchApi<{ id: string; description: string; tools: { name: string; description: string }[]; enabled: boolean }[]>('/tools/groups'),
  toggleToolGroup: (groupId: string) => fetchApi<{ id: string; enabled: boolean }>(`/tools/groups/${groupId}/toggle`, { method: 'POST' }),

  getModels: () => fetchApi<{ id: string; provider: string; base_url: string; context_limit: number }[]>('/models'),

  getMcpServers: () => fetchApi<any[]>('/mcp'),
  refreshMcpServers: () => fetchApi<any[]>('/mcp/refresh', { method: 'POST' }),
  refreshMcpServer: (name: string) => fetchApi<any>(`/mcp/${name}/refresh`, { method: 'POST' }),
  toggleMcpServer: (name: string) => fetchApi<{ name: string; enabled: boolean }>(`/mcp/${name}/toggle`, { method: 'POST' }),
  getSkills: (projectRoot?: string) => {
    const qs = projectRoot ? `?project_root=${encodeURIComponent(projectRoot)}` : ''
    return fetchApi<any[]>(`/skills${qs}`)
  },
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
  getSessionMessages: (id: string, params?: { limit?: number; offset?: number }) => {
    const qs = new URLSearchParams()
    if (params?.limit !== undefined) qs.set('limit', String(params.limit))
    if (params?.offset !== undefined) qs.set('offset', String(params.offset))
    const query = qs.toString()
    return fetchApi<{ total: number; offset: number; limit: number; messages: any[] }>(
      `/sessions/${id}/messages${query ? '?' + query : ''}`
    )
  },
  getMessageTraces: (sessionId: string, messageId: string) =>
    fetchApi<{ traces: any[] }>(`/sessions/${sessionId}/messages/${messageId}/traces`),

  getSummarization: () => fetchApi<{ enabled: boolean; default_model: string; trigger: any; keep: any }>('/settings/summarization'),
  updateSummarization: (data: { enabled?: boolean; default_model?: string; trigger?: any; keep?: any }) =>
    fetchApi<any>('/settings/summarization', { method: 'PUT', body: JSON.stringify(data) }),

  // Prompt library
  getPrompts: () => fetchApi<any[]>('/prompts'),
  createPrompt: (data: { name: string; content: string }) =>
    fetchApi<any>('/prompts', { method: 'POST', body: JSON.stringify(data) }),
  updatePrompt: (id: string, data: { name?: string; content?: string }) =>
    fetchApi<any>(`/prompts/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deletePrompt: (id: string) => fetchApi<void>(`/prompts/${id}`, { method: 'DELETE' }),

  // Agent ↔ prompt bindings
  getAgentPrompts: (agentId: string) => fetchApi<string[]>(`/agents/${agentId}/prompts`),
  setAgentPrompts: (agentId: string, promptIds: string[]) =>
    fetchApi<string[]>(`/agents/${agentId}/prompts`, { method: 'PUT', body: JSON.stringify({ prompt_ids: promptIds }) }),
}

export async function fetchAvailableSubagents(): Promise<Array<{
  id: string
  name: string
  display_name: string | null
  source: string
  description: string
}>> {
  return fetchApi('/agents/available-subagents')
}
