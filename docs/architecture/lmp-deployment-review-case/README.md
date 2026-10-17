# LMP 部署架构评审案例（LMP Deployment Review Case）

日期：2026-10-14。状态：**待用户评审**。本轮先交付 LMP 案例，案例通过后再沉淀通用原则和 Skill。

## 评审入口（Review Entry）

打开 [交互评审页面](output/评审.html)。页面可切换三种样式、放大、平移、逐条高亮通信关系，并查看对应原始参考图。选中一条关系后，其协议标签同步高亮。页面内的 drawio、PNG、SVG 链接对应当前样式。

| 版本 | 原生图源 | 预览 | 矢量预览 | 样式参考 |
| --- | --- | --- | --- | --- |
| 目标 1：部署总览 | [drawio](output/LMP-部署架构-目标1-20261014.drawio) | [PNG](output/LMP-部署架构-目标1-20261014.png) | [SVG](output/LMP-部署架构-目标1-20261014.svg) | [原截图](references/originals/reference-1.png) |
| 目标 2：K8S 横向部署 | [drawio](output/LMP-部署架构-目标2-20261014.drawio) | [PNG](output/LMP-部署架构-目标2-20261014.png) | [SVG](output/LMP-部署架构-目标2-20261014.svg) | [原 drawio](references/originals/reference-2.drawio)、[参考预览](references/originals/reference-2-preview.png) |
| 目标 3：云网络布局 | [drawio](output/LMP-部署架构-目标3-20261014.drawio) | [PNG](output/LMP-部署架构-目标3-20261014.png) | [SVG](output/LMP-部署架构-目标3-20261014.svg) | [原 SVG](references/originals/reference-3.drawio.svg)、[参考预览](references/originals/reference-3-preview.png) |

## 事实与核验（Facts and Verification）

三版采用同一份 [项目模型](references/project-model.json)，共 49 条连接。48 条连接显示标签；堡垒机到 TKE 的管理连接按历史确认要求不显示协议和端口。访问链路示意引用同一组部署节点，不增加服务实例。

项目口径以 [20261012 证据说明](references/baseline/部署架构图-20261012.md)、[原图](references/baseline/部署架构图-20261012.drawio) 和 [用户修订要求摘录](references/baseline/修订要求摘录.md) 为锚点。原双向 XXL-JOB 连接拆为注册上报与反向执行器调度两条单向连接，目标端口分别为 30968 和 8090。

查看 [评审说明](评审说明.md) 了解项目要求、样式适配和验收边界。查看 [来源登记](references/source-register.json)、[结构与语义回执](references/validation.json)、[实际导出回执](references/render-receipts.json) 和 [浏览器检查](references/browser-validation.json) 复核本轮结果。客户环境运行和连通性尚未验证。

## 文件职责（File Responsibilities）

- `output/`：交互评审页面及三个单页 drawio、PNG、SVG。
- `references/originals/`：三份参考原件及参考预览。
- `references/baseline/`：LMP 修订基线、历史回执和用户要求摘录。
- `references/case-assets/`：本案例从目标 1 提取的图标及来源、裁切区域、色彩转换记录。
- `references/`：项目模型、来源、哈希、实际导出和检查结果；包含评审页面截图。
- `work/`：本案例固定模型的绘制、导出、检查脚本及局部检查图。脚本包含本机绘图环境依赖，源图与预览可独立查阅。

## 后续安排（Next Step）

请评审项目内容、三个样式的还原效果和信息密度。反馈可注明“目标编号、区域、节点或连接、预期变化”。本轮新增案例资产及 README 导航。通用原则、通用资产库和部署交付 Skill 等待案例评审通过后继续。
