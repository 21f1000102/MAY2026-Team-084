<template>
  <div>
    <div v-if="msg && !showAdd" class="alert-custom alert-error">{{ msg }}</div>

    <div class="d-flex justify-content-end mb-4" v-if="isAdmin">
      <button class="btn-primary-custom" @click="openAdd"><i class="fas fa-plus me-2"></i>Add Task</button>
    </div>

    <FilterBar :fields="filterFields" :result-count="loading ? null : tasks.length" @change="onFilterChange" />

    <div v-if="loading" class="spinner"></div>
    <div v-else>
      <div v-if="tasks.length===0" class="empty-state card p-4"><i class="fas fa-tools"></i><p>No maintenance tasks</p></div>
      <div v-for="t in tasks" :key="t.id" class="card mb-3 p-4">
        <div class="d-flex justify-content-between align-items-start">
          <div>
            <div class="d-flex gap-2 mb-2">
              <span class="badge-custom badge-low">{{ t.category }}</span>
              <span class="badge-custom" :class="t.status==='COMPLETED'?'badge-paid':t.status==='IN_PROGRESS'?'badge-progress':'badge-open'">{{ t.status }}</span>
            </div>
            <h6 class="fw-bold mb-1">{{ t.title }}</h6>
            <p class="text-muted mb-1" style="font-size:0.85rem;">{{ t.description }}</p>
            <small class="text-muted">📅 {{ t.scheduled_date }}</small>
            <span v-if="t.assigned_to_name" class="ms-3"><small class="text-primary">👷 {{ t.assigned_to_name }}</small></span>
          </div>
          <div class="d-flex gap-2">
            <button v-if="isAdmin" @click="openAssign(t)" class="btn btn-sm btn-outline-primary">
              <i class="fas fa-user-hard-hat me-1"></i>{{ t.assigned_to ? 'Reassign' : 'Assign' }}
            </button>
            <button v-if="t.status!=='COMPLETED' && (isAdmin || isWorker)" @click="complete(t.id)" class="btn btn-sm btn-success"><i class="fas fa-check me-1"></i>Complete</button>
            <button v-if="isAdmin" @click="deleteTask(t.id)" class="btn btn-sm btn-outline-danger"><i class="fas fa-trash"></i></button>
          </div>
        </div>
      </div>
    </div>

    <!-- Assign / Reassign Worker Modal -->
    <div class="modal-overlay" v-if="showAssign" @click.self="showAssign=false">
      <div class="modal-box">
        <div class="modal-header">
          <h6 class="mb-0 fw-bold">Assign Worker</h6>
          <button @click="showAssign=false" class="btn btn-sm btn-light"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div v-if="assignMsg" class="alert-custom alert-error">{{ assignMsg }}</div>
          <div class="form-group">
            <label class="form-label">Worker</label>
            <select v-model="assignWorkerId" class="form-control-custom">
              <option value="">Unassigned</option>
              <option v-for="w in workers" :key="w.id" :value="w.id">{{ w.name }}</option>
            </select>
            <small v-if="workers.length===0" class="text-muted">
              No maintenance workers exist yet. Create a user with the WORKER role first.
            </small>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showAssign=false" class="btn btn-light">Cancel</button>
          <button @click="doAssign" class="btn-primary-custom" :disabled="assigning">
            <span v-if="assigning"><i class="fas fa-spinner fa-spin me-1"></i></span>Save
          </button>
        </div>
      </div>
    </div>

    <!-- Add Task Modal -->
    <div class="modal-overlay" v-if="showAdd" @click.self="closeAdd">
      <div class="modal-box">
        <div class="modal-header">
          <h6 class="mb-0 fw-bold">Add Maintenance Task</h6>
          <button @click="closeAdd" class="btn btn-sm btn-light"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div v-if="msg" class="alert-custom alert-error">{{ msg }}</div>
          <div class="form-group"><label class="form-label">Title *</label><input v-model="form.title" class="form-control-custom" placeholder="e.g. Water tank cleaning"/></div>
          <div class="form-group"><label class="form-label">Description</label><textarea v-model="form.description" class="form-control-custom" rows="2"></textarea></div>
          <div class="form-group"><label class="form-label">Category *</label>
            <select v-model="form.category" class="form-control-custom">
              <option>GENERATOR</option><option>WATER_TANK</option><option>CLEANING</option><option>ELECTRICAL</option><option>PLUMBING</option><option>OTHER</option>
            </select>
          </div>
          <div class="form-group"><label class="form-label">Scheduled Date *</label><input v-model="form.scheduled_date" type="date" class="form-control-custom"/></div>
          <div class="form-group">
            <label class="form-label">Assign To</label>
            <select v-model="form.assigned_to" class="form-control-custom">
              <option value="">Unassigned</option>
              <option v-for="w in workers" :key="w.id" :value="w.id">{{ w.name }}</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeAdd" class="btn btn-light">Cancel</button>
          <button @click="addTask" class="btn-primary-custom" :disabled="saving">
            <span v-if="saving"><i class="fas fa-spinner fa-spin me-1"></i></span>Add Task
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { maintenanceAPI, membersAPI, errText } from '../api/index'
import { authStore } from '../store/auth'
import { orNull, today } from '../utils/format'
import FilterBar from './FilterBar.vue'

