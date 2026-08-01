<template>
  <div>
    <div v-if="msg" class="alert-custom alert-error">{{ msg }}</div>

    <!-- Summary -->
    <div class="row g-3 mb-4">
      <div class="col-12 col-sm-4">
        <div class="stat-card">
          <div class="stat-icon" style="background:#0E7C7B;"><i class="fas fa-check"></i></div>
          <div><div class="stat-value">{{ available }}</div><div class="stat-label">Available</div></div>
        </div>
      </div>
      <div class="col-12 col-sm-4">
        <div class="stat-card">
          <div class="stat-icon" style="background:#dc2626;"><i class="fas fa-car"></i></div>
          <div><div class="stat-value">{{ occupied }}</div><div class="stat-label">Occupied</div></div>
        </div>
      </div>
      <div class="col-12 col-sm-4">
        <div class="stat-card">
          <div class="stat-icon" style="background:#d97706;"><i class="fas fa-clock"></i></div>
          <div><div class="stat-value">{{ reserved }}</div><div class="stat-label">Reserved</div></div>
        </div>
      </div>
    </div>

    <div class="d-flex justify-content-end mb-3 gap-2">
      <button v-if="isAdmin" class="btn-primary-custom" @click="openAdd"><i class="fas fa-plus me-2"></i>Add Slot</button>
    </div>

    <div v-if="loading" class="spinner"></div>
    <div v-else>
      <div v-if="slots.length===0" class="empty-state card p-4"><i class="fas fa-parking"></i><p>No parking slots defined</p></div>
      <div class="row g-3">
        <div v-for="s in slots" :key="s.id" class="col-6 col-md-4 col-lg-3">
          <div class="card p-3 text-center" :style="`border-top:4px solid ${slotColor(s.status)};`">
            <div style="font-size:1.8rem;font-weight:700;color:#1B2A4A;">{{ s.slot_number }}</div>
            <span class="badge-custom mt-1 d-inline-block" :class="badgeClass(s.status)">{{ label(s.status) }}</span>
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
    <div class="modal-overlay" v-if="showAdd" @click.self="closeAdd">
      <div class="modal-box">
        <div class="modal-header">
          <h6 class="mb-0 fw-bold">Add Parking Slot</h6>
          <button @click="closeAdd" class="btn btn-sm btn-light"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div v-if="msg" class="alert-custom alert-error">{{ msg }}</div>
          <div class="form-group"><label class="form-label">Slot Number *</label><input v-model="form.slot_number" class="form-control-custom" placeholder="e.g. P1, P2"/></div>
        </div>
        <div class="modal-footer">
          <button @click="closeAdd" class="btn btn-light">Cancel</button>
          <button @click="addSlot" class="btn-primary-custom" :disabled="saving">
            <span v-if="saving"><i class="fas fa-spinner fa-spin me-1"></i></span>Add Slot
          </button>
        </div>
      </div>
    </div>

    <!-- Reserve Modal -->
    <div class="modal-overlay" v-if="showReserve" @click.self="closeReserve">
      <div class="modal-box">
        <div class="modal-header">
          <h6 class="mb-0 fw-bold">Reserve Slot {{ selectedSlot?.slot_number }}</h6>
          <button @click="closeReserve" class="btn btn-sm btn-light"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div v-if="msg" class="alert-custom alert-error">{{ msg }}</div>
          <div class="form-group"><label class="form-label">Visitor Name</label><input v-model="reserveForm.visitor_name" class="form-control-custom"/></div>
          <div class="form-group"><label class="form-label">Vehicle Number</label><input v-model="reserveForm.visitor_vehicle_number" class="form-control-custom" placeholder="MH12AB1234"/></div>
          <div class="form-group"><label class="form-label">Expected Arrival</label><input v-model="reserveForm.expected_arrival_time" type="datetime-local" class="form-control-custom"/></div>
        </div>
        <div class="modal-footer">
          <button @click="closeReserve" class="btn btn-light">Cancel</button>
          <button @click="doReserve" class="btn-primary-custom" :disabled="saving">
            <span v-if="saving"><i class="fas fa-spinner fa-spin me-1"></i></span>Reserve
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { parkingAPI, errText } from '../api/index'
import { authStore } from '../store/auth'
import { badgeClass, label, orNull } from '../utils/format'

