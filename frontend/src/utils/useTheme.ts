import { ref, watch } from 'vue'
import { usePreferredDark, useStorage } from '@vueuse/core'

export type ThemeMode = 'light' | 'dark' | 'system'

const themeMode = useStorage<ThemeMode>('haibot-theme', 'system')
const isDark = ref(false)
const prefersDark = usePreferredDark()

function applyTheme() {
  const shouldBeDark =
    themeMode.value === 'dark' ||
    (themeMode.value === 'system' && prefersDark.value)

  isDark.value = shouldBeDark
  document.documentElement.setAttribute('data-theme', shouldBeDark ? 'dark' : 'light')
}

watch([themeMode, prefersDark], applyTheme, { immediate: true })

export function useTheme() {
  function setTheme(mode: ThemeMode) {
    themeMode.value = mode
  }

  function toggleTheme() {
    if (isDark.value) {
      themeMode.value = 'light'
    } else {
      themeMode.value = 'dark'
    }
  }

  return {
    themeMode,
    isDark,
    setTheme,
    toggleTheme,
  }
}
