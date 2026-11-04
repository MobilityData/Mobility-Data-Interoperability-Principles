/*
 * MDIP specification registry - progressive enhancement.
 *
 * Every row and every filter control is already in the HTML when this runs;
 * the script only hides, reorders and counts them. With JavaScript off the
 * page is still the complete list, which is why nothing here renders markup
 * for the specifications themselves.
 *
 * Filter semantics: OR inside one facet, AND across facets. State lives in the
 * query string so a filtered view can be linked to and survives back/forward.
 */
(function () {
  "use strict";

  var FACETS = [
    "mode", "status", "confirmed", "lifecycle", "adoption_tier",
    "licence", "licence_category", "maintainer", "maintainer_type", "decade",
    "criterion_cost_restriction_free", "criterion_publicly_documented",
    "criterion_independent_maintainer", "criterion_open_governance",
    "criterion_structured_releases"
  ];

  var SEP = "::";
  var DEFAULT_SORT = "default";

  /* Where this file is served from, to find vendor/ next to it. Only known
     while the script first runs. */
  var SCRIPT_SRC = document.currentScript ? document.currentScript.src : "";

  function ready(fn) {
    if (document.readyState !== "loading") { fn(); }
    else { document.addEventListener("DOMContentLoaded", fn); }
  }

  ready(function () {
    if (document.querySelector(".mdip-specs, .mdip-spec")) {
      document.body.classList.add("mdip-fullbleed");
    }
    initStickyOffset();
    initList();
    initDetail();
    initHistory();
    initDisclosureAnchors();
  });

  /* A link to a collapsed <details> by id (the detail pages link to
     #scoring) should land on it open, not on a closed summary line. */
  function initDisclosureAnchors() {
    function openTarget() {
      var id = location.hash.slice(1);
      var el = id && document.getElementById(id);
      if (el && el.tagName === "DETAILS" && !el.open) {
        el.open = true;
        el.scrollIntoView();
      }
    }
    openTarget();
    window.addEventListener("hashchange", openTarget);
  }

  /* -------------------------------------------------------- sticky offset */

  /*
   * Publish Material's header height as --hdr on the registry roots, so the
   * bars that stick under it (the filter panel, the in-page nav) start exactly
   * at its bottom edge instead of guessing.
   *
   * It cannot be a constant: the header is one row on a phone, a taller row
   * once the custom logo has space, and a row plus a tab strip above
   * Material's tabs breakpoint -- and `navigation.tabs.sticky` keeps the tab
   * strip inside the sticky header, so it counts. The CSS default (one row)
   * is the no-JS fallback and is right at the width where JS is most likely
   * to be missing.
   */
  function initStickyOffset() {
    var roots = Array.prototype.slice.call(
      document.querySelectorAll(".mdip-specs, .mdip-spec")
    );
    var header = document.querySelector(".md-header");
    if (!roots.length || !header) { return; }

    var last = -1;
    var queued = false;

    function publish() {
      queued = false;
      var h = Math.round(header.getBoundingClientRect().height);
      if (h === last || h <= 0) { return; }
      last = h;
      roots.forEach(function (root) { root.style.setProperty("--hdr", h + "px"); });
    }

    function schedule() {
      if (queued) { return; }
      queued = true;
      requestAnimationFrame(publish);
    }

    publish();
    if ("ResizeObserver" in window) {
      new ResizeObserver(schedule).observe(header);
    } else {
      window.addEventListener("resize", schedule);
    }
    /* A late web font can change the header's height after first paint. */
    if (document.fonts && document.fonts.ready) { document.fonts.ready.then(schedule); }
  }

  /* ---------------------------------------------------------------- listing */

  function initList() {
    var root = document.querySelector("[data-specs-root]");
    if (!root) { return; }

    var payload = root.querySelector("[data-specs-json]");
    var data = {};
    try {
      JSON.parse(payload.textContent).specs.forEach(function (s) { data[s.id] = s; });
    } catch (e) {
      return;                       // leave the server-rendered list untouched
    }

    var panel = root.querySelector("[data-panel]");
    var grid = root.querySelector("[data-grid]");
    /* Specifications with no published finding live in a second, collapsed
       list under the first. Both are filtered and sorted as one set; each row
       is only ever re-inserted into the list it was rendered into. */
    var deferBox = root.querySelector("[data-defer]");
    var deferGrid = root.querySelector("[data-grid-defer]");
    var deferCountEl = root.querySelector("[data-defer-count]");
    var rowsOf = function (list) {
      return list ? Array.prototype.slice.call(list.querySelectorAll(".spec-row")) : [];
    };
    var mainRows = rowsOf(grid);
    var deferRows = rowsOf(deferGrid);
    var cards = mainRows.concat(deferRows);
    var shownEl = root.querySelector("[data-shown]");
    var emptyEl = root.querySelector("[data-empty]");
    var chipsEl = root.querySelector("[data-chips]");
    var sortEl = root.querySelector("[data-sort]");
    var qEl = root.querySelector("[data-q]");
    var activeCountEl = root.querySelector("[data-active-count]");
    var boxes = Array.prototype.slice.call(panel.querySelectorAll('input[type="checkbox"]'));
    var labelOf = {};

    boxes.forEach(function (b) {
      var name = b.parentNode.querySelector(".facet__name");
      labelOf[b.name + SEP + b.value] = name ? name.textContent : b.value;
    });

    var suppressPush = false;

    function selection() {
      var sel = {};
      boxes.forEach(function (b) {
        if (!b.checked) { return; }
        (sel[b.name] = sel[b.name] || []).push(b.value);
      });
      return sel;
    }

    function matches(rec, sel, q) {
      for (var key in sel) {
        if (!Object.prototype.hasOwnProperty.call(sel, key)) { continue; }
        var want = sel[key];
        var have = rec[key] || [];
        var hit = false;
        for (var i = 0; i < want.length; i++) {
          if (have.indexOf(want[i]) !== -1) { hit = true; break; }
        }
        if (!hit) { return false; }
      }
      if (q) {
        var terms = q.split(/\s+/);
        for (var j = 0; j < terms.length; j++) {
          if (rec.t.indexOf(terms[j]) === -1) { return false; }
        }
      }
      return true;
    }

    function apply(push) {
      var sel = selection();
      var q = (qEl.value || "").trim().toLowerCase();
      var shown = 0;

      cards.forEach(function (card) {
        var rec = data[card.getAttribute("data-spec")];
        var ok = rec ? matches(rec, sel, q) : true;
        card.hidden = !ok;
        if (ok) { shown++; }
      });

      var shownMain = mainRows.filter(visible).length;
      var shownDefer = deferRows.filter(visible).length;

      shownEl.textContent = shown;
      emptyEl.hidden = shown !== 0;
      grid.hidden = shownMain === 0;
      if (deferBox) {
        deferBox.hidden = shownDefer === 0;
        deferCountEl.textContent = shownDefer;
        /* Filtering to a status that only exists down there would otherwise
           look like an empty result. */
        if (shownDefer > 0 && shownMain === 0) { deferBox.open = true; }
      }

      var nActive = 0;
      for (var k in sel) {
        if (Object.prototype.hasOwnProperty.call(sel, k)) { nActive += sel[k].length; }
      }
      if (q) { nActive++; }

      activeCountEl.hidden = nActive === 0;
      activeCountEl.textContent = nActive;

      Array.prototype.forEach.call(root.querySelectorAll("[data-clear-all]"), function (b) {
        if (b.classList.contains("ghost")) { b.hidden = nActive === 0; }
      });

      Array.prototype.forEach.call(panel.querySelectorAll(".facet"), function (facet) {
        var key = facet.getAttribute("data-facet");
        var badge = facet.querySelector("[data-facet-count]");
        var n = (sel[key] || []).length;
        badge.hidden = n === 0;
        badge.textContent = n;
        if (n > 0) { facet.open = true; }
      });

      renderChips(sel, q);
      sortCards();
      if (push !== false) { pushState(sel, q); }
    }

    function renderChips(sel, q) {
      chipsEl.innerHTML = "";
      var any = false;

      if (q) {
        any = true;
        chipsEl.appendChild(chip('"' + q + '"', function () {
          qEl.value = "";
          apply();
        }));
      }
      Object.keys(sel).forEach(function (key) {
        sel[key].forEach(function (value) {
          any = true;
          chipsEl.appendChild(chip(labelOf[key + SEP + value] || value, function () {
            boxes.forEach(function (b) {
              if (b.name === key && b.value === value) { b.checked = false; }
            });
            apply();
          }));
        });
      });
      chipsEl.hidden = !any;
    }

    function chip(text, onRemove) {
      var el = document.createElement("span");
      el.className = "chip";
      var label = document.createElement("span");
      label.textContent = text;
      var btn = document.createElement("button");
      btn.type = "button";
      btn.setAttribute("aria-label", "Remove filter " + text);
      btn.innerHTML = '<svg class="mdip-i" viewBox="0 0 24 24" aria-hidden="true">' +
        '<path fill="currentColor" d="M19 6.41 17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59' +
        ' 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>';
      btn.addEventListener("click", onRemove);
      el.appendChild(label);
      el.appendChild(btn);
      return el;
    }

    function visible(row) { return !row.hidden; }

    /* Sort keys are arrays: compare element by element, and fall back to the
       name so two specifications with identical keys keep a stable order. */
    function compareKeys(ka, kb) {
      var n = Math.min(ka.length, kb.length);
      for (var i = 0; i < n; i++) {
        if (ka[i] < kb[i]) { return -1; }
        if (ka[i] > kb[i]) { return 1; }
      }
      return 0;
    }

    function sortCards() {
      var mode = sortEl.value;
      [[grid, mainRows], [deferGrid, deferRows]].forEach(function (pair) {
        var list = pair[0];
        if (!list) { return; }
        pair[1].filter(visible).sort(function (a, b) {
          var ra = data[a.getAttribute("data-spec")];
          var rb = data[b.getAttribute("data-spec")];
          if (!ra || !rb) { return 0; }
          var order = compareKeys(ra.sort[mode] || [], rb.sort[mode] || []);
          if (order !== 0) { return order; }
          return compareKeys(ra.sort.name, rb.sort.name);
        }).forEach(function (row) { list.appendChild(row); });
      });
    }

    /* -- url state -------------------------------------------------------- */

    function pushState(sel, q) {
      if (suppressPush) { return; }
      var params = new URLSearchParams();
      FACETS.forEach(function (key) {
        (sel[key] || []).forEach(function (v) { params.append(key, v); });
      });
      if (q) { params.set("q", q); }
      if (sortEl.value !== DEFAULT_SORT) { params.set("sort", sortEl.value); }
      var qs = params.toString();
      history.replaceState(null, "", location.pathname + (qs ? "?" + qs : ""));
    }

    function readState() {
      var params = new URLSearchParams(location.search);
      suppressPush = true;
      boxes.forEach(function (b) { b.checked = false; });
      FACETS.forEach(function (key) {
        var values = params.getAll(key);
        if (!values.length) { return; }
        boxes.forEach(function (b) {
          if (b.name === key && values.indexOf(b.value) !== -1) { b.checked = true; }
        });
      });
      qEl.value = params.get("q") || "";
      /* An old link may carry a sort mode that no longer exists; setting it
         would blank the select and sortCards would compare undefined keys. */
      var s = params.get("sort");
      if (s && sortEl.querySelector('option[value="' + CSS.escape(s) + '"]')) {
        sortEl.value = s;
      } else {
        sortEl.value = DEFAULT_SORT;
      }
      suppressPush = false;
    }

    /* -- facet option search ---------------------------------------------- */

    Array.prototype.forEach.call(panel.querySelectorAll("[data-facet-search]"), function (input) {
      var facet = input.closest(".facet");
      var items = Array.prototype.slice.call(facet.querySelectorAll(".facet__item"));
      var none = facet.querySelector(".facet__none");
      input.addEventListener("input", function () {
        var needle = input.value.trim().toLowerCase();
        var hits = 0;
        items.forEach(function (item) {
          var text = item.textContent.toLowerCase();
          var box = item.querySelector("input");
          var ok = !needle || text.indexOf(needle) !== -1 || box.checked;
          item.hidden = !ok;
          if (ok) { hits++; }
        });
        none.hidden = hits !== 0;
      });
    });

    /* -- drawer ------------------------------------------------------------ */

    var openBtn = root.querySelector("[data-drawer-open]");
    var closeBtn = root.querySelector("[data-drawer-close]");

    function setDrawer(open) {
      if (open) { panel.setAttribute("data-open", ""); }
      else { panel.removeAttribute("data-open"); }
      document.body.classList.toggle("mdip-drawer-open", open);
      openBtn.setAttribute("aria-expanded", open ? "true" : "false");
      if (open) { qEl.focus(); }
    }

    openBtn.setAttribute("aria-expanded", "false");
    openBtn.setAttribute("aria-controls", "specs-filters");
    openBtn.addEventListener("click", function () { setDrawer(true); });
    closeBtn.addEventListener("click", function () { setDrawer(false); });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && panel.hasAttribute("data-open")) { setDrawer(false); }
    });
    document.addEventListener("click", function (e) {
      if (!panel.hasAttribute("data-open")) { return; }
      if (panel.contains(e.target) || openBtn.contains(e.target)) { return; }
      setDrawer(false);
    });

    /* -- wiring ------------------------------------------------------------ */

    panel.addEventListener("change", function (e) {
      if (e.target.type === "checkbox") { apply(); }
    });
    panel.addEventListener("submit", function (e) { e.preventDefault(); });

    var qTimer = null;
    qEl.addEventListener("input", function () {
      clearTimeout(qTimer);
      qTimer = setTimeout(apply, 140);
    });

    sortEl.addEventListener("change", function () { apply(); });

    Array.prototype.forEach.call(root.querySelectorAll("[data-clear-all]"), function (btn) {
      btn.addEventListener("click", function () {
        boxes.forEach(function (b) { b.checked = false; });
        qEl.value = "";
        Array.prototype.forEach.call(
          panel.querySelectorAll("[data-facet-search]"),
          function (i) { i.value = ""; i.dispatchEvent(new Event("input")); }
        );
        apply();
        setDrawer(false);
      });
    });

    window.addEventListener("popstate", function () {
      readState();
      apply(false);
    });

    readState();
    apply(false);
  }

  /* ----------------------------------------------------------------- detail */

  function initDetail() {
    var nav = document.querySelector(".spec-nav");
    if (!nav || !("IntersectionObserver" in window)) { return; }

    var links = Array.prototype.slice.call(nav.querySelectorAll("a"));
    var byId = {};
    var sections = [];

    links.forEach(function (a) {
      var id = a.getAttribute("href").slice(1);
      var section = document.getElementById(id);
      if (section) { byId[id] = a; sections.push(section); }
    });

    var seen = {};
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        seen[entry.target.id] = entry.isIntersecting;
      });
      for (var i = 0; i < sections.length; i++) {
        var id = sections[i].id;
        if (seen[id]) {
          links.forEach(function (a) { a.classList.remove("is-active"); });
          byId[id].classList.add("is-active");
          break;
        }
      }
    }, { rootMargin: "-30% 0px -60% 0px" });

    sections.forEach(function (s) { observer.observe(s); });
  }

  /* -------------------------------------------------------------- history */

  /*
   * The History section of a specification page, read from GitHub's public
   * API in the browser so that an open pull request shows up as soon as it
   * exists, without waiting for the site to be rebuilt.
   *
   * Two lists: pull requests still open on this entry's file ("Review in
   * progress"), then the last MAX_CHANGES changes merged into the branch the
   * site is built from. What a change did is worked out by reading the file
   * before and after it (raw.githubusercontent.com, which has no rate limit)
   * and comparing the two field by field.
   *
   * Without a token GitHub allows 60 API calls an hour per visitor, so every
   * answer is kept in sessionStorage for a few minutes and shared between
   * specification pages, and the per-commit lookups stop as soon as enough
   * changes are found. If GitHub cannot be reached, the server-rendered link
   * to the file's history stays as it is.
   */
  var MAX_CHANGES = 4;
  var MAX_ROWS = 6;
  var EXCERPT = 180;
  var CACHE_MS = 10 * 60 * 1000;

  function initHistory() {
    var root = document.querySelector("[data-history]");
    var labelsEl = root && root.querySelector("[data-history-labels]");
    if (!root || !labelsEl || !window.fetch || !window.Promise) { return; }

    var cfg = JSON.parse(labelsEl.textContent);
    var repo = root.getAttribute("data-repo");
    var branch = root.getAttribute("data-branch");
    var path = root.getAttribute("data-path");
    var body = root.querySelector("[data-history-body]");
    var api = "https://api.github.com/repos/" + repo;
    var fallback = body.innerHTML;

    body.innerHTML = '<p class="hist__note">Loading changes from GitHub...</p>';

    Promise.all([loadYaml(), openProposals(api, path), mergedChanges(api, repo, branch, path)])
      .then(function (res) {
        var open = res[1];
        var merged = res[2];
        return Promise.all([
          Promise.all(open.map(function (pr) {
            return diffOf(
              raw(repo, pr.base, path),
              raw(pr.headRepo || repo, pr.head, path)
            ).then(function (d) { pr.diff = d; return pr; });
          })),
          Promise.all(merged.map(function (ch) {
            return diffOf(
              ch.parent ? raw(repo, ch.parent, path) : Promise.resolve(null),
              raw(repo, ch.sha, path)
            ).then(function (d) { ch.diff = d; return ch; });
          }))
        ]);
      })
      .then(function (lists) {
        body.innerHTML = render(lists[0], lists[1]);
      })
      .catch(function () {
        body.innerHTML = '<p class="hist__note">Recent changes could not be loaded from GitHub ' +
          "right now.</p>" + fallback;
      });

    /* ---- rendering */

    function render(open, merged) {
      if (!open.length && !merged.length) {
        return '<p class="hist__note">No change recorded on GitHub yet.</p>';
      }
      var h = "";
      if (open.length) {
        h += '<h3 class="hist__group">Proposed changes</h3><ol class="hist__list">' +
          open.map(function (pr) {
            return item({
              tone: "info", ico: "source-pull", status: "Review in progress",
              title: pr.title, number: pr.number, url: pr.url, date: pr.created,
              people: [["Change proposed by", pr.user]],
              text: pr.body, diff: pr.diff, after: "Proposed", folded: false
            });
          }).join("") + "</ol>";
      }
      if (merged.length) {
        h += '<h3 class="hist__group">Recent changes</h3><ol class="hist__list">' +
          merged.map(function (ch) {
            var added = ch.diff && ch.diff.added;
            return item({
              tone: added ? "muted" : ch.pr ? "pass" : "muted",
              ico: added ? "plus-circle-outline" : ch.pr ? "source-merge" : "source-commit",
              status: added ? "Added to the registry" : ch.pr ? "Merged" : "Committed",
              title: ch.title, number: ch.pr, url: ch.url, date: ch.date,
              people: ch.pr
                ? [["Change proposed by", ch.user], ["Change merged by", ch.mergedBy]]
                : [["Changed by", ch.user]],
              text: ch.body, diff: added ? null : ch.diff, after: "After", folded: true
            });
          }).join("") + "</ol>";
      }
      return h;
    }

    function item(it) {
      var h = '<li class="hist__item">';
      h += '<div class="hist__top"><span class="pill pill--' + it.tone + '">' +
        cfg.icons[it.ico] + "<span>" + esc(it.status) + "</span></span>";
      if (it.date) {
        h += '<time class="hist__date" datetime="' + esc(it.date) + '">' +
          esc(dateLabel(it.date)) + "</time>";
      }
      h += "</div>";
      h += '<a class="hist__title" href="' + esc(it.url) + '" rel="noopener">' +
        "<span>" + esc(it.title) + "</span>" +
        (it.number ? '<span class="hist__num">#' + it.number + "</span>" : "") + "</a>";
      var people = it.people.filter(function (p) { return p[1]; });
      if (people.length) {
        h += '<p class="hist__by">' + people.map(function (p) {
          return "<span>" + esc(p[0]) + ' <a href="' + esc(p[1].url) + '" rel="noopener">@' +
            esc(p[1].login) + "</a></span>";
        }).join("") + "</p>";
      }
      var text = excerpt(it.text);
      if (text) { h += '<p class="hist__desc">' + esc(text) + "</p>"; }
      if (it.diff && it.diff.removed) {
        h += '<p class="hist__note">' + cfg.icons["delete-outline"] +
          " Removes this entry from the registry.</p>";
      } else if (it.diff && it.diff.rows.length) {
        var table = diffTable(it.diff.rows, it.after, it.url);
        h += it.folded
          ? '<details class="hist__more"><summary>What changed<span class="hist__n">' +
            it.diff.rows.length + (it.diff.rows.length === 1 ? " field" : " fields") +
            "</span></summary>" + table + "</details>"
          : table;
      }
      return h + "</li>";
    }

    function diffTable(rows, after, url) {
      var shown = rows.slice(0, MAX_ROWS);
      var h = '<div class="hist__scroll"><table class="hist__t"><thead><tr>' +
        '<th scope="col">Field</th><th scope="col">Before</th><th scope="col">' +
        esc(after) + "</th></tr></thead><tbody>";
      shown.forEach(function (r) {
        h += '<tr><th scope="row">' + esc(r.label) + "</th>" + cell(r.before, "old") +
          cell(r.after, "new") + "</tr>";
      });
      h += "</tbody></table></div>";
      if (rows.length > shown.length) {
        h += '<p class="hist__extra"><a href="' + esc(url) + '" rel="noopener">and ' +
          (rows.length - shown.length) + " more on GitHub</a></p>";
      }
      return h;
    }

    function cell(value, kind) {
      if (value === "") { return '<td class="hist__' + kind + ' is-empty">Not set</td>'; }
      var short = value.length > 90 ? value.slice(0, 88).replace(/\s+\S*$/, "") + "..." : value;
      return '<td class="hist__' + kind + '"' +
        (short !== value ? ' title="' + esc(value) + '"' : "") + ">" + esc(short) + "</td>";
    }

    /* ---- comparing two versions of the file */

    function diffOf(beforeP, afterP) {
      return Promise.all([beforeP, afterP]).then(function (texts) {
        if (texts[0] === null && texts[1] === null) { return null; }
        if (texts[0] === null) { return { added: true, rows: [] }; }
        if (texts[1] === null) { return { removed: true, rows: [] }; }
        var a = flatten(texts[0]);
        var b = flatten(texts[1]);
        if (!a || !b) { return null; }
        var keys = Object.keys(cfg.fields).filter(function (k) { return k in a || k in b; });
        Object.keys(a).concat(Object.keys(b)).forEach(function (k) {
          if (keys.indexOf(k) < 0) { keys.push(k); }
        });
        var rows = [];
        keys.forEach(function (k) {
          var x = show(k, a[k]);
          var y = show(k, b[k]);
          if (x !== y) { rows.push({ label: cfg.fields[k] || k, before: x, after: y }); }
        });
        return { rows: rows };
      });
    }

    /* The file's fields as { "dotted.path": value }, plus its description. */
    function flatten(text) {
      text = text.replace(/\r\n/g, "\n");
      var m = /^---\n([\s\S]*?)\n---\n?([\s\S]*)$/.exec(text);
      if (!m) { return null; }
      var front;
      try { front = window.jsyaml.load(m[1], { schema: window.jsyaml.CORE_SCHEMA }) || {}; }
      catch (e) { return null; }
      var out = {};
      Object.keys(front).forEach(function (k) {
        var v = front[k];
        if (k === "adoption" && isObj(v)) {
          Object.keys(v).forEach(function (j) { out[k + "." + j] = v[j]; });
        } else if (k === "principles" && isObj(v)) {
          Object.keys(v).forEach(function (p) {
            if (!isObj(v[p])) { return; }
            Object.keys(v[p]).forEach(function (j) {
              out["principles." + p + "." + j] = v[p][j];
            });
          });
        } else if (k === "licences" && Array.isArray(v)) {
          out[k] = v.map(function (l) {
            if (!isObj(l)) { return String(l); }
            var scopes = [].concat(l.scopes || []);
            return l.id + (scopes.length ? " (" + scopes.join(", ") + ")" : "");
          });
        } else {
          out[k] = v;
        }
      });
      var d = /^#\s+Description\s*$([\s\S]*?)(?=^#\s|$(?![\s\S]))/m.exec(m[2]);
      out.description = d ? d[1].trim() : "";
      return out;
    }

    /* One value as the page words it: vocabulary labels, Yes/No, numbers. */
    function show(key, v) {
      if (v === undefined || v === null || v === "") { return ""; }
      var vocab = cfg.values[/^principles\..+\.verdict$/.test(key) ? "verdict" : key];
      var one = function (x) {
        if (x === true) { return "Yes"; }
        if (x === false) { return "No"; }
        if (typeof x === "number" && key !== "first_release_year") {
          return x.toLocaleString("en-US");
        }
        if (isObj(x)) { return JSON.stringify(x); }
        return vocab && vocab[x] ? vocab[x] : String(x);
      };
      return Array.isArray(v) ? v.map(one).join(", ") : one(v);
    }
  }

  /* ---- what GitHub knows */

  function openProposals(api, path) {
    return getJSON(api + "/pulls?state=open&per_page=100", function (list) {
      return list.map(function (p) {
        return {
          number: p.number, title: p.title, url: p.html_url, body: p.body || "",
          created: p.created_at, user: person(p.user), base: p.base.sha, head: p.head.sha,
          headRepo: p.head.repo ? p.head.repo.full_name : null
        };
      });
    }).then(function (prs) {
      return Promise.all(prs.slice(0, 40).map(function (pr) {
        return getJSON(api + "/pulls/" + pr.number + "/files?per_page=100", function (files) {
          return files.map(function (f) { return [f.filename, f.previous_filename || ""]; });
        }, pr.head).then(function (files) {
          var touches = files.some(function (f) { return f[0] === path || f[1] === path; });
          return touches ? pr : null;
        });
      }));
    }).then(function (prs) { return prs.filter(Boolean); });
  }

  /*
   * The latest changes on the branch, one per pull request. A squash merge
   * names its pull request in the message ("Title (#12)"), as does a merge
   * commit; any other commit is looked up once to find whether it came in
   * through a pull request at all. Commits of the same pull request are
   * grouped, and the file before the oldest of them is the "before" side.
   */
  function mergedChanges(api, repo, branch, path) {
    var url = api + "/commits?sha=" + encodeURIComponent(branch) + "&path=" +
      encodeURIComponent(path) + "&per_page=30";
    return getJSON(url, function (list) {
      return list.map(function (c) {
        return {
          sha: c.sha, url: c.html_url, date: c.commit.committer.date,
          message: c.commit.message, user: person(c.author),
          parent: c.parents.length ? c.parents[0].sha : null
        };
      });
    }).then(function (commits) {
      var changes = [];
      var byPr = {};
      var lookups = 0;

      function step(i) {
        if (i >= commits.length) { return Promise.resolve(); }
        var c = commits[i];
        var first = c.message.split("\n")[0];
        var m = /\(#(\d+)\)\s*$/.exec(first) || /^Merge pull request #(\d+)/.exec(first);
        var found = m ? Promise.resolve(Number(m[1]))
          : lookups++ < 8
            ? getJSON(api + "/commits/" + c.sha + "/pulls", function (prs) {
              var pr = prs.filter(function (p) { return p.merged_at; })[0];
              return pr ? pr.number : 0;
            }).catch(function () { return 0; })
            : Promise.resolve(0);
        return found.then(function (num) {
          if (num && byPr[num]) {
            byPr[num].parent = c.parent;       // older commit of the same PR
          } else {
            if (changes.length === MAX_CHANGES) { return; }
            var ch = {
              sha: c.sha, parent: c.parent, pr: num || 0, url: c.url, date: c.date,
              title: first, body: c.message.split("\n").slice(1).join("\n"), user: c.user
            };
            changes.push(ch);
            if (num) { byPr[num] = ch; }
          }
          return step(i + 1);
        });
      }

      return step(0).then(function () {
        return Promise.all(changes.map(function (ch) {
          if (!ch.pr) { return ch; }
          return getJSON(api + "/pulls/" + ch.pr, function (p) {
            return {
              title: p.title, url: p.html_url, body: p.body || "", user: person(p.user),
              mergedBy: person(p.merged_by), merged: p.merged_at
            };
          }).then(function (p) {
            ch.title = p.title;
            ch.url = p.url;
            ch.body = p.body;
            ch.user = p.user;
            ch.mergedBy = p.mergedBy;
            ch.date = p.merged || ch.date;
            return ch;
          }, function () { return ch; });
        }));
      });
    });
  }

  function person(u) {
    return u && u.login ? { login: u.login, url: u.html_url } : null;
  }

  /* A file at one commit, or null where it does not exist there. Commits
     never change, so the answer is kept for the whole session. */
  var RAW = {};
  function raw(repo, sha, path) {
    var url = "https://raw.githubusercontent.com/" + repo + "/" + sha + "/" +
      path.split("/").map(encodeURIComponent).join("/");
    if (!RAW[url]) {
      RAW[url] = fetch(url).then(function (r) {
        if (r.status === 404) { return null; }
        if (!r.ok) { throw new Error("HTTP " + r.status); }
        return r.text();
      });
    }
    return RAW[url];
  }

  /* GET from the API, keep only what `pick` returns, and remember it for
     CACHE_MS. `version` invalidates an entry early (a pull request's head). */
  function getJSON(url, pick, version) {
    var key = "mdip-gh:" + url + (version ? "@" + version : "");
    try {
      var hit = JSON.parse(sessionStorage.getItem(key));
      if (hit && Date.now() - hit.t < CACHE_MS) { return Promise.resolve(hit.v); }
    } catch (e) { /* storage off or full: fetch */ }
    return fetch(url, { headers: { Accept: "application/vnd.github+json" } })
      .then(function (r) {
        if (!r.ok) { throw new Error("HTTP " + r.status); }
        return r.json();
      })
      .then(function (json) {
        var v = pick(json);
        try { sessionStorage.setItem(key, JSON.stringify({ t: Date.now(), v: v })); }
        catch (e) { /* not cached, still shown */ }
        return v;
      });
  }

  /* js-yaml, served next to this script, loaded only on pages that need it. */
  var yamlLoad = null;
  function loadYaml() {
    if (window.jsyaml) { return Promise.resolve(); }
    if (!yamlLoad) {
      yamlLoad = new Promise(function (resolve, reject) {
        var s = document.createElement("script");
        s.src = SCRIPT_SRC.replace(/[^/]*$/, "") + "vendor/js-yaml.min.js";
        s.onload = resolve;
        s.onerror = reject;
        document.head.appendChild(s);
      });
    }
    return yamlLoad;
  }

  /* The first lines of a pull request description, as plain text: headings
     ("## Summary") and list bullets are template scaffolding, not content. */
  function excerpt(text) {
    var t = (text || "")
      .replace(/<!--[\s\S]*?-->/g, " ")
      .replace(/^\s*#+\s.*$/gm, " ")
      .replace(/^\s*(?:[-*+]|\d+\.)\s+/gm, " ")
      .replace(/!?\[([^\]]*)\]\([^)]*\)/g, "$1")
      .replace(/[*`]+/g, "")
      .replace(/^\s*>\s?/gm, " ")
      .replace(/\s+/g, " ")
      .trim();
    if (t.length <= EXCERPT) { return t; }
    return t.slice(0, EXCERPT).replace(/\s+\S*$/, "").replace(/[\s.,;:-]+$/, "") + "...";
  }

  function dateLabel(iso) {
    var d = new Date(iso);
    if (isNaN(d)) { return iso; }
    return d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
  }

  function isObj(v) { return v && typeof v === "object" && !Array.isArray(v); }

  function esc(s) {
    return String(s === undefined || s === null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
})();
