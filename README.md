# 拾光集 · 个人日志站点

一个用 Markdown 写的静态个人日志站点。内容分门别类，自动生成精美网页，可免费托管、公开给关心你的人看。

## 目录结构

```
.
├── content/            # 你写的日志（Markdown），按分类存放
│   ├── reflections/    # 感悟
│   ├── books/          # 书摘
│   ├── markets/        # 股市基金
│   ├── work/           # 工作记录
│   ├── schedule/       # 日程预报
│   ├── weather/        # 天气记录
│   └── misc/           # 杂记
├── assets/             # 样式与脚本（一般不用动）
├── public/             # 生成的网站（别手改，每次 build 会重写）
├── build.js            # 生成器
├── serve.js            # 本地预览服务器
└── site.config.json    # 站点信息（标题/作者/简介）
```

## 如何写一篇新日志

1. 在 `content/` 对应的分类文件夹里，新建一个 `.md` 文件（文件名随意，建议带日期，如 `2026-07-10-我的第一篇.md`）。
2. 文件开头写上头信息（frontmatter），然后写正文：

```markdown
---
title: 文章标题
date: 2026-07-10
category: reflections
tags: [感悟, 生活]
excerpt: 一句话摘要（可不写，会自动截取）
---

这里是正文，支持 **加粗**、列表、引用、表格、代码等 Markdown 语法。
```

3. 运行生成：

```bash
node build.js
```

4. 本地预览：

```bash
node serve.js        # 然后打开 http://localhost:4173
```

> 想一次完成： `npm run dev`（生成 + 预览）。

## 自定义

- **改站点名/作者/简介**：编辑 `site.config.json`。
- **加减分类**：编辑 `build.js` 顶部的 `CATEGORIES` 对象，并在 `content/` 下建对应文件夹。
- **换风格**：编辑 `assets/style.css`（暗色为默认，右上角可切亮色）。
- **删示例**：把 `content/` 里的示例 `.md` 删掉，重新 `node build.js` 即可。

## 发布上线（公开给关心你的人）

推荐用 **Cloudflare Pages**：git 推送即自动发布，免费、自带 HTTPS，国内访问相对最稳。

### 方式一：Cloudflare Pages（推荐 · git 推送自动发布）
1. 把本项目推到你的 GitHub 仓库（仓库已初始化好，只需执行下面两行）：
   ```bash
   git remote add origin <你的GitHub仓库地址>
   git push -u origin main
   ```
2. 打开 Cloudflare 控制台 → **Workers 和 Pages** → **创建** → 连接 Git 仓库。
3. 构建设置：**构建命令** 填 `npm run build`，**构建输出目录** 填 `public`。
4. 保存并部署。以后每次 `git push`，Cloudflare 会自动重新生成并发布，关心你的人立刻看到新日志。

### 其他方式
- **GitHub Pages**：把 `public/` 推到仓库，开启 Pages。
- **CloudStudio / Vercel / Netlify**：上传 `public/` 目录，自动获得公网地址。
- **自己的服务器**：把 `public/` 放到 Web 根目录。

部署后，以后只管往 `content/` 里写，提交一下就自动上线。

---

所有示例内容均为占位演示，可自由删除替换。
