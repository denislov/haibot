<template>
  <div class="auth-screen">
    <div class="auth-shell">
      <div class="brand-panel">
        <div class="brand-mark">
          <span class="brand-hai">Hai</span><span class="brand-bot">Bot</span>
        </div>
        <h1 class="brand-title">{{ $t('auth.title') }}</h1>
        <p class="brand-desc">
          {{ mode === 'register_required' ? $t('auth.registerDesc') : $t('auth.signInDesc') }}
        </p>
      </div>

      <div class="form-panel">
        <div class="panel-header">
          <h2>{{ mode === 'register_required' ? $t('auth.registerTitle') : $t('auth.signInTitle') }}</h2>
          <p>{{ mode === 'register_required' ? $t('auth.registerDesc') : $t('auth.signInDesc') }}</p>
        </div>

        <el-form label-position="top" @submit.prevent>
          <el-form-item :label="$t('auth.username')" required>
            <el-input v-model="form.username" autocomplete="username" />
          </el-form-item>
          <el-form-item :label="$t('auth.password')" required>
            <el-input
              v-model="form.password"
              type="password"
              show-password
              autocomplete="current-password"
              @keyup.enter="submit"
            />
          </el-form-item>
          <el-form-item
            v-if="mode === 'register_required'"
            :label="$t('auth.confirmPassword')"
            required
          >
            <el-input
              v-model="form.confirmPassword"
              type="password"
              show-password
              autocomplete="new-password"
              @keyup.enter="submit"
            />
          </el-form-item>
        </el-form>

        <div class="auth-actions">
          <el-alert
            v-if="errorMessage"
            :title="errorMessage"
            type="error"
            show-icon
            :closable="false"
          />
          <el-button
            type="primary"
            class="submit-btn"
            :loading="submitting"
            @click="submit"
          >
            {{ mode === 'register_required' ? $t('auth.register') : $t('auth.signIn') }}
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const authStore = useAuthStore()

const mode = computed(() => authStore.mode)
const submitting = ref(false)
const errorMessage = ref('')
const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
})

async function submit() {
  errorMessage.value = ''
  if (!form.username.trim() || !form.password) return

  if (
    mode.value === 'register_required' &&
    form.password !== form.confirmPassword
  ) {
    errorMessage.value = t('auth.invalidConfirm')
    return
  }

  submitting.value = true
  try {
    if (mode.value === 'register_required') {
      await authStore.register(form.username, form.password)
    } else {
      await authStore.login(form.username, form.password)
    }
    form.password = ''
    form.confirmPassword = ''
  } catch (e: unknown) {
    errorMessage.value = e instanceof Error ? e.message : String(e)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.auth-screen {
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding:
    calc(28px + var(--safe-top))
    calc(28px + var(--safe-right))
    calc(28px + var(--safe-bottom))
    calc(28px + var(--safe-left));
  overflow-y: auto;
  background:
    radial-gradient(circle at top left, var(--surface-tint) 0, transparent 26%),
    radial-gradient(circle at bottom right, var(--primary-light) 0, transparent 24%),
    linear-gradient(180deg, var(--bg) 0%, var(--bg-soft) 100%);
}

.auth-shell {
  width: min(980px, 100%);
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  border-radius: 28px;
  overflow: hidden;
  border: 1px solid var(--border);
  background:
    linear-gradient(180deg, var(--surface-highlight) 0%, rgba(0, 0, 0, 0) 96px),
    linear-gradient(180deg, var(--bg-card-elevated) 0%, var(--bg-card) 100%);
  box-shadow:
    inset 0 1px 0 var(--surface-highlight),
    0 28px 80px -42px var(--surface-shadow);
}

.brand-panel {
  padding: 40px 38px;
  border-right: 1px solid var(--border);
  background:
    radial-gradient(circle at 24% 16%, var(--surface-tint) 0, transparent 34%),
    linear-gradient(180deg, rgba(99, 102, 241, 0.1) 0%, rgba(0, 0, 0, 0) 42%),
    linear-gradient(180deg, var(--bg-card-elevated) 0%, var(--bg-card) 100%);
}

.brand-mark {
  font-size: 42px;
  font-weight: 800;
  letter-spacing: -0.04em;
}

.brand-hai {
  color: var(--text-1);
}

.brand-bot {
  color: var(--primary);
}

.brand-title {
  margin-top: 28px;
  font-size: 28px;
  line-height: 1.05;
  color: var(--text-1);
}

.brand-desc {
  margin-top: 14px;
  max-width: 420px;
  color: var(--text-3);
  line-height: 1.65;
}

.form-panel {
  padding: 40px 38px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.panel-header h2 {
  font-size: 22px;
  letter-spacing: -0.02em;
  color: var(--text-1);
}

.panel-header p {
  margin-top: 8px;
  color: var(--text-3);
  line-height: 1.55;
}

.auth-actions {
  margin-top: 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.submit-btn {
  width: 100%;
}

@media (max-width: 860px) {
  .auth-shell {
    grid-template-columns: 1fr;
  }

  .brand-panel {
    border-right: none;
    border-bottom: 1px solid var(--border);
    padding: 28px 24px;
  }

  .form-panel {
    padding: 28px 24px;
  }
}

@media (max-width: 560px) {
  .auth-screen {
    align-items: stretch;
    padding:
      calc(14px + var(--safe-top))
      calc(14px + var(--safe-right))
      calc(14px + var(--safe-bottom))
      calc(14px + var(--safe-left));
  }

  .auth-shell {
    border-radius: 20px;
  }

  .brand-mark {
    font-size: 34px;
  }
}
</style>
