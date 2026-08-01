import { reactive } from 'vue'

export const authStore = reactive({
  user: JSON.parse(localStorage.getItem('user') || 'null'),
  token: localStorage.getItem('token') || null,

  get isLoggedIn() { return !!this.token },

  // Nav-level admin: who may SEE the management sections.
  get isAdmin() { return ['ADMIN','SYSTEM_ADMIN','TREASURER','COMMITTEE_MEMBER'].includes(this.user?.role) },

  // Action-level admin for money: the finance endpoints only accept these roles,
  // so a COMMITTEE_MEMBER shown those buttons just collects 403s.
  get isFinanceAdmin() { return ['ADMIN','SYSTEM_ADMIN','TREASURER'].includes(this.user?.role) },

  get isResident() { return ['TENANT','OWNER'].includes(this.user?.role) },
  get isWorker() { return this.user?.role === 'WORKER' },

  login(token, user) {
    this.token = token
    this.user = user
    localStorage.setItem('token', token)
    localStorage.setItem('user', JSON.stringify(user))
  },

  logout() {
    this.token = null
    this.user = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }
})
