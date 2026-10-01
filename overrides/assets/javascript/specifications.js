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
})();
