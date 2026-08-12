<template>
  <div>
    <div v-if="msg" class="alert-custom alert-error">{{ msg }}</div>

    <div class="row g-3 mb-4">
      <div class="col-6 col-md-3">
        <div class="stat-card">
          <div class="stat-icon" style="background:#d97706;"><i class="fas fa-exclamation-circle"></i></div>
          <div><div class="stat-value">{{ pending.length }}</div><div class="stat-label">Pending Complaints</div></div>
        </div>
      </div>
      <div class="col-6 col-md-3">
        <div class="stat-card">
          <div class="stat-icon" style="background:#0E7C7B;"><i class="fas fa-check-circle"></i></div>
          <div><div class="stat-value">{{ completedCount }}</div><div class="stat-label">Completed Complaints</div></div>
        </div>
      </div>
      <div class="col-6 col-md-3">
        <div class="stat-card">
          <div class="stat-icon" style="background:#1B2A4A;"><i class="fas fa-tools"></i></div>
          <div><div class="stat-value">{{ maintenanceSummary.total - (maintenanceSummary.by_status?.COMPLETED || 0) }}</div><div class="stat-label">Pending Tasks</div></div>
        </div>
      </div>
      <div class="col-6 col-md-3">
        <div class="stat-card">
          <div class="stat-icon" style="background:#dc2626;"><i class="fas fa-triangle-exclamation"></i></div>
          <div><div class="stat-value">{{ maintenanceSummary.overdue_count }}</div><div class="stat-label">Overdue Tasks</div></div>
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
                <span class="badge-custom" :class="badgeClass(c.status)">{{ label(c.status) }}</span>
                <span class="badge-custom" :class="badgeClass(c.priority)">{{ label(c.priority) }}</span>
                <span class="badge-custom badge-low">{{ label(c.category) }}</span>
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

      <!-- My Maintenance Tasks -->
      <div class="card mt-4">
        <div class="card-header-custom">🛠️ My Maintenance Tasks</div>
        <div v-if="maintenanceTasks.length === 0" class="empty-state p-4">
          <i class="fas fa-check-circle" style="color:#0E7C7B;"></i>
          <p>No maintenance tasks assigned to you right now!</p>
        </div>
        <div v-for="t in maintenanceTasks" :key="t.id" class="p-4" style="border-bottom:1px solid #f1f5f9;">
          <div class="d-flex justify-content-between align-items-start flex-wrap gap-2">
            <div>
              <div class="d-flex gap-2 mb-2">
                <span class="badge-custom badge-low">{{ t.category }}</span>
                <span class="badge-custom" :class="t.status==='COMPLETED'?'badge-paid':'badge-open'">{{ t.status }}</span>
              </div>
              <h6 class="fw-bold mb-1">{{ t.title }}</h6>
              <small class="text-muted">📅 Scheduled: {{ t.scheduled_date }}</small>
            </div>
            <button v-if="t.status!=='COMPLETED'" @click="completeTask(t.id)" class="btn btn-sm btn-success">
              <i class="fas fa-check me-1"></i>Mark Complete
            </button>
          </div>
        </div>
      </div>

      <div class="row g-3 mt-1">
        <div class="col-md-6">
          <UpcomingCard />
        </div>
        <div class="col-md-6">
          <div class="card">
            <div class="card-header-custom">📜 Work History</div>
            <div v-if="!history || history.totals.total === 0" class="empty-state p-4">
              <i class="fas fa-clock" style="color:#94a3b8;"></i><p>No completed work yet</p>
            </div>
            <div v-else class="p-3">
              <p class="text-muted mb-2" style="font-size:0.85rem;">
                {{ history.totals.complaints }} complaint(s) · {{ history.totals.maintenance }} maintenance task(s) completed
              </p>
              <div v-for="c in history.completed_complaints.slice(0,3)" :key="'c'+c.id" class="d-flex justify-content-between py-1" style="font-size:0.85rem;border-bottom:1px solid #f1f5f9;">
                <span>{{ c.title }}</span><span class="text-muted">{{ c.resolved_at?.slice(0,10) }}</span>
              </div>
              <div v-for="t in history.completed_maintenance.slice(0,3)" :key="'t'+t.id" class="d-flex justify-content-between py-1" style="font-size:0.85rem;border-bottom:1px solid #f1f5f9;">
                <span>{{ t.title }}</span><span class="text-muted">{{ t.completed_at?.slice(0,10) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Complete Complaint Modal -->
    <div class="modal-overlay" v-if="showComplete" @click.self="closeComplete">
      <div class="modal-box">
        <div class="modal-header">
          <h6 class="mb-0 fw-bold">Mark Complaint as Completed</h6>
          <button @click="closeComplete" class="btn btn-sm btn-light"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div v-if="msg" class="alert-custom alert-error">{{ msg }}</div>
          <p class="text-muted mb-3">Complaint: <strong>{{ selectedComplaint?.title }}</strong></p>
          <div class="form-group">
            <label class="form-label">Completion Remarks</label>
            <textarea v-model="remarks" class="form-control-custom" rows="3" placeholder="Describe what was done..."></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeComplete" class="btn btn-light">Cancel</button>
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
import { complaintsAPI, maintenanceAPI, membersAPI, errText } from '../api/index'
import { authStore } from '../store/auth'
import { badgeClass, label } from '../utils/format'
import UpcomingCard from './UpcomingCard.vue'

const allComplaints = ref([])
const maintenanceTasks = ref([])
const maintenanceSummary = ref({ total: 0, by_status: {}, overdue_count: 0 })
const history = ref(null)
const loading = ref(true)
const saving = ref(false)
const msg = ref('')
const showComplete = ref(false)
const selectedComplaint = ref(null)
const remarks = ref('')

// Only the rows actually assigned to the signed-in worker. This used to filter
// on status alone, so every worker saw (and could close) the whole society's
// assigned complaints.
const mine = computed(() => {
  const me = authStore.user?.id
  if (!me) return []
  return allComplaints.value.filter(c => c.assigned_worker_id === me)
})

const myComplaints = computed(() =>
  mine.value.filter(c => ['ASSIGNED', 'IN_PROGRESS'].includes(c.status))
)

const pending = computed(() =>
  mine.value.filter(c => c.status === 'ASSIGNED')
)

// Full list drives the stat count; the card below shows only the latest few.
const allCompleted = computed(() =>
  mine.value.filter(c => c.status === 'COMPLETED')
)
const completedCount = computed(() => allCompleted.value.length)
const completed = computed(() => allCompleted.value.slice(0, 5))

onMounted(async () => {
  try {
    const res = await complaintsAPI.getAll()
    allComplaints.value = Array.isArray(res.data) ? res.data : []
  } catch(e) { msg.value = errText(e) }

  await loadMaintenance()

  // Work history and its own summary are read-only extras for this dashboard;
  // a failure here shouldn't block the complaints panel above from working.
  try {
    const me = authStore.user?.id
    if (me) history.value = (await membersAPI.workHistory(me)).data
  } catch (e) { /* optional widget */ }

  loading.value = false
})

async function loadMaintenance() {
  try {
    // GET /api/maintenance/ already scopes to tasks assigned to this worker.
    maintenanceTasks.value = (await maintenanceAPI.getAll()).data
    maintenanceSummary.value = (await maintenanceAPI.summary()).data
  } catch (e) { /* optional widget */ }
}

async function completeTask(id) {
  msg.value = ''
  try {
    await maintenanceAPI.complete(id)
    await loadMaintenance()
  } catch (e) { msg.value = errText(e) }
}

async function markInProgress(id) {
  msg.value = ''
  try {
    const res = await complaintsAPI.updateStatus(id, { status: 'IN_PROGRESS', remarks: 'Work started' })
    updateLocal(res.data)
  } catch(e) { msg.value = errText(e) }
}

function openComplete(c) {
  selectedComplaint.value = c
  remarks.value = ''
  msg.value = ''
  showComplete.value = true
}

function closeComplete() {
  showComplete.value = false
  msg.value = ''
}

async function doComplete() {
  if (saving.value) return
  if (!selectedComplaint.value) return
  saving.value = true
  msg.value = ''
  try {
    const res = await complaintsAPI.updateStatus(selectedComplaint.value.id, {
      status: 'COMPLETED',
      remarks: remarks.value.trim() || 'Work completed'
    })
    updateLocal(res.data)
    showComplete.value = false
    remarks.value = ''
    selectedComplaint.value = null

    const me = authStore.user?.id
    if (me) { try { history.value = (await membersAPI.workHistory(me)).data } catch (e) { /* optional */ } }
  } catch(e) { msg.value = errText(e) }
  saving.value = false
}

function updateLocal(updated) {
  if (!updated?.id) return
  const idx = allComplaints.value.findIndex(c => c.id === updated.id)
  if (idx > -1) allComplaints.value[idx] = updated
}
</script>
