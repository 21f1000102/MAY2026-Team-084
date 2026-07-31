<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
      <select v-model="filterStatus" class="form-control-custom" style="width:160px;">
        <option value="">All Status</option>
        <option>PAID</option><option>UNPAID</option><option>OVERDUE</option>
      </select>
      <div class="d-flex gap-2" v-if="isAdmin">
        <button class="btn-accent" @click="showBulk=true"><i class="fas fa-bolt me-2"></i>Bulk Generate</button>
        <button class="btn-primary-custom" @click="showAdd=true"><i class="fas fa-plus me-2"></i>Single Invoice</button>
      </div>
    </div>

    <div v-if="loading" class="spinner"></div>
    <div v-else>
      <div v-if="filtered.length===0" class="empty-state card p-4"><i class="fas fa-file-invoice"></i><p>No invoices found</p></div>
      <div v-for="inv in filtered" :key="inv.id" class="card mb-3 p-4">
        <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
          <div>
            <div class="d-flex gap-2 mb-1">
              <span class="badge-custom" :class="`badge-${inv.status.toLowerCase()}`">{{ inv.status }}</span>
            </div>
            <h6 class="fw-bold mb-1">🏠 {{ inv.flat_number }}</h6>
            <small class="text-muted">{{ inv.month }}/{{ inv.year }} · Due: {{ inv.due_date }}</small>
            <div v-if="inv.status==='PAID'" class="mt-1">
              <small class="text-success"><i class="fas fa-check-circle me-1"></i>Paid</small>
            </div>
          </div>
          <div class="d-flex align-items-center gap-3">
            <span style="font-size:1.4rem;font-weight:700;color:#1B2A4A;">₹{{ inv.amount }}</span>
            <div class="d-flex gap-2">
              <button v-if="inv.status==='PAID'" class="btn btn-sm btn-outline-success" @click="viewReceipt(inv)">
                <i class="fas fa-receipt me-1"></i>Receipt
              </button>
              <template v-if="isAdmin && inv.status!=='PAID'">
                <button class="btn btn-sm btn-success" @click="markPaid(inv.id,'UPI')">UPI Paid</button>
                <button class="btn btn-sm btn-outline-secondary" @click="markPaid(inv.id,'CASH')">Cash</button>
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Bulk Generate Modal -->
    <div class="modal-overlay" v-if="showBulk" @click.self="showBulk=false">
      <div class="modal-box">
        <div class="modal-header">
          <h6 class="mb-0 fw-bold">⚡ Bulk Generate Invoices</h6>
          <button @click="showBulk=false" class="btn btn-sm btn-light"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div v-if="bulkMsg" class="alert-custom" :class="bulkMsg.type==='error'?'alert-error':'alert-success'">{{ bulkMsg.text }}</div>
          <p class="text-muted mb-3">Generate invoices for ALL flats at once.</p>
          <div class="form-group"><label class="form-label">Month *</label>
            <select v-model="bulkForm.month" class="form-control-custom">
              <option v-for="i in 12" :key="i" :value="i">{{ i }}</option>
            </select>
          </div>
          <div class="form-group"><label class="form-label">Year *</label>
            <input v-model="bulkForm.year" type="number" class="form-control-custom"/>
          </div>
          <div class="form-group"><label class="form-label">Amount (₹) *</label>
            <input v-model="bulkForm.amount" type="number" class="form-control-custom" placeholder="1500"/>
          </div>
          <div class="form-group"><label class="form-label">Due Date</label>
            <input v-model="bulkForm.due_date" type="date" class="form-control-custom"/>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showBulk=false" class="btn btn-light">Cancel</button>
          <button @click="doBulk" class="btn-accent" :disabled="saving">
            <span v-if="saving"><i class="fas fa-spinner fa-spin me-1"></i></span>Generate All
          </button>
        </div>
      </div>
    </div>

    <!-- Single Invoice Modal -->
    <div class="modal-overlay" v-if="showAdd" @click.self="showAdd=false">
      <div class="modal-box">
        <div class="modal-header">
          <h6 class="mb-0 fw-bold">Generate Invoice</h6>
          <button @click="showAdd=false" class="btn btn-sm btn-light"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div class="form-group"><label class="form-label">Apartment</label>
            <select v-model="addForm.apartment_id" class="form-control-custom">
              <option value="">Select Flat</option>
              <option v-for="a in apartments" :key="a.id" :value="a.id">{{ a.flat_number }}</option>
            </select>
          </div>
          <div class="form-group"><label class="form-label">Month</label><input v-model="addForm.month" type="number" class="form-control-custom"/></div>
          <div class="form-group"><label class="form-label">Year</label><input v-model="addForm.year" type="number" class="form-control-custom"/></div>
          <div class="form-group"><label class="form-label">Amount (₹)</label><input v-model="addForm.amount" type="number" class="form-control-custom"/></div>
          <div class="form-group"><label class="form-label">Due Date</label><input v-model="addForm.due_date" type="date" class="form-control-custom"/></div>
        </div>
        <div class="modal-footer">
          <button @click="showAdd=false" class="btn btn-light">Cancel</button>
          <button @click="doAdd" class="btn-primary-custom" :disabled="saving">Generate</button>
        </div>
      </div>
    </div>

    <!-- Receipt Modal -->
    <div class="modal-overlay" v-if="receipt" @click.self="receipt=null">
      <div class="modal-box">
        <div class="modal-header">
          <h6 class="mb-0 fw-bold">🧾 Payment Receipt</h6>
          <button @click="receipt=null" class="btn btn-sm btn-light"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div class="text-center mb-3">
            <div style="width:60px;height:60px;background:#d1fae5;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 12px;">
              <i class="fas fa-check" style="color:#065f46;font-size:1.4rem;"></i>
            </div>
            <h6 style="color:#065f46;">Payment Confirmed</h6>
          </div>
          <div style="background:#f8fafc;border-radius:10px;padding:16px;" class="text-sm">
            <div class="d-flex justify-content-between py-1 border-bottom"><span class="text-muted">Receipt No.</span><strong>{{ receipt.receipt_number }}</strong></div>
            <div class="d-flex justify-content-between py-1 border-bottom"><span class="text-muted">Flat</span><span>{{ receipt.flat_number }}</span></div>
            <div class="d-flex justify-content-between py-1 border-bottom"><span class="text-muted">Period</span><span>{{ receipt.month }}/{{ receipt.year }}</span></div>
            <div class="d-flex justify-content-between py-1 border-bottom"><span class="text-muted">Amount</span><strong style="color:#065f46;">₹{{ receipt.amount }}</strong></div>
            <div class="d-flex justify-content-between py-1 border-bottom"><span class="text-muted">Mode</span><span>{{ receipt.payment_method }}</span></div>
            <div class="d-flex justify-content-between py-1"><span class="text-muted">Date</span><span>{{ receipt.payment_date?.slice(0,10) }}</span></div>
          </div>
          <p class="text-center text-muted mt-3" style="font-size:0.8rem;">SocietyEase · Apartment Association</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { invoicesAPI, membersAPI } from '../api/index'
