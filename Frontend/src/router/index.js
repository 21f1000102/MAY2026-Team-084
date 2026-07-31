import { createRouter, createWebHistory } from 'vue-router'
import { authStore } from '../store/auth'

import LoginPage from '../components/LoginPage.vue'
import RegisterPage from '../components/RegisterPage.vue'
import DashboardLayout from '../components/DashboardLayout.vue'
import SecretaryDashboard from '../components/SecretaryDashboard.vue'
import ResidentDashboard from '../components/ResidentDashboard.vue'
import WorkerDashboard from '../components/WorkerDashboard.vue'
import MembersPage from '../components/MembersPage.vue'
import ComplaintsPage from '../components/ComplaintsPage.vue'
import InvoicesPage from '../components/InvoicesPage.vue'
import ExpensesPage from '../components/ExpensesPage.vue'
import NoticesPage from '../components/NoticesPage.vue'
import PollsPage from '../components/PollsPage.vue'
import MaintenancePage from '../components/MaintenancePage.vue'
import EquipmentPage from '../components/EquipmentPage.vue'
import HealthScorePage from '../components/HealthScorePage.vue'
import ConflictsPage from '../components/ConflictsPage.vue'
import ParkingPage from '../components/ParkingPage.vue'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: LoginPage, meta: { guest: true } },
  { path: '/register', component: RegisterPage, meta: { guest: true } },
  {
    path: '/app',
    component: DashboardLayout,
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/app/dashboard' },
      { path: 'dashboard', component: SecretaryDashboard, meta: { adminOnly: true } },
      { path: 'home', component: ResidentDashboard, meta: { residentOnly: true } },
      { path: 'worker', component: WorkerDashboard, meta: { workerOnly: true } },
      { path: 'members', component: MembersPage, meta: { adminOnly: true } },
      { path: 'complaints', component: ComplaintsPage },
      { path: 'invoices', component: InvoicesPage },
      { path: 'expenses', component: ExpensesPage, meta: { adminOnly: true } },
      { path: 'notices', component: NoticesPage },
      { path: 'polls', component: PollsPage },
      { path: 'maintenance', component: MaintenancePage, meta: { adminOnly: true } },
      { path: 'equipment', component: EquipmentPage, meta: { adminOnly: true } },
      { path: 'health', component: HealthScorePage, meta: { adminOnly: true } },
      { path: 'conflicts', component: ConflictsPage },
      { path: 'parking', component: ParkingPage },
    ]
  }
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, from, next) => {
  const loggedIn = authStore.isLoggedIn
  const isAdmin = authStore.isAdmin
  const isWorker = authStore.user?.role === 'WORKER'
  const isResident = authStore.isResident

  if (to.meta.requiresAuth && !loggedIn) return next('/login')

  // redirect after login based on role
  if (to.meta.guest && loggedIn) {
    if (isAdmin) return next('/app/dashboard')
    if (isWorker) return next('/app/worker')
    return next('/app/home')
  }

  if (to.meta.adminOnly && !isAdmin) {
    if (isWorker) return next('/app/worker')
    return next('/app/home')
  }
  if (to.meta.residentOnly && !isResident) {
    if (isAdmin) return next('/app/dashboard')
    if (isWorker) return next('/app/worker')
  }
  if (to.meta.workerOnly && !isWorker) {
    if (isAdmin) return next('/app/dashboard')
    return next('/app/home')
  }
  next()
})

export default router
