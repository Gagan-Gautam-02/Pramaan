import { createContext, useContext, useState, useCallback } from 'react'
import axios from 'axios'

const API = import.meta.env.VITE_API_URL || '/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('ds_token'))
  const [user, setUser] = useState(() => {
    const u = localStorage.getItem('ds_user')
    return u ? JSON.parse(u) : null
  })

  const login = useCallback(async (username, password) => {
    const form = new URLSearchParams()
    form.append('username', username)
    form.append('password', password)
    const res = await axios.post(`${API}/token`, form)
    const { access_token } = res.data
    localStorage.setItem('ds_token', access_token)
    setToken(access_token)

    const me = await axios.get(`${API}/users/me`, {
      headers: { Authorization: `Bearer ${access_token}` },
    })
    localStorage.setItem('ds_user', JSON.stringify(me.data))
    setUser(me.data)
    return me.data
  }, [])

  const register = useCallback(async (username, password) => {
    await axios.post(`${API}/register`, { username, password })
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('ds_token')
    localStorage.removeItem('ds_user')
    setToken(null)
    setUser(null)
  }, [])

  const authAxios = useCallback(() => {
    return axios.create({
      baseURL: API,
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
  }, [token])

  return (
    <AuthContext.Provider value={{ token, user, login, register, logout, authAxios, API }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
