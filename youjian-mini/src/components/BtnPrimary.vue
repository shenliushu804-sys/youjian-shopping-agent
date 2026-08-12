<template>
  <button class="btn-primary" :disabled="disabled" @tap="$emit('tap')">
    <text>{{ label }}</text>
  </button>
</template>

<script>
export default {
  props: {
    label: { type: String, default: '确认' },
    disabled: { type: Boolean, default: false }
  },
  emits: ['tap']
}
</script>

<style lang="scss" scoped>
.btn-primary {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 48px;
  padding: 12px 20px;
  background: $btn-bg;
  color: $btn-fg;
  border: 0;
  border-radius: $radius;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.01em;

  &[disabled] {
    opacity: 0.4;
  }
}
</style>
