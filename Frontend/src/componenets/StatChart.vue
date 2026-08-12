<template>
  <div class="stat-chart">
    <div v-if="type === 'bar'" class="d-flex flex-column gap-2">
      <div v-if="normalized.length===0" class="text-muted" style="font-size:0.85rem;">No data yet</div>
      <div v-for="d in normalized" :key="d.label" class="d-flex align-items-center gap-2">
        <div style="min-width:110px;font-size:0.8rem;color:#475569;">{{ d.label }}</div>
        <div style="flex:1;background:#f1f5f9;border-radius:6px;overflow:hidden;height:18px;">
          <div :style="{ width: d.pct + '%', background: d.color }" style="height:100%;border-radius:6px;transition:width 0.3s ease;"></div>
        </div>
        <div style="min-width:32px;text-align:right;font-size:0.8rem;font-weight:600;">{{ d.value }}</div>
      </div>
    </div>

    <template v-else-if="type === 'donut'">
      <div v-if="normalized.length===0" class="text-muted text-center" style="font-size:0.85rem;">No data yet</div>
      <svg v-else viewBox="0 0 42 42" style="width:150px;height:150px;display:block;margin:0 auto;" role="img" aria-label="Distribution chart">
        <circle cx="21" cy="21" r="15.9" fill="transparent" stroke="#f1f5f9" stroke-width="6" />
        <circle v-for="seg in donutSegments" :key="seg.label"
               cx="21" cy="21" r="15.9" fill="transparent"
               :stroke="seg.color" stroke-width="6"
               :stroke-dasharray="`${seg.pct} ${100 - seg.pct}`"
               :stroke-dashoffset="seg.offset" />
      </svg>
      <div class="d-flex flex-wrap gap-3 justify-content-center mt-2">
        <div v-for="d in normalized" :key="d.label" style="font-size:0.78rem;display:flex;align-items:center;gap:6px;">
          <span :style="{ width:'10px', height:'10px', borderRadius:'50%', background:d.color, display:'inline-block' }"></span>
          {{ d.label }}: {{ d.value }}
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  type: { type: String, default: 'bar' },      // 'bar' | 'donut'
  data: { type: Array, required: true },        // [{ label, value, color? }]
})

const PALETTE = ['#1B2A4A', '#0E7C7B', '#F2A541', '#dc2626', '#7c3aed', '#0891b2']

const filtered = computed(() => props.data.filter(d => (d.value || 0) > 0 || props.type === 'bar'))

const normalized = computed(() => {
  const max = Math.max(1, ...filtered.value.map(d => d.value || 0))
  return filtered.value.map((d, i) => ({
    ...d,
    color: d.color || PALETTE[i % PALETTE.length],
    pct: props.type === 'bar' ? Math.round(((d.value || 0) / max) * 100) : 0,
  }))
})

// SVG donut trick: circumference of r=15.9 is ~100, so each segment's
// stroke-dasharray can be expressed directly as a percentage. Offset of 25
// rotates the start to 12 o'clock instead of the default 3 o'clock.
const donutSegments = computed(() => {
  const total = filtered.value.reduce((s, d) => s + (d.value || 0), 0) || 1
  let cursor = 0
  return normalized.value.map(d => {
    const pct = ((d.value || 0) / total) * 100
    const seg = { ...d, pct, offset: 25 - cursor }
    cursor += pct
    return seg
  })
})
</script>
