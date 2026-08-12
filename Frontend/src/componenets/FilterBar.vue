<template>
  <div class="card p-3 mb-3">
    <div class="d-flex flex-wrap gap-2 align-items-end">
      <div v-for="f in fields" :key="f.key" class="form-group mb-0" style="min-width:150px;flex:1 1 150px;">
        <label class="form-label" v-if="f.label">{{ f.label }}</label>

        <select v-if="f.type === 'select'" v-model="model[f.key]" class="form-control-custom">
          <option value="">{{ f.placeholder || 'All' }}</option>
          <option v-for="opt in f.options" :key="opt.value ?? opt" :value="opt.value ?? opt">
            {{ opt.label ?? opt }}
          </option>
        </select>

        <input v-else-if="f.type === 'date'" type="date" v-model="model[f.key]" class="form-control-custom" />

        <input v-else-if="f.type === 'number'" type="number" v-model="model[f.key]"
              class="form-control-custom" :placeholder="f.placeholder" />

        <input v-else type="text" v-model="model[f.key]" class="form-control-custom"
              :placeholder="f.placeholder || 'Search...'" />
      </div>

      <button v-if="hasActive" class="btn btn-light btn-sm" @click="clearAll">
        <i class="fas fa-times me-1"></i>Clear filters
      </button>

      <div v-if="resultCount !== null" class="text-muted ms-auto" style="font-size:0.85rem;white-space:nowrap;">
        {{ resultCount }} result{{ resultCount === 1 ? '' : 's' }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, computed, watch, onBeforeUnmount } from 'vue'

const props = defineProps({
  // [{ key, label, type: 'text'|'select'|'date'|'number', options, placeholder }]
  fields: { type: Array, required: true },
  resultCount: { type: Number, default: null },
  debounceMs: { type: Number, default: 300 },
})

const emit = defineEmits(['change'])

const model = reactive({})
props.fields.forEach(f => { model[f.key] = '' })

const hasActive = computed(() => Object.values(model).some(v => v !== '' && v !== null))

function cleanParams() {
  const out = {}
  for (const [k, v] of Object.entries(model)) {
    if (v !== '' && v !== null && v !== undefined) out[k] = v
  }
  return out
}

let timer = null
onBeforeUnmount(() => clearTimeout(timer))

watch(model, () => {
  clearTimeout(timer)
  timer = setTimeout(() => emit('change', cleanParams()), props.debounceMs)
}, { deep: true })

function clearAll() {
  clearTimeout(timer)
  Object.keys(model).forEach(k => { model[k] = '' })
  emit('change', {})
}
</script>
