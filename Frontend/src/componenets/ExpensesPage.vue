<template>
  <div>
    <div v-if="msg && !showAdd" class="alert-custom alert-error">{{ msg }}</div>

    <div class="row g-3 mb-4" v-if="summary">
      <div class="col-md-4">
        <div class="stat-card"><div class="stat-icon" style="background:#0E7C7B;"><i class="fas fa-arrow-down"></i></div>
          <div><div class="stat-value" style="font-size:1.4rem;">₹{{ summary.total_income }}</div><div class="stat-label">Total Income</div></div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="stat-card"><div class="stat-icon" style="background:#dc2626;"><i class="fas fa-arrow-up"></i></div>
          <div><div class="stat-value" style="font-size:1.4rem;">₹{{ summary.total_expense }}</div><div class="stat-label">Total Expenses</div></div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="stat-card"><div class="stat-icon" style="background:#1B2A4A;"><i class="fas fa-wallet"></i></div>
          <div><div class="stat-value" style="font-size:1.4rem;">₹{{ summary.net_balance }}</div><div class="stat-label">Net Balance</div></div>
        </div>
      </div>
    </div>

    <div class="d-flex justify-content-end mb-3 gap-2">
      <button class="btn btn-outline-secondary" @click="exportCsv" :disabled="exporting">
        <i class="fas fa-file-csv me-2"></i>Export CSV
      </button>
      <button class="btn-primary-custom" @click="openAdd"><i class="fas fa-plus me-2"></i>Log Expense</button>
    </div>

    <FilterBar :fields="filterFields" :result-count="loading ? null : expenses.length" @change="onFilterChange" />

    <div v-if="loading" class="spinner"></div>
    <div v-else class="card">
      <div v-if="expenses.length===0" class="empty-state p-4"><i class="fas fa-receipt"></i><p>No expenses logged</p></div>
      <div v-else class="table-responsive">
      <table class="table-custom">
        <thead><tr><th>Date</th><th>Category</th><th>Description</th><th>Amount</th><th>Paid By</th><th>Actions</th></tr></thead>
        <tbody>
          <tr v-for="e in expenses" :key="e.id">
            <td>{{ e.expense_date }}</td>
            <td><span class="badge-custom badge-open">{{ e.category }}</span></td>
            <td>{{ e.description }}</td>
            <td><strong>₹{{ e.amount }}</strong></td>
            <td>{{ e.paid_by_name }}</td>
            <td>
              <button class="btn btn-sm btn-outline-danger" @click="deleteExp(e.id)"><i class="fas fa-trash"></i></button>
            </td>
          </tr>
        </tbody>
      </table>
      </div>
    </div>

    <!-- Add Expense Modal -->
    <div class="modal-overlay" v-if="showAdd" @click.self="closeAdd">
      <div class="modal-box">
        <div class="modal-header">
          <h6 class="mb-0 fw-bold">Log Expense</h6>
          <button @click="closeAdd" class="btn btn-sm btn-light"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div v-if="msg" class="alert-custom alert-error">{{ msg }}</div>
          <div class="form-group"><label class="form-label">Category *</label>
            <select v-model="form.category" class="form-control-custom">
              <option>SALARY</option><option>MAINTENANCE</option><option>UTILITIES</option><option>CONSUMABLES</option><option>MISCELLANEOUS</option>
            </select>
          </div>
          <div class="form-group"><label class="form-label">Description *</label><input v-model="form.description" class="form-control-custom" placeholder="e.g. Watchman salary June"/></div>
          <div class="form-group"><label class="form-label">Amount (₹) *</label><input v-model="form.amount" type="number" min="0" class="form-control-custom"/></div>
          <div class="form-group"><label class="form-label">Date *</label><input v-model="form.expense_date" type="date" class="form-control-custom"/></div>
        </div>
        <div class="modal-footer">
          <button @click="closeAdd" class="btn btn-light">Cancel</button>
          <button @click="addExpense" class="btn-primary-custom" :disabled="saving">
            <span v-if="saving"><i class="fas fa-spinner fa-spin me-1"></i></span>Save
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { expensesAPI, errText, errTextFromBlob, downloadBlob } from '../api/index'
import { orNull, today } from '../utils/format'
import FilterBar from './FilterBar.vue'

const emptyForm = () => ({ category:'MAINTENANCE', description:'', amount:'', expense_date: today() })

const expenses = ref([])
const summary = ref(null)
const loading = ref(true)
const saving = ref(false)
const exporting = ref(false)
const showAdd = ref(false)
const msg = ref('')
const form = ref(emptyForm())
const activeFilters = ref({})

const filterFields = [
  { key: 'q', label: 'Search', placeholder: 'Description or vendor...' },
  { key: 'category', label: 'Category', type: 'select', options: ['SALARY','MAINTENANCE','UTILITIES','CONSUMABLES','MISCELLANEOUS'] },
  { key: 'min_amount', label: 'Min ₹', type: 'number' },
  { key: 'max_amount', label: 'Max ₹', type: 'number' },
]

onMounted(async () => {
  await loadExpenses()
  await loadSummary()
  loading.value = false
})

async function onFilterChange(params) {
  activeFilters.value = params
  await loadExpenses()
}

async function loadExpenses() {
  try {
    expenses.value = (await expensesAPI.getAll(activeFilters.value)).data
  } catch(e) { msg.value = errText(e) }
}

async function exportCsv() {
  exporting.value = true
  msg.value = ''
  try {
    const res = await expensesAPI.export(activeFilters.value)
    downloadBlob(res.data, 'expenses.csv')
  } catch (e) { msg.value = await errTextFromBlob(e) }
  exporting.value = false
}

// The totals cards are derived data — every mutation has to refresh them or
// they keep showing a stale Net Balance.
async function loadSummary() {
  try {
    const now = new Date()
    summary.value = (await expensesAPI.summary(now.getMonth() + 1, now.getFullYear())).data
  } catch(e) { msg.value = errText(e) }
}

function openAdd() { msg.value = ''; showAdd.value = true }
function closeAdd() { msg.value = ''; showAdd.value = false }

async function addExpense() {
  if (saving.value) return
  msg.value = ''

  const description = String(form.value.description || '').trim()
  if (!description) { msg.value = 'Description is required.'; return }

  const amount = Number(form.value.amount)
  if (form.value.amount === '' || !Number.isFinite(amount) || amount < 0) {
    msg.value = 'Amount must be a number of 0 or more.'
    return
  }

  saving.value = true
  try {
    await expensesAPI.add({
      category: form.value.category,
      description,
      amount,
      // expense_date is a NOT NULL date column — never send ''.
      expense_date: orNull(form.value.expense_date) || today()
    })
    await loadExpenses()
    form.value = emptyForm()
    showAdd.value = false
  } catch(e) {
    msg.value = errText(e)
    saving.value = false
    return
  }
  await loadSummary()
  saving.value = false
}

async function deleteExp(id) {
  if (!confirm('Delete this expense?')) return
  msg.value = ''
  try {
    await expensesAPI.delete(id)
    await loadExpenses()
  } catch(e) { msg.value = errText(e); return }
  await loadSummary()
}
</script>
