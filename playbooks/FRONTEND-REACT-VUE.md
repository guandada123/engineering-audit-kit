# 前端（React/Vue）审计与优化手册

1. 质量基线
- ESLint + TypeScript strict；Prettier；import/order 与 no-restricted-imports
- 单元测试：Vitest/Jest；组件测试：Testing Library；E2E：Playwright
- 可访问性：eslint-plugin-jsx-a11y / vue-a11y；axe 自动扫描

2. 性能基线
- 分包与路由级代码分割；动态 import 提示 chunkName
- 资源优化：svgo、Image AVIF/WebP、字体显示策略
- 性能预算：LCP<2.5s、CLS<0.1、INP<200ms；CI 中集成 Lighthouse CI

3. 交互与动效（Premium）
- 主题切换：light/dark/system；过渡 200–300ms，cubic-bezier(0.16,1,0.3,1)
- 微交互：磁吸按钮、Hover 3D 倾斜、惯性滚动；低配降级
- Three.js：仅在需要时使用，基于 requestIdleCallback/IntersectionObserver 惰性加载

4. 安全
- DOM XSS 防护：严格 use of dangerouslySetInnerHTML；CSP；依赖审计

5. DevOps
- CI：typecheck + lint + test + build；PR 阶段阻断
- 预览：Preview 环境与 Bundle 分析
