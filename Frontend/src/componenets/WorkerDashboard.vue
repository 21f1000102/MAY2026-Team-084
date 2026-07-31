<template>
  <div>
    <div class="row g-3 mb-4">
      <div class="col-6">
        <div class="stat-card">
          <div class="stat-icon" style="background:#d97706;"><i class="fas fa-exclamation-circle"></i></div>
          <div><div class="stat-value">{{ pending.length }}</div><div class="stat-label">Pending Tasks</div></div>
        </div>
      </div>
      <div class="col-6">
        <div class="stat-card">
          <div class="stat-icon" style="background:#0E7C7B;"><i class="fas fa-check-circle"></i></div>
          <div><div class="stat-value">{{ completed.length }}</div><div class="stat-label">Completed Today</div></div>
        </div>
      </div>
    </div>

    <div v-if="loading" class="spinner"></div>
    <div v-else>
      <!-- Pending / In Progress -->
      <div class="card mb-4">
        <div class="card-header-custom">🔧 My Assigned Complaints</div>
        <div v-if="myComplaints.length === 0" class="empty-state p-4">
          <i class="fas fa-check-circle" style="color:#0E7C7B;"></i>
          <p>No complaints assigned to you right now!</p>
        </div>
        <div v-for="c in myComplaints" :key="c.id" class="p-4" style="border-bottom:1px solid #f1f5f9;">
          <div class="d-flex justify-content-between align-items-start flex-wrap gap-2">
            <div>
              <div class="d-flex gap-2 mb-2 flex-wrap">
                <span class="badge-custom" :class="`badge-${c.status.toLowerCase().replace('_','-')}`">{{ c.status }}</span>
                <span class="badge-custom" :class="`badge-${c.priority.toLowerCase()}`">{{ c.priority }}</span>
                <span class="badge-custom badge-low">{{ c.category }}</span>
              </div>
              <h6 class="fw-bold mb-1">{{ c.title }}</h6>
              <p class="text-muted mb-1" style="font-size:0.85rem;">{{ c.description }}</p>
              <small class="text-muted">🏠 Flat {{ c.flat_number }} · Reported: {{ c.created_at?.slice(0,10) }}</small>
            </div>
            <div class="d-flex gap-2">
              <button
                v-if="c.status === 'ASSIGNED'"
                @click="markInProgress(c.id)"
                class="btn btn-sm btn-warning">
                <i class="fas fa-play me-1"></i>Start Work
              </button>
              <button
                v-if="c.status === 'IN_PROGRESS'"
                @click="openComplete(c)"
                class="btn btn-sm btn-success">
                <i class="fas fa-check me-1"></i>Mark Done
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Completed -->
      <div class="card" v-if="completed.length > 0">
        <div class="card-header-custom" style="background:#0E7C7B;">✅ Recently Completed</div>
        <div v-for="c in completed" :key="c.id" class="p-4" style="border-bottom:1px solid #f1f5f9;">
          <div class="d-flex justify-content-between align-items-center">
            <div>
              <h6 class="fw-bold mb-1">{{ c.title }}</h6>
              <small class="text-muted">🏠 Flat {{ c.flat_number }} · Resolved: {{ c.resolved_at?.slice(0,10) }}</small>
            </div>
            <span class="badge-custom badge-paid">COMPLETED</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Complete Complaint Modal -->
    <div class="modal-overlay" v-if="showComplete" @click.self="showComplete=false">
      <div class="modal-box">
        <div class="modal-header">
          <h6 class="mb-0 fw-bold">Mark Complaint as Completed</h6>
          <button @click="showComplete=false" class="btn btn-sm btn-light"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <p class="text-muted mb-3">Complaint: <strong>{{ selectedComplaint?.title }}</strong></p>
          <div class="form-group">
            <label class="form-label">Completion Remarks</label>
            <textarea v-model="remarks" class="form-control-custom" rows="3" placeholder="Describe what was done..."></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showComplete=false" class="btn btn-light">Cancel</button>
          <button @click="doComplete" class="btn btn-success" :disabled="saving">
            <span v-if="saving"><i class="fas fa-spinner fa-spin me-1"></i></span>
            <i class="fas fa-check me-1"></i>Confirm Completed
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { complaintsAPI } from '../api/index'
import { authStore } from '../store/auth'

const allComplaints = ref([])
const loading = ref(true)
const saving = ref(false)
const showComplete = ref(false)
const selectedComplaint = ref(null)
const remarks = ref('')

// worker sees complaints assigned to them
const myComplaints = computed(() =>
  allComplaints.value.filter(c =>
    ['ASSIGNED', 'IN_PROGRESS'].includes(c.status)
  )
)

const pending = computed(() =>
  allComplaints.value.filter(c => c.status === 'ASSIGNED')
)

const completed = computed(() =>
  allComplaints.value.filter(c => c.status === 'COMPLETED').slice(0, 5)
)

onMounted(async () => {
  try {
    const res = await complaintsAPI.getAll()
    allComplaints.value = res.data
  } catch(e) {}
  loading.value = false
})

async function markInProgress(id) {
  try {
    const res = await complaintsAPI.updateStatus(id, { status: 'IN_PROGRESS', remarks: 'Work started' })
    updateLocal(res.data)
  } catch(e) {}
}

function openComplete(c) {
  selectedComplaint.value = c
  remarks.value = ''
  showComplete.value = true
}

async function doComplete() {
  saving.value = true
  try {
    const res = await complaintsAPI.updateStatus(selectedComplaint.value.id, {
      status: 'COMPLETED',
      remarks: remarks.value || 'Work completed'
    })
    updateLocal(res.data)
    showComplete.value = false
  } catch(e) {}
  saving.value = false
}

function updateLocal(updated) {
  const idx = allComplaints.value.findIndex(c => c.id === updated.id)
  if (idx > -1) allComplaints.value[idx] = updated
}
</script>
