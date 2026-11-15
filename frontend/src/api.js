import { reactive } from 'vue'

export const auth = reactive({
  access: localStorage.getItem('access') || '',
  refresh: localStorage.getItem('refresh') || '',
  user: JSON.parse(localStorage.getItem('user') || 'null'),
})

export function setSession({ access, refresh, usuario }) {
  if (access) { auth.access = access; localStorage.setItem('access', access) }
  if (refresh) { auth.refresh = refresh; localStorage.setItem('refresh', refresh) }
  if (usuario) { auth.user = usuario; localStorage.setItem('user', JSON.stringify(usuario)) }
}
export function logout() {
  auth.access = auth.refresh = ''; auth.user = null
  localStorage.clear()
  location.href = '/login'
}

async function renovar() {
  if (!auth.refresh) return false
  const r = await fetch('/api/auth/refresh/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ refresh: auth.refresh }) })
  if (!r.ok) return false
  setSession(await r.json())
  return true
}

export async function api(path, { method = 'GET', body, form, blob } = {}, retry = true) {
  const headers = {}
  if (auth.access) headers.Authorization = `Bearer ${auth.access}`
  if (body) headers['Content-Type'] = 'application/json'
  const r = await fetch('/api' + path, { method, headers, body: form || (body ? JSON.stringify(body) : undefined) })
  if (r.status === 401 && retry && auth.refresh) {
    if (await renovar()) return api(path, { method, body, form, blob }, false)
    logout()
  }
  if (r.status === 204) return null
  if (blob) return r.blob()
  const data = await r.json().catch(() => null)
  if (!r.ok) {
    const msg = data?.detail || (data && Object.entries(data).map(([k, v]) => `${k}: ${[].concat(v).join(' ')}`).join(' | ')) || 'Erro inesperado'
    throw new Error(msg)
  }
  return data
}

export const brl = (v) => Number(v || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
export const dataBR = (d) => d ? new Date(d).toLocaleDateString('pt-BR') : '—'
export const dataHoraBR = (d) => d ? new Date(d).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' }) : '—'
export const STATUS = {
  orcamento: 'Orçamento', em_analise: 'Em análise', aguardando_peca: 'Aguardando peça',
  em_servico: 'Em serviço', finalizado: 'Finalizado', pago: 'Pago', cancelado: 'Cancelado',
}
