<template>
  <div>
    <!-- Summary -->
    <div class="row g-3 mb-4">
      <div class="col-4">
        <div class="stat-card">
          <div class="stat-icon" style="background:#0E7C7B;"><i class="fas fa-check"></i></div>
          <div><div class="stat-value">{{ available }}</div><div class="stat-label">Available</div></div>
        </div>
      </div>
      <div class="col-4">
        <div class="stat-card">
          <div class="stat-icon" style="background:#dc2626;"><i class="fas fa-car"></i></div>
          <div><div class="stat-value">{{ occupied }}</div><div class="stat-label">Occupied</div></div>
        </div>
      </div>
      <div class="col-4">
        <div class="stat-card">
          <div class="stat-icon" style="background:#d97706;"><i class="fas fa-clock"></i></div>
          <div><div class="stat-value">{{ reserved }}</div><div class="stat-label">Reserved</div></div>
        </div>
      </div>
    </div>

    <div class="d-flex justify-content-end mb-3 gap-2">
      <button v-if="isAdmin" class="btn-primary-custom" @click="showAdd=true"><i class="fas fa-plus me-2"></i>Add Slot</button>
    </div>

    <div v-if="loading" class="spinner"></div>
    <div v-else>
      <div v-if="slots.length===0" class="empty-state card p-4"><i class="fas fa-parking"></i><p>No parking slots defined</p></div>
      <div class="row g-3">
        <div v-for="s in slots" :key="s.id" class="col-6 col-md-4 col-lg-3">
          <div class="card p-3 text-center" :style="`border-top:4px solid ${slotColor(s.status)};`">
            <div style="font-size:1.8rem;font-weight:700;color:#1B2A4A;">{{ s.slot_number }}</div>
            <span class="badge-custom mt-1 d-inline-block" :class="`badge-${s.status.toLowerCase()}`">{{ s.status }}</span>
            <div v-if="s.visitor_name" class="mt-2" style="font-size:0.8rem;color:#718096;">👤 {{ s.visitor_name }}</div>
            <div v-if="s.flat_number" style="font-size:0.8rem;color:#718096;">🏠 {{ s.flat_number }}</div>
            <div class="mt-3 d-flex gap-1 justify-content-center flex-wrap">
              <button v-if="s.status==='AVAILABLE'" @click="openReserve(s)" class="btn btn-sm btn-outline-primary">Reserve</button>
              <button v-if="s.status==='RESERVED' && isAdmin" @click="occupy(s.id)" class="btn btn-sm btn-warning">Mark In</button>
              <button v-if="s.status!=='AVAILABLE'" @click="release(s.id)" class="btn btn-sm btn-outline-success">Release</button>
              <button v-if="isAdmin" @click="deleteSlot(s.id)" class="btn btn-sm btn-outline-danger"><i class="fas fa-trash"></i></button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Add Slot Modal -->
    <div class="modal-overlay" v-if="showAdd" @click.self="showAdd=false">
      <div class="modal-box">
        <div class="modal-header">
          <h6 class="mb-0 fw-bold">Add Parking Slot</h6>
          <button @click="showAdd=false" class="btn btn-sm btn-light"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div class="form-group"><label class="form-label">Slot Number *</label><input v-model="form.slot_number" class="form-control-custom" placeholder="e.g. P1, P2"/></div>
        </div>
        <div class="modal-footer">
          <button @click="showAdd=false" class="btn btn-light">Cancel</button>
          <button @click="addSlot" class="btn-primary-custom">Add Slot</button>
        </div>
      </div>
    </div>

    <!-- Reserve Modal -->
    <div class="modal-overlay" v-if="showReserve" @click.self="showReserve=false">
      <div class="modal-box">
        <div class="modal-header">
          <h6 class="mb-0 fw-bold">Reserve Slot {{ selectedSlot?.slot_number }}</h6>
          <button @click="showReserve=false" class="btn btn-sm btn-light"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div class="form-group"><label class="form-label">Visitor Name</label><input v-model="reserveForm.visitor_name" class="form-control-custom"/></div>
          <div class="form-group"><label class="form-label">Vehicle Number</label><input v-model="reserveForm.visitor_vehicle_number" class="form-control-custom" placeholder="MH12AB1234"/></div>
          <div class="form-group"><label class="form-label">Expected Arrival</label><input v-model="reserveForm.expected_arrival_time" type="datetime-local" class="form-control-custom"/></div>
        </div>
        <div class="modal-footer">
          <button @click="showReserve=false" class="btn btn-light">Cancel</button>
          <button @click="doReserve" class="btn-primary-custom">Reserve</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { parkingAPI } from '../api/index'
import { authStore } from '../store/auth'

const slots = ref([])
const loading = ref(true)
const showAdd = ref(false)
const showReserve = ref(false)
const selectedSlot = ref(null)
const isAdmin = authStore.isAdmin
const form = ref({ slot_number:'' })
const reserveForm = ref({ visitor_name:'', visitor_vehicle_number:'', expected_arrival_time:'' })

const available = computed(() => slots.value.filter(s => s.status==='AVAILABLE').length)
const occupied = computed(() => slots.value.filter(s => s.status==='OCCUPIED').length)
const reserved = computed(() => slots.value.filter(s => s.status==='RESERVED').length)

onMounted(async () => {
  try { slots.value = (await parkingAPI.getAll()).data } catch(e) {}
  loading.value = false
})

function slotColor(status) {
  return { AVAILABLE:'#0E7C7B', OCCUPIED:'#dc2626', RESERVED:'#d97706' }[status] || '#718096'
}

function openReserve(s) { selectedSlot.value = s; showReserve.value = true }

async function addSlot() {
  try {
    const res = await parkingAPI.add(form.value)
    slots.value.push(res.data)
    showAdd.value = false
    form.value = { slot_number:'' }
  } catch(e) {}
}

async function doReserve() {
  try {
    const res = await parkingAPI.reserve(selectedSlot.value.id, reserveForm.value)
    updateSlot(res.data.slot)
    showReserve.value = false
  } catch(e) { alert(e.response?.data?.error || 'Failed') }
}

async function occupy(id) {
  try {
    const res = await parkingAPI.occupy(id, {})
    updateSlot(res.data.slot)
  } catch(e) {}
}

async function release(id) {
  try {
    const res = await parkingAPI.release(id)
    updateSlot(res.data.slot)
  } catch(e) {}
}

async function deleteSlot(id) {
  if (!confirm('Delete this slot?')) return
  try {
    await parkingAPI.delete(id)
    slots.value = slots.value.filter(s => s.id !== id)
  } catch(e) {}
}

function updateSlot(updated) {
  const idx = slots.value.findIndex(s => s.id === updated.id)
  if (idx > -1) slots.value[idx] = updated
}
</script>
