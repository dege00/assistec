<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { auth, logout } from './api'
const route = useRoute()
const logado = computed(() => auth.access && !route.meta.publico)
const abas = computed(() => [
  { to: '/', t: 'Início' }, { to: '/os', t: 'Ordens' }, { to: '/clientes', t: 'Clientes' }, { to: '/estoque', t: 'Estoque' },
  ...(auth.user?.cargo === 'admin' ? [
    { to: '/financeiro', t: 'Financeiro' }, { to: '/usuarios', t: 'Usuários' }, { to: '/configuracoes', t: 'Ajustes' },
  ] : []),
])
</script>
<template>
  <div v-if="logado" class="shell">
    <aside class="side">
      <div class="marca"><img src="/icon.svg" alt="" width="30" height="30" /><span>{{ auth.user?.loja?.nome || 'Assistec' }}</span></div>
      <nav>
        <RouterLink v-for="a in abas" :key="a.to" :to="a.to" class="aba">{{ a.t }}</RouterLink>
      </nav>
      <button class="sair" @click="logout">Sair</button>
    </aside>
    <main class="conteudo"><RouterView /></main>
  </div>
  <RouterView v-else />
</template>
