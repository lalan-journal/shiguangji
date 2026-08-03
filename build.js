/**
 * 个人日志站点生成器
 * 读取 content/ 下的 Markdown，生成静态网页到 public/
 * 用法： node build.js
 */
const fs = require('fs');
const path = require('path');
const { marked } = require('marked');

const ROOT = __dirname;
const CONTENT_DIR = path.join(ROOT, 'content');
const OUT_DIR = path.join(ROOT, 'public');
const ASSETS_OUT = path.join(OUT_DIR, 'assets');
const SRC_ASSETS = path.join(ROOT, 'assets');

// GitHub Pages 子目录前缀（本地预览为 ""，部署时为 "/shiguangji"）
const BASE = process.env.BASE_URL || "";

// ---- 分类配置（想加减分类改这里即可）----
const CATEGORIES = {
  markets:    { name: '股市基金', desc: '每一日持仓日记，记账户浮沉，也记心湖涟漪' },
  books:      { name: '书摘', desc: '把喜欢的句子请下来，再与自己的心事对坐' },
  reflections:{ name: '感悟', desc: '偶有所得，便落笔成思' },
  work:       { name: '工作记录', desc: '案头的奔波与生长，皆成注脚' },
  schedule:   { name: '日程预报', desc: '未来几日，欲赴之约与将临之事' },
  weather:    { name: '天气记录', desc: '晴雨冷暖，皆成记忆' },
  misc:       { name: '杂记', desc: '人间烟火，皆可入文' },
};

// ---- 站点配置 ----
let SITE = { title: '拾光集', subtitle: '', author: '', bio: '', footer: '', links: [] };
try {
  SITE = Object.assign(SITE, JSON.parse(fs.readFileSync(path.join(ROOT, 'site.config.json'), 'utf8')));
} catch (e) { /* 用默认 */ }

marked.setOptions({ gfm: true, breaks: false });

