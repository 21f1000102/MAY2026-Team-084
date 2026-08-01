<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <div class="d-flex gap-2">
        <select v-model="filterStatus" class="form-control-custom" style="width:100%;max-width:160px;">
          <option value="">All Status</option>
          <option>OPEN</option><option>ASSIGNED</option><option>IN_PROGRESS</option><option>COMPLETED</option><option>CLOSED</option>
        </select>
      </div>
      <button class="btn-primary-custom" @click="openAdd"><i class="fas fa-plus me-2"></i>Raise Complaint</button>
    </div>

    <div v-if="pageMsg" class="alert-custom alert-error">{{ pageMsg }}</div>

    <div v-if="loading" class="spinner"></div>
    <div v-else>
      <div v-if="filtered.length===0" class="empty-state card p-4"><i class="fas fa-check-circle" style="color:#0E7C7B;"></i><p>No complaints found</p></div>
      <div v-for="c in filtered" :key="c.id" class="card mb-3 p-4">
        <div class="d-flex justify-content-between align-items-start">
          <div>
            <div class="d-flex gap-2 mb-2 flex-wrap">
              <span class="badge-custom" :class="badgeClass(c.status)">{{ c.status }}</span>
              <span class="badge-custom" :class="badgeClass(c.priority)">{{ c.priority }}</span>
              <span class="badge-custom badge-low">{{ c.category }}</span>
            </div>
            <h6 class="mb-1 fw-bold">{{ c.title }}</h6>
            <p class="text-muted mb-1" style="font-size:0.85rem;">{{ c.description }}</p>
            <small class="text-muted">🏠 {{ c.flat_number }} · {{ c.raised_by_name }} · {{ c.created_at?.slice(0,10) }}</small>
            <br v-if="c.assigned_worker_name"/>
            <small v-if="c.assigned_worker_name" class="text-primary">👷 Assigned to: {{ c.assigned_worker_name }}</small>
          </div>
          <div class="d-flex gap-2 flex-column" v-if="isAdmin">
            <button v-if="c.status==='OPEN'" class="btn btn-sm btn-outline-primary" @click="openAssign(c)">Assign</button>
            <button v-if="c.status==='ASSIGNED'" class="btn btn-sm btn-outline-warning" @click="updateStatus(c,'IN_PROGRESS')">In Progress</button>
            <button v-if="c.status==='IN_PROGRESS'" class="btn btn-sm btn-outline-success" @click="updateStatus(c,'COMPLETED')">Complete</button>
            <button v-if="['COMPLETED'].includes(c.status)" class="btn btn-sm btn-outline-secondary" @click="updateStatus(c,'CLOSED')">Close</button>
            <button class="btn btn-sm btn-outline-danger" @click="deleteComplaint(c.id)"><i class="fas fa-trash"></i></button>
          </div>
        </div>
      </div>
    </div>

    <!-- Raise Complaint Modal -->
    <div class="modal-overlay" v-if="showAdd" @click.self="showAdd=false">
      <div class="modal-box">
        <div class="modal-header">
          <h6 class="mb-0 fw-bold">Raise Complaint</h6>
          <button @click="showAdd=false" class="btn btn-sm btn-light"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div v-if="msg" class="alert-custom" :class="msg.type==='error'?'alert-error':'alert-success'">{{ msg.text }}</div>
          <div class="form-group"><label class="form-label">Title *</label><input v-model="form.title" class="form-control-custom" placeholder="e.g. Corridor light not working"/></div>
          <div class="form-group">
            <label class="form-label">Description</label>
            <textarea v-model="form.description" class="form-control-custom" rows="3" placeholder="Describe the issue..."></textarea>
          </div>
          <div class="form-group">
            <label class="form-label">Category *</label>
            <select v-model="form.category" class="form-control-custom">
              <option>PLUMBING</option><option>ELECTRICAL</option><option>CLEANING</option><option>SECURITY</option><option>OTHER</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Priority</label>
            <select v-model="form.priority" class="form-control-custom">
              <option>LOW</option><option>MEDIUM</option><option>HIGH</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Apartment *</label>
            <select v-model="form.apartment_id" class="form-control-custom">
              <option value="">Select Flat</option>
              <option v-for="a in apartments" :key="a.id" :value="a.id">{{ a.flat_number }}</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showAdd=false" class="btn btn-light">Cancel</button>
          <button @click="raiseComplaint" class="btn-primary-custom" :disabled="saving">
            <span v-if="saving"><i class="fas fa-spinner fa-spin me-1"></i></span>Submit
          </button>
        </div>
      </div>
    </div>

    <!-- Assign Modal -->
    <div class="modal-overlay" v-if="showAssign" @click.self="showAssign=false">
      <div class="modal-box">
        <div class="modal-header">
          <h6 class="mb-0 fw-bold">Assign Complaint</h6>
          <button @click="showAssign=false" class="btn btn-sm btn-light"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div v-if="assignMsg" class="alert-custom alert-error">{{ assignMsg }}</div>
          <div class="form-group">
            <label class="form-label">Worker *</label>
            <select v-model="assignForm.worker_id" class="form-control-custom">
              <option value="">Select a worker</option>
              <option v-for="w in workers" :key="w.id" :value="w.id">{{ w.name }}</option>
            </select>
            <small v-if="workers.length===0" class="text-muted">
              No maintenance workers exist yet. Create a user with the WORKER role first.
            </small>
          </div>
          <div class="form-group"><label class="form-label">Remarks</label><input v-model="assignForm.remarks" class="form-control-custom"/></div>
        </div>
        <div class="modal-footer">
          <button @click="closeAssign" class="btn btn-light">Cancel</button>
          <button @click="doAssign" class="btn-primary-custom" :disabled="assigning">
            <span v-if="assigning"><i class="fas fa-spinner fa-spin me-1"></i></span>Assign
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { complaintsAPI, membersAPI, errText } from '../api/index'
import { authStore } from '../store/auth'
import { badgeClass } from '../utils/format'

