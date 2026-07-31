<template>
  <div>
    <div class="d-flex justify-content-end mb-4">
      <button class="btn-primary-custom" @click="showAdd=true"><i class="fas fa-plus me-2"></i>Add Task</button>
    </div>
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
            <button v-if="t.status!=='COMPLETED'" @click="complete(t.id)" class="btn btn-sm btn-success"><i class="fas fa-check me-1"></i>Complete</button>
            <button @click="deleteTask(t.id)" class="btn btn-sm btn-outline-danger"><i class="fas fa-trash"></i></button>
          </div>
        </div>
      </div>
    </div>

    <!-- Add Task Modal -->
    <div class="modal-overlay" v-if="showAdd" @click.self="showAdd=false">
      <div class="modal-box">
        <div class="modal-header">
          <h6 class="mb-0 fw-bold">Add Maintenance Task</h6>
          <button @click="showAdd=false" class="btn btn-sm btn-light"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div class="form-group"><label class="form-label">Title *</label><input v-model="form.title" class="form-control-custom" placeholder="e.g. Water tank cleaning"/></div>
          <div class="form-group"><label class="form-label">Description</label><textarea v-model="form.description" class="form-control-custom" rows="2"></textarea></div>
          <div class="form-group"><label class="form-label">Category *</label>
            <select v-model="form.category" class="form-control-custom">
              <option>GENERATOR</option><option>WATER_TANK</option><option>CLEANING</option><option>ELECTRICAL</option><option>PLUMBING</option><option>OTHER</option>
            </select>
          </div>
          <div class="form-group"><label class="form-label">Scheduled Date *</label><input v-model="form.scheduled_date" type="date" class="form-control-custom"/></div>
        </div>
        <div class="modal-footer">
          <button @click="showAdd=false" class="btn btn-light">Cancel</button>
          <button @click="addTask" class="btn-primary-custom" :disabled="saving">
            <span v-if="saving"><i class="fas fa-spinner fa-spin me-1"></i></span>Add Task
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { maintenanceAPI } from '../api/index'

const tasks = ref([])
const loading = ref(true)
const saving = ref(false)
const showAdd = ref(false)
const form = ref({ title:'', description:'', category:'GENERATOR', scheduled_date:'' })

onMounted(async () => {
  try { tasks.value = (await maintenanceAPI.getAll()).data } catch(e) {}
  loading.value = false
})

async function addTask() {
  saving.value = true
  try {
    const res = await maintenanceAPI.add(form.value)
    tasks.value.push(res.data)
    showAdd.value = false
    form.value = { title:'', description:'', category:'GENERATOR', scheduled_date:'' }
  } catch(e) {}
  saving.value = false
}

async function complete(id) {
  try {
    const res = await maintenanceAPI.complete(id)
    const idx = tasks.value.findIndex(t => t.id===id)
    if (idx > -1) tasks.value[idx] = res.data
  } catch(e) {}
}

async function deleteTask(id) {
  if (!confirm('Delete this task?')) return
  try {
    await maintenanceAPI.delete(id)
    tasks.value = tasks.value.filter(t => t.id !== id)
  } catch(e) {}
}
</script>
