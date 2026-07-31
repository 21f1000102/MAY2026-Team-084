import { reactive } from 'vue'

export const authStore = reactive({
  user: JSON.parse(localStorage.getItem('user') || 'null'),
  token: localStorage.getItem('token') || null,

  get isLoggedIn() { return !!this.token },
  get isAdmin() { return ['ADMIN','TREASURER','COMMITTEE_MEMBER'].includes(this.user?.role) },
  get isResident() { return ['TENANT','OWNER'].includes(this.user?.role) },

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
