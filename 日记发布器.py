#!/usr/bin/env python3
"""拾光集日记发布器 v1.0 — 写日记 → 一键发布到 GitHub Pages"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os, subprocess, datetime, re, json

BLOG_DIR = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(BLOG_DIR, "content")
CONFIG_FILE = os.path.join(BLOG_DIR, "publisher_config.json")
REPO_URL = "https://github.com/lalan-journal/shiguangji.git"

CATEGORIES = {
    "reflections": "感悟", "books": "书摘", "markets": "股市基金",
    "work": "工作记录", "schedule": "日程预报", "weather": "天气记录",
    "misc": "杂记",
}


def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {"token": "", "username": "lalan-journal", "repo": "shiguangji"}


def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


def setup_remote(token):
    cfg = load_config()
    url = f"https://{token}@github.com/{cfg['username']}/{cfg['repo']}.git"
    subprocess.run(["git", "remote", "set-url", "origin", url],
                   cwd=BLOG_DIR, capture_output=True)


def git_do(*args):
    return subprocess.run(["git"] + list(args), cwd=BLOG_DIR,
                          capture_output=True, text=True)


def slugify(text):
    return re.sub(r'[^\w\u4e00-\u9fff-]', '', text.replace(" ", "-"))[:40]


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("拾光集 · 日记发布器 v1.0")
        self.root.geometry("680x660")
        self.root.minsize(520, 500)
        self.cfg = load_config()
        self._apply_theme()
        self._build()
        if self.cfg["token"]:
            setup_remote(self.cfg["token"])

    def _apply_theme(self):
        style = ttk.Style()
        style.theme_use("clam")
        BG, BG_DARK, FG = "#F0F0F0", "#E0E0E0", "#333333"
        style.configure(".", background=BG, foreground=FG)
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=FG)
        style.configure("TLabelframe", background=BG)
        style.configure("TLabelframe.Label", background=BG, foreground=FG)
        style.configure("TButton", background=BG_DARK, foreground=FG,
                        font=("Microsoft YaHei UI", 9), padding=[8, 3])
        style.map("TButton", background=[("active", "#D0D0D0")])

    def _build(self):
        # ── Token 设置区 ──
        sf = ttk.LabelFrame(self.root, text="GitHub 发布设置", padding=5)
        sf.pack(fill=tk.X, padx=8, pady=(8, 4))
        s1 = ttk.Frame(sf); s1.pack(fill=tk.X)
        ttk.Label(s1, text="Token:").pack(side=tk.LEFT)
        self.token_var = tk.StringVar(value=self.cfg["token"])
        self.token_entry = ttk.Entry(s1, textvariable=self.token_var, show="*", width=50)
        self.token_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self._cbtn(s1, "保存", "#2196F3", self._save_token, side=tk.LEFT, padx=2)
        self.token_status = ttk.Label(sf, text="", foreground="gray")
        self.token_status.pack(anchor="w", padx=2)
        if self.cfg["token"]:
            self.token_status.config(text="✓ Token 已配置", foreground="#4CAF50")

        # ── 分类/标签/标题 ──
        f1 = ttk.Frame(self.root, padding=(8, 4))
        f1.pack(fill=tk.X)
        ttk.Label(f1, text="分类:").pack(side=tk.LEFT)
        self.cat_var = tk.StringVar(value="reflections")
        cb = ttk.Combobox(f1, textvariable=self.cat_var, state="readonly", width=14)
        cb["values"] = [f"{k} ({v})" for k, v in CATEGORIES.items()]
        cb.set("reflections (感悟)")
        cb.pack(side=tk.LEFT, padx=5)

        ttk.Label(f1, text="  标签:",).pack(side=tk.LEFT)
        self.tags_var = tk.StringVar()
        ttk.Entry(f1, textvariable=self.tags_var, width=18).pack(side=tk.LEFT, padx=5)
        ttk.Label(f1, text="逗号分隔", foreground="gray").pack(side=tk.LEFT)

        f2 = ttk.Frame(self.root, padding=(8, 0))
        f2.pack(fill=tk.X)
        ttk.Label(f2, text="标题:").pack(side=tk.LEFT)
        self.title_var = tk.StringVar()
        ttk.Entry(f2, textvariable=self.title_var, width=60,
                  font=("Microsoft YaHei UI", 10)).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # ── 正文 ──
        f3 = ttk.LabelFrame(self.root, text="正文（Ctrl+Enter 发布）", padding=5)
        f3.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self.text = scrolledtext.ScrolledText(
            f3, font=("Microsoft YaHei UI", 10), wrap=tk.WORD,
            bg="#F0F0F0", fg="#333333", insertbackground="#333"
        )
        self.text.pack(fill=tk.BOTH, expand=True)

        # ── 按钮 ──
        f4 = ttk.Frame(self.root, padding=(8, 6))
        f4.pack(fill=tk.X)
        self._cbtn(f4, "📤 发布到博客", "#4CAF50", self._publish, side=tk.RIGHT, padx=5)
        self._cbtn(f4, "本地预览", "#2196F3", self._preview, side=tk.RIGHT, padx=5)
        ttk.Button(f4, text="清空", command=self._clear).pack(side=tk.RIGHT, padx=5)
        self._cbtn(f4, "打开博客", "#FF9800",
                   lambda: os.startfile("https://lalan-journal.github.io/shiguangji/"),
                   side=tk.LEFT, padx=2)

        # ── 状态栏 ──
        self.status = ttk.Label(self.root, text="就绪", anchor="w",
                                background="#E0E0E0", foreground="#333")
        self.status.pack(fill=tk.X)

        self.root.bind("<Control-Return>", lambda e: self._publish())

    @staticmethod
    def _cbtn(parent, text, color, command, **kw):
        btn = tk.Button(parent, text=text, bg=color, fg="white",
                        font=("Microsoft YaHei UI", 9),
                        relief="flat", activebackground=color,
                        bd=0, padx=12, pady=4, cursor="hand2",
                        command=command)
        btn.pack(**kw)
        return btn

    def _save_token(self):
        t = self.token_var.get().strip()
        if not t:
            messagebox.showwarning("提示", "请输入 Token")
            return
        self.cfg["token"] = t
        save_config(self.cfg)
        setup_remote(t)
        self.token_status.config(text="✓ Token 已配置", foreground="#4CAF50")
        self.status.config(text="Token 已保存并应用到 Git")

    def _get_cat(self):
        return self.cat_var.get().split(" (")[0]

    def _publish(self):
        if not self.cfg["token"]:
            messagebox.showwarning("提醒", "请先填写 GitHub Token")
            return
        title = self.title_var.get().strip()
        content = self.text.get("1.0", tk.END).strip()
        if not title:
            messagebox.showwarning("提醒", "请输入标题"); return
        if not content:
            messagebox.showwarning("提醒", "请输入正文"); return

        ok = messagebox.askokcancel("确认发布",
            f"标题: {title}\n分类: {CATEGORIES[self._get_cat()]}\n\n确认发布?")
        if not ok: return

        self.status.config(text="发布中..."); self.root.update()
        try:
            date = datetime.date.today().isoformat()
            slug = slugify(title)
            filename = f"{date}-{slug}.md" if slug else f"{date}.md"
            filepath = os.path.join(CONTENT_DIR, self._get_cat(), filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            fm = f"---\ntitle: {title}\ndate: {date}\ncategory: {self._get_cat()}\n"
            tags = self.tags_var.get().strip()
            if tags: fm += f"tags: [{tags}]\n"
            fm += "---\n\n"
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(fm + content)

            git_do("add", filepath)
            git_do("commit", "-m", f"新日记: {title}")
            r = git_do("push", "origin", "master")

            if r.returncode != 0 and "denied" in r.stderr.lower():
                messagebox.showerror("发布失败", "Token 可能无效，请重新获取")
                self.status.config(text="❌ Token 无效")
                return

            self.status.config(text="✅ 已发布！")
            messagebox.showinfo("成功",
                f"「{title}」已发布\nhttps://lalan-journal.github.io/shiguangji/")
            self._clear()
        except Exception as e:
            self.status.config(text=f"❌ {e}")
            messagebox.showerror("失败", str(e))

    def _preview(self):
        try:
            subprocess.Popen(["node", "build.js"], cwd=BLOG_DIR,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.Popen(["node", "serve.js"], cwd=BLOG_DIR)
            self.status.config(text="本地预览: http://localhost:4173")
        except Exception as e:
            self.status.config(text=f"预览失败: {e}")

    def _clear(self):
        self.title_var.set("")
        self.text.delete("1.0", tk.END)
        self.tags_var.set("")


if __name__ == "__main__":
    App().root.mainloop()
