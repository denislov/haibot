import { createRouter, createWebHistory } from 'vue-router'

export default createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/chat',
    },
    {
      path: '/chat',
      name: 'chat',
      component: () => import('@/modules/chat/ChatLayout.vue'),
    },
    {
      path: '/settings',
      component: () => import('@/modules/settings/SettingsLayout.vue'),
      redirect: '/settings/models',
      children: [
        {
          path: 'models',
          name: 'settings-models',
          component: () => import('@/modules/settings/pages/ModelsSettings.vue'),
        },
        {
          path: 'mcp',
          name: 'settings-mcp',
          component: () => import('@/modules/settings/pages/MCPSettings.vue'),
        },
        {
          path: 'agents',
          name: 'settings-agents',
          component: () => import('@/modules/settings/pages/AgentsSettings.vue'),
        },
        {
          path: 'channels',
          name: 'settings-channels',
          component: () => import('@/modules/settings/pages/ChannelsSettings.vue'),
        },
        {
          path: 'sessions',
          name: 'settings-sessions',
          component: () => import('@/modules/settings/pages/SessionsSettings.vue'),
        },
        {
          path: 'workspace',
          name: 'settings-workspace',
          component: () => import('@/modules/settings/pages/WorkspaceSettings.vue'),
        },
        {
          path: 'skills',
          name: 'settings-skills',
          component: () => import('@/modules/settings/pages/SkillsSettings.vue'),
        },
        {
          path: 'envs',
          name: 'settings-envs',
          component: () => import('@/modules/settings/pages/EnvsSettings.vue'),
        },
        {
          path: 'crons',
          name: 'settings-crons',
          component: () => import('@/modules/settings/pages/CronsSettings.vue'),
        },
        {
          path: 'group-chats',
          name: 'settings-group-chats',
          component: () => import('@/modules/settings/pages/GroupChatSettings.vue'),
        },
      ],
    },
  ],
})
