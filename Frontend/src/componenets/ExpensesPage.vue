<template>
  <div>
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

    <div class="d-flex justify-content-end mb-3">
      <button class="btn-primary-custom" @click="showAdd=true"><i class="fas fa-plus me-2"></i>Log Expense</button>
    </div>

    <div v-if="loading" class="spinner"></div>
    <div v-else class="card">
      <div v-if="expenses.length===0" class="empty-state p-4"><i class="fas fa-receipt"></i><p>No expenses logged</p></div>
      <table v-else class="table-custom">
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

    <!-- Add Expense Modal -->
    <div class="modal-overlay" v-if="showAdd" @click.self="showAdd=false">
      <div class="modal-box">
        <div class="modal-header">
          <h6 class="mb-0 fw-bold">Log Expense</h6>
          <button @click="showAdd=false" class="btn btn-sm btn-light"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div class="form-group"><label class="form-label">Category *</label>
            <select v-model="form.category" class="form-control-custom">
              <option>SALARY</option><option>MAINTENANCE</option><option>UTILITIES</option><option>CONSUMABLES</option><option>MISCELLANEOUS</option>
            </select>
          </div>
          <div class="form-group"><label class="form-label">Description *</label><input v-model="form.description" class="form-control-custom" placeholder="e.g. Watchman salary June"/></div>
          <div class="form-group"><label class="form-label">Amount (₹) *</label><input v-model="form.amount" type="number" class="form-control-custom"/></div>
          <div class="form-group"><label class="form-label">Date *</label><input v-model="form.expense_date" type="date" class="form-control-custom"/></div>
        </div>
        <div class="modal-footer">
          <button @click="showAdd=false" class="btn btn-light">Cancel</button>
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
import { expensesAPI } from '../api/index'

const expenses = ref([])
const summary = ref(null)
const loading = ref(true)
const saving = ref(false)
const showAdd = ref(false)
const form = ref({ category:'MAINTENANCE', description:'', amount:'', expense_date:'' })

onMounted(async () => {
  try {
    const now = new Date()
    const [e, s] = await Promise.all([
      expensesAPI.getAll(),
      expensesAPI.summary(now.getMonth() + 1, now.getFullYear())
    ])
    expenses.value = e.data
    summary.value = s.data
  } catch(e) {}
  loading.value = false
})

async function addExpense() {
  saving.value = true
  try {
    const res = await expensesAPI.add(form.value)
    expenses.value.unshift(res.data)
    showAdd.value = false
    form.value = { category:'MAINTENANCE', description:'', amount:'', expense_date:'' }
    const now2 = new Date()
    const s = await expensesAPI.summary(now2.getMonth() + 1, now2.getFullYear())
    summary.value = s.data
  } catch(e) {}
  saving.value = false
}

async function deleteExp(id) {
  if (!confirm('Delete this expense?')) return
  try {
    await expensesAPI.delete(id)
    expenses.value = expenses.value.filter(e => e.id !== id)
  } catch(e) {}
}
</script>
