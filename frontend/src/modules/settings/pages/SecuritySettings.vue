<template>
  <div class="page">
    <section class="section">
      <h2 class="section-title">{{ $t('settings.security.title') }}</h2>
      <p class="section-desc">{{ $t('settings.security.desc') }}</p>

      <el-tabs v-model="activeTab" class="security-tabs">
        <el-tab-pane :label="$t('settings.security.toolGuard')" name="toolGuard">
          <div class="tab-content" v-loading="loadingToolGuard">
            <p class="tab-desc">{{ $t('settings.security.toolGuardDesc') }}</p>
            
            <div class="card mb-6">
              <div class="form-row flex-row justify-between align-center">
                <label>{{ $t('settings.security.enableToolGuard') }} <el-icon class="info-icon"><InfoFilled /></el-icon></label>
                <el-switch v-model="toolGuardForm.enabled" @change="saveToolGuard" />
              </div>

              <div class="form-row mt-4">
                <label>{{ $t('settings.security.protectedTools') }} <el-icon class="info-icon"><InfoFilled /></el-icon></label>
                <el-select 
                  v-model="toolGuardForm.protected_tools" 
                  multiple 
                  filterable 
                  allow-create 
                  default-first-option
                  :placeholder="$t('settings.security.selectProtectedTools')"
                  style="width: 100%"
                  @change="saveToolGuard"
                >
                </el-select>
              </div>

              <div class="form-row mt-4">
                <label>{{ $t('settings.security.bannedTools') }} <el-icon class="info-icon"><InfoFilled /></el-icon></label>
                <el-select 
                  v-model="toolGuardForm.banned_tools" 
                  multiple 
                  filterable 
                  allow-create 
                  default-first-option
                  :placeholder="$t('settings.security.selectBannedTools')"
                  style="width: 100%"
                  @change="saveToolGuard"
                >
                </el-select>
              </div>
            </div>

            <div class="rules-section">
              <div class="section-header-row">
                <h3 class="subsection-title">{{ $t('settings.security.detectionRules') }}</h3>
                <el-button type="primary" plain size="small" :icon="Plus">{{ $t('settings.security.addRule') }}</el-button>
              </div>

              <el-table :data="builtinRules" border stripe style="width: 100%">
                <el-table-column prop="id" :label="$t('settings.security.ruleId')" width="240" />
                <el-table-column prop="severity" :label="$t('settings.security.severity')" width="100">
                  <template #default="scope">
                    <el-tag :type="getSeverityTag(scope.row.severity)" size="small">{{ scope.row.severity }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="description" :label="$t('settings.security.description')" />
                <el-table-column :label="$t('settings.security.source')" width="90">
                  <template #default>
                    <span class="text-xs text-info">{{ $t('settings.security.builtin') }}</span>
                  </template>
                </el-table-column>
                <el-table-column :label="$t('settings.security.actions')" width="160" align="center">
                  <template #default="scope">
                    <div class="actions-cell">
                      <el-switch 
                        v-model="toolGuardForm.rules[scope.row.id]" 
                        @change="saveToolGuard"
                      />
                      <el-button link type="primary" :icon="View" @click="openPreview(scope.row)">
                        {{ $t('settings.security.preview') }}
                      </el-button>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane :label="$t('settings.security.skillScanner')" name="skillScanner">
          <div class="tab-content" v-loading="loadingSkillScanner">
            <p class="tab-desc">{{ $t('settings.security.skillScannerDesc') }}</p>

            <div class="card mb-6">
              <div class="form-row-group">
                <div class="form-row flex-1">
                  <label>{{ $t('settings.security.scanMode') }}</label>
                  <el-select v-model="skillScannerForm.mode" @change="saveSkillScanner" style="width: 100%">
                    <el-option :label="$t('settings.security.scanModeRemind')" value="remind" />
                    <el-option :label="$t('settings.security.scanModeBlock')" value="block" />
                    <el-option :label="$t('settings.security.scanModeAutoWhitelist')" value="auto_whitelist" />
                  </el-select>
                </div>
                <div class="form-row flex-1">
                  <label>{{ $t('settings.security.scanTimeout') }}</label>
                  <el-input-number v-model="skillScannerForm.scan_timeout" :min="1" @change="saveSkillScanner" style="width: 100%" controls-position="right" />
                </div>
              </div>
            </div>

            <el-tabs v-model="innerScannerTab" class="inner-tabs">
              <el-tab-pane :label="$t('settings.security.scanAlerts')" name="alerts">
                <el-empty :description="$t('settings.security.noScanAlerts')" v-if="!skillBlockedHistory.length" />
                <el-table v-else :data="skillBlockedHistory" border>
                  <el-table-column prop="timestamp" label="Time" width="180" />
                  <el-table-column prop="skill" label="Skill" width="180" />
                  <el-table-column prop="reason" label="Reason" />
                  <el-table-column label="Actions" width="120">
                    <template #default="scope">
                      <el-button text type="danger" @click="removeBlockedHistory(scope.$index)">
                        {{ $t('common.delete') }}
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </el-tab-pane>
              
              <el-tab-pane :label="$t('settings.security.whitelist')" name="whitelist">
                <div class="whitelist-toolbar mb-4 flex justify-end">
                  <el-input v-model="newWhitelistSkill" placeholder="Skill Name" size="small" style="width: 200px; margin-right: 8px;" />
                  <el-button type="primary" size="small" @click="addWhitelist" :disabled="!newWhitelistSkill">
                    {{ $t('common.add') }}
                  </el-button>
                </div>
                <el-table :data="skillScannerForm.whitelist" border>
                  <el-table-column prop="skill_name" label="Skill Name" />
                  <el-table-column prop="added_at" label="Added At" width="180" />
                  <el-table-column label="Actions" width="120">
                    <template #default="scope">
                      <el-button text type="danger" @click="removeWhitelist(scope.row.skill_name)">
                        {{ $t('common.delete') }}
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </el-tab-pane>
            </el-tabs>

          </div>
        </el-tab-pane>
      </el-tabs>

      <!-- Rule Preview Dialog -->
      <el-dialog
        v-model="previewDialogVisible"
        :title="$t('settings.security.ruleDetails')"
        width="600px"
        destroy-on-close
      >
        <div v-if="previewRule" class="preview-content">
          <div class="preview-row">
            <span class="preview-label">{{ $t('settings.security.ruleId') }}:</span>
            <span class="preview-value">{{ previewRule.id }}</span>
          </div>
          <div class="preview-row">
            <span class="preview-label">{{ $t('settings.security.severity') }}:</span>
            <el-tag :type="getSeverityTag(previewRule.severity)" size="small" effect="light" class="severity-tag">
              {{ previewRule.severity }}
            </el-tag>
          </div>
          <div class="preview-row">
            <span class="preview-label">{{ $t('settings.security.targetTool') }}:</span>
            <span class="preview-value">{{ previewRule.tools.join(', ') }}</span>
          </div>
          <div class="preview-row">
            <span class="preview-label">{{ $t('settings.security.targetParam') }}:</span>
            <span class="preview-value">{{ previewRule.params.join(', ') }}</span>
          </div>
          <div class="preview-row">
            <span class="preview-label">{{ $t('settings.security.triggerAction') }}:</span>
            <el-tag type="warning" size="small" effect="light" class="action-tag">
              {{ $t('settings.security.waitApproval') }}
            </el-tag>
          </div>
          <div class="preview-row">
            <span class="preview-label">{{ $t('settings.security.description') }}:</span>
            <span class="preview-value">{{ previewRule.description }}</span>
          </div>

          <div v-if="previewRule.patterns && previewRule.patterns.length > 0" class="preview-code-section">
            <span class="preview-label">{{ $t('settings.security.regexPattern') }}:</span>
            <div class="code-box">
              <div v-for="(pattern, idx) in previewRule.patterns" :key="idx" class="code-line">
                {{ pattern }}
              </div>
            </div>
          </div>
        </div>

        <template #footer>
          <div class="dialog-footer">
            <el-button @click="previewDialogVisible = false">{{ $t('common.close') }}</el-button>
          </div>
        </template>
      </el-dialog>

    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { InfoFilled, Plus, View } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import {
  getToolGuardConfig,
  updateToolGuardConfig,
  getToolGuardBuiltinRules,
  getSkillScannerConfig,
  updateSkillScannerConfig,
  getSkillScannerBlockedHistory,
  deleteSkillScannerBlockedHistoryEntry,
  addSkillScannerWhitelist,
  removeSkillScannerWhitelist
} from '@/api/config'
import type { ToolGuardConfig, ToolGuardRuleConfig, SkillScannerConfig, SkillScannerBlockedHistoryEntry } from '@/types'

const activeTab = ref('toolGuard')
const innerScannerTab = ref('alerts')

// Tool Guard
const loadingToolGuard = ref(false)
const previewDialogVisible = ref(false)
const previewRule = ref<ToolGuardRuleConfig | null>(null)
const toolGuardForm = ref<ToolGuardConfig>({
  enabled: false,
  protected_tools: [],
  banned_tools: [],
  rules: {}
})
const builtinRules = ref<ToolGuardRuleConfig[]>([])

// Skill Scanner
const loadingSkillScanner = ref(false)
const skillScannerForm = ref<SkillScannerConfig>({
  enabled: false,
  mode: 'remind',
  scan_timeout: 30,
  whitelist: []
})
const skillBlockedHistory = ref<SkillScannerBlockedHistoryEntry[]>([])
const newWhitelistSkill = ref('')

function getSeverityTag(severity: string) {
  switch (severity.toLowerCase()) {
    case 'critical': return 'danger'
    case 'high': return 'warning'
    case 'medium': return 'info'
    default: return ''
  }
}

function openPreview(rule: ToolGuardRuleConfig) {
  previewRule.value = rule
  previewDialogVisible.value = true
}

async function loadToolGuard() {
  loadingToolGuard.value = true
  try {
    const [config, rules] = await Promise.all([
      getToolGuardConfig(),
      getToolGuardBuiltinRules()
    ])
    toolGuardForm.value = config
    builtinRules.value = rules
    // Initialize rules dict if missing
    if (!toolGuardForm.value.rules) toolGuardForm.value.rules = {}
    for (const rule of rules) {
      if (typeof toolGuardForm.value.rules[rule.id] === 'undefined') {
        toolGuardForm.value.rules[rule.id] = true // Default to true
      }
    }
  } catch (e: any) {
    ElMessage.error('Failed to load tool guard config: ' + e.message)
  } finally {
    loadingToolGuard.value = false
  }
}

async function saveToolGuard() {
  try {
    await updateToolGuardConfig(toolGuardForm.value)
    ElMessage.success('Saved')
  } catch (e: any) {
    ElMessage.error('Save failed: ' + e.message)
  }
}

async function loadSkillScanner() {
  loadingSkillScanner.value = true
  try {
    const [config, history] = await Promise.all([
      getSkillScannerConfig(),
      getSkillScannerBlockedHistory()
    ])
    skillScannerForm.value = config
    skillBlockedHistory.value = history
  } catch (e: any) {
    ElMessage.error('Failed to load skill scanner config: ' + e.message)
  } finally {
    loadingSkillScanner.value = false
  }
}

async function saveSkillScanner() {
  try {
    await updateSkillScannerConfig(skillScannerForm.value)
    ElMessage.success('Saved')
  } catch (e: any) {
    ElMessage.error('Save failed: ' + e.message)
  }
}

async function removeBlockedHistory(index: number) {
  try {
    await deleteSkillScannerBlockedHistoryEntry(index)
    ElMessage.success('Removed')
    await loadSkillScanner()
  } catch (e: any) {
    ElMessage.error('Remove failed: ' + e.message)
  }
}

async function addWhitelist() {
  if (!newWhitelistSkill.value) return
  try {
    await addSkillScannerWhitelist(newWhitelistSkill.value)
    newWhitelistSkill.value = ''
    ElMessage.success('Added to whitelist')
    await loadSkillScanner() // Refresh to get the updated whitelist
  } catch (e: any) {
    ElMessage.error('Add failed: ' + e.message)
  }
}

async function removeWhitelist(skillName: string) {
  try {
    await removeSkillScannerWhitelist(skillName)
    ElMessage.success('Removed from whitelist')
    await loadSkillScanner()
  } catch (e: any) {
    ElMessage.error('Remove failed: ' + e.message)
  }
}

onMounted(() => {
  loadToolGuard()
  loadSkillScanner()
})
</script>

<style scoped>
.page { max-width: 960px; }
.section { margin-bottom: 36px; }
.section-title { font-size: 18px; font-weight: 700; color: var(--text-1); margin-bottom: 4px; }
.section-desc { font-size: 13px; color: var(--text-3); margin-bottom: 16px; }

.tab-content { padding-top: 16px; }
.tab-desc { font-size: 13px; color: var(--text-3); margin-bottom: 20px; }

.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 24px;
}

