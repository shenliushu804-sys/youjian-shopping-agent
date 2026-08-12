<template>
  <view class="topbar">
    <view v-if="showBack" class="back-btn" @tap="$emit('back')">
      <text class="back-icon">‹</text>
    </view>
    <view class="titles">
      <text class="title">{{ title }}</text>
      <text v-if="sub" class="sub">{{ sub }}</text>
    </view>
  </view>
</template>

<script>
export default {
  props: {
    title: { type: String, default: '' },
    sub: { type: String, default: '' },
    showBack: { type: Boolean, default: true }
  },
  emits: ['back']
}
</script>

<style lang="scss" scoped>
.topbar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 2px 20px 12px;
}
.back-btn {
  width: 34px;
  height: 34px;
  border-radius: 999px;
  border: 1px solid $border-c;
  background: $surface;
  display: flex;
  align-items: center;
  justify-content: center;
}
.back-icon {
  font-size: 20px;
  color: $fg;
}
.titles {
  flex: 1;
  min-width: 0;
}
.title {
  font-size: $fs-h2;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: $fg;
}
.sub {
  font-size: $fs-meta;
  color: $muted;
  letter-spacing: 0.01em;
  margin-top: 1px;
}
</style>
