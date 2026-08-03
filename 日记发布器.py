#!/usr/bin/env python3
"""拾光集日记发布器 — 写日记 → 一键发布到 GitHub Pages"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os, subprocess, datetime, re

BLOG_DIR = r"E:\workbuddy\拾光集"
CONTENT_DIR = os.path.join(BLOG_DIR, "content")
REPO_URL = "https://github.com/lalan-journal/shiguangji.git"

CATEGORIES = {
    "reflections": "感悟",
    "books": "书摘",
    "markets": "股市基金",
    "work": "工作记录",
    "schedule": "日程预报",
    "weather": "天气记录",
    "misc": "杂记",
}


def slugify(text):
    return re.sub(r'[^\w\u4e00-\u9fff-]', '', text.replace(" ", "-"))[:40]


def git_do(*args):
    return subprocess.run(
        ["git"] + list(args), cwd=BLOG_DIR,
        capture_output=True, text=True
    )


def publish(title, category, content, tags=""):
    date = datetime.date.today().isoformat()
    slug = slugify(title)
    filename = f"{date}-{slug}.md" if slug else f"{date}.md"
    filepath = os.path.join(CONTENT_DIR, category, filename)

    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    frontmatter = f"---\ntitle: {title}\ndate: {date}\ncategory: {category}\n"
    if tags:
        frontmatter += f"tags: [{tags}]\n"
    frontmatter += "---\n\n"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(frontmatter + content)

    # git push
    git_do("add", filepath)
    git_do("commit", "-m", f"新日记: {title}")
    git_do("push", "origin", "master")
    return True


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("拾光集 · 日记发布器")
        self.root.geometry("680x620")
        self.root.minsize(520, 480)
        self._build()

    def _build(self):
        # --- Category ---
        f1 = ttk.Frame(self.root, padding=10)
        f1.pack(fill=tk.X)
        ttk.Label(f1, text="分类:").pack(side=tk.LEFT)
        self.cat_var = tk.StringVar(value="reflections")
        cb = ttk.Combobox(f1, textvariable=self.cat_var, state="readonly", width=12)
        cb["values"] = [f"{k} ({v})" for k, v in CATEGORIES.items()]
        cb.pack(side=tk.LEFT, padx=5)
        cb.set("reflections (感悟)")

        ttk.Label(f1, text="  标签:",).pack(side=tk.LEFT)
        self.tags_var = tk.StringVar()
        ttk.Entry(f1, textvariable=self.tags_var, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Label(f1, text="逗号分隔", foreground="gray").pack(side=tk.LEFT)

        # --- Title ---
        f2 = ttk.Frame(self.root, padding=(10, 0))
        f2.pack(fill=tk.X)
        ttk.Label(f2, text="标题:").pack(side=tk.LEFT)
        self.title_var = tk.StringVar()
        ttk.Entry(f2, textvariable=self.title_var, width=60,
                  font=("Microsoft YaHei UI", 10)).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # --- Content ---
        f3 = ttk.LabelFrame(self.root, text="正文", padding=5)
        f3.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.text = scrolledtext.ScrolledText(
            f3, font=("Microsoft YaHei UI", 10), wrap=tk.WORD,
            bg="#1e1e1e", fg="#d4d4d4", insertbackground="white"
        )
        self.text.pack(fill=tk.BOTH, expand=True)

        # --- Buttons ---
        f4 = ttk.Frame(self.root, padding=10)
        f4.pack(fill=tk.X)
        self._cbtn(f4, "📤 发布", "#4CAF50", self._publish, side=tk.RIGHT, padx=5)
        self._cbtn(f4, "本地预览", "#2196F3", self._preview, side=tk.RIGHT, padx=5)
        ttk.Button(f4, text="清空", command=self._clear).pack(side=tk.RIGHT, padx=5)

        self.status = ttk.Label(self.root, text="就绪", anchor="w",
                                background="#333", foreground="#aaa")
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

    def _get_cat(self):
        return self.cat_var.get().split(" (")[0]

    def _publish(self):
        title = self.title_var.get().strip()
        content = self.text.get("1.0", tk.END).strip()
        if not title:
            messagebox.showwarning("提醒", "请输入标题")
            return
        if not content:
            messagebox.showwarning("提醒", "请输入正文")
            return

        ok = messagebox.askokcancel("确认发布",
            f"标题: {title}\n分类: {CATEGORIES[self._get_cat()]}\n\n确认发布到 {REPO_URL}?")
        if not ok:
            return

        self.status.config(text="发布中...")
        self.root.update()

        try:
            publish(title, self._get_cat(), content,
                    self.tags_var.get().strip())
            self.status.config(text="✅ 已发布！", foreground="#4CAF50")
            messagebox.showinfo("成功",
                f"「{title}」已发布\nhttps://lalan-journal.github.io/shiguangji/")
            self._clear()
        except Exception as e:
            self.status.config(text=f"❌ {e}", foreground="#F44336")
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
