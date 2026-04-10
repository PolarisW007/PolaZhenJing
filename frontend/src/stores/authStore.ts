/**
 * =============================================================================
 * Module: stores/authStore.ts
 * Description: Zustand store for authentication state management.
 *              Handles login, register, logout, and user profile fetching.
 * Created: 2026-04-06
 * Author: PolaZhenjing Team
 * Dependencies: zustand, api/client
 * =============================================================================
 */

import { create } from 'zustand'
import client from '../api/client'

export interface User {
  id: string
  username: string
  email: string
  display_name: string | null
  is_active: boolean
  is_superuser: boolean
  created_at: string
}

interface AuthState {
  user: User | null
  isLoading: boolean
  error: string | null

  login: (username: string, password: string) => Promise<void>
  register: (username: string, email: string, password: string, displayName?: string) => Promise<void>
  logout: () => void
  fetchUser: () => Promise<void>
  clearError: () => void
}

const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: false,
  error: null,

  login: async (username, password) => {
    set({ isLoading: true, error: null })
    try {
      const res = await client.post('/auth/login', { username, password })
      localStorage.setItem('access_token', res.data.access_token)
      localStorage.setItem('refresh_token', res.data.refresh_token)
      // Fetch user profile
      const userRes = await client.get('/auth/me')
      set({ user: userRes.data, isLoading: false })
    } catch (err: any) {
      set({
        error: err.response?.data?.detail || 'Login failed',
        isLoading: false,
      })
      throw err
    }
  },

  register: async (username, email, password, displayName) => {
    set({ isLoading: true, error: null })
    try {
      await client.post('/auth/register', {
        username,
        email,
        password,
        display_name: displayName || null,
      })
      set({ isLoading: false })
    } catch (err: any) {
      set({
        error: err.response?.data?.detail || 'Registration failed',
        isLoading: false,
      })
      throw err
    }
  },

  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    set({ user: null })
  },

  fetchUser: async () => {
    const token = localStorage.getItem('access_token')
    if (!token) return
    set({ isLoading: true })
    try {
      const res = await client.get('/auth/me')
      set({ user: res.data, isLoading: false })
    } catch {
      set({ user: null, isLoading: false })
    }
  },

  clearError: () => set({ error: null }),
}))

export default useAuthStore