// ---------- 工具 ----------
function parseFrontmatter(raw) {
  const m = raw.match(/^---\s*\n([\s\S]*?)\n---\s*\n?([\s\S]*)$/);
  if (!m) return { data: {}, content: raw };
  const data = {};
  m[1].split('\n').forEach(line => {
    const idx = line.indexOf(':');
    if (idx === -1) return;
    const key = line.slice(0, idx).trim();
    let val = line.slice(idx + 1).trim();
    if (val.startsWith('[') && val.endsWith(']')) {
      val = val.slice(1, -1).split(',').map(s => s.trim().replace(/^["']|["']$/g, '')).filter(Boolean);
    } else {
      val = val.replace(/^["']|["']$/g, '');
    }
    data[key] = val;
  });
  return { data, content: m[2] };
}

function readingTime(text) {
  const len = (text.replace(/\s/g, '').match(/[一-龥]|[a-zA-Z0-9]/g) || []).length;
  return Math.max(1, Math.round(len / 350));
}

function plainExcerpt(md, len = 90) {
  let t = md.replace(/```[\s\S]*?```/g, ' ')
    .replace(/`[^`]*`/g, ' ')
    .replace(/!\[[^\]]*\]\([^)]*\)/g, ' ')
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/[#>*_~`-]/g, ' ')
    .replace(/\s+/g, ' ').trim();
  return t.length > len ? t.slice(0, len) + '…' : t;
}

function fmtDate(d) {
  if (!d) return '';
  const dt = new Date(d);
  if (isNaN(dt)) return String(d);
  const p = n => String(n).padStart(2, '0');
  return `${dt.getFullYear()}-${p(dt.getMonth() + 1)}-${p(dt.getDate())}`;
}

// ---------- 读取文章 ----------
function readPosts() {
  const posts = [];
  for (const cat of Object.keys(CATEGORIES)) {
    const dir = path.join(CONTENT_DIR, cat);
    if (!fs.existsSync(dir)) continue;
    fs.readdirSync(dir).filter(f => f.endsWith('.md')).forEach(f => {
      const raw = fs.readFileSync(path.join(dir, f), 'utf8');
      const { data, content } = parseFrontmatter(raw);
      const slug = f.replace(/\.md$/, '');
      posts.push({
        category: cat,
        slug,
        title: data.title || slug,
        date: data.date || '',
        tags: Array.isArray(data.tags) ? data.tags : (data.tags ? [data.tags] : []),
        excerpt: data.excerpt || plainExcerpt(content),
        html: marked.parse(content),
        readingTime: readingTime(content),
        url: `${BASE}/posts/${cat}/${slug}.html`,
      });
    });
  }
  posts.sort((a, b) => (b.date || '').localeCompare(a.date || '') || a.title.localeCompare(b.title));
  return posts;
}

// ---------- 布局 ----------
function layout({ title, body, active = '', desc = '' }) {
  const catNav = Object.entries(CATEGORIES).map(([k, c]) =>
    `<a href="${BASE}/category/${k}.html" class="${active === k ? 'cur' : ''}">${c.name}</a>`).join('');
  const social = (SITE.links || []).map(l => `<a href="${l.url}" target="_blank" rel="noopener">${l.label}</a>`).join('');
  const contactLine = SITE.contact ? `<span class="contact">${SITE.contact.label} · ${SITE.contact.value}</span>` : '';
  return `<!doctype html>
<html lang="zh-CN" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${title} · ${SITE.title}</title>
<meta name="description" content="${desc || SITE.subtitle}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="${BASE}/assets/style.css">
</head>
<body>
<header class="site-head">
  <div class="wrap head-inner">
    <a class="brand" href="${BASE}/index.html">${SITE.title}</a>
    <nav class="nav">
      <a href="${BASE}/index.html" class="${active === 'home' ? 'cur' : ''}">首页</a>
      ${catNav}
      <a href="${BASE}/about.html" class="${active === 'about' ? 'cur' : ''}">关于</a>
    </nav>
    <button class="theme-toggle" id="themeToggle" aria-label="切换主题">◐</button>
  </div>
</header>
<main class="wrap">
${body}
</main>
<footer class="site-foot">
  <div class="wrap">
    <div class="foot-social">${contactLine || social || ''}</div>
    <p class="foot-note">${SITE.footer || '用 Markdown 写就，静态生成'}</p>
    <p class="foot-copy">© ${new Date().getFullYear()} ${SITE.author || SITE.title}</p>
  </div>
</footer>
<script src="${BASE}/assets/main.js"></script>
</body>
</html>`;
}

function catBadge(cat) {
  const c = CATEGORIES[cat] || { name: cat };
  return `<span class="badge" data-cat="${cat}">${c.name}</span>`;
}

// ---------- 各页面 ----------
function homePage(posts) {
  const cats = Object.entries(CATEGORIES).map(([k, c]) => {
    const count = posts.filter(p => p.category === k).length;
    return `<a class="cat-card" href="${BASE}/category/${k}.html">
      <span class="cat-name">${c.name}</span>
      <span class="cat-count">${count} 篇</span>
      <span class="cat-desc">${c.desc}</span>
    </a>`;
  }).join('');

  const recent = posts.slice(0, 10).map(p => `
    <article class="post-row">
      <a class="post-row-main" href="${p.url}">
        <div class="post-row-meta">${catBadge(p.category)}<time>${fmtDate(p.date)}</time></div>
        <h3>${p.title}</h3>
        <p class="excerpt">${p.excerpt}</p>
      </a>
    </article>`).join('');

  const body = `
  <section class="hero">
    <h1>${SITE.title}</h1>
    <p class="sub">${SITE.subtitle || ''}</p>
    <p class="hero-bio">${SITE.bio || ''}</p>
  </section>
  <section class="block">
    <h2 class="block-title">栏目</h2>
    <div class="cat-grid">${cats}</div>
  </section>
  <section class="block">
    <h2 class="block-title">近作</h2>
    <div class="post-list">${recent || '<p class="empty">此处尚空，待你执笔，落第一行文墨。</p>'}</div>
  </section>`;
  return layout({ title: '首页', body, active: 'home' });
}

function categoryPage(cat, posts) {
  const c = CATEGORIES[cat];
  const list = posts.map(p => `
    <article class="post-row">
      <a class="post-row-main" href="${p.url}">
        <div class="post-row-meta"><time>${fmtDate(p.date)}</time></div>
        <h3>${p.title}</h3>
        <p class="excerpt">${p.excerpt}</p>
        <div class="tags">${p.tags.map(t => `<span class="tag">#${t}</span>`).join('')}</div>
      </a>
    </article>`).join('');
  const body = `
  <section class="cat-head">
    <div>
      <h1>${c.name}</h1>
      <p>${c.desc} · 已录 ${posts.length} 篇</p>
    </div>
  </section>
  <div class="post-list">${list || '<p class="empty">这一辑尚无声息，静候来日。</p>'}</div>`;
  return layout({ title: c.name, body, active: cat });
}

function postPage(p, all, idx) {
  const prev = all[idx - 1];
  const next = all[idx + 1];
  const nav = `
    <nav class="post-nav">
      ${prev ? `<a href="${prev.url}" class="pn prev"><span>上一篇</span><b>${prev.title}</b></a>` : '<span></span>'}
      ${next ? `<a href="${next.url}" class="pn next"><span>下一篇</span><b>${next.title}</b></a>` : '<span></span>'}
    </nav>`;
  const body = `
  <article class="post">
    <a class="back" href="${BASE}/category/${p.category}.html">← 回到「${CATEGORIES[p.category].name}」</a>
    <div class="post-meta">${catBadge(p.category)}<time>${fmtDate(p.date)}</time><span class="rt">约 ${p.readingTime} 分钟</span></div>
    <h1 class="post-title">${p.title}</h1>
    <div class="post-body">${p.html}</div>
    ${p.tags.length ? `<div class="tags post-tags">${p.tags.map(t => `<span class="tag">#${t}</span>`).join('')}</div>` : ''}
    ${nav}
  </article>`;
  return layout({ title: p.title, body, desc: p.excerpt });
}

function aboutPage() {
  const contactLine2 = SITE.contact ? `<p class="about-contact">${SITE.contact.label} · ${SITE.contact.value}</p>` : '';
  const body = `
  <section class="about">
    <h1>关于</h1>
    <p class="about-author">${SITE.author || SITE.title}</p>
    <p>${SITE.bio || ''}</p>
    <p>这是一处用 Markdown 写就的私人园地。所有字句都安放在 <code>content/</code> 之下，分门别类。写完一篇，只需轻敲 <code>node build.js</code>，网页便悄然重生。</p>
    ${contactLine2}
    ${SITE.links && SITE.links.length ? `<div class="about-links">${(SITE.links||[]).map(l=>`<a href="${l.url}" target="_blank" rel="noopener">${l.label}</a>`).join('')}</div>` : ''}
  </section>`;
  return layout({ title: '关于', body, active: 'about' });
}

// ---------- 输出 ----------
function writeFile(p, content) {
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, content, 'utf8');
}

function build() {
  const posts = readPosts();
  const idxOf = {};
  posts.forEach((p, i) => idxOf[p.url] = i);

  writeFile(path.join(OUT_DIR, 'index.html'), homePage(posts));
  writeFile(path.join(OUT_DIR, 'about.html'), aboutPage());
  Object.keys(CATEGORIES).forEach(cat => {
    const list = posts.filter(p => p.category === cat);
    writeFile(path.join(OUT_DIR, 'category', `${cat}.html`), categoryPage(cat, list));
  });
  posts.forEach(p => {
    const i = idxOf[p.url];
    writeFile(path.join(OUT_DIR, 'posts', p.category, `${p.slug}.html`), postPage(p, posts, i));
  });

  // 复制静态资源
  if (fs.existsSync(SRC_ASSETS)) {
    fs.mkdirSync(ASSETS_OUT, { recursive: true });
    fs.readdirSync(SRC_ASSETS).forEach(f => {
      fs.copyFileSync(path.join(SRC_ASSETS, f), path.join(ASSETS_OUT, f));
    });
  }

  console.log(`✓ 生成完成：${posts.length} 篇文章 → public/`);
}

build();
