import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import HomeView from '@/views/HomeView.vue'
import AccountView from '@/views/AccountView.vue'
import HistoryView from '../views/HistoryView.vue'
import GroupDetailView from '../views/GroupDetailView.vue'
import ValidationResultsView from '../views/ValidationResultsView.vue'
import LoginPage from '@/components/LoginPage.vue'
import RegisterView from '@/views/RegisterView.vue'
import WerView from '@/views/WerView.vue'
import ValidationEditorView from '@/views/ValidationEditorView.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
    meta: { requiresAuth: true },
  },
  {
    path: '/login',
    name: 'login',
    component: LoginPage,
  },
  {
    path: '/register',
    name: 'register',
    component: RegisterView,
  },
  {
    path: '/account',
    name: 'account',
    component: AccountView,
    meta: { requiresAuth: true },
  },
  {
    path: '/history',
    name: 'history',
    component: HistoryView,
    meta: { requiresAuth: true },
  },
  {
    path: '/group-detail/:groupId',
    name: 'group-detail',
    component: GroupDetailView,
    meta: { requiresAuth: true },
    props: true,
  },
  {
    path: '/validation-editor/:groupId',
    name: 'validation-editor',
    component: ValidationEditorView,
    meta: { requiresAuth: true },
    props: true,
  },
  {
    path: '/validation-results/:groupId',
    name: 'validation-results',
    component: ValidationResultsView,
    meta: { requiresAuth: true },
    props: true,
  },
  {
    path: '/wer',
    name: 'wer',
    component: WerView,
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory('/'),
  routes,
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  // Si la ruta requiere autenticación y el usuario no está autenticado
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'login' })
  } else if (to.name === 'login' && authStore.isAuthenticated) {
    next({ name: 'home' })
  } else {
    next()
  }
})

export default router
