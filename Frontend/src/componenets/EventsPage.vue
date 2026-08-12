<template>
  <div>
    <div class="d-flex justify-content-end mb-4" v-if="isAdmin">
      <button class="btn-primary-custom" @click="openAdd"><i class="fas fa-plus me-2"></i>Add Event</button>
    </div>

    <FilterBar :fields="filterFields" :result-count="loading ? null : events.length" @change="onFilterChange" />

    <div v-if="pageMsg" class="alert-custom alert-error">{{ pageMsg }}</div>

    <div v-if="loading" class="spinner"></div>
    <div v-else>
      <div v-if="events.length===0" class="empty-state card p-4"><i class="fas fa-calendar-alt"></i><p>No events found</p></div>
      <div v-for="e in events" :key="e.id" class="card mb-3 p-4">
        <div class="d-flex justify-content-between align-items-start flex-wrap gap-2">
          <div>
            <div class="d-flex gap-2 mb-2">
              <span class="badge-custom badge-low">{{ e.event_type }}</span>
            </div>
            <h6 class="fw-bold mb-1">{{ e.title }}</h6>
            <p class="text-muted mb-1" style="font-size:0.85rem;">{{ e.description }}</p>
            <small class="text-muted">
              📅 {{ formatDate(e.event_date) }}<span v-if="e.event_time"> · 🕐 {{ e.event_time }}</span>
              <span v-if="e.location"> · 📍 {{ e.location }}</span>
            </small>
          </div>
          <div class="d-flex gap-2" v-if="isAdmin">
            <button class="btn btn-sm btn-outline-primary" @click="openEdit(e)"><i class="fas fa-pen"></i></button>
            <button class="btn btn-sm btn-outline-danger" @click="deleteEvent(e.id)"><i class="fas fa-trash"></i></button>
          </div>
        </div>
      </div>
    </div>

    <!-- Add / Edit Event Modal -->
    <div class="modal-overlay" v-if="showForm" @click.self="closeForm">
      <div class="modal-box">
        <div class="modal-header">
          <h6 class="mb-0 fw-bold">{{ editingId ? 'Edit Event' : 'Add Event' }}</h6>
          <button @click="closeForm" class="btn btn-sm btn-light"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div v-if="formMsg" class="alert-custom alert-error">{{ formMsg }}</div>
          <div class="form-group"><label class="form-label">Title *</label><input v-model="form.title" class="form-control-custom" placeholder="e.g. Annual General Meeting"/></div>
          <div class="form-group"><label class="form-label">Description</label><textarea v-model="form.description" class="form-control-custom" rows="2"></textarea></div>
          <div class="form-group"><label class="form-label">Type *</label>
            <select v-model="form.event_type" class="form-control-custom">
              <option>MEETING</option><option>EVENT</option><option>HOLIDAY</option><option>DEADLINE</option><option>OTHER</option>
            </select>
          </div>
          <div class="form-group"><label class="form-label">Date *</label><input v-model="form.event_date" type="date" class="form-control-custom"/></div>
          <div class="form-group"><label class="form-label">Time</label><input v-model="form.event_time" type="time" class="form-control-custom"/></div>
          <div class="form-group"><label class="form-label">Location</label><input v-model="form.location" class="form-control-custom" placeholder="e.g. Clubhouse"/></div>
        </div>
        <div class="modal-footer">
          <button @click="closeForm" class="btn btn-light">Cancel</button>
          <button @click="saveEvent" class="btn-primary-custom" :disabled="saving">
            <span v-if="saving"><i class="fas fa-spinner fa-spin me-1"></i></span>Save
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { eventsAPI, errText } from '../api/index'
import { authStore } from '../store/auth'
import { orNull, today, formatDate } from '../utils/format'
import FilterBar from './FilterBar.vue'

const isAdmin = computed(() => authStore.isAdmin)

const events = ref([])
const loading = ref(true)
const saving = ref(false)
const showForm = ref(false)
const editingId = ref(null)
const pageMsg = ref('')
const formMsg = ref('')
const activeFilters = ref({})

const emptyForm = () => ({ title: '', description: '', event_type: 'MEETING', event_date: today(), event_time: '', location: '' })
const form = ref(emptyForm())

const filterFields = [
  { key: 'q', label: 'Search', placeholder: 'Title...' },
  { key: 'event_type', label: 'Type', type: 'select', options: ['MEETING','EVENT','HOLIDAY','DEADLINE','OTHER'] },
  { key: 'from', label: 'From', type: 'date' },
  { key: 'to', label: 'To', type: 'date' },
]

onMounted(async () => {
  await loadEvents()
  loading.value = false
})

async function onFilterChange(params) {
  activeFilters.value = params
  await loadEvents()
}

async function loadEvents() {
  try { events.value = (await eventsAPI.getAll(activeFilters.value)).data }
  catch (e) { pageMsg.value = errText(e) }
}

function openAdd() { editingId.value = null; form.value = emptyForm(); formMsg.value = ''; showForm.value = true }
function openEdit(e) {
  editingId.value = e.id
  form.value = { title: e.title, description: e.description || '', event_type: e.event_type,
                event_date: e.event_date, event_time: e.event_time || '', location: e.location || '' }
  formMsg.value = ''
  showForm.value = true
}
function closeForm() { showForm.value = false; formMsg.value = '' }

async function saveEvent() {
  if (!form.value.title?.trim()) { formMsg.value = 'Title is required.'; return }
  if (!form.value.event_date) { formMsg.value = 'Date is required.'; return }
  saving.value = true
  formMsg.value = ''
  const payload = {
    title: form.value.title.trim(),
    description: orNull(form.value.description),
    event_type: form.value.event_type,
    event_date: form.value.event_date,
    event_time: orNull(form.value.event_time),
    location: orNull(form.value.location),
  }
  try {
    if (editingId.value) await eventsAPI.update(editingId.value, payload)
    else await eventsAPI.add(payload)
    await loadEvents()
    showForm.value = false
  } catch (e) { formMsg.value = errText(e) }
  saving.value = false
}

async function deleteEvent(id) {
  if (!confirm('Delete this event?')) return
  pageMsg.value = ''
  try {
    await eventsAPI.delete(id)
    await loadEvents()
  } catch (e) { pageMsg.value = errText(e) }
}
</script>
