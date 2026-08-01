import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/api/http'

export interface PromptTemplate {
  id: string
  name: string
  content: string
  created_at: string
  updated_at: string
}

export const usePromptsStore = defineStore('prompts', () => {
  const prompts = ref<PromptTemplate[]>([])
  const loading = ref(false)

  async function fetchPrompts() {
    loading.value = true
    try {
      prompts.value = await api.getPrompts()
    } catch (e) {
      console.error('[PromptsStore] Failed to fetch:', e)
    } finally {
      loading.value = false
    }
  }

  async function createPrompt(data: { name: string; content: string }): Promise<PromptTemplate> {
    const created = await api.createPrompt(data)
    prompts.value.push(created)
    return created
  }

  async function updatePrompt(id: string, data: { name?: string; content?: string }): Promise<PromptTemplate> {
    const updated = await api.updatePrompt(id, data)
    const idx = prompts.value.findIndex(p => p.id === id)
    if (idx >= 0) prompts.value[idx] = updated
    return updated
  }

  async function deletePrompt(id: string): Promise<void> {
    await api.deletePrompt(id)
    prompts.value = prompts.value.filter(p => p.id !== id)
  }

  function getById(id: string): PromptTemplate | undefined {
    return prompts.value.find(p => p.id === id)
  }

  return { prompts, loading, fetchPrompts, createPrompt, updatePrompt, deletePrompt, getById }
})
