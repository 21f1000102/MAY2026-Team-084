<template>
  <div class="login-page">
    <div class="login-card">
      <div class="text-center mb-4">
        <h3 style="font-weight:700;color:#1B2A4A;">Create Account</h3>
        <p style="color:#718096;font-size:0.9rem;">SocietyEase Portal</p>
      </div>

      <div v-if="error" class="alert-custom alert-error">{{ error }}</div>
      <div v-if="success" class="alert-custom alert-success">{{ success }}</div>

      <div class="form-group">
        <label class="form-label">Full Name</label>
        <input v-model="form.name" class="form-control-custom" placeholder="Ravi Kumar"/>
      </div>
      <div class="form-group">
        <label class="form-label">Email</label>
        <input v-model="form.email" type="email" class="form-control-custom" placeholder="ravi@apt.com"/>
      </div>
      <div class="form-group">
        <label class="form-label">Phone</label>
        <input v-model="form.phone" class="form-control-custom" placeholder="9876543210"/>
      </div>
      <div class="form-group">
        <label class="form-label">Password</label>
        <input v-model="form.password" type="password" class="form-control-custom"/>
      </div>
      <div class="form-group">
        <label class="form-label">Role</label>
        <select v-model="form.role" class="form-control-custom">
          <option value="TENANT">Tenant</option>
          <option value="OWNER">Owner</option>
          <option value="ADMIN">Admin / Secretary</option>
          <option value="TREASURER">Treasurer</option>
        </select>
      </div>

      <button @click="register" class="btn-primary-custom w-100 mt-3" :disabled="loading">
        <span v-if="loading"><i class="fas fa-spinner fa-spin me-2"></i>Creating...</span>
        <span v-else>Create Account</span>
      </button>

      <p class="text-center mt-3" style="font-size:0.85rem;color:#718096;">
        Already have an account?
        <router-link to="/login" style="color:#1B2A4A;font-weight:600;">Sign In</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authAPI } from '../api/index'
import { authStore } from '../store/auth'

const router = useRouter()
const form = ref({ name: '', email: '', phone: '', password: '', role: 'TENANT' })
const error = ref('')
const success = ref('')
const loading = ref(false)

async function register() {
  loading.value = true
  error.value = ''
  try {
    const res = await authAPI.register(form.value)
    authStore.login(res.data.token, res.data.user)
    router.push(authStore.isAdmin ? '/app/dashboard' : '/app/home')
  } catch (e) {
    error.value = e.response?.data?.error || 'Registration failed'
  } finally {
    loading.value = false
  }
}
</script>
