<template>
  <div>
    <div v-if="loading" class="spinner"></div>
    <div v-else>
      <!-- Due Alert -->
      <div v-if="unpaidInvoices.length > 0" class="alert-custom alert-error mb-4">
        <i class="fas fa-exclamation-triangle me-2"></i>
        You have <strong>{{ unpaidInvoices.length }} unpaid invoice(s)</strong> totalling
        <strong>₹{{ unpaidTotal }}</strong>. Please pay before the due date.
      </div>

      <!-- Stats -->
      <div class="row g-3 mb-4">
        <div class="col-6">
          <div class="stat-card">
            <div class="stat-icon" style="background:#dc2626;"><i class="fas fa-rupee-sign"></i></div>
            <div><div class="stat-value">₹{{ unpaidTotal }}</div><div class="stat-label">Pending Dues</div></div>
          </div>
        </div>
        <div class="col-6">
          <div class="stat-card">
            <div class="stat-icon" style="background:#d97706;"><i class="fas fa-exclamation-circle"></i></div>
            <div><div class="stat-value">{{ myComplaints.length }}</div><div class="stat-label">My Complaints</div></div>
          </div>
        </div>
      </div>

      <div class="row g-3">
        <!-- Latest Notices -->
        <div class="col-md-6">
          <div class="card">
            <div class="card-header-custom">📢 Latest Notices</div>
            <div v-if="notices.length === 0" class="empty-state p-4">
              <i class="fas fa-bell-slash"></i><p>No notices</p>
            </div>
            <div v-for="n in notices.slice(0,3)" :key="n.id" class="p-3" style="border-bottom:1px solid #f1f5f9;">
              <p class="mb-0 fw-semibold">{{ n.title }}</p>
              <small class="text-muted">{{ n.created_at?.slice(0,10) }}</small>
            </div>
          </div>
        </div>

        <!-- My Complaints -->
        <div class="col-md-6">
          <div class="card">
            <div class="card-header-custom">🔧 My Complaints</div>
            <div v-if="myComplaints.length === 0" class="empty-state p-4">
              <i class="fas fa-check-circle" style="color:#0E7C7B;"></i><p>No complaints!</p>
            </div>
            <div v-for="c in myComplaints.slice(0,4)" :key="c.id" class="p-3" style="border-bottom:1px solid #f1f5f9;">
              <div class="d-flex justify-content-between align-items-center">
                <p class="mb-0 fw-semibold">{{ c.title }}</p>
                <span class="badge-custom" :class="`badge-${c.status.toLowerCase().replace('_','-')}`">{{ c.status }}</span>
              </div>
              <small class="text-muted">{{ c.created_at?.slice(0,10) }}</small>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { invoicesAPI, complaintsAPI, noticesAPI } from '../api/index'
import { authStore } from '../store/auth'

const loading = ref(true)
const unpaidInvoices = ref([])
const unpaidTotal = ref(0)
const myComplaints = ref([])
const notices = ref([])

onMounted(async () => {
  try {
    const [inv, comp, not] = await Promise.all([
      invoicesAPI.getAll(), complaintsAPI.getAll(), noticesAPI.getAll()
    ])
    unpaidInvoices.value = inv.data.filter(i => i.status !== 'PAID')
    unpaidTotal.value = unpaidInvoices.value.reduce((s, i) => s + i.amount, 0).toLocaleString('en-IN')
    myComplaints.value = comp.data
    notices.value = not.data
  } catch(e) {}
  loading.value = false
})
</script>
