<template>
  <div>
    <div v-if="loading" class="spinner"></div>
    <div v-else>
      <div v-if="msg" class="alert-custom alert-error">{{ msg }}</div>

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
                <span class="badge-custom" :class="badgeClass(c.status)">{{ label(c.status) }}</span>
              </div>
              <small class="text-muted">{{ c.created_at?.slice(0,10) }}</small>
            </div>
          </div>
        </div>

        <!-- Emergency Contacts quick-dial (hidden when none exist) -->
        <div class="col-12" v-if="emergency.length > 0">
          <div class="card">
            <div class="card-header-custom d-flex justify-content-between align-items-center">
              <span>🚨 Emergency Contacts</span>
              <router-link to="/app/emergency" class="text-white text-decoration-underline" style="font-size:0.8rem;">
                View all
              </router-link>
            </div>
            <div class="row g-0">
              <div v-for="c in emergency" :key="c.id" class="col-12 col-sm-6 col-lg-3 p-3"
                   style="border-bottom:1px solid #f1f5f9;">
                <div class="d-flex align-items-center gap-2 mb-1">
                  <i class="fas" :class="serviceMeta(c.service_type).icon" style="color:#1B2A4A;"></i>
                  <span class="fw-semibold" style="font-size:0.9rem;">{{ serviceMeta(c.service_type).label }}</span>
                </div>
                <div class="text-muted mb-2" style="font-size:0.8rem;">{{ label(c.name) }}</div>
                <a v-if="telHref(c.phone)" :href="telHref(c.phone)"
                   class="btn btn-sm btn-outline-danger w-100 text-decoration-none">
                  <i class="fas fa-phone me-1"></i>{{ c.phone }}
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { invoicesAPI, complaintsAPI, noticesAPI, emergencyAPI, errText } from '../api/index'
import { badgeClass, label, num, serviceMeta, telHref } from '../utils/format'

const loading = ref(true)
const msg = ref('')
const unpaidInvoices = ref([])
const unpaidTotal = ref(0)
const myComplaints = ref([])
const notices = ref([])
const emergency = ref([])

onMounted(async () => {
  // allSettled, not all: a single failing endpoint used to zero out every panel,
  // which is indistinguishable from having nothing due and no complaints.
  const sections = ['Invoices', 'Complaints', 'Notices', 'Emergency Contacts']
  const results = await Promise.allSettled([
    invoicesAPI.getAll(), complaintsAPI.getAll(), noticesAPI.getAll(), emergencyAPI.getAll()
  ])
  const [inv, comp, not, emg] = results.map(r =>
    r.status === 'fulfilled' && Array.isArray(r.value?.data) ? r.value.data : null
  )

  if (inv) {
    unpaidInvoices.value = inv.filter(i => i.status !== 'PAID')
    // num(): a null amount used to render the dues total as "₹NaN".
    unpaidTotal.value = unpaidInvoices.value
      .reduce((s, i) => s + num(i.amount), 0).toLocaleString('en-IN')
  }
  if (comp) myComplaints.value = comp
  if (not) notices.value = not
  if (emg) emergency.value = emg.slice(0, 4)   // quick-dial shortlist

  const failed = results
    .map((r, i) => (r.status === 'rejected' ? sections[i] : null))
    .filter(Boolean)
  if (failed.length) {
    const first = results.find(r => r.status === 'rejected')
    msg.value = `Could not load ${failed.join(', ')}. ${errText(first.reason)}`
  }
  loading.value = false
})
</script>
