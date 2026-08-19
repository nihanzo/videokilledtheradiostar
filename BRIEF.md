# nihanzo — Video Editing Portfolio · Project Brief & Handoff

> **Purpose of this file:** a complete, self-contained spec so any new Claude
> session (or developer) can continue building without re-reading the whole
> conversation. Read this top to bottom, run the site locally, then pick up
> from **§8 Roadmap**.

---

## 1. What this is
A personal portfolio website for **nihanzo**, a video editor & colorist. It
showcases skills and a body of work, and gives potential clients a way to get
in touch. Built as a fast, dependency-free **static site** so it can be hosted
free on **GitHub Pages** and edited without a build step.

## 2. Concept (decided)
- **Visual direction:** *Dark & cinematic.* Deep near-black backgrounds, a film
  grain overlay, bold display type, and a warm→hot accent gradient (coral→pink)
  that evokes a cinematic color grade. Footage/thumbnails are the visual stars.
- **Tone of copy:** confident, concise, story-focused ("Stories, cut to keep
  people watching.").
- **Sections (all present):** Showreel hero → Portfolio grid → About/bio →
  Services → Contact.

## 3. Current status
✅ Full single-page site scaffolded and styled. Renders and is interactive.
✅ All content is **placeholder** and clearly marked for swap-in.
✅ Local git repo initialized; GitHub CLI (`gh`) authenticated as `nihanzo`.
⬜ Real content (videos, bio, photo, links) — **owner will provide later.**
⬜ Pushed to GitHub / deployed to Pages — **not done yet** (see §7, §8).

## 4. Tech stack & file structure
Plain HTML + CSS + vanilla JS. No framework, no build, no npm.

```
nihanzo/
├── index.html          # All markup / page content
├── css/styles.css      # Design tokens + all styling (dark cinematic)
├── js/main.js          # Nav, scroll-reveal, stat counters, filters, modal
├── .claude/launch.json # Local preview server config (python http.server :8756)
├── BRIEF.md            # This file
└── README.md           # Short repo readme
```

### Run locally
```bash
cd ~/Downloads/nihanzo
python3 -m http.server 8756
# open http://localhost:8756
```

## 5. Design system (for consistency when extending)
Defined as CSS custom properties at the top of `css/styles.css`:
- **Backgrounds:** `--bg #0a0a0c`, `--bg-2 #101014`, `--bg-3 #16161c`
- **Text:** `--text #f4f4f6`, `--muted #9b9ba6`, `--muted-2 #6f6f7a`
- **Accent:** `--accent #ff6b3d` + `--accent-2 #ff3d6e` → `--grad` gradient;
  `--teal #2dd4bf` used only as a background glow.
- **Type:** `Sora` (display/headings), `Inter` (body) via Google Fonts.
- **Shape/motion:** `--radius 16px`, `--ease cubic-bezier(0.22,1,0.36,1)`.
- Fully responsive (breakpoints at 900px and 680px) + `prefers-reduced-motion`
  and mobile hamburger nav already handled.

## 6. Placeholder → real content swap map
Everything a non-developer needs to replace, and exactly where:

| What | Where | How |
|---|---|---|
| **Videos** (showreel + each project) | `index.html` — `data-video=""` on the `[data-open-reel]` button and each `.card` | Paste a YouTube/Vimeo **embed** URL, or a path to an `.mp4`. The modal auto-detects and plays it. |
| **Project titles/tags/durations** | `.card` markup in `#workGrid` | Edit the `<h3>`, `.tag`, `.dur`, and `data-title`. Add/remove cards freely. |
| **Card thumbnail colors** | `style="--g1:…;--g2:…"` on each `.card` | Or replace the gradient with a real poster image (add an `<img>` + minor CSS). |
| **Stats** | `.hero__stats` (`data-count`, `data-suffix`) | Change numbers; counter animates automatically. |
| **Bio / about copy** | `#about` section | Replace placeholder paragraphs. |
| **Portrait photo** | `.about__portrait` (`.portrait-ph`) | Swap the placeholder div for `<img src="assets/portrait.jpg" alt="nihanzo">`. |
| **Skills & tools** | `.about__cols` ticked lists | Edit list items. |
| **Services** | `.svc-grid` | Edit the four cards. |
| **Contact email** | `mailto:hello@nihanzo.com` in `#contact` | Replace with real email. |
| **Social links** | footer `.footer__social` | Replace `#` hrefs. |
| **Contact form delivery** | `#contactForm` | Currently front-end only. Wire to Formspree/Getform (set `action` + `method="POST"`) or a serverless function to actually receive messages. |

## 7. Deployment plan (GitHub Pages)
GitHub CLI is already authenticated as **nihanzo**. To publish:
```bash
cd ~/Downloads/nihanzo
git add -A && git commit -m "Initial portfolio scaffold"
gh repo create nihanzo-portfolio --public --source=. --remote=origin --push
# Enable Pages (serve from main branch root):
gh api -X POST repos/nihanzo/nihanzo-portfolio/pages -f source[branch]=main -f source[path]=/ 2>/dev/null || \
  echo "Enable Pages in repo Settings → Pages → Deploy from branch → main → /(root)"
```
Site will be at `https://nihanzo.github.io/nihanzo-portfolio/`. (A custom domain
can be added later in Settings → Pages.) **Note:** creating a public repo
publishes the code — confirm with the owner before running this.

## 8. Roadmap / suggested next steps
1. **Owner provides content** → do the swaps in §6.
2. **Contact form** → connect Formspree (or similar) so messages are received.
3. **Real thumbnails** → replace gradient placeholders with poster frames for a
   more premium look; consider lazy-loading.
4. **SEO/meta** → fill in the Open Graph image + real description in `<head>`.
5. **Optional polish:** per-project detail pages or a lightbox gallery; a
   testimonials section; a downloadable résumé/rate card.
6. **Deploy** → push + enable Pages (§7). Optionally add a GitHub Action to
   deploy automatically on push.

## 9. Constraints & preferences captured so far
- Owner wants to **learn the workflow** (how to build/iterate with Claude),
  not just receive a finished product — explain steps as you go.
- Keep it **simple to maintain** (no framework unless there's a strong reason).
- Commit identity is set to `nihanzo` with a GitHub noreply email. Owner may
  later switch to their real name on commits/site.
- Real name, exact email, and social handles were **not yet provided.**

---
*Last updated by the concept/scaffold session. Site is live-previewable and
ready for content + deployment.*
