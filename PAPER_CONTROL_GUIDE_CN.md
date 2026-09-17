# Paper Control Center 使用说明

这个控制中心用于独立管理两件事：

- **Deep GEO**：是否在永久论文页面显示增强语义内容。
- **Homepage Featured**：是否出现在首页 Featured Research，以及显示顺序。

关闭任一开关都不会删除论文的永久 HTML/Markdown 页面。关闭 Deep GEO 也不会删除已经保存的增强内容。

## 操作路径

1. 打开 GitHub 仓库 `DrZoggg/Ge-Zhang.github.io`。
2. 点击 **Actions**。
3. 左侧选择 **Paper Control Center**。
4. 点击右侧 **Run workflow**。
5. 在 **Paper** 中输入论文标识。批量操作时每行一个 DOI / exact slug / exact title；也接受逗号分隔。
   单篇模式仍兼容 unique title substring；如果匹配不唯一会安全失败。
6. 按需要选择 **Deep GEO** 和 **Homepage Featured**。
7. Featured position 从 1 开始；留空时，新加入的论文排在最后。
8. 点击绿色 **Run workflow**。
9. 打开本次运行，在 Summary 中查看论文、前后状态、验证结果和是否触发部署。

## 示例

要把 DOI `10.1038/s41698-026-01699-1` 开启 Deep GEO，并放到首页第一位：

- Paper：`10.1038/s41698-026-01699-1`
- Deep GEO：`enable`
- Homepage Featured：`add`
- Featured position：`1`
- Featured summary：可留空，也可填写已经核实过的简介

批量开启 Deep GEO（本期批量模式只控制 Deep GEO）：

- Paper：每行粘贴一个 DOI，也可用逗号分隔
- Deep GEO：`enable`
- Homepage Featured：必须选择 `no_change`
- Featured position / summary：必须留空

```text
10.1038/xxxx
10.1002/xxxx
10.1016/xxxx
```

## 安全规则

- 已经开启的功能再次开启，会成功结束，但不产生 commit 或 Pages 部署。
- 模糊标题匹配到多篇时会失败并列出候选，不会猜测。
- 批量操作会先验证全部输入；任意一项不存在、匹配多篇或属于 withdrawn，整批都不会修改。
- 批量输入会去除空行和重复项；一次运行只 build、validate、commit 和部署一次。
- 批量模式不能同时修改 Featured；Featured 的增加、删除、排序和简介继续使用单篇模式。
- withdrawn 记录不能开启 Deep GEO，也不能加入 Featured。
- 新 Deep GEO 没有内容源时只生成保守的 metadata starter，不生成样本量、P 值、机制或研究结论。
- `disable` 只关闭展示；原 Deep GEO 内容文件永久保留，以便以后重新启用。
