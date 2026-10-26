// Claude Developer course — highlighting, copy buttons, active session, scroll-in motion, prompt anatomy, practice questions
(function () {
  var root = document.querySelector('.cca');
  if (!root) return;
  if (window.hljs) root.querySelectorAll('pre code[class*="language-"]:not(.language-plaintext)').forEach(function (el) { hljs.highlightElement(el); });

  // copy buttons: copy the nearest code block
  root.querySelectorAll('.copy').forEach(function (b) {
    b.addEventListener('click', function () {
      var box = b.closest('.code, .pcard, .side');
      var code = box.querySelector('pre').innerText;
      var done = function () { b.textContent = 'Copied'; setTimeout(function () { b.textContent = 'Copy'; }, 1400); };
      if (navigator.clipboard) navigator.clipboard.writeText(code).then(done, function () {});
      else { var t = document.createElement('textarea'); t.value = code; document.body.appendChild(t); t.select(); document.execCommand('copy'); t.remove(); done(); }
    });
  });

  // stagger index for chat bubbles and panel rows
  root.querySelectorAll('.thread').forEach(function (t) { t.querySelectorAll('.msg').forEach(function (m, k) { m.style.setProperty('--k', k); }); });
  root.querySelectorAll('.panel .rows').forEach(function (t) { t.querySelectorAll('.row').forEach(function (m, k) { m.style.setProperty('--k', k); }); });

  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var anims = root.querySelectorAll('.anim');
  if ('IntersectionObserver' in window && !reduce) {
    anims.forEach(function (a) { a.classList.add('pre'); });
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (!e.isIntersecting) return;
        e.target.classList.add('in');
        io.unobserve(e.target);
      });
    }, { rootMargin: '0px 0px -15% 0px' });
    anims.forEach(function (a) { io.observe(a); });
  }

  // prompt anatomy: tap a label to spotlight that part; tap again to show all
  root.querySelectorAll('.anatomy').forEach(function (fig) {
    fig.querySelectorAll('.legend button').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var part = btn.dataset.part, on = btn.classList.contains('sel');
        fig.querySelectorAll('.legend button').forEach(function (x) { x.classList.remove('sel'); });
        fig.querySelectorAll('mark.part').forEach(function (m) { m.classList.remove('on'); });
        if (on) { fig.classList.remove('focus'); return; }
        btn.classList.add('sel'); fig.classList.add('focus');
        fig.querySelectorAll('mark.part.' + part).forEach(function (m) { m.classList.add('on'); });
      });
    });
  });

  // practice questions
  root.querySelectorAll('.quiz').forEach(function (q) {
    var multi = q.dataset.multi === '1', opts = q.querySelectorAll('.opts button'), why = q.querySelector('.why'), done = false;
    function reveal() {
      done = true;
      opts.forEach(function (b) {
        var ok = b.dataset.ok === '1', sel = b.classList.contains('sel');
        if (ok) b.classList.add('right'); else if (sel) b.classList.add('wrong');
        b.disabled = true;
      });
      var allRight = Array.prototype.every.call(opts, function (b) { return (b.dataset.ok === '1') === b.classList.contains('sel'); });
      why.hidden = false;
      why.insertAdjacentHTML('afterbegin', '<b>' + (allRight ? 'Correct. ' : 'Not quite. ') + '</b>');
      var c = q.querySelector('.check'); if (c) c.remove();
    }
    opts.forEach(function (b) {
      b.addEventListener('click', function () {
        if (done) return;
        if (!multi) { b.classList.add('sel'); reveal(); return; }
        b.classList.toggle('sel');
      });
    });
    var c = q.querySelector('.check'); if (c) c.addEventListener('click', function () { if (!done) reveal(); });
  });

  // active session in the sidebar
  var links = {};
  root.querySelectorAll('.toc a').forEach(function (a) { links[a.getAttribute('href').slice(1)] = a; });
  if (!('IntersectionObserver' in window)) return;
  var io2 = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      if (!e.isIntersecting) return;
      Object.keys(links).forEach(function (k) { links[k].classList.toggle('on', k === e.target.id); });
    });
  }, { rootMargin: '-30% 0px -60% 0px' });
  root.querySelectorAll('.session').forEach(function (s) { io2.observe(s); });
})();
