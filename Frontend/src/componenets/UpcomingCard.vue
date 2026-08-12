<template>
  <div class="card">
    <div class="card-header-custom">📅 Upcoming</div>
    <div v-if="loading" class="p-4 text-muted" style="font-size:0.85rem;">Loading…</div>
    <div v-else-if="items.length===0" class="empty-state p-4">
      <i class="fas fa-check-circle" style="color:#0E7C7B;"></i><p>Nothing coming up</p>
    </div>
    <div v-else>
      <div v-for="(item, i) in items" :key="i" class="p-3" style="border-bottom:1px solid #f1f5f9;">
        <div class="d-flex justify-content-between align-items-center gap-2">
          <div>
            <div style="font-size:0.9rem;font-weight:600;">{{ item.title }}</div>
            <small class="text-muted">{{ formatDate(item.date) }}</small>
          </div>
          <span class="badge-custom" :class="severityBadge(item.severity)">{{ dueLabel(item.days_until) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { eventsAPI } from '../api/index'
import { formatDate, dueLabel, severityBadge } from '../utils/format'

const props = defineProps({ limit: { type: Number, default: 5 }, days: { type: Number, default: 30 } })

const items = ref([])
const loading = ref(true)

onMounted(async () => {
  // A dashboard widget: a failure here (e.g. offline) should not block the
  // rest of the dashboard from rendering, so it fails quietly rather than
  // surfacing a page-level error banner — same pattern already used for the
  // optional worker dropdown on ComplaintsPage.
  try {
    const res = await eventsAPI.upcoming(props.days)
    items.value = (res.data || []).slice(0, props.limit)
  } catch (e) { /* optional widget */ }
  loading.value = false
})
</script>
