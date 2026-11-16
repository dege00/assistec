<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, setSession } from '../api'
const router = useRouter()
const erro = ref(''), carregando = ref(false)
const f = reactive({ username: '', senha: '' })
async function entrar() {
  erro.value = ''; carregando.value = true
  try {
    const t = await api('/auth/login/', { method: 'POST', body: { username: f.username, password: f.senha } })
    setSession(t)
    setSession({ usuario: await api('/auth/eu/') })
    router.push('/')
  } catch (e) {
    if (e.status === 429) erro.value = 'Muitas tentativas. Aguarde um minuto e tente de novo.'
    else erro.value = e.message === 'No active account found with the given credentials' ? 'Usuário ou senha incorretos.' : e.message
  } finally { carregando.value = false }
}
</script>
<template>
  <div class="centro">
    <form class="card caixa" @submit.prevent="entrar">
      <h1>Entrar</h1>
      <p class="mudo">Ordens de serviço, estoque e caixa no celular.</p>
      <div v-if="erro" class="erro" role="alert">{{ erro }}</div>
      <label>Usuário<input v-model="f.username" autocomplete="username" required /></label>
      <label>Senha<input v-model="f.senha" type="password" autocomplete="current-password" required /></label>
      <button class="btn" style="width:100%" :disabled="carregando">Entrar</button>
    </form>
  </div>
</template>
