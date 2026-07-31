<template>
  <div class="admin-wrapper">
    <AssociationNavBar />

    <div class="admin-container">
      <div class="announcement-card">
          <div class="card-header">
            <h2 class="card-title">Announcements</h2>
            <button class="btn-add" @click="addAnnouncement">Add announcement</button>
          </div>
        <div class="card-body">
          <div v-if="loading" class="empty-state">Loading announcements…</div>
          <div v-else>
            <div v-if="announcements.length === 0" class="empty-state">No announcements found</div>
            <div v-else class="announcement-list">
              <div class="table-wrap">
                <table class="announcement-table">
                  <thead>
                    <tr>
                      <th>Title</th>
                      <th>Content</th>
                      <th>Category</th>
                      <th>Date</th>
                      <th>Status</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="a in announcements" :key="a.id" class="announcement-row">
                      <td class="td-title">{{ a.title }}</td>
                      <td class="td-content">{{ (a.content && a.content.length > 120) ? (a.content.slice(0,120) + '…') : a.content }}</td>
                      <td class="td-category">{{ a.category }}</td>
                      <td class="td-date">{{ formatDateLocal(a.created_at) }}</td>
                      <td class="td-status">{{ a.is_active ? 'Active' : 'Inactive' }}</td>
                      <td class="td-actions">
                        <button class="btn-modify" @click="modifyAnnouncement(a)">Modify</button>
                        <button class="btn-delete" @click="deleteAnnouncement(a)">Delete</button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
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
const announcements = ref([])
const loading = ref(true)
const API_BASE = getApiBase()

onMounted(async () => {
  await fetchAnnouncements()
})

async function fetchAnnouncements() {
  try {
    const auth = getAuthHeader()
    if (!auth.Authorization) { router.push('/login'); return }
    const resp = await axios.get(`${API_BASE}/api/notices/`, { headers: auth })
    announcements.value = resp.data || []
  } catch (err) {
    console.error('Failed to fetch announcements:', err)
    announcements.value = []
  } finally {
    loading.value = false
  }
}

function formatDateLocal(dateStr) {
  const date = new Date(dateStr)
  return date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

async function addAnnouncement() {
  router.push('/add-announcement')
}

function modifyAnnouncement(a) {
  router.push(`/edit-announcement/${a.id}`)
}

async function deleteAnnouncement(a) {
  if (!confirm('Delete this announcement?')) return
  try {
    const auth = getAuthHeader()
    if (!auth.Authorization) { router.push('/login'); return }
    await axios.delete(`${API_BASE}/api/notices/${a.id}`, { headers: auth })
    await fetchAnnouncements()
  } catch (err) {
    console.error('Failed to delete announcement:', err)
    alert('Failed to delete announcement')
  }
}


</script>

<style scoped>
* { box-sizing: border-box; margin:0; padding:0 }

.admin-wrapper {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: radial-gradient(circle at top center, #f7fbff 0%, #f2f7ff 45%, #eef4ff 100%);
}

.admin-container {
  max-width: 2000px;
  margin: 1.5rem auto;
  padding: 1rem;
}

.announcement-card {
  background: #ffffff;
  max-width: 100%;
  border-radius: 1.25rem;
  box-shadow: 0 12px 40px rgba(0,0,0,0.06);
  overflow: hidden;
  width: 90vw;
  max-width: none;
  margin: 1.5rem auto;
}

.announcement-card .card-header {
  padding: 1.25rem 1.5rem;
  background: linear-gradient(145deg, #e5f2ff 0%, #d6e8ff 100%);
  border-bottom: 1px solid rgba(34,49,63,0.04);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.card-title { font-size:1.4rem; font-weight:800; color:#0f2540 }

.card-body { padding: 1.75rem 2rem }

.announcement-list { display:flex; flex-direction:column; gap:1rem }
.announcement-item { background:#fbfdff; padding:1.25rem; border-radius:14px; box-shadow:0 10px 28px rgba(34,49,63,0.04); display:block }
.ann-title { font-size:1.15rem; font-weight:800; color:#0f2540; margin-bottom:0.25rem }
.ann-meta { font-size:0.9rem; color:#556c86; margin-bottom:0.5rem }
.ann-content { color:#2b3b4a; line-height:1.6; margin-top:0.5rem }

.ann-top { display:flex; align-items:flex-start; justify-content:space-between; gap:1rem }
.ann-actions { display:flex; gap:0.5rem }
.btn-add {
  background: linear-gradient(90deg,#2b7ef7,#0b63e6);
  color: white;
  border: none;
  padding: 0.5rem 0.9rem;
  border-radius: 8px;
  font-weight:700;
  cursor: pointer;
}
.btn-modify, .btn-delete {
  padding: 0.35rem 0.6rem;
  border-radius: 8px;
  font-weight:700;
  cursor: pointer;
  border: 1px solid rgba(15,37,64,0.08);
  background: white;
  color: #0f2540;
}
.btn-delete { border-color: rgba(220,38,38,0.12); color: #c53030 }

.table-wrap { overflow-x:auto }
.announcement-table { width:100%; border-collapse: collapse; min-width: 800px }
.announcement-table thead th { text-align:left; padding:0.9rem 1rem; background:#f5f9ff; color:#0f2540; font-weight:800; border-bottom:1px solid rgba(34,49,63,0.06) }
.announcement-table tbody td { padding:0.85rem 1rem; border-bottom:1px solid rgba(34,49,63,0.04); vertical-align:top }
.td-title { font-weight:700; color:#0f2540 }
.td-content { color:#2b3b4a }
.td-category { color:#475b71; font-weight:600 }
.td-date { color:#556c86 }
.td-status { font-weight:700 }
.td-actions { display:flex; gap:0.5rem }

@media (max-width: 768px) {
  .announcement-table { min-width: 640px }
  .td-content { max-width: 220px; white-space:normal }
}


.empty-state { text-align:center; padding:1.5rem; color:#6d7b86; font-style:italic; background:#fbfdff; border-radius:12px }

@media (max-width: 768px) {
  .admin-container { margin:1rem; padding:0.75rem }
  .card-title { font-size:1.2rem }
}
</style>
