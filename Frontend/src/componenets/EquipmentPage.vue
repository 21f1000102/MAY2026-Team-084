<template>
  <div>
    <div v-if="msg && !showAdd && !showService" class="alert-custom alert-error">{{ msg }}</div>

    <!-- Forecast Banner -->
    <div v-if="forecast" class="card mb-4 p-4" style="background:linear-gradient(135deg,#1B2A4A,#2d4270);color:#fff;">
      <div class="d-flex justify-content-between align-items-center flex-wrap gap-3">
        <div>
          <h6 class="mb-1" style="color:#F2A541;">⚡ 30-Day Maintenance Forecast</h6>
          <p class="mb-0">{{ forecast.count }} equipment due for service</p>
        </div>
        <div style="text-align:right;">
          <div style="font-size:1.6rem;font-weight:700;">₹{{ forecast.total_estimated_cost }}</div>
          <small style="color:rgba(255,255,255,0.7);">Estimated Cost</small>
        </div>
      </div>
      <div v-if="forecast.due_in_30_days.length > 0" class="mt-3 d-flex gap-2 flex-wrap">
        <div v-for="item in forecast.due_in_30_days" :key="item.id"
          style="background:rgba(255,255,255,0.1);border-radius:8px;padding:8px 14px;font-size:0.8rem;">
          <span class="badge-custom" :class="badgeClass(item.risk_level)">{{ item.risk_level }}</span>
          <span class="ms-2">{{ item.name }} — {{ item.days_until_due }}d left</span>
        </div>
      </div>
    </div>

    <div class="d-flex justify-content-end mb-3">
      <button class="btn-primary-custom" @click="openAdd"><i class="fas fa-plus me-2"></i>Add Equipment</button>
    </div>

    <div v-if="loading" class="spinner"></div>
    <div v-else class="row g-3">
      <div v-if="equipment.length===0" class="col-12"><div class="empty-state card p-4"><i class="fas fa-cog"></i><p>No equipment added</p></div></div>
      <div v-for="eq in equipment" :key="eq.id" class="col-md-6">
        <div class="card p-4">
          <div class="d-flex justify-content-between align-items-start mb-3">
            <div>
              <span class="badge-custom mb-2 d-inline-block" :class="badgeClass(eq.risk_level)">{{ eq.risk_level }} RISK</span>
              <h6 class="fw-bold mb-1">{{ eq.name }}</h6>
              <small class="text-muted">{{ eq.category }}</small>
            </div>
            <button @click="deleteEq(eq.id)" class="btn btn-sm btn-outline-danger"><i class="fas fa-trash"></i></button>
          </div>

          <!-- Progress bar -->
          <div class="mb-3">
            <div class="d-flex justify-content-between mb-1" style="font-size:0.8rem;">
              <span class="text-muted">Service progress</span>
              <span>{{ eq.days_until_due }} days left</span>
            </div>
            <div class="progress-bar-custom">
              <div class="progress-fill" :style="`width:${serviceProgress(eq)}%;background:${riskColor(eq.risk_level)};`"></div>
            </div>
          </div>

          <div class="d-flex justify-content-between" style="font-size:0.85rem;">
            <span class="text-muted">Last serviced: {{ eq.last_serviced_date }}</span>
            <span class="text-muted">Est. cost: ₹{{ eq.estimated_service_cost || 'N/A' }}</span>
          </div>

          <button @click="openService(eq)" class="btn-primary-custom mt-3 w-100">
            <i class="fas fa-wrench me-2"></i>Mark Serviced Today
          </button>
        </div>
      </div>
    </div>

    <!-- Add Equipment Modal -->
    <div class="modal-overlay" v-if="showAdd" @click.self="closeAdd">
      <div class="modal-box">
        <div class="modal-header">
          <h6 class="mb-0 fw-bold">Add Equipment</h6>
          <button @click="closeAdd" class="btn btn-sm btn-light"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div v-if="msg" class="alert-custom alert-error">{{ msg }}</div>
          <div class="form-group"><label class="form-label">Name *</label><input v-model="form.name" class="form-control-custom" placeholder="e.g. Diesel Generator"/></div>
          <div class="form-group"><label class="form-label">Category *</label>
            <select v-model="form.category" class="form-control-custom">
              <option>GENERATOR</option><option>WATER_TANK</option><option>LIFT</option><option>PEST_CONTROL</option><option>FIRE_SAFETY</option><option>OTHER</option>
            </select>
          </div>
          <div class="form-group"><label class="form-label">Last Serviced Date *</label><input v-model="form.last_serviced_date" type="date" class="form-control-custom"/></div>
          <div class="form-group"><label class="form-label">Service Frequency (days) *</label><input v-model="form.service_frequency_days" type="number" min="1" step="1" class="form-control-custom" placeholder="90"/></div>
          <div class="form-group"><label class="form-label">Estimated Service Cost (₹)</label><input v-model="form.estimated_service_cost" type="number" min="0" class="form-control-custom"/></div>
        </div>
        <div class="modal-footer">
          <button @click="closeAdd" class="btn btn-light">Cancel</button>
          <button @click="addEq" class="btn-primary-custom" :disabled="saving">
            <span v-if="saving"><i class="fas fa-spinner fa-spin me-1"></i></span>Add
          </button>
        </div>
      </div>
    </div>

    <!-- Mark Serviced Modal -->
    <div class="modal-overlay" v-if="showService" @click.self="closeService">
      <div class="modal-box">
        <div class="modal-header">
          <h6 class="mb-0 fw-bold">Mark Serviced — {{ selectedEq?.name }}</h6>
          <button @click="closeService" class="btn btn-sm btn-light"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div v-if="msg" class="alert-custom alert-error">{{ msg }}</div>
          <div class="form-group"><label class="form-label">Vendor Name</label><input v-model="serviceForm.vendor_name" class="form-control-custom"/></div>
          <div class="form-group"><label class="form-label">Cost (₹)</label><input v-model="serviceForm.cost" type="number" min="0" class="form-control-custom"/></div>
          <div class="form-group"><label class="form-label">Notes</label><textarea v-model="serviceForm.notes" class="form-control-custom" rows="2"></textarea></div>
        </div>
        <div class="modal-footer">
          <button @click="closeService" class="btn btn-light">Cancel</button>
          <button @click="doService" class="btn-primary-custom" :disabled="saving">Confirm Serviced</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { equipmentAPI, errText } from '../api/index'