const isAdmin = computed(() => authStore.isAdmin)
const isWorker = computed(() => authStore.isWorker)

const emptyForm = () => ({ title:'', description:'', category:'GENERATOR', scheduled_date: today(), assigned_to:'' })

const tasks = ref([])
const workers = ref([])
const loading = ref(true)
const saving = ref(false)
const assigning = ref(false)
const showAdd = ref(false)
const showAssign = ref(false)
const msg = ref('')
const assignMsg = ref('')
const form = ref(emptyForm())
const activeFilters = ref({})
const assignTask = ref(null)
const assignWorkerId = ref('')

const filterFields = [
  { key: 'status', label: 'Status', type: 'select', options: ['PENDING','IN_PROGRESS','COMPLETED'] },
  { key: 'category', label: 'Category', type: 'select', options: ['GENERATOR','WATER_TANK','CLEANING','ELECTRICAL','PLUMBING','OTHER'] },
  { key: 'worker', label: 'Worker', placeholder: 'Worker name...' },
]

onMounted(async () => {
  try { workers.value = (await membersAPI.getWorkers()).data } catch (e) { /* admin-only; ignore for other roles */ }
  await loadTasks()
  loading.value = false
})

async function onFilterChange(params) {
  activeFilters.value = params
  await loadTasks()
}

async function loadTasks() {
  try { tasks.value = (await maintenanceAPI.getAll(activeFilters.value)).data }
  catch(e) { msg.value = errText(e) }
}

function openAdd() { msg.value = ''; form.value = emptyForm(); showAdd.value = true }
function closeAdd() { msg.value = ''; showAdd.value = false }

async function addTask() {
  if (saving.value) return
  msg.value = ''

  const title = String(form.value.title || '').trim()
  if (!title) { msg.value = 'Title is required.'; return }

  saving.value = true
  try {
    await maintenanceAPI.add({
      title,
      // description is optional — '' would be stored as a blank string.
      description: orNull(form.value.description),
      category: form.value.category,
      // scheduled_date is a NOT NULL date column — never send ''.
      scheduled_date: orNull(form.value.scheduled_date) || today(),
      assigned_to: orNull(form.value.assigned_to),
    })
    await loadTasks()
    form.value = emptyForm()
    showAdd.value = false
  } catch(e) { msg.value = errText(e) }
  saving.value = false
}

function openAssign(task) {
  assignTask.value = task
  assignWorkerId.value = task.assigned_to || ''
  assignMsg.value = ''
  showAssign.value = true
}

async function doAssign() {
  if (!assignTask.value) return
  assigning.value = true
  assignMsg.value = ''
  try {
    await maintenanceAPI.update(assignTask.value.id, { assigned_to: orNull(assignWorkerId.value) })
    await loadTasks()
    showAssign.value = false
  } catch(e) { assignMsg.value = errText(e) }
  assigning.value = false
}

async function complete(id) {
  msg.value = ''
  try {
    await maintenanceAPI.complete(id)
    await loadTasks()
  } catch(e) { msg.value = errText(e) }
}

async function deleteTask(id) {
  if (!confirm('Delete this task?')) return
  msg.value = ''
  try {
    await maintenanceAPI.delete(id)
    await loadTasks()
  } catch(e) { msg.value = errText(e) }
}
</script>
