/* ============================================================
   nihanzo — interactions
   Vanilla JS, no dependencies. Each block is self-contained
   and commented so it's easy to extend later.
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {

  /* ---- Footer year ---- */
  const yearEl = document.getElementById('year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  /* ---- Nav: solid background after scrolling, mobile toggle ---- */
  const nav = document.getElementById('nav');
  const navToggle = document.getElementById('navToggle');
  const navLinks = document.getElementById('navLinks');

  const onScroll = () => nav.classList.toggle('is-scrolled', window.scrollY > 20);
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  navToggle?.addEventListener('click', () => {
    const open = navLinks.classList.toggle('is-open');
    navToggle.classList.toggle('is-open', open);
    navToggle.setAttribute('aria-expanded', String(open));
  });
  // Close the mobile menu after tapping a link
  navLinks?.querySelectorAll('a').forEach((a) =>
    a.addEventListener('click', () => {
      navLinks.classList.remove('is-open');
      navToggle.classList.remove('is-open');
      navToggle.setAttribute('aria-expanded', 'false');
    })
  );

  /* ---- Scroll reveal (fade/slide elements in as they enter view) ---- */
  const revealEls = document.querySelectorAll('.reveal');
  const io = new IntersectionObserver((entries, obs) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('is-visible');
      // Kick off the stat counter if this element contains one
      entry.target.querySelectorAll?.('.stat').forEach(runCounter);
      obs.unobserve(entry.target);
    });
  }, { threshold: 0.15 });
  revealEls.forEach((el) => io.observe(el));

  /* ---- Animated stat counters ---- */
  function runCounter(el) {
    if (el.dataset.done) return;
    el.dataset.done = '1';
    const target = parseFloat(el.dataset.count) || 0;
    const suffix = el.dataset.suffix || '';
    const duration = 1400;
    const start = performance.now();
    const tick = (now) => {
      const p = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3); // easeOutCubic
      el.textContent = Math.round(target * eased) + suffix;
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }

  /* ---- Portfolio filters ---- */
  const filters = document.querySelectorAll('.filter');
  const cards = document.querySelectorAll('#workGrid .card');
  filters.forEach((btn) => {
    btn.addEventListener('click', () => {
      filters.forEach((f) => f.classList.remove('is-active'));
      btn.classList.add('is-active');
      const f = btn.dataset.filter;
      cards.forEach((card) => {
        const show = f === 'all' || card.dataset.category === f;
        card.classList.toggle('is-hidden', !show);
      });
    });
  });

  /* ---- Video modal ----
     Opens for the showreel button and for any portfolio card.
     If an element has a data-video URL (YouTube/Vimeo embed or an .mp4),
     it plays; otherwise a friendly placeholder is shown. */
  const modal = document.getElementById('modal');
  const modalFrame = document.getElementById('modalFrame');
  const modalTitle = document.getElementById('modalTitle');
  let lastFocused = null;

  function openModal(videoUrl, title) {
    lastFocused = document.activeElement;
    modalTitle.textContent = title || '';

    if (videoUrl) {
      const isFile = /\.(mp4|webm|mov)$/i.test(videoUrl);
      modalFrame.innerHTML = isFile
        ? `<video src="${videoUrl}" controls autoplay playsinline></video>`
        : `<iframe src="${videoUrl}" allow="autoplay; fullscreen; picture-in-picture" allowfullscreen></iframe>`;
    } else {
      // Placeholder shown until a real video URL is added
      modalFrame.innerHTML = `<div class="modal__ph">
        <strong>${title || 'Showreel'}</strong>
        Add a YouTube/Vimeo embed URL (or an .mp4 path) to <code>data-video</code> and it plays right here.
      </div>`;
    }

    modal.classList.add('is-open');
    modal.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
    modal.querySelector('.modal__close')?.focus();
  }

  function closeModal() {
    modal.classList.remove('is-open');
    modal.setAttribute('aria-hidden', 'true');
    modalFrame.innerHTML = ''; // stop playback
    document.body.style.overflow = '';
    lastFocused?.focus();
  }

  // Showreel button(s)
  document.querySelectorAll('[data-open-reel]').forEach((btn) =>
    btn.addEventListener('click', () =>
      openModal(btn.dataset.video || '', 'Showreel 2026')
    )
  );

  // Portfolio cards
  cards.forEach((card) =>
    card.addEventListener('click', () =>
      openModal(card.dataset.video || '', card.dataset.title || '')
    )
  );

  // Close interactions
  document.querySelectorAll('[data-close-modal]').forEach((el) =>
    el.addEventListener('click', closeModal)
  );
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal.classList.contains('is-open')) closeModal();
  });

});
