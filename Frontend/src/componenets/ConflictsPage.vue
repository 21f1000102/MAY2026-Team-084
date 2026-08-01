<template>
  <div>
    <div v-if="msg" class="alert-custom alert-error">{{ msg }}</div>

    <div class="d-flex justify-content-end mb-4">
      <button class="btn-primary-custom" @click="openAdd"><i class="fas fa-plus me-2"></i>Report Concern</button>
    </div>

    <div v-if="loading" class="spinner"></div>
    <div v-else>
      <div v-if="conflicts.length===0" class="empty-state card p-4">
        <i class="fas fa-handshake" style="color:#0E7C7B;"></i>
        <p>No conflicts reported. Great community!</p>
      </div>
      <div v-for="c in conflicts" :key="c.id" class="card mb-3 p-4">
        <div class="d-flex justify-content-between align-items-start mb-2">
          <div>
            <span class="badge-custom me-2" :class="statusClass(c.status)">{{ c.status }}</span>
            <span class="badge-custom badge-low">{{ c.category }}</span>
          </div>
          <small class="text-muted">{{ c.created_at?.slice(0,10) }}</small>
        </div>

        <p class="mb-2"><strong>Concern:</strong> {{ c.description }}</p>
        <p class="mb-2 text-muted" style="font-size:0.85rem;">
          <i class="fas fa-building me-1"></i>Reported about: Flat {{ c.reported_flat }}
          <span v-if="isAdmin && c.reported_by_name"> · Raised by: {{ c.reported_by_name }}</span>
        </p>

        <!-- Response section -->
        <div v-if="c.reported_flat_response" class="p-3 mt-2" style="background:#f0f4f8;border-radius:8px;">
          <small class="fw-bold text-muted">Their Response:</small>
          <p class="mb-0 mt-1" style="font-size:0.875rem;">{{ c.reported_flat_response }}</p>
        </div>

        <div v-if="c.resolution_note" class="p-3 mt-2" style="background:#d1fae5;border-radius:8px;">
          <small class="fw-bold" style="color:#065f46;">Resolution:</small>
          <p class="mb-0 mt-1" style="font-size:0.875rem;color:#065f46;">{{ c.resolution_note }}</p>
        </div>

        <!-- Admin resolve button -->
        <div v-if="isAdmin && c.status !== 'RESOLVED'" class="mt-3 d-flex gap-2">
          <input v-model="resolveNote[c.id]" class="form-control-custom" placeholder="Resolution note..." style="flex:1;"/>
          <button @click="resolve(c.id)" class="btn-primary-custom" :disabled="resolving === c.id">
            <span v-if="resolving === c.id"><i class="fas fa-spinner fa-spin me-1"></i></span>Resolve
          </button>
        </div>
      </div>
    </div>

    <!-- Report Concern Modal -->
    <div class="modal-overlay" v-if="showAdd" @click.self="closeAdd">
      <div class="modal-box">
        <div class="modal-header">
          <h6 class="mb-0 fw-bold">Report a Concern</h6>
          <button @click="closeAdd" class="btn btn-sm btn-light"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div v-if="msg" class="alert-custom alert-error">{{ msg }}</div>
          <div class="alert-custom alert-info mb-3">
            <i class="fas fa-shield-alt me-2"></i>Your identity will be kept anonymous from the reported flat.
          </div>
          <div class="form-group">
            <label class="form-label">Concerned about which flat? *</label>
            <select v-model="form.reported_apartment_id" class="form-control-custom">
              <option value="">Select Flat</option>
              <option v-for="a in apartments" :key="a.id" :value="a.id">{{ a.flat_number }}</option>
            </select>
          </div>
          <div class="form-group"><label class="form-label">Category *</label>
            <select v-model="form.category" class="form-control-custom">
              <option>NOISE</option><option>PARKING</option><option>GARBAGE</option><option>COMMON_AREA_MISUSE</option><option>PETS</option><option>OTHER</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Description *</label>
            <textarea v-model="form.description" class="form-control-custom" rows="3" placeholder="Describe the concern..."></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeAdd" class="btn btn-light">Cancel</button>
          <button @click="raiseConflict" class="btn-primary-custom" :disabled="saving">
            <span v-if="saving"><i class="fas fa-spinner fa-spin me-1"></i></span>Submit
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { conflictsAPI, membersAPI, errText } from '../api/index'
import { authStore } from '../store/auth'

const conflicts = ref([])
const apartments = ref([])
const loading = ref(true)
const saving = ref(false)
const resolving = ref(null)
const msg = ref('')
const showAdd = ref(false)
const resolveNote = ref({})
const isAdmin = authStore.isAdmin
const blankForm = () => ({ reported_apartment_id:'', category:'NOISE', description:'' })
const form = ref(blankForm())

onMounted(async () => {
  const [c, a] = await Promise.allSettled([conflictsAPI.getAll(), membersAPI.getApartments()])
  if (c.status === 'fulfilled' && Array.isArray(c.value.data)) conflicts.value = c.value.data
  if (a.status === 'fulfilled' && Array.isArray(a.value.data)) apartments.value = a.value.data
  if (c.status === 'rejected') msg.value = errText(c.reason)
  else if (a.status === 'rejected') msg.value = `Could not load the flat list. ${errText(a.reason)}`
  loading.value = false
})

function openAdd() {
  form.value = blankForm()
  msg.value = ''
  showAdd.value = true
}

function closeAdd() {
  showAdd.value = false
  msg.value = ''
}

async function raiseConflict() {
  if (saving.value) return
  const description = form.value.description.trim()
  if (!form.value.reported_apartment_id) { msg.value = 'Please select the flat this concern is about.'; return }
  if (!form.value.category) { msg.value = 'Please choose a category.'; return }
  if (!description) { msg.value = 'Please describe the concern.'; return }

  saving.value = true
  msg.value = ''
  try {
    await conflictsAPI.raise({ ...form.value, description })
    const res = await conflictsAPI.getAll()
    conflicts.value = res.data
    showAdd.value = false
    form.value = blankForm()
  } catch(e) { msg.value = errText(e) }
  saving.value = false
}

async function resolve(id) {
  if (resolving.value) return
  resolving.value = id
  msg.value = ''
  try {
    const note = (resolveNote.value[id] || '').trim()
    await conflictsAPI.resolve(id, { resolution_note: note || 'Resolved by secretary' })
    const res = await conflictsAPI.getAll()
    conflicts.value = res.data
    delete resolveNote.value[id]
  } catch(e) { msg.value = errText(e) }
  resolving.value = null
}

function statusClass(s) {
  return { OPEN:'badge-open', UNDER_REVIEW:'badge-progress', RESOLVED:'badge-paid' }[s] || 'badge-low'
}
</script>
