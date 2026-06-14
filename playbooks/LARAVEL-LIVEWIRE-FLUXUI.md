# Laravel + Livewire + FluxUI 审计与优化手册

适用：Laravel 10/11，Livewire v3，FluxUI 组件库。

1. 目录结构与架构
- 模块化：按领域组织 Service、Actions、ViewModels；Blade/Livewire 组件分层
- 服务容器绑定与契约：接口驱动，替换性强
- 配置与环境：.env.example 完整、config 缓存、config() 使用

2. 质量基线
- 静态分析：Larastan（level 6+）、PHP CS Fixer
- 测试：Pest 优先；Feature + Livewire 交互测试；Factories + Seeders
- 安全：CSRF、授权策略、速率限制、CSP、队列重试与幂等

3. 性能优化
- 缓存：Response/Fragment/Repository 层缓存；Cache tags；Redis
- 数据库：N+1 审计（Laravel Debugbar/Telescope/Clockwork）；Eager Load；索引建议
- 前端：FluxUI 组件按需；Alpine 随 Livewire 注入；懒加载

4. 体验与设计（Premium）
- 主题：light/dark/system 切换（FluxUI ThemeSwitch）
- 动效：磁吸按钮、平滑过渡、进入动画（使用 CSS 自定义属性与 prefers-reduced-motion）
- Three.js：英雄区粒子/产品 3D，需要时引入，IntersectionObserver 懒挂载

5. DevOps
- CI：PHPUnit/Pest + Larastan + PHP CS Fixer；Node 构建（Vite）
- 部署：.env 管理、Secrets 扫描；数据库迁移与回滚；Sentry/Datadog 接入

附：常见反模式清单与修复示例见 templates。
