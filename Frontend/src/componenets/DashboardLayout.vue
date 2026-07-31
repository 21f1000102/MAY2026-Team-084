<template>
  <div style="display:flex;">
    <!-- SIDEBAR -->
    <aside class="sidebar">
      <div class="sidebar-brand">
        <h4><i class="fas fa-building me-2" style="color:#F2A541;"></i>SocietyEase</h4>
        <small>{{ authStore.user?.role }}</small>
      </div>
      <nav class="sidebar-nav">
        <!-- Admin nav -->
        <template v-if="authStore.isAdmin">
          <router-link class="nav-item" to="/app/dashboard"><i class="fas fa-chart-pie"></i> Dashboard</router-link>
          <router-link class="nav-item" to="/app/members"><i class="fas fa-users"></i> Members</router-link>
          <router-link class="nav-item" to="/app/complaints"><i class="fas fa-exclamation-circle"></i> Complaints</router-link>
          <router-link class="nav-item" to="/app/invoices"><i class="fas fa-file-invoice"></i> Invoices</router-link>
          <router-link class="nav-item" to="/app/expenses"><i class="fas fa-wallet"></i> Expenses</router-link>
          <router-link class="nav-item" to="/app/notices"><i class="fas fa-bullhorn"></i> Notices</router-link>
          <router-link class="nav-item" to="/app/polls"><i class="fas fa-poll"></i> Polls</router-link>
          <router-link class="nav-item" to="/app/maintenance"><i class="fas fa-tools"></i> Maintenance</router-link>
          <router-link class="nav-item" to="/app/equipment"><i class="fas fa-cog"></i> Equipment</router-link>
          <router-link class="nav-item" to="/app/health"><i class="fas fa-heartbeat"></i> Health Score</router-link>
          <router-link class="nav-item" to="/app/conflicts"><i class="fas fa-handshake"></i> Conflicts</router-link>
          <router-link class="nav-item" to="/app/parking"><i class="fas fa-parking"></i> Parking</router-link>
        </template>
        <!-- Worker nav -->
        <template v-else-if="isWorker">
          <router-link class="nav-item" to="/app/worker"><i class="fas fa-hard-hat"></i> My Tasks</router-link>
          <router-link class="nav-item" to="/app/notices"><i class="fas fa-bullhorn"></i> Notices</router-link>
          <router-link class="nav-item" to="/app/parking"><i class="fas fa-parking"></i> Parking</router-link>
        </template>

        <!-- Resident nav -->
        <template v-else>
          <router-link class="nav-item" to="/app/home"><i class="fas fa-home"></i> Dashboard</router-link>
          <router-link class="nav-item" to="/app/invoices"><i class="fas fa-file-invoice"></i> My Invoices</router-link>
          <router-link class="nav-item" to="/app/complaints"><i class="fas fa-exclamation-circle"></i> Complaints</router-link>
          <router-link class="nav-item" to="/app/notices"><i class="fas fa-bullhorn"></i> Notices</router-link>
          <router-link class="nav-item" to="/app/polls"><i class="fas fa-poll"></i> Polls</router-link>
          <router-link class="nav-item" to="/app/conflicts"><i class="fas fa-handshake"></i> Conflicts</router-link>
          <router-link class="nav-item" to="/app/parking"><i class="fas fa-parking"></i> Parking</router-link>
        </template>
      </nav>
      <div class="sidebar-footer">
        <div style="color:rgba(255,255,255,0.7);font-size:0.85rem;margin-bottom:8px;">
          <i class="fas fa-user me-2"></i>{{ authStore.user?.name }}
        </div>
        <button @click="logout" style="background:rgba(255,255,255,0.1);color:#fff;border:none;padding:8px 14px;border-radius:8px;font-size:0.8rem;cursor:pointer;width:100%;">
          <i class="fas fa-sign-out-alt me-2"></i>Logout
        </button>
      </div>
    </aside>

    <!-- MAIN CONTENT -->
    <div class="main-content">
      <div class="topbar">
        <h5 style="margin:0;font-weight:600;color:#1B2A4A;">{{ pageTitle }}</h5>
        <div style="font-size:0.85rem;color:#718096;">
          <i class="fas fa-calendar me-1"></i>{{ today }}
        </div>
      </div>
      <div class="page-content">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authStore } from '../store/auth'

const route = useRoute()
const router = useRouter()

const today = new Date().toLocaleDateString('en-IN', { weekday:'long', year:'numeric', month:'long', day:'numeric' })
const isWorker = authStore.user?.role === 'WORKER'

const titles = {
  '/app/dashboard': 'Dashboard',
  '/app/home': 'My Dashboard',
  '/app/worker': 'My Assigned Tasks',
  '/app/members': 'Member Management',
  '/app/complaints': 'Complaints',
  '/app/invoices': 'Invoices & Payments',
  '/app/expenses': 'Expense Tracker',
  '/app/notices': 'Notice Board',
  '/app/polls': 'Polls & Voting',
  '/app/maintenance': 'Maintenance Tasks',
  '/app/equipment': 'Smart Maintenance Predictor',
  '/app/health': 'Society Health Score',
  '/app/conflicts': 'Conflict Resolver',
  '/app/parking': 'Visitor Parking',
}

const pageTitle = computed(() => titles[route.path] || 'SocietyEase')

function logout() {
  authStore.logout()
  router.push('/login')
}
</script>
