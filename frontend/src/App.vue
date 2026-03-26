<template>
  <div v-if="!authStore.initialized || authStore.initializing" class="app-loading">
    <div class="loading-card">
      <div class="loading-brand">
        <span>Hai</span><span class="accent">Bot</span>
      </div>
      <p>{{ $t('auth.loading') }}</p>
    </div>
  </div>
  <AuthScreen v-else-if="authStore.requiresAuthScreen" />
  <router-view v-else />
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import AuthScreen from '@/modules/auth/AuthScreen.vue'

const authStore = useAuthStore()

onMounted(() => {
  authStore.initialize()
})
</script>

<style scoped>
.app-loading {
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding:
    calc(24px + var(--safe-top))
    calc(24px + var(--safe-right))
    calc(24px + var(--safe-bottom))
    calc(24px + var(--safe-left));
  background:
    radial-gradient(circle at top left, var(--surface-tint) 0, transparent 24%),
    linear-gradient(180deg, var(--bg) 0%, var(--bg-soft) 100%);
}

.loading-card {
  min-width: 280px;
  padding: 28px 30px;
  text-align: center;
  border-radius: 24px;
  border: 1px solid var(--border);
  background:
    linear-gradient(180deg, var(--surface-highlight) 0%, rgba(0, 0, 0, 0) 56px),
    linear-gradient(180deg, var(--bg-card-elevated) 0%, var(--bg-card) 100%);
  box-shadow:
    inset 0 1px 0 var(--surface-highlight),
    0 22px 56px -38px var(--surface-shadow);
}

.loading-brand {
  font-size: 28px;
  font-weight: 800;
  letter-spacing: -0.04em;
  color: var(--text-1);
}

.loading-brand .accent {
  color: var(--primary);
}

.loading-card p {
  margin-top: 10px;
  color: var(--text-3);
}
</style>
