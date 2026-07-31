<template>
  <div>
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
          <span :class="`badge-custom badge-${item.risk_level.toLowerCase()}`">{{ item.risk_level }}</span>
          <span class="ms-2">{{ item.name }} — {{ item.days_until_due }}d left</span>
        </div>
      </div>
    </div>

    <div class="d-flex justify-content-end mb-3">
      <button class="btn-primary-custom" @click="showAdd=true"><i class="fas fa-plus me-2"></i>Add Equipment</button>
    </div>

    <div v-if="loading" class="spinner"></div>
    <div v-else class="row g-3">
      <div v-if="equipment.length===0" class="col-12"><div class="empty-state card p-4"><i class="fas fa-cog"></i><p>No equipment added</p></div></div>
      <div v-for="eq in equipment" :key="eq.id" class="col-md-6">
        <div class="card p-4">
          <div class="d-flex justify-content-between align-items-start mb-3">
            <div>
              <span class="badge-custom mb-2 d-inline-block" :class="`badge-${eq.risk_level.toLowerCase()}`">{{ eq.risk_level }} RISK</span>
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
    <div class="modal-overlay" v-if="showAdd" @click.self="showAdd=false">
      <div class="modal-box">
        <div class="modal-header">
          <h6 class="mb-0 fw-bold">Add Equipment</h6>
          <button @click="showAdd=false" class="btn btn-sm btn-light"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div class="form-group"><label class="form-label">Name *</label><input v-model="form.name" class="form-control-custom" placeholder="e.g. Diesel Generator"/></div>
          <div class="form-group"><label class="form-label">Category *</label>
            <select v-model="form.category" class="form-control-custom">
              <option>GENERATOR</option><option>WATER_TANK</option><option>LIFT</option><option>PEST_CONTROL</option><option>FIRE_SAFETY</option><option>OTHER</option>
            </select>
          </div>
          <div class="form-group"><label class="form-label">Last Serviced Date *</label><input v-model="form.last_serviced_date" type="date" class="form-control-custom"/></div>
          <div class="form-group"><label class="form-label">Service Frequency (days) *</label><input v-model="form.service_frequency_days" type="number" class="form-control-custom" placeholder="90"/></div>
          <div class="form-group"><label class="form-label">Estimated Service Cost (₹)</label><input v-model="form.estimated_service_cost" type="number" class="form-control-custom"/></div>
        </div>
        <div class="modal-footer">
          <button @click="showAdd=false" class="btn btn-light">Cancel</button>
          <button @click="addEq" class="btn-primary-custom" :disabled="saving">
            <span v-if="saving"><i class="fas fa-spinner fa-spin me-1"></i></span>Add
          </button>
        </div>
      </div>
    </div>

    <!-- Mark Serviced Modal -->
    <div class="modal-overlay" v-if="showService" @click.self="showService=false">
      <div class="modal-box">
        <div class="modal-header">
          <h6 class="mb-0 fw-bold">Mark Serviced — {{ selectedEq?.name }}</h6>
          <button @click="showService=false" class="btn btn-sm btn-light"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div class="form-group"><label class="form-label">Vendor Name</label><input v-model="serviceForm.vendor_name" class="form-control-custom"/></div>
          <div class="form-group"><label class="form-label">Cost (₹)</label><input v-model="serviceForm.cost" type="number" class="form-control-custom"/></div>
          <div class="form-group"><label class="form-label">Notes</label><textarea v-model="serviceForm.notes" class="form-control-custom" rows="2"></textarea></div>
        </div>
        <div class="modal-footer">
          <button @click="showService=false" class="btn btn-light">Cancel</button>
          <button @click="doService" class="btn-primary-custom">Confirm Serviced</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { equipmentAPI } from '../api/index'

const equipment = ref([])
const forecast = ref(null)
const loading = ref(true)
const saving = ref(false)
const showAdd = ref(false)
const showService = ref(false)
const selectedEq = ref(null)
const form = ref({ name:'', category:'GENERATOR', last_serviced_date:'', service_frequency_days:90, estimated_service_cost:'' })
const serviceForm = ref({ vendor_name:'', cost:'', notes:'' })

onMounted(async () => {
  try {
    const [eq, fc] = await Promise.all([equipmentAPI.getAll(), equipmentAPI.forecast()])
    equipment.value = eq.data
    forecast.value = fc.data
  } catch(e) {}
  loading.value = false
})

function serviceProgress(eq) {
  const used = eq.service_frequency_days - eq.days_until_due
  return Math.min(Math.round((used / eq.service_frequency_days) * 100), 100)
}

function riskColor(risk) {
  return { HIGH:'#dc2626', MEDIUM:'#d97706', LOW:'#0E7C7B' }[risk] || '#0E7C7B'
}

function openService(eq) { selectedEq.value = eq; showService.value = true }

async function addEq() {
  saving.value = true
  try {
    const res = await equipmentAPI.add(form.value)
    equipment.value.push(res.data)
    showAdd.value = false
    const fc = await equipmentAPI.forecast()
    forecast.value = fc.data
  } catch(e) {}
  saving.value = false
}

async function doService() {
  try {
    const res = await equipmentAPI.markServiced(selectedEq.value.id, serviceForm.value)
    const idx = equipment.value.findIndex(e => e.id === selectedEq.value.id)
    if (idx > -1) equipment.value[idx] = res.data.equipment
    showService.value = false
    const fc = await equipmentAPI.forecast()
    forecast.value = fc.data
  } catch(e) {}
}

async function deleteEq(id) {
  if (!confirm('Delete this equipment?')) return
  try {
    await equipmentAPI.delete(id)
    equipment.value = equipment.value.filter(e => e.id !== id)
  } catch(e) {}
}
</script>
