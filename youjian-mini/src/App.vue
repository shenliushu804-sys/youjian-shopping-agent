<script>
export default {
  onLaunch() {
    console.log('优拣 App Launch')
  }
}
</script>

<style>
html, body {
  margin: 0;
  padding: 0;
  overflow-x: hidden;
  background: #e8e8e8;
}

#app {
  max-width: 430px;
  margin: 0 auto;
  overflow: hidden;
  background: #fafafa;
  min-height: 100vh;
  position: relative;
}

page {
  background: #fafafa;
  color: #0d0d0d;
  font-family: -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 14.5px;
  line-height: 1.45;
  -webkit-font-smoothing: antialiased;
  max-width: 100%;
  overflow: hidden;
}

/* ── uni-app H5 容器宽度约束 ── */
uni-page,
uni-page-body,
uni-page-wrapper {
  max-width: 100% !important;
  overflow: hidden !important;
}

uni-scroll-view,
.uni-scroll-view,
.uni-scroll-view-content {
  max-width: 100% !important;
  overflow-x: hidden !important;
  box-sizing: border-box !important;
}

uni-view {
  max-width: 100% !important;
  box-sizing: border-box !important;
}

/* 框架内部带行内 width:400px 的 div — 用属性选择器强制覆盖 */
div[style*="width: 400px"] {
  width: 100% !important;
  max-width: 430px !important;
  height: auto !important;
}

/* 兜底：所有 scroll-view 子 div */
uni-scroll-view > div,
.uni-scroll-view > div,
.uni-scroll-view-content > div {
  max-width: 100% !important;
  width: auto !important;
  box-sizing: border-box !important;
}

#app div {
  max-width: 430px !important;
  box-sizing: border-box !important;
}

.num {
  font-family: ui-monospace, Menlo, monospace;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.01em;
}

.safe-bottom {
  padding-bottom: constant(safe-area-inset-bottom);
  padding-bottom: env(safe-area-inset-bottom);
}
</style>
