<template>
  <div>
    <div v-if="loading" class="spinner"></div>
    <div v-else>
      <div v-if="msg" class="alert-custom alert-error">{{ msg }}</div>

      <!-- Stats Row -->
      <div class="row g-3 mb-4">
        <div class="col-6 col-md-3">
          <div class="stat-card">
            <div class="stat-icon" style="background:#1B2A4A;"><i class="fas fa-users"></i></div>
            <div><div class="stat-value">{{ stats.members }}</div><div class="stat-label">Active Members</div></div>
          </div>
        </div>
        <div class="col-6 col-md-3">
          <div class="stat-card">
            <div class="stat-icon" style="background:#dc2626;"><i class="fas fa-exclamation-circle"></i></div>
            <div><div class="stat-value">{{ stats.openComplaints }}</div><div class="stat-label">Open Complaints</div></div>
          </div>
        </div>
        <div class="col-6 col-md-3">
          <div class="stat-card">
            <div class="stat-icon" style="background:#d97706;"><i class="fas fa-file-invoice"></i></div>
            <div><div class="stat-value">{{ stats.unpaidInvoices }}</div><div class="stat-label">Unpaid Invoices</div></div>
          </div>
        </div>
        <div class="col-6 col-md-3">
          <div class="stat-card">
            <div class="stat-icon" style="background:#0E7C7B;"><i class="fas fa-poll"></i></div>
            <div><div class="stat-value">{{ stats.activePolls }}</div><div class="stat-label">Active Polls</div></div>
          </div>
        </div>
      </div>

      <!-- Payment Summary + Recent Complaints -->
      <div class="row g-3">
        <div class="col-md-5">
          <div class="card">
            <div class="card-header-custom">💰 Payment Summary</div>
            <div class="p-4">
              <div class="d-flex gap-3">
                <div style="flex:1;background:#d1fae5;border-radius:10px;padding:16px;text-align:center;">
                  <div style="font-size:1.4rem;font-weight:700;color:#065f46;">₹{{ collected }}</div>
                  <div style="font-size:0.8rem;color:#065f46;">Collected</div>
                </div>
                <div style="flex:1;background:#fee2e2;border-radius:10px;padding:16px;text-align:center;">
                  <div style="font-size:1.4rem;font-weight:700;color:#991b1b;">₹{{ pending }}</div>
                  <div style="font-size:0.8rem;color:#991b1b;">Pending</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="col-md-7">
          <div class="card">
            <div class="card-header-custom">🔧 Recent Complaints</div>
            <div v-if="recentComplaints.length === 0" class="empty-state p-4">
              <i class="fas fa-check-circle" style="color:#0E7C7B;"></i>
              <p>No complaints!</p>
            </div>
            <div v-else class="table-responsive">
            <table class="table-custom">
              <thead><tr><th>Title</th><th>Flat</th><th>Status</th></tr></thead>
              <tbody>
                <tr v-for="c in recentComplaints" :key="c.id">
                  <td>{{ c.title }}</td>
                  <td>{{ c.flat_number }}</td>
                  <td><span class="badge-custom" :class="badgeClass(c.status)">{{ label(c.status) }}</span></td>
                </tr>
              </tbody>
            </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { membersAPI, complaintsAPI, invoicesAPI, pollsAPI, errText } from '../api/index'
import { badgeClass, label, num } from '../utils/format'

const loading = ref(true)
const msg = ref('')
const stats = ref({ members: 0, openComplaints: 0, unpaidInvoices: 0, activePolls: 0 })
const collected = ref(0)
const pending = ref(0)
const recentComplaints = ref([])

onMounted(async () => {
  // allSettled, not all: one failing endpoint used to reject the whole batch and
  // leave every stat at 0 / "No complaints!", which reads as an empty society
  // rather than a broken request. Render whatever came back and name what didn't.
  const sections = ['Members', 'Complaints', 'Invoices', 'Polls']
  const results = await Promise.allSettled([
    membersAPI.getAll(), complaintsAPI.getAll(), invoicesAPI.getAll(), pollsAPI.getAll()
  ])
  const [members, complaints, invoices, polls] = results.map(r =>
    r.status === 'fulfilled' && Array.isArray(r.value?.data) ? r.value.data : null
  )

  if (members) stats.value.members = members.filter(m => m.is_active).length
  if (complaints) {
    stats.value.openComplaints = complaints.filter(c => ['OPEN','ASSIGNED','IN_PROGRESS'].includes(c.status)).length
    recentComplaints.value = complaints.slice(0, 5)
  }
  if (invoices) {
    stats.value.unpaidInvoices = invoices.filter(i => i.status === 'UNPAID').length
    // num(): a null amount used to poison the whole sum into "₹NaN".
    collected.value = invoices.filter(i => i.status === 'PAID')
      .reduce((s, i) => s + num(i.amount), 0).toLocaleString('en-IN')
    pending.value = invoices.filter(i => i.status !== 'PAID')
      .reduce((s, i) => s + num(i.amount), 0).toLocaleString('en-IN')
  }
  if (polls) stats.value.activePolls = polls.filter(p => p.status === 'ACTIVE').length

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
