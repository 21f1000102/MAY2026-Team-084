<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <div>
        <input v-model="search" class="form-control-custom" placeholder="🔍 Search by name or flat..." style="width:260px;display:inline-block;"/>
      </div>
      <button class="btn-primary-custom" @click="showAdd=true"><i class="fas fa-user-plus me-2"></i>Add Member</button>
    </div>

    <div v-if="loading" class="spinner"></div>
    <div v-else class="card">
      <div v-if="filtered.length===0" class="empty-state"><i class="fas fa-users"></i><p>No members found</p></div>
      <table v-else class="table-custom">
        <thead>
          <tr><th>Name</th><th>Flat</th><th>Role</th><th>Type</th><th>Phone</th><th>Status</th><th>Actions</th></tr>
        </thead>
        <tbody>
          <tr v-for="m in filtered" :key="m.id">
            <td><strong>{{ m.name }}</strong><br><small class="text-muted">{{ m.email }}</small></td>
            <td>{{ m.flat_number }}</td>
            <td>{{ m.role }}</td>
            <td><span class="badge-custom" :class="m.is_owner ? 'badge-open' : 'badge-medium'">{{ m.is_owner ? 'Owner' : 'Tenant' }}</span></td>
            <td>{{ m.phone }}</td>
            <td><span class="badge-custom" :class="m.is_active ? 'badge-paid' : 'badge-unpaid'">{{ m.is_active ? 'Active' : 'Inactive' }}</span></td>
            <td>
              <button class="btn btn-sm btn-outline-danger" @click="deactivate(m.id)">
                <i class="fas fa-ban"></i>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Add Member Modal -->
    <div class="modal-overlay" v-if="showAdd" @click.self="showAdd=false">
      <div class="modal-box">
        <div class="modal-header">
          <h6 class="mb-0 fw-bold">Add New Member</h6>
          <button @click="showAdd=false" class="btn btn-sm btn-light"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div v-if="msg" class="alert-custom" :class="msg.type==='error'?'alert-error':'alert-success'">{{ msg.text }}</div>
          <div class="form-group"><label class="form-label">Full Name *</label><input v-model="form.name" class="form-control-custom" placeholder="Ravi Kumar"/></div>
          <div class="form-group"><label class="form-label">Email *</label><input v-model="form.email" type="email" class="form-control-custom"/></div>
          <div class="form-group"><label class="form-label">Phone</label><input v-model="form.phone" class="form-control-custom"/></div>
          <div class="form-group"><label class="form-label">Password *</label><input v-model="form.password" type="password" class="form-control-custom"/></div>
          <div class="form-group">
            <label class="form-label">Role *</label>
            <select v-model="form.role" class="form-control-custom">
              <option value="TENANT">Tenant</option>
              <option value="OWNER">Owner</option>
              <option value="WORKER">Worker</option>
              <option value="TREASURER">Treasurer</option>
              <option value="COMMITTEE_MEMBER">Committee Member</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Apartment *</label>
            <select v-model="form.apartment_id" class="form-control-custom">
              <option value="">Select Flat</option>
              <option v-for="a in apartments" :key="a.id" :value="a.id">{{ a.flat_number }} ({{ a.block }})</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Is Owner?</label>
            <select v-model="form.is_owner" class="form-control-custom">
              <option :value="false">No (Tenant)</option>
              <option :value="true">Yes (Owner)</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showAdd=false" class="btn btn-light">Cancel</button>
          <button @click="addMember" class="btn-primary-custom" :disabled="saving">
            <span v-if="saving"><i class="fas fa-spinner fa-spin me-1"></i>Saving...</span>
            <span v-else>Add Member</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { membersAPI } from '../api/index'

const members = ref([])
const apartments = ref([])
const loading = ref(true)
const showAdd = ref(false)
const saving = ref(false)
const search = ref('')
const msg = ref(null)
const form = ref({ name:'', email:'', phone:'', password:'', role:'TENANT', apartment_id:'', is_owner:false })

const filtered = computed(() =>
  members.value.filter(m =>
    m.name.toLowerCase().includes(search.value.toLowerCase()) ||
    m.flat_number?.toLowerCase().includes(search.value.toLowerCase())
  )
)

onMounted(async () => {
  try {
    const [m, a] = await Promise.all([membersAPI.getAll(), membersAPI.getApartments()])
    members.value = m.data
    apartments.value = a.data
  } catch(e) {}
  loading.value = false
})

async function addMember() {
  saving.value = true
  msg.value = null
  try {
    const res = await membersAPI.add(form.value)
    members.value.push(res.data)
    showAdd.value = false
    form.value = { name:'', email:'', phone:'', password:'', role:'TENANT', apartment_id:'', is_owner:false }
  } catch(e) {
    msg.value = { type:'error', text: e.response?.data?.error || 'Failed to add member' }
  }
  saving.value = false
}

async function deactivate(id) {
  if (!confirm('Deactivate this member?')) return
  try {
    await membersAPI.deactivate(id)
    members.value = members.value.map(m => m.id===id ? {...m, is_active:false} : m)
  } catch(e) {}
}
</script>
