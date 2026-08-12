import { createRouter, createWebHistory } from 'vue-router'
import { authStore } from '../store/auth'

import LoginPage from '../componenets/LoginPage.vue'
import RegisterPage from '../componenets/RegisterPage.vue'
import DashboardLayout from '../componenets/DashboardLayout.vue'
import SecretaryDashboard from '../componenets/SecretaryDashboard.vue'
import ResidentDashboard from '../componenets/ResidentDashboard.vue'
import WorkerDashboard from '../componenets/WorkerDashboard.vue'
import MembersPage from '../componenets/MembersPage.vue'
import ComplaintsPage from '../componenets/ComplaintsPage.vue'
import InvoicesPage from '../componenets/InvoicesPage.vue'
import ExpensesPage from '../componenets/ExpensesPage.vue'
import NoticesPage from '../componenets/NoticesPage.vue'
import PollsPage from '../componenets/PollsPage.vue'
import MaintenancePage from '../componenets/MaintenancePage.vue'
import EquipmentPage from '../componenets/EquipmentPage.vue'
import HealthScorePage from '../componenets/HealthScorePage.vue'
import ConflictsPage from '../componenets/ConflictsPage.vue'
import ParkingPage from '../componenets/ParkingPage.vue'
import EmergencyPage from '../componenets/EmergencyPage.vue'
import EventsPage from '../componenets/EventsPage.vue'
import ReportsPage from '../componenets/ReportsPage.vue'

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
      // Admin sees/manages every task; a worker sees only their own assigned
      // tasks (the backend scopes the list) and may mark them complete.
      { path: 'maintenance', component: MaintenancePage },
      { path: 'equipment', component: EquipmentPage, meta: { adminOnly: true } },
      { path: 'health', component: HealthScorePage, meta: { adminOnly: true } },
      { path: 'conflicts', component: ConflictsPage },
      { path: 'parking', component: ParkingPage },
      { path: 'emergency', component: EmergencyPage },
      { path: 'events', component: EventsPage },
      { path: 'reports', component: ReportsPage, meta: { adminOnly: true } },
    ]
  }
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, from, next) => {
  const loggedIn = authStore.isLoggedIn
  const isAdmin = authStore.isAdmin
  const isWorker = authStore.isWorker
  const isResident = authStore.isResident

  // The landing route for whatever role is logged in. Roles that match none of
  // the three dashboards (AUDITOR, ...) get a route with no role restriction —
  // sending them to a guarded one would bounce them straight back here.
  const homeFor = () => {
    if (isAdmin) return '/app/dashboard'
    if (isWorker) return '/app/worker'
    if (isResident) return '/app/home'
    return '/app/notices'
  }

  if (to.meta.requiresAuth && !loggedIn) return next('/login')

  // redirect after login based on role
  if (to.meta.guest && loggedIn) return next(homeFor())

  // Every branch below terminates with a next(): the residentOnly guard used to
  // fall through when the user was neither admin nor worker nor resident, which
  // let unrelated roles land on the resident dashboard.
  if (to.meta.adminOnly && !isAdmin) return next(homeFor())
  if (to.meta.residentOnly && !isResident) return next(homeFor())
  if (to.meta.workerOnly && !isWorker) return next(homeFor())

  return next()
})

export default router
