<template>
  <div>
    <div v-if="msg" class="alert-custom alert-error">{{ msg }}</div>

    <div class="d-flex justify-content-end mb-4" v-if="isAdmin">
      <button class="btn-primary-custom" @click="openAdd"><i class="fas fa-bullhorn me-2"></i>Post Notice</button>
    </div>
    <div v-if="loading" class="spinner"></div>
    <div v-else>
      <div v-if="notices.length===0" class="empty-state card p-4"><i class="fas fa-bell-slash"></i><p>No notices posted yet</p></div>
      <div v-for="n in notices" :key="n.id" class="card mb-3 p-4" style="border-left:4px solid #1B2A4A;">
        <div class="d-flex justify-content-between align-items-start">
          <div>
            <div class="d-flex gap-2 mb-2">
              <span class="badge-custom" :class="categoryClass(n.category)">{{ n.category }}</span>
            </div>
            <h6 class="fw-bold mb-1">{{ n.title }}</h6>
            <p class="text-muted mb-2" style="font-size:0.9rem;">{{ n.content }}</p>
            <small class="text-muted"><i class="fas fa-calendar me-1"></i>{{ n.created_at?.slice(0,10) }} · {{ n.published_by_name }}</small>
          </div>
          <button v-if="isAdmin" @click="deleteNotice(n.id)" class="btn btn-sm btn-outline-danger ms-3"><i class="fas fa-trash"></i></button>
        </div>
      </div>
    </div>

    <!-- Post Notice Modal -->
    <div class="modal-overlay" v-if="showAdd" @click.self="closeAdd">
      <div class="modal-box">
        <div class="modal-header">
          <h6 class="mb-0 fw-bold">Post Notice</h6>
          <button @click="closeAdd" class="btn btn-sm btn-light"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div v-if="msg" class="alert-custom alert-error">{{ msg }}</div>
          <div class="form-group"><label class="form-label">Title *</label><input v-model="form.title" class="form-control-custom" placeholder="e.g. Water Shutdown Notice"/></div>
          <div class="form-group">
            <label class="form-label">Message *</label>
            <textarea v-model="form.content" class="form-control-custom" rows="4" placeholder="Write the full announcement here..."></textarea>
          </div>
          <div class="form-group">
            <label class="form-label">Category</label>
            <select v-model="form.category" class="form-control-custom">
              <option>GENERAL</option><option>FINANCIAL</option><option>MAINTENANCE</option><option>EMERGENCY</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeAdd" class="btn btn-light">Cancel</button>
          <button @click="postNotice" class="btn-primary-custom" :disabled="saving">
            <span v-if="saving"><i class="fas fa-spinner fa-spin me-1"></i></span>Post Notice
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { noticesAPI, errText } from '../api/index'
import { authStore } from '../store/auth'

const notices = ref([])
const loading = ref(true)
const saving = ref(false)
const msg = ref('')
const showAdd = ref(false)
const isAdmin = authStore.isAdmin
const blankForm = () => ({ title:'', content:'', category:'GENERAL' })
const form = ref(blankForm())

onMounted(async () => {
  try {
    const res = await noticesAPI.getAll()
    notices.value = Array.isArray(res.data) ? res.data : []
  } catch(e) { msg.value = errText(e) }
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

async function postNotice() {
  if (saving.value) return
  // The backend rejects a blank title/content; without this the button just
  // flashed and nothing was posted.
  const title = form.value.title.trim()
  const content = form.value.content.trim()
  if (!title) { msg.value = 'Title is required.'; return }
  if (!content) { msg.value = 'Message is required.'; return }

  saving.value = true
  msg.value = ''
  try {
    const res = await noticesAPI.add({ ...form.value, title, content })
    notices.value.unshift(res.data)
    showAdd.value = false
    form.value = blankForm()
  } catch(e) { msg.value = errText(e) }
  saving.value = false
}

async function deleteNotice(id) {
  if (!confirm('Remove this notice? This cannot be undone.')) return
  msg.value = ''
  try {
    await noticesAPI.delete(id)
    notices.value = notices.value.filter(n => n.id !== id)
  } catch(e) { msg.value = errText(e) }
}

function categoryClass(cat) {
  return { EMERGENCY:'badge-urgent', FINANCIAL:'badge-open', MAINTENANCE:'badge-medium', GENERAL:'badge-low' }[cat] || 'badge-low'
}
</script>
