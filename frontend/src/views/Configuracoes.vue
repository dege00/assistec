<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api, setSession } from '../api'
import { urlMidia } from '../utils/midia'

const f = reactive({ nome: '', telefone: '', documento: '', endereco: '', termo_garantia: '' })
const erro = ref(''), msg = ref(''), salvando = ref(false)
const logoAtual = ref(''), arquivoLogo = ref(null)

async function carregar() {
  try {
    const u = await api('/auth/eu/')
    setSession({ usuario: u })
    Object.assign(f, {
      nome: u.loja?.nome || '', telefone: u.loja?.telefone || '', documento: u.loja?.documento || '',
      endereco: u.loja?.endereco || '', termo_garantia: u.loja?.termo_garantia || '',
    })
    logoAtual.value = u.loja?.logo || ''
  } catch (e) { erro.value = e.message }
}
onMounted(carregar)

function escolherLogo(e) {
  const file = e.target.files[0]
  arquivoLogo.value = file || null
  if (file) logoAtual.value = URL.createObjectURL(file)
}

async function salvar() {
  erro.value = ''; msg.value = ''; salvando.value = true
  try {
    const form = new FormData()
    for (const [k, v] of Object.entries(f)) form.append(k, v ?? '')
    if (arquivoLogo.value) form.append('logo', arquivoLogo.value)
    const u = await api('/auth/eu/', { method: 'PATCH', form })
    setSession({ usuario: u })
    logoAtual.value = u.loja?.logo || logoAtual.value
    arquivoLogo.value = null
    msg.value = 'Dados da assistência salvos.'
  } catch (e) { erro.value = e.message } finally { salvando.value = false }
}
</script>

<template>
  <h1>Configurações da assistência</h1>
  <div v-if="erro" class="erro" role="alert">{{ erro }}</div>
  <div v-if="msg" class="card" role="status">{{ msg }}</div>

  <form class="card" @submit.prevent="salvar">
    <h2>Dados que aparecem na OS e no PDF</h2>
    <label>Nome da assistência<input v-model="f.nome" required /></label>
    <div class="linha2">
      <label>WhatsApp / telefone<input v-model="f.telefone" inputmode="tel" /></label>
      <label>CNPJ / CPF<input v-model="f.documento" /></label>
    </div>
    <label>Endereço<input v-model="f.endereco" /></label>
    <label>Termo de garantia<textarea v-model="f.termo_garantia" placeholder="Ex.: Garantia de 90 dias sobre o serviço executado."></textarea></label>

    <label>Logotipo (usado no PDF)
      <input type="file" accept="image/*" @change="escolherLogo" />
    </label>
    <p v-if="logoAtual" class="mudo"><img :src="urlMidia(logoAtual)" alt="Logotipo atual" style="max-width:160px;max-height:80px;border:1px solid var(--linha);border-radius:8px;background:#fff;padding:.25rem" /></p>

    <button class="btn" :disabled="salvando">{{ salvando ? 'Salvando…' : 'Salvar configurações' }}</button>
  </form>
</template>
