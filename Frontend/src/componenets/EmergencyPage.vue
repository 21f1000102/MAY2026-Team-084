<template>
  <div>
    <div v-if="msg && !showForm" class="alert-custom alert-error">{{ msg }}</div>

    <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
      <input v-model="search" class="form-control-custom" placeholder="🔍 Search name, service or number..."
             style="width:100%;max-width:300px;"/>
      <button v-if="isAdmin" class="btn-primary-custom" @click="openAdd">
        <i class="fas fa-plus me-2"></i>Add Contact
      </button>
    </div>

    <div v-if="loading" class="spinner"></div>
    <div v-else>
      <div v-if="contacts.length===0" class="empty-state card p-4">
        <i class="fas fa-phone-slash"></i>
        <p>No emergency contacts have been added yet.</p>
        <p v-if="isAdmin" style="font-size:0.85rem;">Click "Add Contact" to add the society's plumber, electrician and security numbers.</p>
      </div>
      <div v-else-if="filtered.length===0" class="empty-state card p-4">
        <i class="fas fa-search"></i><p>No contacts match "{{ search }}"</p>
      </div>

      <!-- grouped by service type -->
      <div v-for="group in grouped" :key="group.type" class="mb-4">
        <h6 class="fw-bold mb-2" style="color:#1B2A4A;">
          <i class="fas" :class="serviceMeta(group.type).icon"></i>
          <span class="ms-2">{{ serviceMeta(group.type).label }}</span>
          <span class="text-muted" style="font-weight:400;font-size:0.85rem;"> ({{ group.items.length }})</span>
        </h6>
        <div class="row g-3">
          <div v-for="c in group.items" :key="c.id" class="col-12 col-md-6 col-lg-4">
            <div class="card p-3 h-100">
              <div class="d-flex justify-content-between align-items-start mb-2">
                <span class="badge-custom" :class="serviceMeta(c.service_type).badge">
                  {{ serviceMeta(c.service_type).label }}
                </span>
                <div v-if="isAdmin" class="d-flex gap-1">
                  <button class="btn btn-sm btn-outline-primary" @click="openEdit(c)" title="Edit">
                    <i class="fas fa-pen"></i>
                  </button>
                  <button class="btn btn-sm btn-outline-danger" @click="removeContact(c)" title="Delete">
                    <i class="fas fa-trash"></i>
                  </button>
                </div>
              </div>
              <h6 class="fw-bold mb-1">{{ label(c.name) }}</h6>
              <div v-if="c.availability" class="text-muted mb-2" style="font-size:0.8rem;">
                <i class="fas fa-clock me-1"></i>{{ c.availability }}
              </div>
              <a v-if="telHref(c.phone)" :href="telHref(c.phone)" class="btn-primary-custom d-block text-center text-decoration-none mt-auto">
                <i class="fas fa-phone me-2"></i>{{ c.phone }}
              </a>
              <span v-else class="text-muted" style="font-size:0.85rem;">No number on record</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Add / Edit Modal (admin only) -->
    <div class="modal-overlay" v-if="showForm" @click.self="closeForm">
      <div class="modal-box">
        <div class="modal-header">
          <h6 class="mb-0 fw-bold">{{ editingId ? 'Edit Contact' : 'Add Emergency Contact' }}</h6>
          <button @click="closeForm" class="btn btn-sm btn-light"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div v-if="msg" class="alert-custom alert-error">{{ msg }}</div>
          <div class="form-group">
            <label class="form-label">Name *</label>
            <input v-model="form.name" class="form-control-custom" placeholder="e.g. Ramesh Plumbing Services"/>
          </div>
          <div class="form-group">
            <label class="form-label">Service Type *</label>
            <select v-model="form.service_type" class="form-control-custom">
              <option v-for="t in SERVICE_TYPES" :key="t" :value="t">{{ serviceMeta(t).label }}</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Phone Number *</label>
            <input v-model="form.phone" class="form-control-custom" placeholder="e.g. 9876543210"/>
          </div>
          <div class="form-group">
            <label class="form-label">Availability</label>
            <input v-model="form.availability" class="form-control-custom" placeholder="e.g. 24x7 or Mon-Sat 9am-7pm"/>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeForm" class="btn btn-light">Cancel</button>
          <button @click="save" class="btn-primary-custom" :disabled="saving">
            <span v-if="saving"><i class="fas fa-spinner fa-spin me-1"></i></span>
            {{ editingId ? 'Save Changes' : 'Add Contact' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { emergencyAPI, errText } from '../api/index'
import { authStore } from '../store/auth'
import { SERVICE_TYPES, serviceMeta, telHref, label, orNull } from '../utils/format'

const contacts = ref([])
const loading = ref(true)
const saving = ref(false)
const msg = ref('')
const search = ref('')
const showForm = ref(false)
const editingId = ref(null)
const isAdmin = computed(() => authStore.isAdmin)

const blankForm = () => ({ name: '', service_type: 'PLUMBER', phone: '', availability: '' })
const form = ref(blankForm())

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return contacts.value
  return contacts.value.filter(c =>
    (c.name || '').toLowerCase().includes(q) ||
    (c.service_type || '').toLowerCase().includes(q) ||
    (c.phone || '').toLowerCase().includes(q)
  )
})