.mb-6 { margin-bottom: 24px; }
.mb-4 { margin-bottom: 16px; }
.mt-4 { margin-top: 16px; }
.flex-row { display: flex; }
.justify-between { justify-content: space-between; }
.justify-end { justify-content: flex-end; }
.align-center { align-items: center; }
.flex { display: flex; }
.flex-1 { flex: 1; }

.form-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.form-row-group {
  display: flex;
  gap: 16px;
}
.form-row label {
  font-size: 13px;
  color: var(--text-2);
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
}
.info-icon {
  color: var(--text-4);
  font-size: 14px;
  cursor: help;
}

.section-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.subsection-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-1);
}

.actions-cell {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: center;
}

.text-xs { font-size: 12px; }
.text-info { color: var(--info); }

/* Preview Dialog */
.preview-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
  font-size: 14px;
}
.preview-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
}
.preview-label {
  font-weight: 600;
  color: var(--text-2);
  min-width: 70px;
}
.preview-value {
  color: var(--text-1);
}
.severity-tag {
  font-weight: 600;
}
.action-tag {
  color: #d97706;
  background-color: #fef3c7;
  border-color: #fde68a;
  font-weight: 500;
}
[data-theme="dark"] .action-tag {
  color: #fcd34d;
  background-color: rgba(217, 119, 6, 0.2);
  border-color: rgba(217, 119, 6, 0.3);
}

.preview-code-section {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.code-box {
  background-color: var(--bg);
  border-radius: var(--radius);
  padding: 12px;
  color: var(--text-2);
  font-family: Consolas, Monaco, monospace;
  overflow-x: auto;
}
.code-line {
  line-height: 1.5;
}
</style>
