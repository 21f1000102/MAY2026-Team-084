<template>
  <div>
    <div class="d-flex justify-content-end mb-4">
      <button class="btn-primary-custom" @click="calculate" :disabled="calculating">
        <span v-if="calculating"><i class="fas fa-spinner fa-spin me-2"></i>Calculating...</span>
        <span v-else><i class="fas fa-sync me-2"></i>Calculate This Month</span>
      </button>
    </div>

    <div v-if="loading" class="spinner"></div>
    <div v-else>
      <!-- Current Score -->
      <div v-if="current" class="card mb-4 p-4">
        <div class="row align-items-center">
          <div class="col-md-4 text-center">
            <div class="score-circle" :style="`background:${scoreColor(current.grade)};`">
              <div>{{ current.total_score }}</div>
              <div style="font-size:0.9rem;font-weight:400;">/100</div>
            </div>
            <h5 class="mt-3 fw-bold">{{ current.month }}/{{ current.year }}</h5>
            <span class="badge-custom" :class="`badge-${current.grade.toLowerCase()}`">{{ current.grade }}</span>
          </div>
          <div class="col-md-8">
            <h6 class="fw-bold mb-3">Score Breakdown</h6>
            <div v-for="item in breakdown(current)" :key="item.label" class="mb-3">
              <div class="d-flex justify-content-between mb-1" style="font-size:0.85rem;">
                <span>{{ item.label }}</span>
                <span class="fw-semibold">{{ item.score }} / {{ item.max }}</span>
              </div>
              <div class="progress-bar-custom">
                <div class="progress-fill" :style="`width:${(item.score/item.max)*100}%;background:#1B2A4A;`"></div>
              </div>
            </div>
            <div v-if="current.alert_reason" class="alert-custom alert-info mt-3">
              <i class="fas fa-info-circle me-2"></i>{{ current.alert_reason }}
            </div>
          </div>
        </div>
      </div>

      <!-- History -->
      <div class="card p-4" v-if="history.length > 0">
        <h6 class="fw-bold mb-3">📈 6-Month Trend</h6>
        <table class="table-custom">
          <thead><tr><th>Month</th><th>Year</th><th>Score</th><th>Grade</th><th>Alert</th></tr></thead>
          <tbody>
            <tr v-for="s in history" :key="s.id">
              <td>{{ s.month }}</td>
              <td>{{ s.year }}</td>
              <td><strong>{{ s.total_score }}/100</strong></td>
              <td><span class="badge-custom" :class="`badge-${s.grade.toLowerCase()}`">{{ s.grade }}</span></td>
              <td style="font-size:0.8rem;color:#718096;">{{ s.alert_reason }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="!current && history.length === 0" class="empty-state card p-4">
        <i class="fas fa-heartbeat"></i>
        <p>No health scores calculated yet. Click "Calculate This Month" to start.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { healthAPI } from '../api/index'

const current = ref(null)
const history = ref([])
const loading = ref(true)
const calculating = ref(false)

onMounted(async () => {
  try { history.value = (await healthAPI.history()).data } catch(e) {}
  if (history.value.length > 0) current.value = history.value[0]
  loading.value = false
})

async function calculate() {
  calculating.value = true
  try {
    const now = new Date()
    const res = await healthAPI.calculate(now.getMonth()+1, now.getFullYear())
    current.value = res.data
    const h = await healthAPI.history()
    history.value = h.data
  } catch(e) {}
  calculating.value = false
}

function scoreColor(grade) {
  return { GREEN:'#0E7C7B', YELLOW:'#d97706', RED:'#dc2626' }[grade] || '#1B2A4A'
}

function breakdown(s) {
  return [
    { label:'💰 Payment Collection', score: s.payment_score, max: 30 },
    { label:'🔧 Complaint Resolution', score: s.complaint_score, max: 25 },
    { label:'📢 Notice Engagement', score: s.notice_score, max: 15 },
    { label:'🗳️ Poll Participation', score: s.poll_score, max: 15 },
    { label:'⚙️ Maintenance On-Time', score: s.maintenance_score, max: 15 },
  ]
}
</script>