// Group by service type, ordered as SERVICE_TYPES declares.
const grouped = computed(() => {
  const buckets = new Map()
  for (const c of filtered.value) {
    const t = c.service_type || 'OTHER'
    if (!buckets.has(t)) buckets.set(t, [])
    buckets.get(t).push(c)
  }
  const known = SERVICE_TYPES.filter(t => buckets.has(t)).map(t => ({ type: t, items: buckets.get(t) }))
  const unknown = [...buckets.keys()].filter(t => !SERVICE_TYPES.includes(t))
                    .map(t => ({ type: t, items: buckets.get(t) }))
  return [...known, ...unknown]
})

onMounted(load)

async function load() {
  try { contacts.value = (await emergencyAPI.getAll()).data }
  catch (e) { msg.value = errText(e) }
  loading.value = false
}

function openAdd() { editingId.value = null; form.value = blankForm(); msg.value = ''; showForm.value = true }

function openEdit(c) {
  editingId.value = c.id
  form.value = {
    name: c.name || '', service_type: c.service_type || 'OTHER',
    phone: c.phone || '', availability: c.availability || '',
  }
  msg.value = ''
  showForm.value = true
}

function closeForm() { showForm.value = false; msg.value = '' }

async function save() {
  if (saving.value) return
  if (!form.value.name.trim()) { msg.value = 'Name is required'; return }
  if (!form.value.phone.trim()) { msg.value = 'Phone number is required'; return }

  saving.value = true
  msg.value = ''
  const payload = {
    name: form.value.name.trim(),
    service_type: form.value.service_type,
    phone: form.value.phone.trim(),
    availability: orNull(form.value.availability),
  }
  try {
    if (editingId.value) {
      const res = await emergencyAPI.update(editingId.value, payload)
      const idx = contacts.value.findIndex(c => c.id === editingId.value)
      if (idx > -1) contacts.value[idx] = res.data
    } else {
      const res = await emergencyAPI.add(payload)
      contacts.value.push(res.data)
    }
    showForm.value = false
    form.value = blankForm()
    editingId.value = null
  } catch (e) { msg.value = errText(e) }
  saving.value = false
}

async function removeContact(c) {
  if (!confirm(`Delete "${c.name}"? This cannot be undone.`)) return
  msg.value = ''
  try {
    await emergencyAPI.remove(c.id)
    contacts.value = contacts.value.filter(x => x.id !== c.id)
  } catch (e) { msg.value = errText(e) }
}
</script>
