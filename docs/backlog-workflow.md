# Backlog Workflow — How to render `BACKLOG.md` in VS Code

The backlog lives at `/BACKLOG.md`. This guide shows how to render it nicely in VS Code itself — no Obsidian, no GitHub Issues, no extra tooling.

---

## 1. Quick preview (no install)

VS Code has a built-in markdown preview that handles every feature `BACKLOG.md` uses:

1. Open `BACKLOG.md` in VS Code.
2. Press **`⌘ K` then `V`** (macOS) or **`Ctrl K V`** (Windows/Linux) — this opens the **Markdown Preview** side-by-side with your editor.
3. Press **`⌘ Shift V`** to open it as a full tab instead.

What you get:

- ✅ Rendered headings and tables
- ✅ **Clickable checkboxes** — clicking a `- [ ]` toggles it to `- [x]` in the source file
- ✅ **Clickable links** to files and headings
- ✅ **Tag highlighting** via `#tag` syntax
- ✅ **Code blocks** with syntax highlighting

That's it. No extension needed for basic rendering.

### Tip: Pin the preview

Right-click the preview tab → **"Open Preview to the Side"** to keep it permanently open while you edit.

---

## 2. Make it a dashboard (recommended)

The **Markdown Preview Enhanced** extension turns the preview into a proper task-management UI.

### Install

1. Open the Extensions panel: **`⌘ Shift X`**
2. Search: **`Markdown Preview Enhanced`**
3. Author: **Yiyi Wang** (verify the publisher before installing)
4. Click **Install**

### What you get

- **Live preview** that updates as you type.
- **Task list rendering** with checkboxes that toggle on click and persist to the file.
- **Mermaid diagrams** render inline (useful when you add diagrams to stories later).
- **Code chunks** that can run (useful for verification commands in acceptance criteria).
- **Table of Contents** generated automatically from headings.
- **Print to PDF** or export to HTML for sharing.

### Use it

1. Open `BACKLOG.md`.
2. Press **`⌘ K V`** to open the preview.
3. Click any `- [ ]` checkbox — it becomes `- [x]` and the change persists in the file.
4. Use the preview's TOC (top of the preview window) to jump between phases.

---

## 3. Render it as a Kanban board (still in VS Code)

This is one step further: turn the status fields into draggable cards.

### The truth about VS Code + Kanban

There's no VS Code extension that turns `BACKLOG.md` into a draggable Kanban board. The **Obsidian Kanban plugin** does this perfectly — that's why we picked `BACKLOG.md` as a format that's compatible with it — but Obsidian is a separate app.

If you want a Kanban board inside VS Code, the realistic options are:

- **Use the Markdown Preview Enhanced** approach (above). The status tables at the bottom of each phase act as your "board."
- **Install Obsidian separately** for the Kanban view. Obsidian reads `BACKLOG.md` directly from disk — no import needed.
- **Use GitHub Issues + Projects** (the board lives on github.com, the file stays in the repo).

### Suggested board layout (use Markdown Preview Enhanced)

A simple ASCII board you can paste at the end of `BACKLOG.md` whenever you want to see all stories at once:

```markdown
## Board View

| Backlog | In Progress | Blocked | Done |
|---|---|---|---|
| P1-S1 | P2-S1 | — | — |
| P1-S2 |  |  |  |
| P1-S3 |  |  |  |
```

Update the cells as you move stories between columns. The Markdown Preview Enhanced renders this as a clean 4-column table.

---

## 4. Daily workflow

### Morning

1. Open VS Code.
2. Open `BACKLOG.md` in the editor + preview (`⌘ K V`).
3. Find the next `todo` story whose dependencies are all `done`.
4. Update its status to `in-progress`:
   ```markdown
   - **Status:** todo
   ```
   becomes
   ```markdown
   - **Status:** in-progress
   ```

### During work

1. Tick acceptance criteria as you complete them:
   ```markdown
   - [x] First thing
   - [ ] Second thing
   ```

### When done

1. Update status to `done`.
2. Update the Board View table at the bottom.
3. Move on to the next story.

### When blocked

1. Update status to `blocked`.
2. Add a note at the bottom of the story:
   ```markdown
   - **Notes:** Waiting for #15 — Ollama service is down on local dev box.
   ```
3. Pick a different `todo` story.

---

## 5. Querying the file from the terminal

Useful one-liners:

```bash
# Count stories by status
grep -c "^- \*\*Status:\*\* todo" BACKLOG.md
grep -c "^- \*\*Status:\*\* in-progress" BACKLOG.md
grep -c "^- \*\*Status:\*\* done" BACKLOG.md

# List story IDs that are ready to start
grep -B1 "^- \*\*Status:\*\* todo" BACKLOG.md

# Show all content for a single story
awk '/P1-S1/,/P1-S2/' BACKLOG.md

# Count unchecked acceptance criteria across the whole file
grep -c "^- \[ \]" BACKLOG.md

# Count done acceptance criteria
grep -c "^- \[x\]" BACKLOG.md
```

Drop these into `scripts/backlog-stats.sh` if you want them handy.

---

## 6. Sharing the file

When you want to share progress:

- **GitHub:** push to a repo, link the file. Anyone with the link sees rendered markdown.
- **Email:** paste the file contents; markdown renders in most modern email clients.
- **HTML export:** in Markdown Preview Enhanced, click the **"..."** menu in the preview → **"Chrome (Puppeteer)" → "PDF" or "HTML"** for a self-contained file.
- **Print:** `⌘ P` in the preview tab → print or save as PDF.

---

## 7. When to graduate from this file

`BACKLOG.md` is great until you have:

- More than ~50 stories
- Multiple collaborators
- Stories that need discussion threads
- Release tracking (which stories ship in v1.0 vs v1.1)

At that point, mirror each story as a **GitHub Issue**, keep `BACKLOG.md` as the index, and use a **GitHub Project board** for the Kanban view. The file stays the source of truth; the issues become the conversation log.
