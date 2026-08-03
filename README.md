# 拾光集 · 个人日志站点

> 捡拾日常里的微光，写给愿意慢下来的人。

用 Markdown 写日记，自动生成静态网页，GitHub Actions 自动构建部署到 GitHub Pages。

## 目录结构

```
├── content/            # 日志（Markdown），按分类存放
│   ├── reflections/    # 感悟
│   ├── books/          # 书摘
│   ├── markets/        # 股市基金
│   ├── work/           # 工作记录
│   ├── schedule/       # 日程预报
│   ├── weather/        # 天气记录
│   └── misc/           # 杂记
├── assets/             # 样式与脚本
├── build.js            # 生成器
├── serve.js            # 本地预览
├── .github/workflows/  # 自动部署
└── site.config.json    # 站点信息
```

## 写一篇新日志

在 `content/` 对应文件夹新建 `.md` 文件：

```markdown
---
title: 文章标题
date: 2026-08-03
category: reflections
tags: [感悟, 生活]
---

正文内容，支持 Markdown 语法。
```

## 本地预览

```bash
npm install
npm run dev
# 打开 http://localhost:4173
```

## 发布上线

`git push` 到 GitHub 后，Actions 自动构建并部署到 GitHub Pages。无需手动操作。

首次使用需要在 GitHub 仓库 Settings → Pages 中启用 GitHub Pages，Source 选 **GitHub Actions**。

## 自定义

- 改站点名/作者：编辑 `site.config.json`
- 加减分类：编辑 `build.js` 顶部 `CATEGORIES`

## 许可

MIT License · 仅供个人使用
