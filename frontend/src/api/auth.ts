const BASE_URL = '/api/auth'

export interface LoginResponse {
  token: string
  user: { id: string; username: string; role: string }
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const resp = await fetch(`${BASE_URL}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  if (!resp.ok) throw new Error('认证失败')
  return resp.json()
}

export async function getMe(token: string): Promise<{ id: string; username: string; role: string }> {
  const resp = await fetch(`${BASE_URL}/me`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!resp.ok) throw new Error('Token 无效')
  return resp.json()
}

export async function changePassword(oldPassword: string, newPassword: string): Promise<void> {
  const token = localStorage.getItem('token') || ''
  const resp = await fetch(`${BASE_URL}/change-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
  })
  if (!resp.ok) {
    const data = await resp.json().catch(() => ({}))
    throw new Error(data.detail || '修改失败')
  }
}
