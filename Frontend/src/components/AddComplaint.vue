<template>
  <div class="add-ann-wrapper">
    <AssociationNavBar />
    <div class="form-card">
      <h2>Add Complaint</h2>
      <form @submit.prevent="submit">
        <label>Title</label>
        <input v-model="title" type="text" placeholder="Complaint title" required />

        <label>Category</label>
        <select v-model="category">
          <option value="PLUMBING">Plumbing</option>
          <option value="ELECTRICAL">Electrical</option>
          <option value="CLEANING">Cleaning</option>
          <option value="SECURITY">Security</option>
          <option value="OTHER">Other</option>
        </select>

        <label>Priority</label>
        <select v-model="priority">
          <option value="LOW">Low</option>
          <option value="MEDIUM">Medium</option>
          <option value="HIGH">High</option>
        </select>

        <label>Flat / Apartment</label>
        <select v-model="apartmentId">
          <option disabled value="">Select apartment</option>
          <option v-for="apt in apartments" :key="apt.id" :value="apt.id">{{ apt.flat_number }} · Block {{ apt.block || 'N/A' }} · Floor {{ apt.floor || 'N/A' }}</option>
        </select>

        <label>Description</label>
        <textarea v-model="description" rows="6" placeholder="Describe the issue" required></textarea>

        <div class="form-actions">
          <button type="button" class="btn-cancel" @click="cancel">Cancel</button>
          <button type="submit" class="btn-submit">Create</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import AssociationNavBar from './AssociationNavBar.vue'
import { getApiBase, getAuthHeader } from '../utils/auth'

const router = useRouter()
const title = ref('')
const description = ref('')
const category = ref('PLUMBING')
const priority = ref('MEDIUM')
const apartmentId = ref('')
const apartments = ref([])
const API_BASE = getApiBase()

onMounted(async () => {
  await loadApartments()
})

async function loadApartments() {
  try {
    const auth = getAuthHeader()
    if (!auth.Authorization) { router.push('/login'); return }
    const resp = await axios.get(`${API_BASE}/api/members/apartments`, { headers: auth })
    apartments.value = resp.data || []
  } catch (err) {
    console.error('Failed to load apartments', err)
    apartments.value = []
  }
}

async function submit() {
  if (!title.value.trim() || !description.value.trim() || !apartmentId.value) return alert('Title, description and apartment are required')
  try {
    const auth = getAuthHeader()
    if (!auth.Authorization) { router.push('/login'); return }
    const payload = { title: title.value, description: description.value, category: category.value, priority: priority.value, apartment_id: apartmentId.value }
    await axios.post(`${API_BASE}/api/complaints/`, payload, { headers: auth })
    router.push('/complaints')
  } catch (err) {
    console.error('Failed to create complaint', err)
    alert('Failed to create complaint')
  }
}

function cancel() { router.back() }
</script>

<style scoped>
* { box-sizing: border-box; margin:0; padding:0 }
.add-ann-wrapper { min-height:100vh; background: radial-gradient(circle at top center, #f7fbff 0%, #f2f7ff 45%, #eef4ff 100%); padding-bottom:2rem }
.form-card { max-width:820px; margin:2rem auto; background:#ffffff; padding:2rem; border-radius:2rem; box-shadow:0 10px 30px rgba(132,170,210,0.08); overflow:hidden }
.form-card h2 { margin-bottom:0.6rem; color:#000000; font-weight:800 }
label { display:block; margin-top:0.9rem; color:#264863; font-weight:700 }
input[type="text"], textarea, select { width:100%; padding:0.75rem 0.9rem; margin-top:0.45rem; border-radius:12px; border:1px solid rgba(129,167,210,0.18); background:#f8fbff;color:black }
.form-actions { display:flex; justify-content:flex-end; gap:0.75rem; margin-top:1.25rem }
.btn-cancel { background:white; border:1px solid rgba(129,167,210,0.18); padding:0.55rem 0.95rem; border-radius:12px; cursor:pointer; font-weight:700;color:black }
.btn-submit { background: linear-gradient(90deg,#2b7ef7,#0b63e6); color:white; border:none; padding:0.55rem 0.95rem; border-radius:12px; cursor:pointer; font-weight:800 }

@media (max-width: 768px) {
  .form-card { margin:1rem; padding:1rem }
  input[type="text"], textarea, select { padding:0.6rem }
}
</style>