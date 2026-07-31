<template>
  <div class="register-wrapper">
    <nav class="navbar-top">
      <div class="navbar-container">
        <div class="logo-section">
          <span class="logo"> SocietyEase</span>
        </div>
        <div class="nav-info">
          <span class="nav-text">Already have an account? <router-link to="/login" class="signin-link">Sign In</router-link></span>
        </div>
      </div>
    </nav>


    <div class="register-container">
      <div class="left-section">
        <div class="background-content">
          <div class="content-overlay">
            <h1 class="left-title">Join SocietyEase</h1>
            <p class="left-subtitle">Create Your Profile Today</p>
            <p class="left-description">Register with us to access our community features, connect with other members, and enjoy a personalized experience.</p>
          </div>
        </div>
      </div>

      <div class="right-section">
        <div class="form-container card border-0 shadow-sm">
          <div class="card-body p-4 p-md-5">
            <h2 class="form-title">Sign up with your Email</h2>
            <p class="form-subtitle">Create your SocietyEase account in just a few steps</p>

            <form @submit.prevent="submit">
              <div class="form-group">
                <label for="username" class="form-label">Email Address</label>
                <input 
                  id="username" 
                  v-model="form.username" 
                  type="email" 
                  class="form-input" 
                  placeholder="Enter your email"
                  required 
                />
              </div>

            <div class="form-group">
              <label for="full_name" class="form-label">Full Name</label>
              <input 
                id="full_name" 
                v-model="form.full_name" 
                type="text" 
                class="form-input" 
                placeholder="Enter your full name"
                required 
              />
            </div>

            <div class="form-group">
              <label for="password" class="form-label">Password</label>
              <input 
                id="password" 
                v-model="form.password" 
                type="password" 
                class="form-input" 
                placeholder="Enter your password"
                required 
              />
            </div>

            <div class="form-group">
              <label for="role" class="form-label">Role</label>
              <select 
                id="role" 
                v-model="form.role" 
                class="form-input" 
                required 
              >
                <option value="">Select a role</option>
                <option value="ADMIN">Admin</option>
                <option value="TENANT">Tenant</option>
                <option value="OWNER">Owner</option>
                <option value="TREASURER">Treasurer</option>
                <option value="WORKER">Worker</option>
                <option value="COMMITTEE_MEMBER">Committee Member</option>
                <option value="AUDITOR">Auditor</option>
                <option value="SYSTEM_ADMIN">System Admin</option>
              </select>
            </div>

            <div v-if="error" class="alert alert-error">
              ✕ {{ error }}
            </div>

            <div v-if="success" class="alert alert-success">
              ✓ {{ success }}
            </div>

            <button type="submit" class="sign-up-btn" :disabled="loading">
              {{ loading ? 'Creating account...' : 'Sign Up' }}
            </button>
          </form>

          <p class="signin-prompt">
            Already have an account? 
            <router-link to="/login" class="signin-link-bottom">Sign In</router-link>
          </p>
        </div>
      </div>
    </div>
  </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { getApiBase } from '../utils/auth'

const form = reactive({ 
  username: '', 
  full_name: '', 
  password: '', 
  role: 'TENANT' 
})
const loading = ref(false)
const error = ref('')
const success = ref('')

const router = useRouter()

