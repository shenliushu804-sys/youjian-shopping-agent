<template>
  <text :class="['platform-badge', pClass]">{{ label }}</text>
</template>

<script>
export default {
  props: {
    platform: { type: String, default: 'jd' }
  },
  computed: {
    pClass() { return this.platform === 'tmall' ? 'tmall' : 'jd' },
    label() { return this.platform === 'tmall' ? '天猫' : '京东' }
  }
}
</script>

<style lang="scss" scoped>
.platform-badge {
  display: inline-flex;
  align-items: center;
  padding: 1.5px 7px;
  border-radius: 999px;
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: 0.02em;

  &.jd {
    background: $jd-soft;
    color: $jd;
  }

  &.tmall {
    background: $tmall-soft;
    color: $tmall;
  }
}
</style>