import { badgeClass, orNull, today } from '../utils/format'

const emptyForm = () => ({ name:'', category:'GENERATOR', last_serviced_date: today(), service_frequency_days:90, estimated_service_cost:'' })
const emptyServiceForm = () => ({ vendor_name:'', cost:'', notes:'' })

const equipment = ref([])
const forecast = ref(null)
const loading = ref(true)
const saving = ref(false)
const showAdd = ref(false)
const showService = ref(false)
const selectedEq = ref(null)
const msg = ref('')
const form = ref(emptyForm())
const serviceForm = ref(emptyServiceForm())

onMounted(async () => {
  try {
    const [eq, fc] = await Promise.all([equipmentAPI.getAll(), equipmentAPI.forecast()])
    equipment.value = eq.data
    forecast.value = fc.data
  } catch(e) { msg.value = errText(e) }
  loading.value = false
})

async function loadForecast() {
  try {
    forecast.value = (await equipmentAPI.forecast()).data
  } catch(e) { msg.value = errText(e) }
}

function serviceProgress(eq) {
  const freq = Number(eq.service_frequency_days)
  // A legacy row with 0/NULL frequency would produce Infinity/NaN here.
  if (!Number.isFinite(freq) || freq <= 0) return 100
  const used = freq - Number(eq.days_until_due || 0)
  return Math.max(0, Math.min(Math.round((used / freq) * 100), 100))
}

function riskColor(risk) {
  return { HIGH:'#dc2626', MEDIUM:'#d97706', LOW:'#0E7C7B' }[risk] || '#0E7C7B'
}

function openAdd() { msg.value = ''; showAdd.value = true }
function closeAdd() { msg.value = ''; showAdd.value = false }
function openService(eq) {
  msg.value = ''
  serviceForm.value = emptyServiceForm()
  selectedEq.value = eq
  showService.value = true
}
function closeService() { msg.value = ''; showService.value = false }

/** '' -> null (typed column), otherwise a Number. Returns undefined if invalid. */
function optionalNumber(raw) {
  const v = orNull(raw)
  if (v === null) return null
  const n = Number(v)
  return Number.isFinite(n) && n >= 0 ? n : undefined
}

async function addEq() {
  if (saving.value) return
  msg.value = ''

  const name = String(form.value.name || '').trim()
  if (!name) { msg.value = 'Name is required.'; return }

  // 0 used to be accepted and then divided by on every read of the page.
  const freq = Number(form.value.service_frequency_days)
  if (!Number.isInteger(freq) || freq < 1) {
    msg.value = 'Service frequency must be a whole number of at least 1 day.'
    return
  }

  const cost = optionalNumber(form.value.estimated_service_cost)
  if (cost === undefined) { msg.value = 'Estimated service cost must be a number of 0 or more.'; return }

  saving.value = true
  try {
    const res = await equipmentAPI.add({
      name,
      category: form.value.category,
      last_serviced_date: orNull(form.value.last_serviced_date) || today(),
      service_frequency_days: freq,
      estimated_service_cost: cost
    })
    equipment.value.push(res.data)
    form.value = emptyForm()
    showAdd.value = false
  } catch(e) {
    msg.value = errText(e)
    saving.value = false
    return
  }
  await loadForecast()
  saving.value = false
}

async function doService() {
  if (saving.value || !selectedEq.value) return
  msg.value = ''

  const cost = optionalNumber(serviceForm.value.cost)
  if (cost === undefined) { msg.value = 'Cost must be a number of 0 or more.'; return }

  saving.value = true
  try {
    const res = await equipmentAPI.markServiced(selectedEq.value.id, {
      vendor_name: orNull(serviceForm.value.vendor_name),
      cost,
      notes: orNull(serviceForm.value.notes)
    })
    const idx = equipment.value.findIndex(e => e.id === selectedEq.value.id)
    if (idx > -1) equipment.value[idx] = res.data.equipment
    serviceForm.value = emptyServiceForm()
    showService.value = false
  } catch(e) {
    msg.value = errText(e)
    saving.value = false
    return
  }
  await loadForecast()
  saving.value = false
}

async function deleteEq(id) {
  if (!confirm('Delete this equipment?')) return
  msg.value = ''
  try {
    await equipmentAPI.delete(id)
    equipment.value = equipment.value.filter(e => e.id !== id)
  } catch(e) { msg.value = errText(e); return }
  await loadForecast()
}
</script>