const slots = ref([])
const loading = ref(true)
const saving = ref(false)
const msg = ref('')
const showAdd = ref(false)
const showReserve = ref(false)
const selectedSlot = ref(null)
const isAdmin = authStore.isAdmin
const blankForm = () => ({ slot_number:'' })
const blankReserve = () => ({ visitor_name:'', visitor_vehicle_number:'', expected_arrival_time:'' })
const form = ref(blankForm())
const reserveForm = ref(blankReserve())

const available = computed(() => slots.value.filter(s => s.status==='AVAILABLE').length)
const occupied = computed(() => slots.value.filter(s => s.status==='OCCUPIED').length)
const reserved = computed(() => slots.value.filter(s => s.status==='RESERVED').length)

onMounted(async () => {
  try {
    const res = await parkingAPI.getAll()
    slots.value = Array.isArray(res.data) ? res.data : []
  } catch(e) { msg.value = errText(e) }
  loading.value = false
})

function slotColor(status) {
  return { AVAILABLE:'#0E7C7B', OCCUPIED:'#dc2626', RESERVED:'#d97706' }[status] || '#718096'
}

function openAdd() {
  form.value = blankForm()
  msg.value = ''
  showAdd.value = true
}

function closeAdd() {
  showAdd.value = false
  msg.value = ''
}

function openReserve(s) {
  selectedSlot.value = s
  // Reset: the form used to keep the previous visitor's details, so the next
  // slot's Reserve dialog opened pre-filled and would submit someone else's data.
  reserveForm.value = blankReserve()
  msg.value = ''
  showReserve.value = true
}

function closeReserve() {
  showReserve.value = false
  msg.value = ''
}

async function addSlot() {
  if (saving.value) return
  const slot_number = form.value.slot_number.trim()
  if (!slot_number) { msg.value = 'Slot number is required.'; return }

  saving.value = true
  msg.value = ''
  try {
    const res = await parkingAPI.add({ slot_number })
    slots.value.push(res.data)
    showAdd.value = false
    form.value = blankForm()
  } catch(e) { msg.value = errText(e) }
  saving.value = false
}

async function doReserve() {
  if (saving.value) return
  if (!selectedSlot.value) return

  saving.value = true
  msg.value = ''
  try {
    const res = await parkingAPI.reserve(selectedSlot.value.id, {
      visitor_name: orNull(reserveForm.value.visitor_name),
      visitor_vehicle_number: orNull(reserveForm.value.visitor_vehicle_number),
      // orNull: an empty datetime-local sent as "" failed date parsing server-side.
      expected_arrival_time: orNull(reserveForm.value.expected_arrival_time)
    })
    updateSlot(res.data.slot)
    showReserve.value = false
    reserveForm.value = blankReserve()
    selectedSlot.value = null
  } catch(e) { msg.value = errText(e) }
  saving.value = false
}

async function occupy(id) {
  msg.value = ''
  try {
    const res = await parkingAPI.occupy(id, {})
    updateSlot(res.data.slot)
  } catch(e) { msg.value = errText(e) }
}

async function release(id) {
  // Releasing wipes the visitor details and frees the slot for anyone else.
  if (!confirm('Release this slot? The current reservation details will be cleared.')) return
  msg.value = ''
  try {
    const res = await parkingAPI.release(id)
    updateSlot(res.data.slot)
  } catch(e) { msg.value = errText(e) }
}

async function deleteSlot(id) {
  if (!confirm('Delete this slot? This cannot be undone.')) return
  msg.value = ''
  try {
    await parkingAPI.delete(id)
    slots.value = slots.value.filter(s => s.id !== id)
  } catch(e) { msg.value = errText(e) }
}

function updateSlot(updated) {
  if (!updated?.id) return
  const idx = slots.value.findIndex(s => s.id === updated.id)
  if (idx > -1) slots.value[idx] = updated
}
</script>
