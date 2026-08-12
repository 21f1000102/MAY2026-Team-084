<template>
  <div>
    <div class="card p-3 mb-4 no-print">
      <div class="d-flex flex-wrap gap-2 align-items-end">
        <div class="form-group mb-0">
          <label class="form-label">From</label>
          <input type="date" v-model="range.from" class="form-control-custom" />
        </div>
        <div class="form-group mb-0">
          <label class="form-label">To</label>
          <input type="date" v-model="range.to" class="form-control-custom" />
        </div>
        <button class="btn btn-light btn-sm" @click="applyThisMonth">This Month</button>
        <button class="btn btn-light btn-sm" @click="clearRange">All Time</button>
        <div class="ms-auto d-flex gap-2">
          <button class="btn btn-outline-secondary btn-sm" @click="exportCsv('complaints')">
            <i class="fas fa-file-csv me-1"></i>Complaints CSV
          </button>
          <button class="btn btn-outline-secondary btn-sm" @click="exportCsv('invoices')">
            <i class="fas fa-file-csv me-1"></i>Invoices CSV
          </button>
          <button class="btn btn-outline-secondary btn-sm" @click="exportCsv('expenses')">
            <i class="fas fa-file-csv me-1"></i>Expenses CSV
          </button>
          <button class="btn-primary-custom btn-sm" @click="printReport"><i class="fas fa-print me-1"></i>Print / Save PDF</button>
        </div>
      </div>
    </div>

    <div v-if="msg" class="alert-custom alert-error no-print">{{ msg }}</div>
    <div v-if="loading" class="spinner"></div>

    <div v-else>
      <!-- Headline stat cards -->
      <div class="row g-3 mb-4">
        <div class="col-6 col-md-3">
          <div class="stat-card"><div><div class="stat-value">{{ complaints.total }}</div><div class="stat-label">Total Complaints</div></div></div>
        </div>
        <div class="col-6 col-md-3">
          <div class="stat-card"><div><div class="stat-value">{{ complaints.pending }}</div><div class="stat-label">Pending Complaints</div></div></div>
        </div>
        <div class="col-6 col-md-3">
          <div class="stat-card"><div><div class="stat-value">{{ complaints.resolved }}</div><div class="stat-label">Resolved Complaints</div></div></div>
        </div>
        <div class="col-6 col-md-3">
          <div class="stat-card"><div><div class="stat-value">{{ complaints.avg_resolution_days ?? '—' }}</div><div class="stat-label">Avg. Days to Resolve</div></div></div>
        </div>
        <div class="col-6 col-md-3">
          <div class="stat-card"><div><div class="stat-value">₹{{ money(invoices.total_invoiced) }}</div><div class="stat-label">Total Invoiced</div></div></div>
        </div>
        <div class="col-6 col-md-3">
          <div class="stat-card"><div><div class="stat-value">₹{{ money(invoices.total_collected) }}</div><div class="stat-label">Collected</div></div></div>
        </div>
        <div class="col-6 col-md-3">
          <div class="stat-card"><div><div class="stat-value">₹{{ money(invoices.overdue_amount) }}</div><div class="stat-label">Overdue Amount</div></div></div>
        </div>
        <div class="col-6 col-md-3">
          <div class="stat-card"><div><div class="stat-value">{{ invoices.collection_rate }}%</div><div class="stat-label">Collection Rate</div></div></div>
        </div>
      </div>

      <!-- Charts -->
      <div class="row g-3">
        <div class="col-md-6">
          <div class="card">
            <div class="card-header-custom">Complaints by Status</div>
            <div class="p-4"><StatChart type="bar" :data="complaintsByStatusChart" /></div>
          </div>
        </div>
        <div class="col-md-6">
          <div class="card">
            <div class="card-header-custom">Complaints by Category</div>
            <div class="p-4"><StatChart type="bar" :data="complaintsByCategoryChart" /></div>
          </div>
        </div>
        <div class="col-md-6">
          <div class="card">
            <div class="card-header-custom">Payments: Paid vs Pending</div>
            <div class="p-4"><StatChart type="donut" :data="paymentSplitChart" /></div>
          </div>
        </div>
        <div class="col-md-6">
          <div class="card">
            <div class="card-header-custom">Monthly Collection (₹ Invoiced)</div>
            <div class="p-4"><StatChart type="bar" :data="monthlyCollectionChart" /></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { complaintsAPI, invoicesAPI, expensesAPI, errText, errTextFromBlob, downloadBlob } from '../api/index'
import { money, today } from '../utils/format'
import StatChart from './StatChart.vue'

const loading = ref(true)
const msg = ref('')
const range = ref({ from: '', to: '' })

const complaints = ref({ total: 0, pending: 0, resolved: 0, by_status: {}, by_category: {}, avg_resolution_days: null })
const invoices = ref({ total_invoiced: 0, total_collected: 0, total_pending: 0, overdue_amount: 0, collection_rate: 0, by_month: {} })

onMounted(load)

function activeParams() {
  const p = {}
  if (range.value.from) p.from = range.value.from
  if (range.value.to) p.to = range.value.to
  return p
}

async function load() {
  loading.value = true
  msg.value = ''
  try {
    const [c, i] = await Promise.all([
      complaintsAPI.summary(activeParams()),
      invoicesAPI.summary(activeParams()),
    ])
    complaints.value = c.data
    invoices.value = i.data
  } catch (e) { msg.value = errText(e) }
  loading.value = false
}

function applyThisMonth() {
  const now = new Date()
  const pad = n => String(n).padStart(2, '0')
  range.value.from = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-01`
  range.value.to = today()
  load()
}

function clearRange() {
  range.value = { from: '', to: '' }
  load()
}

const STATUS_LABELS = { OPEN: 'Open', ASSIGNED: 'Assigned', IN_PROGRESS: 'In Progress', COMPLETED: 'Completed', CLOSED: 'Closed' }
const complaintsByStatusChart = computed(() =>
  Object.entries(complaints.value.by_status || {}).map(([label, value]) => ({ label: STATUS_LABELS[label] || label, value }))
)
const complaintsByCategoryChart = computed(() =>
  Object.entries(complaints.value.by_category || {}).map(([label, value]) => ({ label, value }))
)
const paymentSplitChart = computed(() => [
  { label: 'Collected', value: invoices.value.total_collected || 0, color: '#0E7C7B' },
  { label: 'Pending', value: invoices.value.total_pending || 0, color: '#dc2626' },
])
const monthlyCollectionChart = computed(() =>
  Object.entries(invoices.value.by_month || {})
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([label, v]) => ({ label, value: Math.round(v.invoiced || 0) }))
)

async function exportCsv(kind) {
  msg.value = ''
  const api = { complaints: complaintsAPI, invoices: invoicesAPI, expenses: expensesAPI }[kind]
  try {
    const res = await api.export(activeParams())
    downloadBlob(res.data, `${kind}.csv`)
  } catch (e) { msg.value = await errTextFromBlob(e) }
}

function printReport() { window.print() }
</script>
