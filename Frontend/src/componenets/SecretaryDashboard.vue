<template>
  <div>
    <div v-if="loading" class="spinner"></div>
    <div v-else>
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
            <table v-else class="table-custom">
              <thead><tr><th>Title</th><th>Flat</th><th>Status</th></tr></thead>
              <tbody>
                <tr v-for="c in recentComplaints" :key="c.id">
                  <td>{{ c.title }}</td>
                  <td>{{ c.flat_number }}</td>
                  <td><span class="badge-custom" :class="`badge-${c.status.toLowerCase().replace('_','-')}`">{{ c.status }}</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { membersAPI, complaintsAPI, invoicesAPI, pollsAPI } from '../api/index'

const loading = ref(true)
const stats = ref({ members: 0, openComplaints: 0, unpaidInvoices: 0, activePolls: 0 })
const collected = ref(0)
const pending = ref(0)
const recentComplaints = ref([])

onMounted(async () => {
  try {
    const [members, complaints, invoices, polls] = await Promise.all([
      membersAPI.getAll(), complaintsAPI.getAll(), invoicesAPI.getAll(), pollsAPI.getAll()
    ])
    stats.value.members = members.data.filter(m => m.is_active).length
    stats.value.openComplaints = complaints.data.filter(c => ['OPEN','ASSIGNED','IN_PROGRESS'].includes(c.status)).length
    stats.value.unpaidInvoices = invoices.data.filter(i => i.status === 'UNPAID').length
    stats.value.activePolls = polls.data.filter(p => p.status === 'ACTIVE').length

    collected.value = invoices.data.filter(i => i.status === 'PAID').reduce((s, i) => s + i.amount, 0).toLocaleString('en-IN')
    pending.value = invoices.data.filter(i => i.status !== 'PAID').reduce((s, i) => s + i.amount, 0).toLocaleString('en-IN')
    recentComplaints.value = complaints.data.slice(0, 5)
  } catch(e) {}
  loading.value = false
})
</script>
