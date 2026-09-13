/* XploreAI motion graphics for the AI Weekly Briefing.
   Add ONE line to an issue page:  <script src="/assets/motion.js" defer></script>
   It reads the highlights strip (.strip), picks the first listed topic that has an animation,
   and inserts it right after the strip. To place one by hand instead, put
   <div class="mx-slot" data-motion="agentic-ai"></div> anywhere on the page.
   Animations play by default; they pause off screen only once the browser has proven it
   reports visibility, and visitors with Reduce motion see a still frame + a Play button. */
(function(){
  var CSS = `.mx-slot{margin:4px 0 36px}
.mx{--mx-t:9s;max-width:520px;margin:0 auto;background:#FFFDF8;border:1px solid rgba(74,66,56,.14);border-radius:18px;padding:14px 14px 10px;font-family:'Quicksand',-apple-system,'Segoe UI',Arial,sans-serif;text-align:left}
.mx .mx-kicker{display:block;font-size:12px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#766B5F;margin:2px 4px 4px}
.mx svg{display:block;width:100%;height:auto}
.mx figcaption{font-size:14.5px;color:#6B6155;padding:8px 4px 4px;line-height:1.5;margin:0}
.mx figcaption b{color:#4A4238}
.mx .mx-lbl{font-size:15.5px;font-weight:700;fill:#4A4238}
.mx .mx-cap{font-size:16px;font-weight:700;fill:#4A4238}
.mx .mx-agent{font-size:20px;font-weight:700;fill:#F5EFE4}
.mx .mx-ico{fill:none;stroke:#4A4238;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.mx .mx-sig,.mx .mx-tick,.mx .mx-hl,.mx .mx-slotfill,.mx .mx-cap{opacity:0}
.mx .mx-cap0{opacity:1}
.mx .mx-ring,.mx .mx-tick{transform-box:fill-box;transform-origin:center}
.mx .mx-ring{animation:mx-pulse var(--mx-t) ease-out infinite}
.mx .mx-s1{animation:mx-s1 var(--mx-t) ease-in-out infinite}
.mx .mx-s2{animation:mx-s2 var(--mx-t) ease-in-out infinite}
.mx .mx-s3{animation:mx-s3 var(--mx-t) ease-in-out infinite}
.mx .mx-s4{animation:mx-s4 var(--mx-t) ease-in-out infinite}
.mx .mx-h1{animation:mx-h1 var(--mx-t) linear infinite}
.mx .mx-h2{animation:mx-h2 var(--mx-t) linear infinite}
.mx .mx-h3{animation:mx-h3 var(--mx-t) linear infinite}
.mx .mx-h4{animation:mx-h4 var(--mx-t) linear infinite}
.mx .mx-t1{animation:mx-t1 var(--mx-t) ease-out infinite}
.mx .mx-t2,.mx .mx-slotfill{animation:mx-t2 var(--mx-t) ease-out infinite}
.mx .mx-t3{animation:mx-t3 var(--mx-t) ease-out infinite}
.mx .mx-t4{animation:mx-t4 var(--mx-t) ease-out infinite}
.mx .mx-cap0{animation:mx-cap0 var(--mx-t) linear infinite}
.mx .mx-cap1{animation:mx-cap1 var(--mx-t) linear infinite}
.mx .mx-cap2{animation:mx-cap2 var(--mx-t) linear infinite}
.mx .mx-cap3{animation:mx-cap3 var(--mx-t) linear infinite}
.mx .mx-cap4{animation:mx-cap4 var(--mx-t) linear infinite}
.mx .mx-cap5{animation:mx-cap5 var(--mx-t) linear infinite}
.mx.mx-off *{animation-play-state:paused}
@keyframes mx-pulse{0%{transform:scale(1);opacity:.7}12%,100%{transform:scale(1.75);opacity:0}}
@keyframes mx-s1{0%,10%{transform:translate(0,0);opacity:0}11%{opacity:1}20%{transform:translate(-118px,-60px);opacity:1}22%,100%{transform:translate(-118px,-60px);opacity:0}}
@keyframes mx-s2{0%,28%{transform:translate(0,0);opacity:0}29%{opacity:1}38%{transform:translate(118px,-60px);opacity:1}40%,100%{transform:translate(118px,-60px);opacity:0}}
@keyframes mx-s3{0%,46%{transform:translate(0,0);opacity:0}47%{opacity:1}56%{transform:translate(-118px,60px);opacity:1}58%,100%{transform:translate(-118px,60px);opacity:0}}
@keyframes mx-s4{0%,64%{transform:translate(0,0);opacity:0}65%{opacity:1}74%{transform:translate(118px,60px);opacity:1}76%,100%{transform:translate(118px,60px);opacity:0}}
@keyframes mx-h1{0%,18%{opacity:0}21%,27%{opacity:1}30%,100%{opacity:0}}
@keyframes mx-h2{0%,36%{opacity:0}39%,45%{opacity:1}48%,100%{opacity:0}}
@keyframes mx-h3{0%,54%{opacity:0}57%,63%{opacity:1}66%,100%{opacity:0}}
@keyframes mx-h4{0%,72%{opacity:0}75%,81%{opacity:1}84%,100%{opacity:0}}
@keyframes mx-t1{0%,20%{opacity:0;transform:scale(.4)}23%{opacity:1;transform:scale(1.15)}25%,93%{opacity:1;transform:scale(1)}97%,100%{opacity:0;transform:scale(1)}}
@keyframes mx-t2{0%,38%{opacity:0;transform:scale(.4)}41%{opacity:1;transform:scale(1.15)}43%,93%{opacity:1;transform:scale(1)}97%,100%{opacity:0;transform:scale(1)}}
@keyframes mx-t3{0%,56%{opacity:0;transform:scale(.4)}59%{opacity:1;transform:scale(1.15)}61%,93%{opacity:1;transform:scale(1)}97%,100%{opacity:0;transform:scale(1)}}
@keyframes mx-t4{0%,74%{opacity:0;transform:scale(.4)}77%{opacity:1;transform:scale(1.15)}79%,93%{opacity:1;transform:scale(1)}97%,100%{opacity:0;transform:scale(1)}}
@keyframes mx-cap0{0%,8%{opacity:1}10%,98%{opacity:0}100%{opacity:1}}
@keyframes mx-cap1{0%,9%{opacity:0}11%,26%{opacity:1}28%,100%{opacity:0}}
@keyframes mx-cap2{0%,27%{opacity:0}29%,44%{opacity:1}46%,100%{opacity:0}}
@keyframes mx-cap3{0%,45%{opacity:0}47%,62%{opacity:1}64%,100%{opacity:0}}
@keyframes mx-cap4{0%,63%{opacity:0}65%,80%{opacity:1}82%,100%{opacity:0}}
@keyframes mx-cap5{0%,81%{opacity:0}83%,95%{opacity:1}98%,100%{opacity:0}}
.mx .mx-play{display:none;margin:6px 4px 0;font:inherit;font-weight:700;font-size:14px;color:#F5EFE4;background:#4A4238;border:0;border-radius:30px;padding:6px 16px;cursor:pointer}
@media (prefers-reduced-motion:reduce){.mx:not(.mx-force) *{animation:none!important}.mx:not(.mx-force) .mx-tick,.mx:not(.mx-force) .mx-slotfill{opacity:1}.mx:not(.mx-force) .mx-cap{opacity:0}.mx:not(.mx-force) .mx-cap5{opacity:1}.mx:not(.mx-force) .mx-play{display:inline-block}}`;

  var MOTIONS = {
    'agentic-ai': { match: /agentic ai/i, html: `<figure class="mx">
    <span class="mx-kicker">What is agentic AI?</span>
    <svg viewBox="0 0 360 272" role="img" aria-label="An AI agent reads a WhatsApp booking request, finds a free slot in the calendar, updates the patient record and emails the confirmation, ticking off each step.">
      <!-- spokes -->
      <g stroke="#4A4238" stroke-opacity=".18" stroke-width="2" stroke-dasharray="4 5">
        <line x1="180" y1="118" x2="62" y2="58"/><line x1="180" y1="118" x2="298" y2="58"/>
        <line x1="180" y1="118" x2="62" y2="178"/><line x1="180" y1="118" x2="298" y2="178"/>
      </g>

      <!-- 1 WhatsApp -->
      <g transform="translate(62 58)">
        <rect x="-27" y="-27" width="54" height="54" rx="15" fill="#FFFDF8" stroke="#4A4238" stroke-opacity=".22" stroke-width="1.5"/>
        <rect class="mx-hl mx-h1" x="-27" y="-27" width="54" height="54" rx="15" fill="none" stroke="#E2571B" stroke-width="2.5"/>
        <rect class="mx-ico" x="-14" y="-12" width="28" height="19" rx="6"/><path class="mx-ico" d="M-7 7 l-3 6 l8 -6"/>
        <line class="mx-ico" x1="-8" y1="-5" x2="8" y2="-5"/><line class="mx-ico" x1="-8" y1="0" x2="3" y2="0"/>
        <text class="mx-lbl" y="46" text-anchor="middle">WhatsApp</text>
        <g class="mx-tick mx-t1"><circle cx="24" cy="-24" r="10" fill="#E2571B"/><path d="M19 -24 l3.5 3.5 l6 -7" fill="none" stroke="#FFFDF8" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></g>
      </g>

      <!-- 2 Calendar -->
      <g transform="translate(298 58)">
        <rect x="-27" y="-27" width="54" height="54" rx="15" fill="#FFFDF8" stroke="#4A4238" stroke-opacity=".22" stroke-width="1.5"/>
        <rect class="mx-hl mx-h2" x="-27" y="-27" width="54" height="54" rx="15" fill="none" stroke="#E2571B" stroke-width="2.5"/>
        <rect class="mx-ico" x="-13" y="-11" width="26" height="24" rx="4"/><line class="mx-ico" x1="-13" y1="-4" x2="13" y2="-4"/>
        <line class="mx-ico" x1="-6" y1="-15" x2="-6" y2="-8"/><line class="mx-ico" x1="6" y1="-15" x2="6" y2="-8"/>
        <rect class="mx-slotfill" x="2" y="1" width="7" height="7" rx="1.5" fill="#E2571B"/>
        <text class="mx-lbl" y="46" text-anchor="middle">Calendar</text>
        <g class="mx-tick mx-t2"><circle cx="24" cy="-24" r="10" fill="#E2571B"/><path d="M19 -24 l3.5 3.5 l6 -7" fill="none" stroke="#FFFDF8" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></g>
      </g>

      <!-- 3 Records -->
      <g transform="translate(62 178)">
        <rect x="-27" y="-27" width="54" height="54" rx="15" fill="#FFFDF8" stroke="#4A4238" stroke-opacity=".22" stroke-width="1.5"/>
        <rect class="mx-hl mx-h3" x="-27" y="-27" width="54" height="54" rx="15" fill="none" stroke="#E2571B" stroke-width="2.5"/>
        <rect class="mx-ico" x="-12" y="-14" width="24" height="28" rx="3"/>
        <line class="mx-ico" x1="-7" y1="-7" x2="7" y2="-7"/><line class="mx-ico" x1="-7" y1="-1" x2="7" y2="-1"/><line class="mx-ico" x1="-7" y1="5" x2="3" y2="5"/>
        <text class="mx-lbl" y="46" text-anchor="middle">Records</text>
        <g class="mx-tick mx-t3"><circle cx="24" cy="-24" r="10" fill="#E2571B"/><path d="M19 -24 l3.5 3.5 l6 -7" fill="none" stroke="#FFFDF8" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></g>
      </g>

      <!-- 4 Email -->
      <g transform="translate(298 178)">
        <rect x="-27" y="-27" width="54" height="54" rx="15" fill="#FFFDF8" stroke="#4A4238" stroke-opacity=".22" stroke-width="1.5"/>
        <rect class="mx-hl mx-h4" x="-27" y="-27" width="54" height="54" rx="15" fill="none" stroke="#E2571B" stroke-width="2.5"/>
        <rect class="mx-ico" x="-14" y="-10" width="28" height="20" rx="3"/><path class="mx-ico" d="M-14 -9 l14 10 l14 -10"/>
        <text class="mx-lbl" y="46" text-anchor="middle">Email</text>
        <g class="mx-tick mx-t4"><circle cx="24" cy="-24" r="10" fill="#E2571B"/><path d="M19 -24 l3.5 3.5 l6 -7" fill="none" stroke="#FFFDF8" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></g>
      </g>

      <!-- travelling signals (start at the agent, end at each tool) -->
      <circle class="mx-sig mx-s1" cx="180" cy="118" r="6" fill="#E2571B"/>
      <circle class="mx-sig mx-s2" cx="180" cy="118" r="6" fill="#E2571B"/>
      <circle class="mx-sig mx-s3" cx="180" cy="118" r="6" fill="#E2571B"/>
      <circle class="mx-sig mx-s4" cx="180" cy="118" r="6" fill="#E2571B"/>

      <!-- the agent -->
      <circle class="mx-ring" cx="180" cy="118" r="30" fill="none" stroke="#E2571B" stroke-width="2"/>
      <circle cx="180" cy="118" r="30" fill="#E2571B"/>
      <text class="mx-agent" x="180" y="125" text-anchor="middle">AI</text>
      <text class="mx-lbl" x="180" y="170" text-anchor="middle">Agent</text>

      <!-- narration -->
      <text class="mx-cap mx-cap0" x="180" y="262" text-anchor="middle">Goal: book a patient in for Tuesday</text>
      <text class="mx-cap mx-cap1" x="180" y="262" text-anchor="middle">1 · Reads the WhatsApp request</text>
      <text class="mx-cap mx-cap2" x="180" y="262" text-anchor="middle">2 · Finds a free slot in the calendar</text>
      <text class="mx-cap mx-cap3" x="180" y="262" text-anchor="middle">3 · Updates the patient record</text>
      <text class="mx-cap mx-cap4" x="180" y="262" text-anchor="middle">4 · Emails the confirmation</text>
      <text class="mx-cap mx-cap5" x="180" y="262" text-anchor="middle">Done. Four steps, zero hand-offs.</text>
    </svg>
    <button type="button" class="mx-play">▶ Play animation</button>
    <figcaption><b>Agentic AI</b> — instead of answering one question, the AI plans the steps and uses your tools to finish the job.</figcaption>
  </figure>` }
  };

  function place(){
    if (!document.querySelector('.mx-slot')) {
      var strip = document.querySelector('.strip');
      if (strip) {
        var txt = strip.textContent, best = null, at = Infinity;
        Object.keys(MOTIONS).forEach(function(id){
          var pos = txt.search(MOTIONS[id].match);
          if (pos >= 0 && pos < at) { at = pos; best = id; }
        });
        if (best) {
          var slot = document.createElement('div');
          slot.className = 'mx-slot'; slot.setAttribute('data-motion', best);
          strip.parentNode.insertBefore(slot, strip.nextSibling);
        }
      }
    }
    var slots = document.querySelectorAll('.mx-slot[data-motion]');
    if (!slots.length) return;
    if (!document.getElementById('mx-style')) {
      var st = document.createElement('style'); st.id = 'mx-style'; st.textContent = CSS;
      document.head.appendChild(st);
    }
    slots.forEach(function(slot){ var m = MOTIONS[slot.getAttribute('data-motion')]; if (m) slot.innerHTML = m.html; });

    var figs = document.querySelectorAll('.mx');
    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function(entries){
        entries.forEach(function(e){
          if (e.isIntersecting) { e.target.setAttribute('data-seen', '1'); e.target.classList.remove('mx-off'); }
          else if (e.target.getAttribute('data-seen')) { e.target.classList.add('mx-off'); }
        });
      });
      figs.forEach(function(f){ io.observe(f); });
    }
    document.querySelectorAll('.mx-play').forEach(function(b){
      b.addEventListener('click', function(){ b.closest('.mx').classList.add('mx-force'); });
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', place); else place();
})();
