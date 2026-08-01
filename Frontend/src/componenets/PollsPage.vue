<template>
  <div>
    <div v-if="msg && !showAdd" class="alert-custom alert-error">{{ msg }}</div>

    <div class="d-flex justify-content-end mb-4" v-if="isAdmin">
      <button class="btn-primary-custom" @click="openAdd"><i class="fas fa-plus me-2"></i>Create Poll</button>
    </div>
    <div v-if="loading" class="spinner"></div>
    <div v-else>
      <div v-if="polls.length===0" class="empty-state card p-4"><i class="fas fa-poll"></i><p>No polls yet</p></div>
      <div v-for="p in polls" :key="p.id" class="card mb-4 p-4">
        <div class="d-flex justify-content-between align-items-start mb-3">
          <div>
            <span class="badge-custom me-2" :class="p.status==='ACTIVE'?'badge-paid':'badge-low'">{{ p.status }}</span>
            <h6 class="fw-bold mt-2 mb-1">{{ p.title }}</h6>
            <p class="text-muted mb-0" style="font-size:0.875rem;">{{ p.description }}</p>
          </div>
          <button v-if="isAdmin && p.status==='ACTIVE'" @click="closePoll(p.id)" class="btn btn-sm btn-outline-secondary">Close</button>
        </div>

        <!-- Options -->
        <div v-for="opt in p.options" :key="opt.id" class="mb-3">
          <div class="d-flex justify-content-between align-items-center mb-1">
            <button v-if="p.status==='ACTIVE' && !hasVoted(p)" @click="castVote(p.id, opt.id)"
              :disabled="voting" class="btn btn-sm btn-outline-primary">{{ opt.text }}</button>
            <span v-else class="fw-semibold" style="font-size:0.9rem;">{{ opt.text }}</span>
            <span class="text-muted" style="font-size:0.8rem;">{{ opt.votes }} votes · {{ opt.percentage }}%</span>
          </div>
          <div class="progress-bar-custom">
            <div class="progress-fill" :style="`width:${opt.percentage}%;background:#1B2A4A;`"></div>
          </div>
        </div>

        <small class="text-muted"><i class="fas fa-users me-1"></i>{{ p.total_votes }} total votes · Created {{ p.created_at?.slice(0,10) }}</small>
      </div>
    </div>

    <!-- Create Poll Modal -->
    <div class="modal-overlay" v-if="showAdd" @click.self="closeAdd">
      <div class="modal-box">
        <div class="modal-header">
          <h6 class="mb-0 fw-bold">Create Poll</h6>
          <button @click="closeAdd" class="btn btn-sm btn-light"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
          <div v-if="msg" class="alert-custom alert-error">{{ msg }}</div>
          <div class="form-group"><label class="form-label">Question *</label><input v-model="form.title" class="form-control-custom" placeholder="e.g. Should we get AMC for generator?"/></div>
          <div class="form-group"><label class="form-label">Description</label><textarea v-model="form.description" class="form-control-custom" rows="2"></textarea></div>
          <div class="form-group">
            <label class="form-label">Options (min 2)</label>
            <div v-for="(opt,i) in form.options" :key="i" class="d-flex gap-2 mb-2">
              <input v-model="form.options[i]" class="form-control-custom" :placeholder="`Option ${i+1}`"/>
              <button v-if="i>1" @click="form.options.splice(i,1)" class="btn btn-sm btn-outline-danger"><i class="fas fa-times"></i></button>
            </div>
            <button @click="form.options.push('')" class="btn btn-sm btn-outline-primary mt-1"><i class="fas fa-plus me-1"></i>Add Option</button>
          </div>
          <div class="form-group"><label class="form-label">Start Date *</label><input v-model="form.start_date" type="date" class="form-control-custom"/></div>
          <div class="form-group"><label class="form-label">End Date *</label><input v-model="form.end_date" type="date" class="form-control-custom"/></div>
        </div>
        <div class="modal-footer">
          <button @click="closeAdd" class="btn btn-light">Cancel</button>
          <button @click="createPoll" class="btn-primary-custom" :disabled="saving">
            <span v-if="saving"><i class="fas fa-spinner fa-spin me-1"></i></span>Create Poll
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { pollsAPI, errText } from '../api/index'
import { orNull, today } from '../utils/format'
import { authStore } from '../store/auth'

const emptyForm = () => ({ title:'', description:'', options:['',''], start_date: today(), end_date:'' })

const polls = ref([])
const loading = ref(true)
const saving = ref(false)
const voting = ref(false)
const showAdd = ref(false)
const isAdmin = authStore.isAdmin
const msg = ref('')
const form = ref(emptyForm())
// Optimistic fallback only — `has_voted` from the API is the source of truth,
// this object used to be the only lock and reset on every page reload.
const myVotes = ref({})

onMounted(async () => {
  try { polls.value = (await pollsAPI.getAll()).data }
  catch(e) { msg.value = errText(e) }
  loading.value = false
})

function hasVoted(p) { return p.has_voted === true || !!myVotes.value[p.id] }

function openAdd() { msg.value = ''; showAdd.value = true }
function closeAdd() { msg.value = ''; showAdd.value = false }

async function castVote(pollId, optionId) {
  if (voting.value) return
  voting.value = true
  msg.value = ''
  try {
    const res = await pollsAPI.vote(pollId, { option_id: optionId })
    myVotes.value[pollId] = optionId
    const idx = polls.value.findIndex(p => p.id === pollId)
    if (idx > -1) polls.value[idx] = res.data.poll
  } catch(e) { msg.value = errText(e) }
  voting.value = false
}

async function closePoll(id) {
  if (!confirm('Close this poll? Members will no longer be able to vote.')) return
  msg.value = ''
  try {
    const res = await pollsAPI.close(id)
    const idx = polls.value.findIndex(p => p.id === id)
    if (idx > -1) polls.value[idx] = res.data.poll
  } catch(e) { msg.value = errText(e) }
}

async function createPoll() {
  if (saving.value) return
  msg.value = ''

  const title = String(form.value.title || '').trim()
  if (!title) { msg.value = 'Question is required.'; return }

  const options = form.value.options.map(o => String(o || '').trim()).filter(Boolean)
  if (options.length < 2) { msg.value = 'Please enter at least 2 non-empty options.'; return }

  // Both dates are NOT NULL on the backend; the form used to send neither.
  const start_date = orNull(form.value.start_date) || today()
  const end_date = orNull(form.value.end_date)
  if (!end_date) { msg.value = 'End date is required.'; return }
  if (end_date < start_date) { msg.value = 'End date cannot be before the start date.'; return }

  saving.value = true
  try {
    const res = await pollsAPI.create({
      title,
      description: orNull(form.value.description),
      options,
      start_date,
      end_date
    })
    polls.value.unshift(res.data)
    form.value = emptyForm()
    showAdd.value = false
  } catch(e) { msg.value = errText(e) }
  saving.value = false
}
</script>