import { authStore } from '../store/auth'

const invoices = ref([])
const apartments = ref([])
const loading = ref(true)
const saving = ref(false)
const showBulk = ref(false)
const showAdd = ref(false)
const receipt = ref(null)
const bulkMsg = ref(null)
const filterStatus = ref('')
const isAdmin = authStore.isAdmin
const now = new Date()
const bulkForm = ref({ month: now.getMonth()+1, year: now.getFullYear(), amount: 1500, due_date:'' })
const addForm = ref({ apartment_id:'', month: now.getMonth()+1, year: now.getFullYear(), amount: 1500, due_date:'' })

const filtered = computed(() =>
  invoices.value.filter(i => !filterStatus.value || i.status === filterStatus.value)
)

onMounted(async () => {
  try {
    const [inv, apt] = await Promise.all([invoicesAPI.getAll(), membersAPI.getApartments()])
    invoices.value = inv.data
    apartments.value = apt.data
  } catch(e) {}
  loading.value = false
})

async function doBulk() {
  saving.value = true; bulkMsg.value = null
  try {
    const res = await invoicesAPI.bulkGenerate(bulkForm.value)
    bulkMsg.value = { type:'success', text: res.data.message }
    const fresh = await invoicesAPI.getAll()
    invoices.value = fresh.data
    setTimeout(() => { showBulk.value = false; bulkMsg.value = null }, 2000)
  } catch(e) {
    bulkMsg.value = { type:'error', text: e.response?.data?.error || 'Failed' }
  }
  saving.value = false
}

async function doAdd() {
  saving.value = true
  try {
    const res = await invoicesAPI.create(addForm.value)
    invoices.value.unshift(res.data)
    showAdd.value = false
  } catch(e) {}
  saving.value = false
}

async function markPaid(id, mode) {
  try {
    const res = await invoicesAPI.markPaid(id, { payment_method: mode })
    const idx = invoices.value.findIndex(i => i.id === id)
    if (idx > -1) invoices.value[idx] = res.data.invoice
    receipt.value = res.data.receipt
  } catch(e) {}
}

async function viewReceipt(inv) {
  try {
    const res = await invoicesAPI.getReceipt(inv.id)
    receipt.value = res.data
  } catch(e) {}
}
</script>
