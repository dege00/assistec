<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, setSession } from '../api'
const router = useRouter()
const novo = ref(false), erro = ref(''), carregando = ref(false)
const f = reactive({ loja: '', nome: '', telefone: '', username: '', senha: '' })
async function entrar() {
  erro.value = ''; carregando.value = true
  try {
    if (novo.value) {
      const r = await api('/auth/registrar/', { method: 'POST', body: f })
      setSession(r)
    } else {
      const t = await api('/auth/login/', { method: 'POST', body: { username: f.username, password: f.senha } })
      setSession(t)
      setSession({ usuario: await api('/auth/eu/') })
    }
    router.push('/')
  } catch (e) { erro.value = e.message === 'No active account found with the given credentials' ? 'Usuário ou senha incorretos.' : e.message }
  finally { carregando.value = false }
}
</script>
<template>
  <div class="centro">
    <form class="card caixa" @submit.prevent="entrar">
      <h1>{{ novo ? 'Criar conta da assistência' : 'Entrar' }}</h1>
      <p class="mudo">Ordens de serviço, estoque e caixa no celular.</p>
      <div v-if="erro" class="erro" role="alert">{{ erro }}</div>
      <template v-if="novo">
        <label>Nome da assistência<input v-model="f.loja" required /></label>
        <label>Seu nome<input v-model="f.nome" required /></label>
        <label>WhatsApp da loja<input v-model="f.telefone" inputmode="tel" placeholder="86 99999-0000" /></label>
      </template>
      <label>Usuário<input v-model="f.username" autocomplete="username" required /></label>
      <label>Senha<input v-model="f.senha" type="password" minlength="8" autocomplete="current-password" required /></label>
      <p v-if="novo" class="mudo" style="margin-top:-.5rem">Use pelo menos 8 caracteres, evitando senhas óbvias.</p>
      <button class="btn" style="width:100%" :disabled="carregando">{{ novo ? 'Criar conta' : 'Entrar' }}</button>
      <p style="text-align:center"><a href="#" @click.prevent="novo = !novo; erro = ''">{{ novo ? 'Já tenho conta' : 'Cadastrar minha assistência' }}</a></p>
    </form>
  </div>
</template>
