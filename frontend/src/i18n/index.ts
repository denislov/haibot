import { createI18n } from 'vue-i18n'
import zhCN from './locales/zh-CN'
import en from './locales/en'

const i18n = createI18n({
  legacy: false,
  locale: localStorage.getItem('haibot-locale') || 'zh-CN',
  fallbackLocale: 'en',
  messages: {
    'zh-CN': zhCN,
    en,
  },
})

export default i18n

export function setLocale(locale: 'zh-CN' | 'en') {
  ;(i18n.global.locale as unknown as { value: string }).value = locale
  localStorage.setItem('haibot-locale', locale)
}