const complaints = ref([])
const apartments = ref([])
const workers = ref([])
const loading = ref(true)
const saving = ref(false)
const assigning = ref(false)
const showAdd = ref(false)
const showAssign = ref(false)
const selectedComplaint = ref(null)
const filterStatus = ref('')
const msg = ref(null)
const pageMsg = ref('')
const assignMsg = ref('')
const emptyForm = () => ({ title:'', description:'', category:'ELECTRICAL', priority:'MEDIUM', apartment_id:'' })
const form = ref(emptyForm())
const assignForm = ref({ worker_id:'', remarks:'' })
const isAdmin = computed(() => authStore.isAdmin)

const filtered = computed(() =>
  complaints.value.filter(c => !filterStatus.value || c.status === filterStatus.value)
)

onMounted(async () => {
  const [c, a] = await Promise.allSettled([complaintsAPI.getAll(), membersAPI.getApartments()])
  if (c.status === 'fulfilled') complaints.value = c.value.data
  else pageMsg.value = errText(c.reason)
  if (a.status === 'fulfilled') apartments.value = a.value.data

  // Workers are admin-only; ignore the 403 for residents.
  if (authStore.isAdmin) {
    try { workers.value = (await membersAPI.getWorkers()).data } catch (e) { /* optional */ }
  }
  loading.value = false
})

function openAdd() { msg.value = null; form.value = emptyForm(); showAdd.value = true }

async function raiseComplaint() {
  if (!form.value.title?.trim()) { msg.value = { type:'error', text:'Title is required' }; return }
  if (!form.value.apartment_id) { msg.value = { type:'error', text:'Please select a flat' }; return }
  saving.value = true
  msg.value = null
  try {
    const res = await complaintsAPI.raise(form.value)
    complaints.value.unshift(res.data)
    showAdd.value = false
    form.value = emptyForm()
  } catch(e) {
    msg.value = { type:'error', text: errText(e) }
  }
  saving.value = false
}

function openAssign(c) {
  selectedComplaint.value = c
  assignForm.value = { worker_id:'', remarks:'' }   // was persisting between complaints
  assignMsg.value = ''
  showAssign.value = true
}

function closeAssign() { showAssign.value = false; assignMsg.value = '' }

async function doAssign() {
  // Previously always sent worker_id: null, so nothing was ever really assigned.
  if (!assignForm.value.worker_id) { assignMsg.value = 'Please select a worker'; return }
  assigning.value = true
  assignMsg.value = ''
  try {
    const res = await complaintsAPI.assign(selectedComplaint.value.id, {
      worker_id: assignForm.value.worker_id,
      remarks: assignForm.value.remarks,
    })
    updateLocal(res.data)
    showAssign.value = false
  } catch(e) { assignMsg.value = errText(e) }
  assigning.value = false
}

async function updateStatus(c, status) {
  pageMsg.value = ''
  try {
    const res = await complaintsAPI.updateStatus(c.id, { status })
    updateLocal(res.data)
  } catch(e) { pageMsg.value = errText(e) }
}

function updateLocal(updated) {
  const idx = complaints.value.findIndex(c => c.id === updated.id)
  if (idx > -1) complaints.value[idx] = updated
}

async function deleteComplaint(id) {
  if (!confirm('Delete this complaint?')) return
  pageMsg.value = ''
  try {
    await complaintsAPI.delete(id)
    complaints.value = complaints.value.filter(c => c.id !== id)
  } catch(e) { pageMsg.value = errText(e) }
}
</script>
