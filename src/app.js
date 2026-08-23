/* CCAO-F practice deck — drill engine.
   Two modes: practice marks on commit, exam holds everything until submit. */
(function () {
  'use strict';

  const BANK = window.BANK;
  const Q = BANK.questions;
  const DOMS = BANK.domains;
  const DMAP = Object.fromEntries(DOMS.map(d => [d.id, d]));
  const META = BANK.meta;
  const PASS = META.pass_scaled || 720;
  const DC = id => `var(--${DMAP[id].accent})`;

  const LENGTHS = [10, 20, 40, 60, 100, 250];
  const MODES = [
    { id: 'practice', label: 'Practice', note: 'Marked as you go. Commit to an answer, see immediately whether it was right, and read why before moving on. This is the mode for learning the material.' },
    { id: 'exam', label: 'Exam simulation', note: 'Nothing is revealed until you submit. Move back and forth and change answers as you would in the real exam, against a two-minutes-per-question clock, then get a scaled 100–1000 result.' }
  ];

  const $ = s => document.querySelector(s);
  const $$ = s => [...document.querySelectorAll(s)];
  const el = (tag, cls, html) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (html != null) n.innerHTML = html;
    return n;
  };
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  /* ── persistence ─────────────────────────────────────────── */
  const KEY = 'ccao.deck.v1';
  const blank = () => ({ seen: {}, topics: {}, doubts: {}, history: [] });
  let S = blank();
  try { S = Object.assign(blank(), JSON.parse(localStorage.getItem(KEY) || '{}')); } catch (e) { S = blank(); }
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {} };

  /* ── chrome ──────────────────────────────────────────────── */
  const SCREENS = { home: '#s-home', quiz: '#s-quiz', results: '#s-results', bank: '#s-bank', blueprint: '#s-blueprint' };
  function go(name) {
    Object.entries(SCREENS).forEach(([k, sel]) => { $(sel).hidden = k !== name; });
    $$('.navlink').forEach(b => b.classList.toggle('on', b.dataset.go === name));
    window.scrollTo(0, 0);
    if (name === 'home') renderHome();
    if (name === 'bank') renderBank();
    if (name === 'blueprint') renderBlueprint();
  }
  document.addEventListener('click', e => {
    const b = e.target.closest('[data-go]');
    if (b) go(b.dataset.go);
  });
  $('#brand').addEventListener('click', () => go('home'));

  let toastT;
  function toast(msg, ms) {
    const t = $('#toast');
    t.textContent = msg; t.hidden = false;
    clearTimeout(toastT);
    toastT = setTimeout(() => { t.hidden = true; }, ms || 2800);
  }

  /* ── progress helpers ────────────────────────────────────── */
  const seenCount = () => Object.keys(S.seen).length;
  const doubtCount = () => Object.keys(S.doubts).length;
  function weakConcepts() {
    return Object.entries(S.topics)
      .filter(([, t]) => t.n >= 2 && t.ok / t.n < 0.7)
      .sort((a, b) => a[1].ok / a[1].n - b[1].ok / b[1].n)
      .map(([c]) => c);
  }

  /* ── session selection ───────────────────────────────────── */
  const sel = { mode: 'practice', len: 20, doms: DOMS.map(d => d.id) };

  function chips(target, items, isOn, onPick) {
    const wrap = $(target);
    wrap.innerHTML = '';
    items.forEach(it => {
      const c = el('button', 'chip' + (isOn(it.id) ? ' on' : ''), esc(it.label));
      if (it.dom) { c.dataset.dc = '1'; c.style.setProperty('--dc', DC(it.dom)); }
      c.onclick = () => onPick(it.id);
      wrap.appendChild(c);
    });
  }

  /* largest-remainder apportionment across the live domains */
  function apportion(total, domIds) {
    const w = domIds.map(id => DMAP[id].weight);
    const sum = w.reduce((a, b) => a + b, 0) || 1;
    const exact = w.map(x => total * x / sum);
    const base = exact.map(Math.floor);
    let left = total - base.reduce((a, b) => a + b, 0);
    const order = exact.map((x, i) => [x - base[i], i]).sort((a, b) => b[0] - a[0]);
    for (let k = 0; k < order.length && left > 0; k++, left--) base[order[k][1]]++;
    return Object.fromEntries(domIds.map((id, i) => [id, base[i]]));
  }

  function renderSplit() {
    const out = $('#splitOut');
    out.innerHTML = '';
    if (!sel.doms.length) { out.appendChild(el('span', 'empty', 'Pick at least one domain.')); return; }
    const split = apportion(sel.len, sel.doms);
    sel.doms.forEach(id => {
      const p = el('span', 'splitpill', `<span class="sv">${split[id]}</span><span class="sn">${esc(DMAP[id].short)}</span>`);
      p.style.setProperty('--sc', DC(id));
      out.appendChild(p);
    });
  }

  function renderHome() {
    $('#statTotal').textContent = META.total;

    const grid = $('#domGrid');
    grid.innerHTML = '';
    DOMS.forEach(d => {
      const held = Q.filter(q => q.domain === d.id).length;
      let n = 0, ok = 0;
      Object.keys(BANK.concepts[d.id] || {}).forEach(c => {
        if (S.topics[c]) { n += S.topics[c].n; ok += S.topics[c].ok; }
      });
      const card = el('div', 'domcard');
      card.style.setProperty('--dc', DC(d.id));
      card.innerHTML =
        `<span class="dn">${esc(d.name)}</span>` +
        `<span class="dw">${d.weight}<small>% of the exam</small></span>` +
        `<p class="dq">${held} in the bank · about ${Math.round(60 * d.weight / 100)} of the exam's 60` +
        (n ? ` · you ${Math.round(100 * ok / n)}% over ${n}` : '') + `</p>` +
        `<div class="dbar"></div>`;
      grid.appendChild(card);
    });

    const pg = $('#progressPanel');
    if (seenCount()) {
      pg.hidden = false;
      const tot = Object.values(S.topics).reduce((a, t) => a + t.n, 0);
      const ok = Object.values(S.topics).reduce((a, t) => a + t.ok, 0);
      $('#pgSeen').textContent = seenCount();
      $('#pgAcc').textContent = tot ? Math.round(100 * ok / tot) + '%' : '—';
      $('#pgDoubt').textContent = doubtCount();
      $('#pgLeft').textContent = Q.length - seenCount();
      const weak = weakConcepts();
      $('#weakWrap').hidden = !weak.length;
      const wc = $('#weakChips');
      wc.innerHTML = '';
      weak.slice(0, 12).forEach(c => wc.appendChild(el('span', 'chip mini', esc(c))));
    } else {
      pg.hidden = true;
    }

    chips('#modeChips', MODES.map(m => ({ id: m.id, label: m.label })),
      v => sel.mode === v, v => { sel.mode = v; renderHome(); });
    $('#modeNote').textContent = MODES.find(m => m.id === sel.mode).note;

    chips('#lenChips', LENGTHS.map(n => ({ id: n, label: n + ' questions' })),
      v => sel.len === v, v => { sel.len = v; renderHome(); });

    chips('#domChips', DOMS.map(d => ({ id: d.id, dom: d.id, label: d.short + ' · ' + d.weight + '%' })),
      v => sel.doms.includes(v),
      v => {
        const i = sel.doms.indexOf(v);
        if (i < 0) sel.doms.push(v); else if (sel.doms.length > 1) sel.doms.splice(i, 1);
        sel.doms.sort((a, b) => DOMS.findIndex(d => d.id === a) - DOMS.findIndex(d => d.id === b));
        renderHome();
      });

    renderSplit();
  }

  $('#allDoms').onclick = () => { sel.doms = DOMS.map(d => d.id); renderHome(); };
  $('#resetBtn').onclick = () => {
    if (!confirm('Clear your answer history, flags and progress on this device?')) return;
    S = blank(); save(); renderHome(); toast('Progress cleared.');
  };

  /* ── drawing a session ───────────────────────────────────── */
  function shuffle(pool) {
    const a = pool.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }
  const pick = (pool, n) => shuffle(pool).slice(0, n);

  function draw() {
    const split = apportion(sel.len, sel.doms);
    const weak = new Set(weakConcepts());
    const out = [];
    sel.doms.forEach(id => {
      const want = split[id];
      if (!want) return;
      const all = Q.filter(q => q.domain === id);
      const unseen = all.filter(q => !S.seen[q.id]);
      const pool = unseen.length >= want ? unseen : all;
      const weakPool = pool.filter(q => weak.has(q.concept));
      const chosen = pick(weakPool, Math.min(Math.floor(want * 0.4), weakPool.length));
      const taken = new Set(chosen.map(q => q.id));
      chosen.push(...pick(pool.filter(q => !taken.has(q.id)), want - chosen.length));
      out.push(...chosen);
    });
    return shuffle(out);
  }

  /* ── quiz ────────────────────────────────────────────────── */
  let run = null;

  function startSession() {
    if (!sel.doms.length) { toast('Pick at least one domain first.'); return; }
    const items = draw();
    if (!items.length) { toast('No questions available for that selection.'); return; }
    run = {
      mode: sel.mode,
      items, i: 0,
      answers: new Array(items.length).fill(null),
      marked: new Array(items.length).fill(false),
      started: Date.now(),
      limitMs: sel.mode === 'exam' ? items.length * 2 * 60 * 1000 : 0
    };
    go('quiz');
    renderQ();
    if (run.mode === 'exam') startTimer(); else stopTimer();
  }
  $('#startBtn').onclick = startSession;

  let timerT = null;
  function startTimer() {
    const t = $('#qTimer');
    t.hidden = false;
    const tick = () => {
      if (!run || run.mode !== 'exam') return;
      const left = run.limitMs - (Date.now() - run.started);
      if (left <= 0) { t.textContent = 'time up'; finish(); return; }
      const m = Math.floor(left / 60000), s = Math.floor((left % 60000) / 1000);
      t.textContent = m + ':' + String(s).padStart(2, '0');
      t.classList.toggle('low', left < 300000);
    };
    tick();
    clearInterval(timerT);
    timerT = setInterval(tick, 1000);
  }
  function stopTimer() { clearInterval(timerT); timerT = null; $('#qTimer').hidden = true; }

  function renderRail() {
    const rail = $('#rail');
    rail.innerHTML = '';
    run.items.forEach((q, i) => {
      const seg = el('i');
      if (run.mode === 'practice') {
        if (run.marked[i]) seg.className = run.answers[i] === q.answer ? 'hit' : 'miss';
      } else if (run.answers[i] != null) seg.className = 'hit';
      if (i === run.i) seg.className = 'now';
      if (run.mode === 'exam') { seg.style.cursor = 'pointer'; seg.onclick = () => { run.i = i; renderQ(); }; }
      rail.appendChild(seg);
    });
  }

  function renderQ() {
    const q = run.items[run.i];
    const d = DMAP[q.domain];
    $('#qCount').textContent = (run.i + 1) + ' / ' + run.items.length;
    const dp = $('#qDomain');
    dp.textContent = d.short; dp.dataset.dc = '1'; dp.style.setProperty('--dc', DC(q.domain));
    $('#qConcept').textContent = q.concept;
    $('#stem').textContent = q.stem;
    $('#doubtBtn').classList.toggle('on', !!S.doubts[q.id]);

    const practice = run.mode === 'practice';
    const marked = run.marked[run.i];

    const opts = $('#options');
    opts.innerHTML = '';
    q.options.forEach((text, i) => {
      const b = el('button', 'option', `<span class="marker">${'ABCD'[i]}</span><span class="otext">${esc(text)}</span>`);
      if (run.answers[run.i] === i) b.classList.add('selected');
      if (practice && marked) {
        b.disabled = true;
        if (i === q.answer) b.classList.add('correct');
        else if (i === run.answers[run.i]) b.classList.add('incorrect');
      }
      b.onclick = () => {
        if (practice && run.marked[run.i]) return;
        run.answers[run.i] = i;
        renderQ();
      };
      opts.appendChild(b);
    });

    $('#checkBtn').hidden = !practice || marked;
    $('#checkBtn').disabled = run.answers[run.i] == null;
    $('#prevBtn').hidden = practice || run.i === 0;
    $('#advBtn').hidden = practice;
    $('#advBtn').textContent = run.i === run.items.length - 1 ? 'Submit exam' : 'Next';
    $('#feedback').hidden = !(practice && marked);
    if (practice && marked) showFeedback();
    renderRail();
  }

  function showFeedback() {
    const q = run.items[run.i];
    const ok = run.answers[run.i] === q.answer;
    const v = $('#verdict');
    v.className = 'verdict ' + (ok ? 'ok' : 'no');
    v.innerHTML = `<span class="g">${ok ? '✓' : '✕'}</span>` +
      (ok ? 'Correct' : 'Not quite — the answer is ' + 'ABCD'[q.answer]);
    $('#exWhyH').textContent = ok ? 'Why that answer is right' : 'Why ' + 'ABCD'[q.answer] + ' is right';
    $('#exWhy').textContent = q.why;
    $('#exTraps').textContent = q.traps;
    $('#nextBtn').textContent = run.i === run.items.length - 1 ? 'See my results' : 'Next question';
  }

  function record(i) {
    const q = run.items[i];
    S.seen[q.id] = 1;
    const t = S.topics[q.concept] || (S.topics[q.concept] = { n: 0, ok: 0 });
    t.n++; if (run.answers[i] === q.answer) t.ok++;
  }

  $('#checkBtn').onclick = () => {
    if (run.answers[run.i] == null) return;
    run.marked[run.i] = true;
    record(run.i); save(); renderQ();
  };
  $('#nextBtn').onclick = () => {
    if (run.i === run.items.length - 1) { finish(); return; }
    run.i++; renderQ();
  };
  $('#advBtn').onclick = () => {
    if (run.i === run.items.length - 1) {
      const un = run.answers.filter(a => a == null).length;
      if (un && !confirm(un + ' question' + (un > 1 ? 's are' : ' is') + ' still unanswered. Submit anyway?')) return;
      finish(); return;
    }
    run.i++; renderQ();
  };
  $('#prevBtn').onclick = () => { if (run.i > 0) { run.i--; renderQ(); } };
  $('#doubtBtn').onclick = () => {
    const q = run.items[run.i];
    if (S.doubts[q.id]) delete S.doubts[q.id]; else S.doubts[q.id] = 1;
    save(); renderQ();
    toast(S.doubts[q.id] ? 'Flagged for review.' : 'Flag removed.');
  };
  $('#quitBtn').onclick = () => {
    if (confirm('End this session and see your results so far?')) finish();
  };

  /* ── results ─────────────────────────────────────────────── */
  function finish() {
    stopTimer();
    run.items.forEach((q, i) => { if (!run.marked[i]) { run.marked[i] = true; record(i); } });
    save();

    const n = run.items.length;
    const correct = run.items.reduce((a, q, i) => a + (run.answers[i] === q.answer ? 1 : 0), 0);
    const pct = Math.round(100 * correct / n);

    const per = {};
    run.items.forEach((q, i) => {
      const p = per[q.domain] || (per[q.domain] = { n: 0, ok: 0 });
      p.n++; if (run.answers[i] === q.answer) p.ok++;
    });
    const live = Object.keys(per);
    const wsum = live.reduce((a, id) => a + DMAP[id].weight, 0) || 1;
    const weighted = live.reduce((a, id) => a + (per[id].ok / per[id].n) * DMAP[id].weight, 0) / wsum;
    const scaled = Math.round(100 + weighted * 900);

    $('#scorePct').textContent = pct + '%';
    $('#scoreLine').textContent = `${correct} of ${n} correct · ${run.mode === 'exam' ? 'exam simulation' : 'practice session'}`;
    $('#scaledOut').textContent = scaled;
    $('#scaleFill').style.width = Math.max(0, Math.min(100, (scaled - 100) / 9)) + '%';

    const r = $('#readiness');
    if (n < 20) {
      r.textContent = `A ${n}-question run is too short to say much about readiness — the margin of error is wide. Treat this as a drill rather than a verdict.`;
    } else if (scaled >= PASS + 60) {
      r.textContent = `Comfortably above the 720 pass mark on this sample. Keep the weaker domains ticking over, then sit a full 60-question exam simulation to confirm.`;
    } else if (scaled >= PASS) {
      r.textContent = `Above 720, but not by much. A sample this size carries real margin of error, so read this as on-track rather than ready.`;
    } else {
      r.textContent = `Below the 720 pass mark on this sample. The per-domain breakdown below shows where the ground is softest.`;
    }

    const db = $('#domBreak');
    db.innerHTML = '';
    DOMS.filter(d => per[d.id]).forEach(d => {
      const p = per[d.id];
      const a = Math.round(100 * p.ok / p.n);
      const tag = p.n < 3 ? 'thin' : a >= 80 ? 'strong' : a >= 60 ? 'review' : 'weak';
      const label = p.n < 3 ? 'Thin' : a >= 80 ? 'Strong' : a >= 60 ? 'Fair' : 'Weak';
      const row = el('div', 'dbrow');
      row.style.setProperty('--dc', DC(d.id));
      row.innerHTML =
        `<span class="dbn">${esc(d.name)}<i>${p.ok} of ${p.n} correct · ${d.weight}% of the exam</i></span>` +
        `<span class="dbs">${a}%</span>` +
        `<span class="tag ${tag}">${label}</span>`;
      db.appendChild(row);
    });

    S.history.push({ at: Date.now(), mode: run.mode, n, correct, scaled });
    if (S.history.length > 60) S.history = S.history.slice(-60);
    save();
    go('results');
  }

  $('#againBtn').onclick = () => go('home');
  $('#reviewMissed').onclick = () => {
    const missed = run ? run.items.filter((q, i) => run.answers[i] !== q.answer) : [];
    if (!missed.length) { toast('Nothing missed in that session.'); return; }
    bankState.explicit = missed.map(q => q.id);
    bankState.view = 'explicit';
    go('bank');
  };

  /* ── bank browser ────────────────────────────────────────── */
  const bankState = { q: '', doms: DOMS.map(d => d.id), view: 'all', topic: null, limit: 25, explicit: null };

  function bankPool() {
    if (bankState.view === 'explicit' && bankState.explicit) {
      const set = new Set(bankState.explicit);
      return Q.filter(q => set.has(q.id));
    }
    let pool = Q.filter(q => bankState.doms.includes(q.domain));
    if (bankState.view === 'doubts') pool = pool.filter(q => S.doubts[q.id]);
    if (bankState.view === 'unseen') pool = pool.filter(q => !S.seen[q.id]);
    if (bankState.topic) pool = pool.filter(q => q.concept === bankState.topic);
    const needle = bankState.q.trim().toLowerCase();
    if (needle) {
      pool = pool.filter(q =>
        q.stem.toLowerCase().includes(needle) ||
        q.concept.toLowerCase().includes(needle) ||
        q.options.some(o => o.toLowerCase().includes(needle)) ||
        q.why.toLowerCase().includes(needle));
    }
    return pool;
  }

  function renderBank() {
    chips('#bankDomChips', DOMS.map(d => ({ id: d.id, dom: d.id, label: d.short })),
      v => bankState.doms.includes(v),
      v => {
        const i = bankState.doms.indexOf(v);
        if (i < 0) bankState.doms.push(v); else bankState.doms.splice(i, 1);
        if (bankState.view === 'explicit') { bankState.view = 'all'; bankState.explicit = null; }
        bankState.limit = 25; renderBank();
      });

    const views = [{ id: 'all', label: 'All' }, { id: 'unseen', label: 'Not yet seen' }, { id: 'doubts', label: 'Flagged (' + doubtCount() + ')' }];
    if (bankState.explicit) views.push({ id: 'explicit', label: 'Missed last session' });
    chips('#bankViewChips', views, v => bankState.view === v,
      v => { bankState.view = v; bankState.limit = 25; renderBank(); });

    const topics = new Set();
    Q.filter(q => bankState.doms.includes(q.domain)).forEach(q => topics.add(q.concept));
    chips('#bankTopicChips', [{ id: null, label: 'Any topic' }].concat([...topics].sort().map(t => ({ id: t, label: t }))),
      v => bankState.topic === v,
      v => { bankState.topic = v; bankState.limit = 25; renderBank(); });

    const pool = bankPool();
    $('#bankCount').textContent = pool.length
      ? `${pool.length} question${pool.length === 1 ? '' : 's'} matching`
      : 'Nothing matches that combination.';

    const list = $('#bankList');
    list.innerHTML = '';
    if (!pool.length) list.appendChild(el('p', 'empty', 'Nothing matches that combination.'));
    pool.slice(0, bankState.limit).forEach(q => list.appendChild(bankCard(q)));
    $('#bankMore').hidden = pool.length <= bankState.limit;
  }

  function bankCard(q) {
    const d = DMAP[q.domain];
    const card = el('article', 'bq');
    const head = el('button', 'bq-head');
    head.innerHTML =
      `<span class="bq-tags"><span class="pill" data-dc="1" style="--dc:${DC(q.domain)}">${esc(d.short)}</span>` +
      `<span class="pill">${esc(q.concept)}</span>` +
      (S.doubts[q.id] ? '<span class="pill">flagged</span>' : '') + '</span>' +
      `<span class="bq-stem">${esc(q.stem)}</span>`;
    const body = el('div', 'bq-body');
    body.hidden = true;
    body.innerHTML =
      q.options.map((o, i) =>
        `<div class="bq-opt${i === q.answer ? ' right' : ''}"><span class="m">${'ABCD'[i]}</span><span>${esc(o)}</span></div>`).join('') +
      `<div class="expl expl-mint"><h4>Why</h4><p>${esc(q.why)}</p></div>` +
      `<div class="expl expl-indigo"><h4>The traps</h4><p>${esc(q.traps)}</p></div>`;
    head.onclick = () => { body.hidden = !body.hidden; };
    card.append(head, body);
    return card;
  }

  $('#bankSearch').addEventListener('input', e => { bankState.q = e.target.value; bankState.limit = 25; renderBank(); });
  $('#bankMore').onclick = () => { bankState.limit += 25; renderBank(); };

  /* ── blueprint ───────────────────────────────────────────── */
  function renderBlueprint() {
    const g = $('#bpGrid');
    g.innerHTML = '';
    DOMS.forEach(d => {
      const held = Q.filter(q => q.domain === d.id).length;
      const row = el('div', 'dbrow');
      row.style.setProperty('--dc', DC(d.id));
      row.innerHTML =
        `<span class="dbn">${esc(d.name)}<i>${Math.round(60 * d.weight / 100)} of the exam's 60 questions · ${held} held here</i></span>` +
        `<span class="dbs">${d.weight}%</span>` +
        `<span class="tag review">${held}</span>`;
      g.appendChild(row);
    });
  }

  /* ── keyboard ────────────────────────────────────────────── */
  document.addEventListener('keydown', e => {
    if ($('#s-quiz').hidden || e.target.tagName === 'INPUT') return;
    const idx = 'abcd'.indexOf(e.key.toLowerCase());
    if (idx >= 0) {
      const btns = $$('#options .option');
      if (btns[idx] && !btns[idx].disabled) btns[idx].click();
    } else if (e.key === 'Enter') {
      for (const s of ['#nextBtn', '#checkBtn', '#advBtn']) {
        const b = $(s);
        if (b && !b.hidden && !b.disabled) { b.click(); break; }
      }
    } else if (e.key === 'ArrowLeft') { const b = $('#prevBtn'); if (b && !b.hidden) b.click(); }
    else if (e.key === 'ArrowRight') { const b = $('#advBtn'); if (b && !b.hidden) b.click(); }
  });

  go('home');
})();