async function submit() {
    error.value = ''
    success.value = ''
    loading.value = true

    if (!form.username || !form.full_name || !form.password || !form.role) {
        error.value = 'Please fill in all required fields.'
        loading.value = false
        return
    }

    if (form.password.length < 6) {
        error.value = 'Password must be at least 6 characters long.'
        loading.value = false
        return
    }

    try {
        const res = await axios.post(`${getApiBase()}/api/auth/register`, {
            name: form.full_name,
            email: form.username,
            password: form.password,
            role: form.role
        }, { headers: { 'Content-Type': 'application/json' } })

        if (res.status === 201 || res.data?.message) {
            success.value = res.data?.message || 'Account created successfully! Redirecting to login...'
            setTimeout(() => { router.push('/login') }, 1500)
        } else {
            error.value = 'Registration failed.'
        }
    } catch (err) {
        error.value = err.response?.data?.error || err.message || 'Registration failed.'
    } finally {
        loading.value = false
    }
}
</script>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.register-wrapper {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  padding: 1.5rem 0 2rem;
  background: radial-gradient(circle at top center, #f7fbff 0%, #f2f7ff 45%, #eef4ff 100%);
  color: #000000;
}

.navbar-top {
  background: #ffffff;
  border-bottom: 1px solid rgba(135, 172, 210, 0.2);
  padding: 1rem 0;
  box-shadow: 0 10px 30px rgba(132, 170, 210, 0.08);
}

.navbar-container {
  max-width: 1240px;
  margin: 0 auto;
  padding: 0 0.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo-section {
  display: flex;
  align-items: center;
}

.logo {
  font-size: 1.4rem;
  font-weight: 800;
  color: #000000;
  cursor: pointer;
  transition: color 0.3s ease;
  letter-spacing: -0.02em;
}

.logo:hover {
  color: #000000;
}

.nav-info {
  display: flex;
  align-items: center;
}

.nav-text {
  color: #000000;
  font-size: 0.95rem;
}

.signin-link {
  color: #000000;
  text-decoration: none;
  font-weight: 700;
  margin-left: 0.5rem;
  transition: color 0.3s ease;
}

.signin-link:hover {
  color: #000000;
  text-decoration: underline;
}

.register-container {
  flex: 1;
  width: 100%;
  max-width: 1400px;
  margin: 1.5rem auto 2rem;
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 2rem;
  align-items: stretch;
  padding: 0 1rem;
}

.left-section {
  background: linear-gradient(145deg, #e5f2ff 0%, #d6e8ff 100%);
  padding: 2.2rem 1.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #264863;
  position: relative;
  overflow: hidden;
  max-width: 1000px;
  min-height: 520px;
  border-radius: 2rem;
}


.background-content {
  position: relative;
  z-index: 2;
  text-align: center;
}

.content-overlay {
  animation: slideInLeft 0.8s ease-out;
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.left-title {
  font-size: clamp(2rem, 2.8vw, 2.6rem);
  font-weight: 800;
  margin-bottom: 0.9rem;
  line-height: 1.15;
  letter-spacing: -0.02em;
  color: #000000;
}

.left-subtitle {
  font-size: clamp(1.05rem, 1.4vw, 1.25rem);
  margin-bottom: 1.35rem;
  opacity: 0.95;
  font-weight: 700;
  color: #000000;
}

.left-description {
  font-size: 1rem;
  opacity: 0.95;
  line-height: 1.6;
  max-width: 350px;
  color: #000000;
}

.right-section {
  background: transparent;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: visible;
}

.form-container {
  width: 100%;
  max-width: 520px;
  border-radius: 2rem;
  overflow: hidden;
  animation: slideInRight 0.8s ease-out;
}

.form-container .card-body {
  padding: 2rem 1.75rem;
  background: #ffffff;
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.form-title {
  font-size: 1.8rem;
  color: #000000;
  margin-bottom: 0.5rem;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.form-subtitle {
  color: #000000;
  font-size: 0.95rem;
  margin-bottom: 1.5rem;
  font-weight: 500;
}

.form-group {
  margin-bottom: 1.2rem;
}

.form-label {
  display: block;
  margin-bottom: 0.5rem;
  color: #000000;
  font-weight: 700;
  font-size: 0.9rem;
  letter-spacing: 0.3px;
}

.form-input {
  width: 100%;
  padding: 0.85rem 1.1rem;
  color: #000000;
  border: 2px solid #d7e5f5;
  border-radius: 16px;
  font-size: 0.95rem;
  transition: all 0.3s ease;
  background: #fbfdff;
  font-weight: 500;
}

.form-input:hover {
  border-color: #b7d1ec;
}

.form-input:focus {
  outline: none;
  border-color: #aac9ed;
  background: #ffffff;
  box-shadow: 0 0 0 4px rgba(170, 201, 237, 0.15);
}

.form-input::placeholder {
  color: #888888;
}

.alert {
  padding: 1rem 1.1rem;
  border-radius: 16px;
  margin-bottom: 1rem;
  font-size: 0.9rem;
  font-weight: 600;
  border: 2px solid rgba(209, 226, 242, 0.9);
}

.alert-error {
  background: #f8fbff;
  color: #356a93;
  border: 2px solid #c7ddef;
}

.alert-success {
  background: #f0fdf4;
  color: #2e5f74;
  border: 2px solid #c8e6c9;
}

.sign-up-btn {
  width: 100%;
  padding: 1rem;
  background: linear-gradient(135deg, #5c92df 0%, #84b5f1 100%);
  color: white;
  border: none;
  border-radius: 16px;
  font-size: 1rem;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 8px 20px rgba(92, 146, 223, 0.2);
  margin-top: 0.5rem;
  letter-spacing: 0.5px;
}

.sign-up-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 12px 28px rgba(92, 146, 223, 0.28);
}

.sign-up-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.sign-up-btn:active:not(:disabled) {
  transform: translateY(0);
}

.signin-prompt {
  text-align: center;
  margin-top: 1.75rem;
  color: #000000;
  font-size: 0.95rem;
  font-weight: 500;
}

.signin-link-bottom {
  color: #5c92df;
  text-decoration: none;
  font-weight: 700;
  transition: color 0.3s ease;
}

.signin-link-bottom:hover {
  color: #4774b1;
  text-decoration: underline;
}

@media (max-width: 992px) {
  .register-container {
    grid-template-columns: 1fr;
  }

  .left-section {
    display: none;
  }

  .right-section {
    padding: 2rem;
  }

  .form-container {
    max-width: 100%;
  }
}

@media (max-width: 768px) {
  .navbar-container {
    padding: 0 1rem;
    flex-direction: column;
    gap: 0.5rem;
  }

  .nav-info {
    font-size: 0.85rem;
  }

  .right-section {
    padding: 1.5rem;
  }

  .form-title {
    font-size: 1.5rem;
  }

  .form-input {
    padding: 0.65rem 0.9rem;
    color: #000000;
  }

  .form-group {
    margin-bottom: 0.8rem;
  }
}

@media (max-width: 480px) {
  .navbar-top {
    padding: 0.75rem 0;
  }

  .navbar-container {
    padding: 0 1rem;
  }

  .logo {
    font-size: 1.2rem;
  }

  .nav-text {
    display: none;
  }

  .right-section {
    padding: 1rem;
  }

  .form-container {
    padding: 0;
  }

  .form-title {
    font-size: 1.3rem;
  }

  .form-subtitle {
    font-size: 0.85rem;
  }

  .left-title {
    font-size: 1.8rem;
  }

  .left-subtitle {
    font-size: 1.1rem;
  }

  .form-group {
    margin-bottom: 0.7rem;
  }

  .form-input {
    padding: 0.6rem 0.8rem;
    font-size: 0.9rem;
  }

  .form-label {
    font-size: 0.85rem;
  }
}
</style>
