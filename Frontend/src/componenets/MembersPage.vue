<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <div>
        <input v-model="search" class="form-control-custom" placeholder="🔍 Search by name or flat..." style="width:100%;max-width:260px;display:inline-block;"/>
      </div>
      <div class="d-flex gap-2">
        <button class="btn-accent" @click="openApt"><i class="fas fa-building me-2"></i>Add Flat</button>
        <button class="btn-primary-custom" @click="openAdd"><i class="fas fa-user-plus me-2"></i>Add Member</button>
      </div>
    </div>

    <div v-if="pageMsg" class="alert-custom alert-error">{{ pageMsg }}</div>
    <div v-if="apartments.length===0 && !loading" class="alert-custom alert-info">
      No flats exist yet. Add a flat first — members, complaints and invoices all attach to one.
    </div>

    <div v-if="loading" class="spinner"></div>
    <div v-else class="card">
      <div v-if="filtered.length===0" class="empty-state"><i class="fas fa-users"></i><p>No members found</p></div>
      <div v-else class="table-responsive">
      <table class="table-custom">
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

    <!-- Add Flat Modal -->
    <div class="modal-overlay" v-if="showApt" @click.self="showApt=false">
      <div class="modal-box">
        <div class="modal-header">
          <h6 class="mb-0 fw-bold">Add Flat</h6>
          <button @click="showApt=false" class="btn btn-sm btn-light"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div v-if="aptMsg" class="alert-custom alert-error">{{ aptMsg }}</div>
          <div class="form-group"><label class="form-label">Flat Number *</label><input v-model="aptForm.flat_number" class="form-control-custom" placeholder="e.g. A-101"/></div>
          <div class="form-group"><label class="form-label">Block</label><input v-model="aptForm.block" class="form-control-custom" placeholder="e.g. A"/></div>
          <div class="form-group"><label class="form-label">Floor</label><input v-model="aptForm.floor" type="number" class="form-control-custom" placeholder="e.g. 1"/></div>
        </div>
        <div class="modal-footer">
          <button @click="showApt=false" class="btn btn-light">Cancel</button>
          <button @click="addApartment" class="btn-primary-custom" :disabled="savingApt">
            <span v-if="savingApt"><i class="fas fa-spinner fa-spin me-1"></i>Saving...</span>
            <span v-else>Add Flat</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { membersAPI, errText } from '../api/index'
import { orNull } from '../utils/format'

const members = ref([])
const apartments = ref([])
const loading = ref(true)
const showAdd = ref(false)
const showApt = ref(false)
const saving = ref(false)
const savingApt = ref(false)
const search = ref('')
const msg = ref(null)
const pageMsg = ref('')
const aptMsg = ref('')
const emptyForm = () => ({ name:'', email:'', phone:'', password:'', role:'TENANT', apartment_id:'', is_owner:false })
const form = ref(emptyForm())
const aptForm = ref({ flat_number:'', block:'', floor:'' })

const filtered = computed(() =>
  members.value.filter(m =>
    (m.name || '').toLowerCase().includes(search.value.toLowerCase()) ||
    (m.flat_number || '').toLowerCase().includes(search.value.toLowerCase())
  )
)

onMounted(load)

async function load() {
  const [m, a] = await Promise.allSettled([membersAPI.getAll(), membersAPI.getApartments()])
  if (m.status === 'fulfilled') members.value = m.value.data
  else pageMsg.value = errText(m.reason)
  if (a.status === 'fulfilled') apartments.value = a.value.data
  loading.value = false
}

function openAdd() { msg.value = null; form.value = emptyForm(); showAdd.value = true }
function openApt() { aptMsg.value = ''; aptForm.value = { flat_number:'', block:'', floor:'' }; showApt.value = true }

async function addMember() {
  if (!form.value.name?.trim() || !form.value.email?.trim() || !form.value.password) {
    msg.value = { type:'error', text:'Name, email and password are required' }; return
  }
  if (!form.value.apartment_id) { msg.value = { type:'error', text:'Please select a flat' }; return }
  saving.value = true
  msg.value = null
  try {
    const res = await membersAPI.add({ ...form.value, phone: orNull(form.value.phone) })
    members.value.push(res.data)
    showAdd.value = false
    form.value = emptyForm()
  } catch(e) {
    msg.value = { type:'error', text: errText(e) }
  }
  saving.value = false
}

// The API method existed but nothing ever called it, so a fresh install had no
// flats and therefore no way to add members, complaints or invoices.
async function addApartment() {
  if (!aptForm.value.flat_number?.trim()) { aptMsg.value = 'Flat number is required'; return }
  savingApt.value = true
  aptMsg.value = ''
  try {
    const res = await membersAPI.addApartment({
      flat_number: aptForm.value.flat_number.trim(),
      block: orNull(aptForm.value.block),
      floor: orNull(aptForm.value.floor),
    })
    apartments.value.push(res.data)
    showApt.value = false
  } catch(e) { aptMsg.value = errText(e) }
  savingApt.value = false
}

async function deactivate(id) {
  if (!confirm('Deactivate this member?')) return
  pageMsg.value = ''
  try {
    await membersAPI.deactivate(id)
    members.value = members.value.map(m => m.id===id ? {...m, is_active:false} : m)
  } catch(e) { pageMsg.value = errText(e) }
}
</script>
