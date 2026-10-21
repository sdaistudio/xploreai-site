// Financial Data Analytics using R — syntax highlighting, copy buttons, active session in the sidebar
(function () {
  if (window.hljs) document.querySelectorAll('.fdar pre code.language-r').forEach(function (el) { hljs.highlightElement(el); });

  document.querySelectorAll('.fdar .copy').forEach(function (b) {
    b.addEventListener('click', function () {
      var code = b.closest('.code').querySelector('code').innerText;
      var done = function () { b.textContent = 'Copied'; setTimeout(function () { b.textContent = 'Copy'; }, 1400); };
      if (navigator.clipboard) navigator.clipboard.writeText(code).then(done, function () {});
      else { var t = document.createElement('textarea'); t.value = code; document.body.appendChild(t); t.select(); document.execCommand('copy'); t.remove(); done(); }
    });
  });

  var links = {};
  document.querySelectorAll('.fdar .toc a').forEach(function (a) { links[a.getAttribute('href').slice(1)] = a; });
  if (!('IntersectionObserver' in window)) return;
  var io = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      if (!e.isIntersecting) return;
      Object.keys(links).forEach(function (k) { links[k].classList.toggle('on', k === e.target.id); });
    });
  }, { rootMargin: '-30% 0px -60% 0px' });
  document.querySelectorAll('.fdar .session').forEach(function (s) { io.observe(s); });
})();
