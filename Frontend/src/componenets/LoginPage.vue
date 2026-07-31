<template>
  <div class="login-page">
    <div class="login-card">
      <div class="text-center mb-4">
        <div style="width:60px;height:60px;background:#1B2A4A;border-radius:14px;display:flex;align-items:center;justify-content:center;margin:0 auto 16px;">
          <i class="fas fa-building" style="color:#F2A541;font-size:1.5rem;"></i>
        </div>
        <h3 style="font-weight:700;color:#1B2A4A;">SocietyEase</h3>
        <p style="color:#718096;font-size:0.9rem;">Sign in to your account</p>
      </div>

      <div v-if="error" class="alert-custom alert-error">{{ error }}</div>

      <div class="form-group">
        <label class="form-label">Email Address</label>
        <input v-model="form.email" type="email" class="form-control-custom" placeholder="admin@apt.com" @keyup.enter="login"/>
      </div>
      <div class="form-group">
        <label class="form-label">Password</label>
        <input v-model="form.password" type="password" class="form-control-custom" placeholder="••••••••" @keyup.enter="login"/>
      </div>

      <button @click="login" class="btn-primary-custom w-100 mt-3" :disabled="loading">
        <span v-if="loading"><i class="fas fa-spinner fa-spin me-2"></i>Signing in...</span>
        <span v-else>Sign In <i class="fas fa-arrow-right ms-2"></i></span>
      </button>

      <p class="text-center mt-3" style="font-size:0.85rem;color:#718096;">
        Don't have an account?
        <router-link to="/register" style="color:#1B2A4A;font-weight:600;">Register</router-link>
      </p>

      <div class="mt-4 p-3" style="background:#f0f4f8;border-radius:10px;font-size:0.8rem;">
        <strong style="color:#1B2A4A;">Demo Accounts:</strong><br>
        <span style="color:#718096;">Admin: admin@apt.com / Admin@123</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authAPI } from '../api/index'
import { authStore } from '../store/auth'

const router = useRouter()
const form = ref({ email: '', password: '' })
const error = ref('')
const loading = ref(false)

async function login() {
  if (!form.value.email || !form.value.password) {
    error.value = 'Please enter email and password'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const res = await authAPI.login(form.value)
    authStore.login(res.data.token, res.data.user)
    router.push(authStore.isAdmin ? '/app/dashboard' : '/app/home')
  } catch (e) {
    error.value = e.response?.data?.error || 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>
