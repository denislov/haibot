import { Marked } from 'marked'
import hljs from 'highlight.js'

const marked = new Marked({
  breaks: true,
  gfm: true,
})

// Custom renderer for code blocks with syntax highlighting
marked.use({
  renderer: {
    code({ text, lang }: { text: string; lang?: string }) {
      if (lang && hljs.getLanguage(lang)) {
        const highlighted = hljs.highlight(text, { language: lang, ignoreIllegals: true }).value
        return `<pre><code class="hljs language-${lang}">${highlighted}</code></pre>`
      }
      return `<pre><code class="hljs">${escapeHtml(text)}</code></pre>`
    },
  },
})

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

/**
 * Render markdown text to HTML.
 */
export function renderMarkdown(text: string): string {
  return marked.parse(text || '', { async: false }) as string
}

/**
 * Render markdown, stripping optional YAML front-matter first.
 */
export function renderMarkdownWithFrontMatter(text: string): string {
  let content = text || ''
  const yamlMatch = content.match(/^---\r?\n[\s\S]*?\r?\n---/)
  if (yamlMatch) {
    content = content.slice(yamlMatch[0].length)
  }
  return renderMarkdown(content)
}

/**
 * Render raw JSON as syntax-highlighted table rows with line numbers.
 * Returns HTML string for v-html in a <tbody>.
 */
export function renderJsonCode(raw: string | undefined): string {
  if (!raw) return '<tr><td class="ln">1</td><td class="lc">&nbsp;</td></tr>'
  let formatted: string
  try {
    formatted = JSON.stringify(JSON.parse(raw), null, 2)
  } catch {
    formatted = raw
  }
  const highlighted = hljs.highlight(formatted, { language: 'json', ignoreIllegals: true }).value
  const lines = highlighted.split('\n')
  return lines
    .map((line, i) => `<tr><td class="ln">${i + 1}</td><td class="lc">${line || '&nbsp;'}</td></tr>`)
    .join('')
}
