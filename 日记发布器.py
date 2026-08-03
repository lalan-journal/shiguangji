#!/usr/bin/env python3
"""拾光集日记发布器 v1.5 — 写日记 · 草稿箱 · 改旧稿 · 一键发布"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os, sys, subprocess, datetime, re, json, glob

if getattr(sys, 'frozen', False):
    BLOG_DIR = os.path.dirname(sys.executable)
else:
    BLOG_DIR = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(BLOG_DIR, "content")
DRAFT_DIR = os.path.join(BLOG_DIR, "drafts")
CONFIG_FILE = os.path.join(BLOG_DIR, "publisher_config.json")

CATEGORIES = {
    "reflections": "感悟", "books": "书摘", "markets": "股市基金",
    "work": "工作记录", "schedule": "日程预报", "weather": "天气记录",
    "misc": "杂记",
}
CAT_KEYS = list(CATEGORIES.keys())

os.makedirs(DRAFT_DIR, exist_ok=True)
for c in CAT_KEYS:
    os.makedirs(os.path.join(CONTENT_DIR, c), exist_ok=True)


def load_config():
    try:
        with open(CONFIG_FILE, "r") as f: return json.load(f)
    except: return {"token": "", "username": "lalan-journal", "repo": "shiguangji"}

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f: json.dump(cfg, f, indent=2)

def setup_remote(token):
    cfg = load_config()
    url = f"https://{token}@github.com/{cfg['username']}/{cfg['repo']}.git"
    subprocess.run(["git", "remote", "set-url", "origin", url], cwd=BLOG_DIR, capture_output=True)

def git_do(*args):
    return subprocess.run(["git"] + list(args), cwd=BLOG_DIR, capture_output=True, text=True)

def slugify(text):
    return re.sub(r'[^\w\u4e00-\u9fff-]', '', text.replace(" ", "-"))[:40]

def parse_post(filepath):
    """解析 .md 文件返回 {title, date, category, tags, content}"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            raw = f.read()
    except: return None
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n', raw, re.DOTALL)
    if not m: return None
    meta = {}
    for line in m.group(1).split("\n"):
        kv = line.split(":", 1)
        if len(kv) == 2: meta[kv[0].strip()] = kv[1].strip()
    content = raw[m.end():].strip()
    return {
        "title": meta.get("title", ""),
        "date": meta.get("date", ""),
        "category": meta.get("category", ""),
        "tags": meta.get("tags", ""),
        "content": content,
        "path": filepath
    }


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("拾光集 · 日记发布器 v1.5")
        self.root.geometry("780x700")
        self.root.minsize(600, 520)
        self.cfg = load_config()
        self._apply_theme()
        self._build()
        if self.cfg["token"]: setup_remote(self.cfg["token"])

    def _apply_theme(self):
        style = ttk.Style(); style.theme_use("clam")
        BG, BG_DARK, FG = "#F0F0F0", "#E0E0E0", "#333333"
        style.configure(".", background=BG, foreground=FG)
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=FG)
        style.configure("TLabelframe", background=BG)
        style.configure("TLabelframe.Label", background=BG, foreground=FG)
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=BG_DARK, foreground=FG,
                        padding=[10, 4], font=("Microsoft YaHei UI", 9))
        style.map("TNotebook.Tab", background=[("selected", BG)])
        style.configure("TButton", background=BG_DARK, foreground=FG,
                        font=("Microsoft YaHei UI", 9), padding=[8, 3])
        style.map("TButton", background=[("active", "#D0D0D0")])
        style.configure("Treeview", background=BG, foreground=FG,
                        fieldbackground=BG, rowheight=22)
        style.configure("Treeview.Heading", background=BG_DARK, foreground=FG,
                        font=("Microsoft YaHei UI", 9, "bold"))
        style.map("Treeview", background=[("selected", "#B3D4FC")])

    @staticmethod
    def _cbtn(parent, text, color, command, **kw):
        btn = tk.Button(parent, text=text, bg=color, fg="white",
                        font=("Microsoft YaHei UI", 9),
                        relief="flat", activebackground=color,
                        bd=0, padx=10, pady=3, cursor="hand2", command=command)
        btn.pack(**kw); return btn

    def _build(self):
        # Token
        sf = ttk.LabelFrame(self.root, text="GitHub 设置", padding=5)
        sf.pack(fill=tk.X, padx=8, pady=(8, 2))
        s1 = ttk.Frame(sf); s1.pack(fill=tk.X)
        ttk.Label(s1, text="Token:").pack(side=tk.LEFT)
        self.token_var = tk.StringVar(value=self.cfg["token"])
        ttk.Entry(s1, textvariable=self.token_var, show="*", width=48).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self._cbtn(s1, "保存", "#2196F3", self._save_token, side=tk.LEFT, padx=2)
        self.token_status = ttk.Label(sf, text="✓ 已配置" if self.cfg["token"] else "未配置", foreground="#4CAF50" if self.cfg["token"] else "gray")
        self.token_status.pack(anchor="w", padx=2)

        # Notebook
        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self._build_write_tab()
        self._build_draft_tab()
        self._build_posts_tab()

        # Status
        self.status = ttk.Label(self.root, text="就绪", anchor="w", background="#E0E0E0", foreground="#333")
        self.status.pack(fill=tk.X)
        self.root.bind("<Control-Return>", lambda e: self._publish())

    # ==================== WRITE ====================
    def _build_write_tab(self):
        f = ttk.Frame(self.nb); self.nb.add(f, text="✏ 写作")
        # cat/tags
        r1 = ttk.Frame(f, padding=(4, 6))
        r1.pack(fill=tk.X)
        ttk.Label(r1, text="分类:").pack(side=tk.LEFT)
        self.cat_var = tk.StringVar(value="reflections")
        cb = ttk.Combobox(r1, textvariable=self.cat_var, state="readonly", width=14)
        cb["values"] = [f"{k} ({v})" for k, v in CATEGORIES.items()]
        cb.set("reflections (感悟)"); cb.pack(side=tk.LEFT, padx=5)

        ttk.Label(r1, text="  标签:").pack(side=tk.LEFT)
        self.tags_var = tk.StringVar()
        ttk.Entry(r1, textvariable=self.tags_var, width=18).pack(side=tk.LEFT, padx=5)
        ttk.Label(r1, text="逗号分隔", foreground="gray").pack(side=tk.LEFT)

        r2 = ttk.Frame(f, padding=(4, 0))
        r2.pack(fill=tk.X)
        ttk.Label(r2, text="标题:").pack(side=tk.LEFT)
        self.title_var = tk.StringVar()
        ttk.Entry(r2, textvariable=self.title_var, font=("Microsoft YaHei UI", 10)).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        f3 = ttk.LabelFrame(f, text="正文", padding=5)
        f3.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.text = scrolledtext.ScrolledText(f3, font=("Microsoft YaHei UI", 10), wrap=tk.WORD,
                                               bg="#F0F0F0", fg="#333333", insertbackground="#333")
        self.text.pack(fill=tk.BOTH, expand=True)

        f4 = ttk.Frame(f, padding=(4, 4))
        f4.pack(fill=tk.X)
        self._cbtn(f4, "📤 发布", "#4CAF50", self._publish, side=tk.RIGHT, padx=2)
        self._cbtn(f4, "📝 存草稿", "#FF9800", self._save_draft, side=tk.RIGHT, padx=2)
        ttk.Button(f4, text="清空", command=self._clear).pack(side=tk.RIGHT, padx=2)

    # ==================== DRAFTS ====================
    def _build_draft_tab(self):
        f = ttk.Frame(self.nb); self.nb.add(f, text="📝 草稿")
        bar = ttk.Frame(f, padding=4); bar.pack(fill=tk.X)
        self._cbtn(bar, "刷新列表", "#2196F3", self._load_drafts, side=tk.LEFT, padx=2)
        ttk.Label(bar, text="双击编辑", foreground="gray").pack(side=tk.LEFT, padx=5)
        self._cbtn(bar, "删除选中", "#F44336", self._delete_draft, side=tk.RIGHT, padx=2)

        treef = ttk.Frame(f, padding=4); treef.pack(fill=tk.BOTH, expand=True)
        self.draft_tree = ttk.Treeview(treef, columns=("title","date","cat"), show="headings", height=12)
        self.draft_tree.heading("title", text="标题"); self.draft_tree.column("title", width=400)
        self.draft_tree.heading("date", text="日期"); self.draft_tree.column("date", width=100, anchor="center")
        self.draft_tree.heading("cat", text="分类"); self.draft_tree.column("cat", width=80, anchor="center")
        vs = ttk.Scrollbar(treef, orient=tk.VERTICAL, command=self.draft_tree.yview)
        self.draft_tree.configure(yscrollcommand=vs.set)
        self.draft_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True); vs.pack(side=tk.RIGHT, fill=tk.Y)
        self.draft_tree.bind("<Double-1>", self._open_draft)

        bf = ttk.Frame(f, padding=4); bf.pack(fill=tk.X)
        self._cbtn(bf, "📤 发布此草稿", "#4CAF50", self._publish_draft, side=tk.RIGHT, padx=2)
        self._cbtn(bf, "💾 保存修改", "#2196F3", self._update_draft, side=tk.RIGHT, padx=2)

        self.draft_edit = scrolledtext.ScrolledText(f, height=6, font=("Microsoft YaHei UI", 10),
                                                     wrap=tk.WORD, bg="#F0F0F0", fg="#333333")
        self.draft_edit.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.current_draft_id = None

        self._load_drafts()

    def _load_drafts(self):
        self.draft_tree.delete(*self.draft_tree.get_children())
        drafts = sorted(glob.glob(os.path.join(DRAFT_DIR, "*.json")), reverse=True)
        for dp in drafts:
            try:
                with open(dp, "r", encoding="utf-8") as f: d = json.load(f)
                iid = self.draft_tree.insert("", 0, values=(d.get("title","?"), d.get("date",""), CATEGORIES.get(d.get("category",""), "?")))
                self.draft_tree.set(iid, "cat", CATEGORIES.get(d.get("category",""), "?"))
            except: pass

    def _save_draft(self):
        title = self.title_var.get().strip()
        content = self.text.get("1.0", tk.END).strip()
        if not title and not content: return
        draft_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        data = {
            "title": title or "无标题草稿",
            "date": datetime.date.today().isoformat(),
            "category": self._get_cat(),
            "tags": self.tags_var.get().strip(),
            "content": content,
        }
        with open(os.path.join(DRAFT_DIR, f"{draft_id}.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.status.config(text="草稿已保存"); self._load_drafts()

    def _open_draft(self, e):
        sel = self.draft_tree.selection()
        if not sel: return
        vals = self.draft_tree.item(sel[0], "values")
        title = vals[0]
        for dp in sorted(glob.glob(os.path.join(DRAFT_DIR, "*.json")), reverse=True):
            with open(dp, "r", encoding="utf-8") as f: d = json.load(f)
            if d.get("title") == title:
                self.current_draft_id = dp
                self.draft_edit.delete("1.0", tk.END)
                self.draft_edit.insert("1.0", d.get("content", ""))
                self.status.config(text=f"编辑草稿: {title}")
                return

    def _update_draft(self):
        if not self.current_draft_id: return
        with open(self.current_draft_id, "r", encoding="utf-8") as f: d = json.load(f)
        d["content"] = self.draft_edit.get("1.0", tk.END).strip()
        with open(self.current_draft_id, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
        self.status.config(text="草稿已更新")

    def _delete_draft(self):
        sel = self.draft_tree.selection()
        if not sel: return
        vals = self.draft_tree.item(sel[0], "values")
        if not messagebox.askyesno("确认", f"删除草稿「{vals[0]}」?"): return
        for dp in glob.glob(os.path.join(DRAFT_DIR, "*.json")):
            with open(dp, "r", encoding="utf-8") as f: d = json.load(f)
            if d.get("title") == vals[0]:
                os.remove(dp); self.status.config(text="草稿已删除"); self._load_drafts(); return

    def _publish_draft(self):
        if not self.current_draft_id: return
        with open(self.current_draft_id, "r", encoding="utf-8") as f: d = json.load(f)
        d["content"] = self.draft_edit.get("1.0", tk.END).strip()
        if not d["title"] or not d["content"]: return
        self._do_publish(d["title"], d["category"], d["content"], d.get("tags",""),
                         d.get("date", datetime.date.today().isoformat()))
        os.remove(self.current_draft_id)
        self.current_draft_id = None
        self.draft_edit.delete("1.0", tk.END)
        self._load_drafts()

    # ==================== POSTS ====================
    def _build_posts_tab(self):
        f = ttk.Frame(self.nb); self.nb.add(f, text="📄 已发布")
        bar = ttk.Frame(f, padding=4); bar.pack(fill=tk.X)
        self._cbtn(bar, "刷新列表", "#2196F3", self._load_posts, side=tk.LEFT, padx=2)
        ttk.Label(bar, text="双击编辑，改完点「重新发布」", foreground="gray").pack(side=tk.LEFT, padx=5)
        self._cbtn(bar, "重新发布", "#4CAF50", self._republish, side=tk.RIGHT, padx=2)

        treef = ttk.Frame(f, padding=4); treef.pack(fill=tk.BOTH, expand=True)
        self.post_tree = ttk.Treeview(treef, columns=("title","date","cat"), show="headings", height=12)
        self.post_tree.heading("title", text="标题"); self.post_tree.column("title", width=400)
        self.post_tree.heading("date", text="日期"); self.post_tree.column("date", width=100, anchor="center")
        self.post_tree.heading("cat", text="分类"); self.post_tree.column("cat", width=80, anchor="center")
        vs = ttk.Scrollbar(treef, orient=tk.VERTICAL, command=self.post_tree.yview)
        self.post_tree.configure(yscrollcommand=vs.set)
        self.post_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True); vs.pack(side=tk.RIGHT, fill=tk.Y)
        self.post_tree.bind("<Double-1>", self._open_post)

        self.post_edit = scrolledtext.ScrolledText(f, height=6, font=("Microsoft YaHei UI", 10),
                                                    wrap=tk.WORD, bg="#F0F0F0", fg="#333333")
        self.post_edit.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.current_post_path = None
        self._load_posts()

    def _load_posts(self):
        self.post_tree.delete(*self.post_tree.get_children())
        posts = []
        for cat in CAT_KEYS:
            for fp in glob.glob(os.path.join(CONTENT_DIR, cat, "*.md")):
                info = parse_post(fp)
                if info: posts.append(info)
        posts.sort(key=lambda x: x["date"], reverse=True)
        for p in posts:
            iid = self.post_tree.insert("", tk.END, values=(p["title"], p["date"], CATEGORIES.get(p["category"], "?")))
            self.post_tree.set(iid, "cat", CATEGORIES.get(p["category"], "?"))

    def _open_post(self, e):
        sel = self.post_tree.selection()
        if not sel: return
        vals = self.post_tree.item(sel[0], "values")
        for cat in CAT_KEYS:
            for fp in glob.glob(os.path.join(CONTENT_DIR, cat, "*.md")):
                info = parse_post(fp)
                if info and info["title"] == vals[0]:
                    self.current_post_path = fp
                    self.post_edit.delete("1.0", tk.END)
                    self.post_edit.insert("1.0", info["content"])
                    self.status.config(text=f"编辑: {info['title']}")
                    return

    def _republish(self):
        if not self.current_post_path: return
        info = parse_post(self.current_post_path)
        if not info: return
        new_content = self.post_edit.get("1.0", tk.END).strip()
        frontmatter = f"---\ntitle: {info['title']}\ndate: {info['date']}\ncategory: {info['category']}\n"
        if info.get("tags"): frontmatter += f"tags: [{info['tags']}]\n"
        frontmatter += "---\n\n"
        try:
            with open(self.current_post_path, "w", encoding="utf-8") as f:
                f.write(frontmatter + new_content)
            git_do("add", self.current_post_path)
            git_do("commit", "-m", f"更新: {info['title']}")
            r = git_do("push", "origin", "master")
            if r.returncode != 0 and "denied" in r.stderr.lower():
                messagebox.showerror("失败", "Token 无效"); return
            self.status.config(text=f"✅ 已更新: {info['title']}")
            self._load_posts()
        except Exception as ex:
            messagebox.showerror("失败", str(ex))

    # ==================== COMMON ====================
    def _get_cat(self):
        return self.cat_var.get().split(" (")[0]

    def _save_token(self):
        t = self.token_var.get().strip()
        if not t: messagebox.showwarning("提示", "请输入 Token"); return
        self.cfg["token"] = t; save_config(self.cfg); setup_remote(t)
        self.token_status.config(text="✓ 已配置", foreground="#4CAF50")

    def _publish(self):
        title = self.title_var.get().strip()
        content = self.text.get("1.0", tk.END).strip()
        if not title or not content:
            messagebox.showwarning("提醒", "请输入标题和正文"); return
        ok = messagebox.askokcancel("确认", f"「{title}」\n分类: {CATEGORIES[self._get_cat()]}\n\n发布?")
        if not ok: return
        self._do_publish(title, self._get_cat(), content, self.tags_var.get().strip())

    def _do_publish(self, title, cat, content, tags="", date=None):
        if not self.cfg["token"]:
            messagebox.showwarning("提醒", "请先填写 GitHub Token"); return
        self.status.config(text="发布中..."); self.root.update()
        try:
            d = date or datetime.date.today().isoformat()
            slug = slugify(title)
            filename = f"{d}-{slug}.md" if slug else f"{d}.md"
            filepath = os.path.join(CONTENT_DIR, cat, filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            fm = f"---\ntitle: {title}\ndate: {d}\ncategory: {cat}\n"
            if tags: fm += f"tags: [{tags}]\n"
            fm += "---\n\n"
            with open(filepath, "w", encoding="utf-8") as f: f.write(fm + content)

            git_do("add", filepath)
            git_do("commit", "-m", f"发布: {title}")
            r = git_do("push", "origin", "master")
            if r.returncode != 0 and ("denied" in r.stderr.lower() or "403" in r.stderr):
                messagebox.showerror("失败", "Token 无效，请重新获取"); return

            self.status.config(text=f"✅ {title}")
            messagebox.showinfo("成功", f"「{title}」已发布\nhttps://lalan-journal.github.io/shiguangji/")
            self._clear()
            self._load_posts()
        except Exception as e:
            self.status.config(text=f"❌ {e}"); messagebox.showerror("失败", str(e))

    def _preview(self):
        try:
            subprocess.Popen(["node", "build.js"], cwd=BLOG_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.Popen(["node", "serve.js"], cwd=BLOG_DIR)
            self.status.config(text="本地预览: http://localhost:4173")
        except Exception as e: self.status.config(text=f"预览失败: {e}")

    def _clear(self):
        self.title_var.set(""); self.text.delete("1.0", tk.END); self.tags_var.set("")


if __name__ == "__main__":
    App().root.mainloop()
