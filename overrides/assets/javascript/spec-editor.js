/*
 * MDIP specification registry - in-page editor.
 *
 * "Suggest a change" at the foot of a specification page turns the page into
 * an editor: a small edit button appears next to every value that comes from
 * the specification's file (data/specifications/<id>.md), and each opens a
 * control that fits the field: a list for a verdict or a status, a licence
 * picker, a year, a date, a URL. The page redraws the value as it would be
 * published, so the person proposing the change sees the result.
 *
 * Values that follow from one another are kept consistent as they are edited
 * (see `autoRules`): a criterion that is not compliant makes the MDIP status
 * not compliant, a new adopters count takes today's date and the matching
 * tier, a licence that requires a purchase fails "Free of cost restrictions".
 *
 * Nothing is written anywhere but GitHub. The change is sent as a pre-filled
 * issue (.github/ISSUE_TEMPLATE/specification-edit.yml) that the person
 * submits with their own GitHub account, and the coalition reviews it there.
 * Until it is sent, the change is kept in this browser (localStorage), so
 * signing in, creating an account or closing the tab does not lose it.
 *
 * The page works without this script: "Suggest a change" then opens the
 * file in GitHub's own editor.
 */
(function () {
  "use strict";

  var SCRIPT_SRC = document.currentScript ? document.currentScript.src : "";
  var STORE = "mdip-edit:";
  /* GitHub refuses very long URLs; past this the proposal is pasted instead. */
  var URL_MAX = 7000;
  var TONE_ICON = {
    pass: "check-circle", warn: "alert-circle", fail: "close-circle",
    info: "progress-clock", muted: "help-circle"
  };
  var URL_FIELDS = /^(homepage_url|licence_evidence_url|adoption\.adopters_registry_url|principles\..+\.evidence_url)$/;

  function ready(fn) {
    if (document.readyState !== "loading") { fn(); }
    else { document.addEventListener("DOMContentLoaded", fn); }
  }

  ready(function () {
    var cfgEl = document.querySelector("[data-edit-config]");
    var root = document.querySelector(".mdip-spec");
    if (!cfgEl || !root) { return; }
    var cfg;
    try { cfg = JSON.parse(cfgEl.textContent); } catch (e) { return; }
    editor(root, cfg);
  });

  function editor(root, cfg) {
    var ICON = cfg.icons;
    var CRITERIA = cfg.criteria.map(function (c) { return c.key; });
    var ORGS = index(cfg.organizations);
    var LICENCES = index(cfg.licences);
    var orig = normalise(cfg.front, cfg.description);
    var doc = clone(orig);
    var PATHS = fieldPaths();
    var editing = false;
    var snapshot = null;
    var pens = [];
    var bar = null;
    var pop = null;
    /* On /specifications/new/ the page is blank and opens in the editor. The
       registry id follows the short name until it is edited by hand. */
    var isNew = !!cfg["new"];
    var idByHand = false;
    var ID_RE = /^[a-z0-9]+(?:[-_][a-z0-9]+)*$/;
    if (isNew) { PATHS.unshift("id"); }

    if (isNew) {
      start(false);
    } else {
      var startBtn = root.querySelector("[data-edit-start]");
      if (!startBtn) { return; }
      startBtn.addEventListener("click", function (e) {
        e.preventDefault();
        start(true);
      });
      showDraftNotice();
    }
    root.addEventListener("click", function (e) {
      if (!editing || !e.target.closest) { return; }
      /* While editing, a criterion stays open: its summary row holds controls. */
      if (e.target.closest("details.crit > summary")) { e.preventDefault(); }
      /* An empty field is a place to click, like the edit button next to it. */
      var blank = e.target.closest(".sed-empty");
      var owner = blank && blank.closest("[data-edit]");
      if (owner && owner._pen) {
        e.preventDefault();
        openEditor(owner.getAttribute("data-field"), owner._pen);
      }
    });

    /* ================================================================ model */

    function index(list) {
      var out = {};
      list.forEach(function (x) { out[x.id] = x; });
      return out;
    }

    function clone(v) { return JSON.parse(JSON.stringify(v)); }

    /* The file's values in the shapes the editor works with: licences as
       {id, scopes}, lists as lists, and the description beside them. */
    function normalise(front, description) {
      var d = clone(front || {});
      d.licences = [].concat(d.licences || []).filter(function (l) { return l !== null; })
        .map(function (l) {
          if (typeof l !== "object") { return { id: String(l), scopes: [] }; }
          return { id: String(l.id === undefined || l.id === null ? "" : l.id),
            scopes: [].concat(l.scopes || []) };
        });
      d.modes = [].concat(d.modes || []);
      d.maintainers = [].concat(d.maintainers || []);
      d.adoption = isObj(d.adoption) ? d.adoption : {};
      d.principles = isObj(d.principles) ? d.principles : {};
      CRITERIA.forEach(function (k) {
        if (!isObj(d.principles[k])) { d.principles[k] = {}; }
      });
      d.description = description || "";
      return d;
    }

    function fieldPaths() {
      var p = ["short_name", "full_name", "description", "homepage_url", "status", "modes",
        "maintainers", "licences", "licence_evidence_url", "first_release_year",
        "adoption.lifecycle", "adoption.tier", "adoption.adopters_count",
        "adoption.adopters_count_updated", "adoption.adopters_registry_url",
        "adoption.confirmed_by_maintainer"];
      CRITERIA.forEach(function (k) {
        ["verdict", "rationale", "evidence_url"].forEach(function (f) {
          p.push("principles." + k + "." + f);
        });
      });
      return p;
    }

    function get(obj, path) {
      var parts = path.split(".");
      var v = obj;
      for (var i = 0; i < parts.length; i++) {
        if (!isObj(v)) { return undefined; }
        v = v[parts[i]];
      }
      return v;
    }

    function set(obj, path, value) {
      var parts = path.split(".");
      var v = obj;
      for (var i = 0; i < parts.length - 1; i++) {
        if (!isObj(v[parts[i]])) { v[parts[i]] = {}; }
        v = v[parts[i]];
      }
      if (empty(value)) { delete v[parts[parts.length - 1]]; }
      else { v[parts[parts.length - 1]] = value; }
    }

    function empty(v) {
      return v === undefined || v === null || v === "" ||
        (Array.isArray(v) && v.length === 0);
    }

    /* Comparable form of a value: empty in any shape is one thing. */
    function key(v) {
      if (empty(v)) { return ""; }
      if (Array.isArray(v)) {
        return JSON.stringify(v.map(function (x) {
          return isObj(x) ? { id: x.id, scopes: (x.scopes || []).slice().sort(), url: x.url || "" } : x;
        }));
      }
      return JSON.stringify(v);
    }

    function changed(path) { return key(get(orig, path)) !== key(get(doc, path)); }

    function changes() { return PATHS.filter(changed); }

    function label(path) { return cfg.labels[path] || path; }

    /* ========================================================== consistency */

    /*
     * Run after the person edits `path`, before anything is redrawn. Each rule
     * mirrors a rule of the registry (data/README.md): the status the verdicts
     * imply, the tier an adopters count falls in, and the verdict a licence
     * implies for "Free of cost restrictions". The person can still override
     * any of these values afterwards.
     */
    function autoRules(path) {
      if (isNew && path === "id") { idByHand = !empty(get(doc, "id")); }
      if (isNew && path === "short_name" && !idByHand) { set(doc, "id", slug(get(doc, path) || "")); }
      if (path === "adoption.adopters_count") {
        var n = get(doc, path);
        if (typeof n === "number") {
          set(doc, "adoption.adopters_count_updated", today());
          var tier = get(doc, "adoption.tier");
          if (n >= 100) { set(doc, "adoption.tier", "hundred_plus"); }
          else if (n === 0) { set(doc, "adoption.tier", "none"); }
          else if (!tier || tier === "hundred_plus" || tier === "none") {
            set(doc, "adoption.tier", "early");
          }
        }
      }
      if (path === "licences" && CRITERIA.indexOf("cost_restriction_free") !== -1) {
        var cats = doc.licences.map(function (l) {
          return LICENCES[l.id] ? LICENCES[l.id].category : "unknown";
        });
        var verdict = null;
        if (cats.indexOf("closed") !== -1) { verdict = "not_compliant"; }
        else if (cats.indexOf("restricted") !== -1) { verdict = "partially_compliant"; }
        else if (cats.length && cats.every(function (c) { return c === "open"; })) {
          verdict = "compliant";
        }
        if (verdict) { set(doc, "principles.cost_restriction_free.verdict", verdict); }
      }
      if (path === "adoption.lifecycle") {
        if (get(doc, path) === "inactive") { set(doc, "status", "inactive"); }
        else if (get(doc, "status") === "inactive") { deriveStatus(true); }
      }
      if (/\.verdict$/.test(path) || path === "licences") { deriveStatus(false); }
    }

    /* The status the verdicts imply, as `make specs-check` works it out. An
       inactive project keeps its status; unknown verdicts imply nothing. */
    function deriveStatus(force) {
      if (!force && get(doc, "status") === "inactive") { return; }
      var v = CRITERIA.map(function (k) {
        return get(doc, "principles." + k + ".verdict") || "not_assessed";
      });
      var all = function (ok) { return v.every(function (x) { return ok.indexOf(x) !== -1; }); };
      var status = null;
      if (all(["compliant"])) { status = "compliant"; }
      else if (v.indexOf("not_compliant") !== -1) { status = "not_compliant"; }
      else if (all(["compliant", "partially_compliant"])) { status = "partially_compliant"; }
      if (status) { set(doc, "status", status); }
    }

    function slug(text) {
      return text.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase()
        .replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
    }

    function idProblem(id) {
      if (!id) { return "A registry id is required"; }
      if (!ID_RE.test(id)) { return "Use lower case letters and digits, joined by - or _"; }
      if (cfg.ids.indexOf(id) !== -1) { return "This id is already in the registry"; }
      return "";
    }

    function today() {
      var d = new Date();
      return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate());
    }

    function pad(n) { return (n < 10 ? "0" : "") + n; }

    /* ============================================================ edit mode */

    function bound() {
      return Array.prototype.slice.call(root.querySelectorAll("[data-field]"));
    }

    function start(scroll) {
      if (editing) { return; }
      editing = true;
      takeSnapshot();
      var draft = readDraft();
      if (draft) {
        Object.keys(draft.values).forEach(function (p) {
          if (PATHS.indexOf(p) !== -1) { set(doc, p, draft.values[p]); }
        });
        idByHand = isNew && !!draft.idByHand;
      }
      root.classList.add("is-editing");
      Array.prototype.forEach.call(root.querySelectorAll("[data-edit-only]"), function (el) {
        el.hidden = false;
      });
      Array.prototype.forEach.call(root.querySelectorAll("details.crit"), function (d) {
        d.open = true;
      });
      addPens();
      bound().forEach(function (el) {
        var p = el.getAttribute("data-field");
        if (changed(p) || empty(get(doc, p))) { draw(el, p); }
      });
      refreshDerived();
      markChanged();
      showBar();
      hideDraftNotice();
      if (scroll) { root.scrollIntoView({ behavior: "smooth", block: "start" }); }
    }

    function stop() {
      if (isNew) {
        location.href = "../";
        return;
      }
      closePop();
      editing = false;
      doc = clone(orig);
      restoreSnapshot();
      root.classList.remove("is-editing");
      pens.forEach(function (p) { p.remove(); });
      pens = [];
      if (bar) { bar.remove(); bar = null; }
      document.body.classList.remove("sed-has-bar");
      showDraftNotice();
    }

    /* What the page looked like before editing, to put back on discard: the
       server's markup, not a client redraw of it. */
    function takeSnapshot() {
      snapshot = [];
      var seen = [];
      var keep = function (el) {
        if (seen.indexOf(el) !== -1) { return; }
        seen.push(el);
        snapshot.push({ el: el, html: el.innerHTML, hidden: el.hidden, cls: el.className,
          open: el.tagName === "DETAILS" ? el.open : null });
      };
      bound().forEach(keep);
      Array.prototype.forEach.call(root.querySelectorAll(
        "[data-edit-only], .crit, [data-view=meter], .spec-hero, .spec-hero__orgs"), keep);
      Array.prototype.forEach.call(root.querySelectorAll(".crit__icon"), keep);
    }

    function restoreSnapshot() {
      (snapshot || []).forEach(function (s) {
        s.el.innerHTML = s.html;
        s.el.hidden = s.hidden;
        s.el.className = s.cls;
        if (s.open !== null) { s.el.open = s.open; }
      });
      snapshot = null;
    }

    function addPens() {
      Array.prototype.forEach.call(root.querySelectorAll("[data-edit]"), function (el) {
        var path = el.getAttribute("data-field");
        var b = document.createElement("button");
        b.type = "button";
        b.className = "sed-pen";
        b.setAttribute("aria-label", "Edit " + label(path));
        b.title = "Edit " + label(path).toLowerCase();
        b.innerHTML = ICON["pencil-outline"];
        b.addEventListener("click", function (e) {
          e.preventDefault();
          e.stopPropagation();
          openEditor(path, b);
        });
        el._pen = b;
        if (el.getAttribute("data-view") === "block" || el.getAttribute("data-view") === "cards") {
          el.classList.add("sed-block");
        }
        el.appendChild(b);
        pens.push(b);
      });
    }

    /* After a change: redraw what differs from what is on screen, flash what
       a rule changed on its own, save the draft. */
    function commit(path, value) {
      var before = {};
      PATHS.forEach(function (p) { before[p] = key(get(doc, p)); });
      set(doc, path, value);
      autoRules(path);
      bound().forEach(function (el) {
        var p = el.getAttribute("data-field");
        if (before[p] !== key(get(doc, p))) {
          draw(el, p);
          if (p !== path) { flash(el); }
        }
      });
      refreshDerived();
      markChanged();
      saveDraft();
      updateBar();
    }

    function flash(el) {
      el.classList.remove("sed-flash");
      void el.offsetWidth;
      el.classList.add("sed-flash");
    }

    function markChanged() {
      bound().forEach(function (el) {
        el.classList.toggle("is-changed", changed(el.getAttribute("data-field")));
      });
    }

    /* Parts of the page that follow from several fields. */
    function refreshDerived() {
      var met = CRITERIA.filter(function (k) {
        return get(doc, "principles." + k + ".verdict") === "compliant";
      }).length;
      Array.prototype.forEach.call(root.querySelectorAll("[data-view=meter]"), function (el) {
        el.innerHTML = meter(met, CRITERIA.length);
      });
      Array.prototype.forEach.call(root.querySelectorAll("[data-crit]"), function (el) {
        var v = vocab(cfg.verdict, get(doc, "principles." + el.getAttribute("data-crit") + ".verdict")
          || "not_assessed");
        el.className = el.className.replace(/\bcrit--\w+/, "crit--" + v.tone);
        var ico = el.querySelector(".crit__icon");
        if (ico) { ico.innerHTML = ICON[TONE_ICON[v.tone]]; }
      });
      Array.prototype.forEach.call(root.querySelectorAll('[data-field=status][data-view=pill-met]'),
        function (el) { draw(el, "status"); });
      var orgs = root.querySelector(".spec-hero__orgs");
      if (orgs) { orgs.hidden = empty(doc.maintainers); }
      var hero = root.querySelector(".spec-hero");
      var st = vocab(cfg.status, get(doc, "status") || "under_review");
      if (hero) { hero.className = hero.className.replace(/\bspec-hero--\w+/, "spec-hero--" + st.tone); }
    }

    /* ============================================================== drawing */

    function draw(el, path) {
      var v = get(doc, path);
      var view = el.getAttribute("data-view") || "";
      var html = isNew && empty(v) && !/^(status|modes|licences|adoption\.confirmed_by_maintainer)$|\.verdict$/.test(path)
        ? '<span class="sed-empty">' + esc(label(path)) + "</span>"
        : render(path, view, v);
      el.innerHTML = html;
      if (el._pen) { el.appendChild(el._pen); }
    }

    function notSet(what) {
      return '<span class="sed-empty">' + esc(what ? what + " not set" : "Not set") + "</span>";
    }

    function render(path, view, v) {
      if (path === "status") {
        var st = vocab(cfg.status, v || "under_review");
        var h = pill(st.tone, st.label);
        if (view === "pill-met") {
          var met = CRITERIA.filter(function (k) {
            return get(doc, "principles." + k + ".verdict") === "compliant";
          }).length;
          h += '<span class="glance__note">' + met + " of " + CRITERIA.length +
            " criteria met</span>";
        }
        return h;
      }
      if (/\.verdict$/.test(path)) {
        var vd = vocab(cfg.verdict, v || "not_assessed");
        return pill(vd.tone, vd.label);
      }
      if (/\.rationale$/.test(path) || path === "description") {
        return empty(v) ? notSet() : paras(String(v), path === "description" ? "" : "crit__rationale");
      }
      if (/\.evidence_url$/.test(path)) { return empty(v) ? notSet() : srclink(v, "Source", "srclink--crit"); }
      if (path === "adoption.adopters_registry_url") {
        return empty(v) ? notSet() : srclink(v, "Open registry");
      }
      if (path === "licence_evidence_url") {
        return empty(v) ? notSet("Licence text") : [].concat(v).map(function (u) {
          return '<p class="lic__evidence">' + srclink(u, "Licence text") + "</p>";
        }).join("");
      }
      if (path === "homepage_url") {
        return empty(v) ? notSet() : '<a href="' + esc(v) + '" rel="noopener">' + esc(v) +
          ICON["open-in-new"] + "</a>";
      }
      if (path === "id") { return empty(v) ? notSet() : "<code>" + esc(v) + "</code>"; }
      if (path === "short_name" || path === "full_name") {
        return empty(v) ? notSet() : esc(v);
      }
      if (path === "modes") {
        var modes = (v || []).map(function (m) { return vocab(cfg.modes, m).label; });
        if (!modes.length) { modes = ["Unclassified"]; }
        return modes.map(function (m) { return '<span class="tag tag--mode">' + esc(m) + "</span>"; })
          .join(" ");
      }
      if (path === "adoption.lifecycle") {
        if (empty(v)) { return notSet(); }
        var lc = vocab(cfg.lifecycle, v);
        return '<span class="tag">' + esc(lc.label) + '</span><span class="glance__note">' +
          esc(lc.hint || "") + "</span>";
      }
      if (path === "adoption.tier") {
        return empty(v) ? notSet() : '<span class="tag">' + esc(vocab(cfg.tier, v).label) + "</span>";
      }
      if (path === "adoption.confirmed_by_maintainer") {
        var c = vocab(cfg.confirmed, v === true ? "yes" : v === false ? "no" : "unknown");
        return pill(c.tone, c.label);
      }
      if (path === "first_release_year") {
        return empty(v) ? notSet() : "<strong>" + esc(v) + "</strong>";
      }
      if (path === "adoption.adopters_count") {
        return empty(v) ? notSet() : esc(Number(v).toLocaleString("en-US"));
      }
      if (path === "adoption.adopters_count_updated") {
        return empty(v) ? notSet("Date") : "as of " + esc(v);
      }
      if (path === "licences") { return view === "cards" ? licenceCards(v) : licenceTags(v); }
      if (path === "maintainers") { return view === "cards" ? orgCards(v) : orgChips(v); }
      return empty(v) ? notSet() : esc(String(v));
    }

    function vocab(list, id) {
      for (var i = 0; i < list.length; i++) { if (list[i].id === id) { return list[i]; } }
      return { id: id, label: String(id), tone: "muted" };
    }

    function pill(tone, text) {
      return '<span class="pill pill--' + tone + ' ">' + ICON[TONE_ICON[tone] || "help-circle"] +
        "<span>" + esc(text) + "</span></span>";
    }

    function meter(met, total) {
      var dots = "";
      for (var i = 0; i < total; i++) { dots += '<i class="' + (i < met ? "on" : "off") + '"></i>'; }
      return '<span class="meter" role="img" aria-label="' + met + " of " + total +
        ' MDIP criteria met">' + dots + "</span>";
    }

    function srclink(url, text, cls) {
      return '<a class="srclink ' + (cls || "") + '" href="' + esc(url) + '" rel="noopener">' +
        ICON["link-variant"] + "<span>" + esc(text) + "</span>" + ICON["open-in-new"] + "</a>";
    }

    function paras(text, cls) {
      return text.replace(/\r\n/g, "\n").split(/\n\s*\n/).filter(function (b) { return b.trim(); })
        .map(function (b) {
          return '<p class="' + cls + '">' + esc(b.trim()).replace(/\n/g, "<br>") + "</p>";
        }).join("");
    }

    function licenceMeta(l) {
      var m = LICENCES[l.id];
      if (m) { return m; }
      if (!l.id) { return { id: "Unspecified", name: "No licence stated", category: "unknown" }; }
      return { id: l.id, name: l.id, category: "unknown", url: l.url || null, other: true };
    }

    function licenceTags(list) {
      if (!list || !list.length) {
        return '<span class="tag tag--lic tag--lic-unknown">Unspecified</span>';
      }
      return list.map(function (l) {
        var m = licenceMeta(l);
        return '<span class="tag tag--lic tag--lic-' + m.category + '">' + esc(m.id) + "</span>";
      }).join(" ");
    }

    function licenceCards(list) {
      if (!list || !list.length) { list = [{ id: "", scopes: [] }]; }
      return list.map(function (l) {
        var m = licenceMeta(l);
        var h = '<article class="lic lic--' + m.category + '"><div class="lic__head">';
        h += m.url
          ? '<h3><a href="' + esc(m.url) + '" rel="noopener"><span>' + esc(m.id) + "</span>" +
            ICON["open-in-new"] + "</a></h3>"
          : "<h3><span>" + esc(m.id) + "</span></h3>";
        if (l.scopes && l.scopes.length) {
          h += '<span class="lic__scopes">' + l.scopes.map(function (s) {
            return '<span class="tag tag--scope">' + esc(vocab(cfg.scopes, s).label) + "</span>";
          }).join(" ") + "</span>";
        }
        h += "</div>";
        if (m.name !== m.id) { h += '<p class="lic__name">' + esc(m.name) + "</p>"; }
        if (m.note) {
          h += '<p class="lic__note">' + ICON["information-outline"] + esc(m.note) + "</p>";
        }
        return h + "</article>";
      }).join("");
    }

    function orgOf(id) {
      return ORGS[id] || { id: id, name: id, short: id, url: null,
        type_label: "Not in the registry yet" };
    }

    /* The generated monogram the page falls back on. Logos are left out: they
       are hosted by each organization, and the editor loads nothing from
       other sites. */
    function orgLogo(o) {
      return '<span class="org-logo org-logo--mono" style="--org-hue:' + hue(o.id) +
        '" aria-hidden="true">' + esc(monogram(o.short || o.name)) + "</span>";
    }

    function hue(k) {
      var h = 0;
      for (var i = 0; i < k.length; i++) { h = (h * 31 + k.charCodeAt(i)) % 360; }
      return h;
    }

    function monogram(name) {
      var words = name.replace(/-/g, " ").split(/\s+/).filter(function (w) {
        return /^[A-Za-z0-9À-￿]/.test(w);
      });
      if (!words.length) { return "?"; }
      if (words.length === 1) { return words[0].slice(0, 2).toUpperCase(); }
      return (words[0][0] + words[1][0]).toUpperCase();
    }

    function orgChips(list) {
      return (list || []).map(function (id) {
        var o = orgOf(id);
        return '<span class="org-chip org-chip--lg">' + orgLogo(o) + "<span>" + esc(o.name) +
          "</span></span>";
      }).join("") || notSet();
    }

    function orgCards(list) {
      if (!list || !list.length) { return notSet(); }
      return list.map(function (id) {
        var o = orgOf(id);
        var h = '<article class="orgcard">' + orgLogo(o) + '<div class="orgcard__t"><h3>' +
          esc(o.name) + "</h3><p>" + esc(o.type_label || "") + "</p>";
        if (o.url) {
          h += '<a href="' + esc(o.url) + '" rel="noopener">' +
            esc(o.url.replace(/^\w+:\/\//, "").replace(/\/$/, "")) + ICON["open-in-new"] + "</a>";
        }
        return h + "</div></article>";
      }).join("");
    }

    /* =============================================================== popover */

    function closePop() {
      if (!pop) { return; }
      var back = pop._from;
      pop.remove();
      pop = null;
      document.removeEventListener("mousedown", outside, true);
      document.removeEventListener("keydown", popKeys, true);
      if (back && document.body.contains(back)) { back.focus(); }
    }

    function outside(e) {
      if (pop && !pop.contains(e.target) && e.target !== pop._from &&
          !(pop._from && pop._from.contains(e.target))) {
        closePop();
      }
    }

    function popKeys(e) {
      if (e.key === "Escape" && pop) {
        e.preventDefault();
        e.stopPropagation();
        closePop();
      }
    }

    function makePop(path, from, wide) {
      closePop();
      pop = document.createElement("div");
      pop.className = "sed-pop" + (wide ? " sed-pop--wide" : "");
      pop.setAttribute("role", "dialog");
      pop.setAttribute("aria-label", "Edit " + label(path));
      pop._from = from;
      pop.innerHTML = '<p class="sed-pop__head">' + esc(label(path)) + "</p>";
      root.appendChild(pop);
      document.addEventListener("mousedown", outside, true);
      document.addEventListener("keydown", popKeys, true);
      return pop;
    }

    function place() {
      if (!pop) { return; }
      var from = pop._from;
      if (window.matchMedia("(max-width: 40em)").matches) {
        pop.classList.add("sed-pop--sheet");
        return;
      }
      var r = root.getBoundingClientRect();
      var a = from.getBoundingClientRect();
      var w = pop.offsetWidth;
      var left = Math.min(Math.max(a.left - r.left - 12, 12), r.width - w - 12);
      pop.style.left = Math.max(left, 12) + "px";
      pop.style.top = (a.bottom - r.top + 6) + "px";
      /* Keep the whole control on screen when the value is low on the page. */
      var below = window.innerHeight - a.bottom;
      if (below < pop.offsetHeight + 16 && a.top > pop.offsetHeight + 80) {
        pop.style.top = (a.top - r.top - pop.offsetHeight - 6) + "px";
      }
    }

    function footer(onApply) {
      var f = document.createElement("div");
      f.className = "sed-pop__foot";
      f.innerHTML = '<button type="button" class="ghost" data-cancel>Cancel</button>' +
        '<button type="button" class="btn btn--primary sed-apply" data-apply>' + ICON.check +
        "<span>Apply</span></button>";
      f.querySelector("[data-cancel]").addEventListener("click", closePop);
      f.querySelector("[data-apply]").addEventListener("click", onApply);
      return f;
    }

    function openEditor(path, from) {
      if (path === "status") {
        return listEditor(path, from, cfg.status.map(function (s) {
          return { value: s.id, html: pill(s.tone, s.label) };
        }), get(doc, path) || "under_review");
      }
      if (/\.verdict$/.test(path)) {
        return listEditor(path, from, cfg.verdict.map(function (s) {
          return { value: s.id, html: pill(s.tone, s.label) };
        }), get(doc, path) || "not_assessed");
      }
      if (path === "adoption.confirmed_by_maintainer") {
        var cv = get(doc, path);
        return listEditor(path, from, cfg.confirmed.map(function (s) {
          return { value: s.id === "yes" ? true : s.id === "no" ? false : null,
            html: pill(s.tone, s.label) };
        }), cv === true || cv === false ? cv : null);
      }
      if (path === "adoption.lifecycle") {
        return listEditor(path, from, cfg.lifecycle.map(function (s) {
          return { value: s.id, html: '<span class="sed-opt__t">' + esc(s.label) +
            '</span><span class="sed-opt__h">' + esc(s.hint) + "</span>" };
        }).concat([unsetOption()]), get(doc, path) || null);
      }
      if (path === "adoption.tier") {
        return listEditor(path, from, cfg.tier.map(function (s) {
          return { value: s.id, html: '<span class="sed-opt__t">' + esc(s.label) + "</span>" };
        }).concat([unsetOption()]), get(doc, path) || null);
      }
      if (path === "modes") { return modesEditor(path, from); }
      if (path === "licences") { return licencesEditor(path, from); }
      if (path === "maintainers") { return orgsEditor(path, from); }
      if (path === "description" || /\.rationale$/.test(path)) {
        return textEditor(path, from, "textarea");
      }
      if (path === "licence_evidence_url") { return textEditor(path, from, "urls"); }
      if (URL_FIELDS.test(path)) { return textEditor(path, from, "url"); }
      if (path === "first_release_year") { return textEditor(path, from, "year"); }
      if (path === "adoption.adopters_count") { return textEditor(path, from, "count"); }
      if (path === "adoption.adopters_count_updated") { return textEditor(path, from, "date"); }
      return textEditor(path, from, "text");
    }

    function unsetOption() {
      return { value: null, html: '<span class="sed-opt__t sed-opt__t--muted">Not set</span>' };
    }

    /* One choice in a list: a custom listbox, applied as soon as it is
       picked. Arrow keys, Home, End and Enter work as in a native select. */
    function listEditor(path, from, options, current) {
      var p = makePop(path, from);
      var ul = document.createElement("ul");
      ul.className = "sed-list";
      ul.setAttribute("role", "listbox");
      ul.setAttribute("tabindex", "0");
      ul.setAttribute("aria-label", label(path));
      var active = 0;
      options.forEach(function (o, i) {
        var li = document.createElement("li");
        li.className = "sed-opt";
        li.id = "sed-opt-" + i;
        li.setAttribute("role", "option");
        var on = o.value === current;
        li.setAttribute("aria-selected", on ? "true" : "false");
        li.innerHTML = '<span class="sed-opt__v">' + o.html + "</span>" +
          '<span class="sed-opt__ck">' + (on ? ICON.check : "") + "</span>";
        if (on) { active = i; }
        li.addEventListener("click", function () { pick(i); });
        li.addEventListener("mousemove", function () { focusOpt(i); });
        ul.appendChild(li);
      });
      p.appendChild(ul);
      place();
      focusOpt(active);
      ul.focus();
      ul.addEventListener("keydown", function (e) {
        var n = options.length;
        if (e.key === "ArrowDown") { e.preventDefault(); focusOpt((active + 1) % n); }
        else if (e.key === "ArrowUp") { e.preventDefault(); focusOpt((active - 1 + n) % n); }
        else if (e.key === "Home") { e.preventDefault(); focusOpt(0); }
        else if (e.key === "End") { e.preventDefault(); focusOpt(n - 1); }
        else if (e.key === "Enter" || e.key === " ") { e.preventDefault(); pick(active); }
      });

      function focusOpt(i) {
        active = i;
        Array.prototype.forEach.call(ul.children, function (li, j) {
          li.classList.toggle("is-active", j === i);
        });
        ul.setAttribute("aria-activedescendant", "sed-opt-" + i);
        var li = ul.children[i];
        if (li && li.scrollIntoView) { li.scrollIntoView({ block: "nearest" }); }
      }

      function pick(i) {
        var v = options[i].value;
        closePop();
        if (v !== current) { commit(path, v); }
      }
    }

    function textEditor(path, from, kind) {
      var p = makePop(path, from, kind === "textarea" || kind === "urls");
      var v = get(doc, path);
      var field;
      if (kind === "textarea" || kind === "urls") {
        field = document.createElement("textarea");
        field.rows = path === "description" ? 9 : kind === "urls" ? 3 : 6;
        field.value = kind === "urls" ? [].concat(v || []).join("\n") : (v || "");
        if (kind === "urls") { field.placeholder = "https://..., one per line"; }
      } else {
        field = document.createElement("input");
        field.type = { url: "url", year: "number", count: "number", date: "date" }[kind] || "text";
        if (kind === "url") { field.placeholder = "https://"; }
        if (kind === "year") { field.min = 1900; field.max = new Date().getFullYear() + 1; field.step = 1; }
        if (kind === "count") { field.min = 0; field.step = 1; }
        field.value = empty(v) ? "" : String(v);
      }
      field.className = "sed-input";
      field.setAttribute("aria-label", label(path));
      var err = document.createElement("p");
      err.className = "sed-err";
      err.hidden = true;
      p.appendChild(field);
      p.appendChild(err);
      p.appendChild(footer(apply));
      place();
      field.focus();
      if (field.select && kind !== "textarea") { field.select(); }
      field.addEventListener("keydown", function (e) {
        var multi = field.tagName === "TEXTAREA";
        if (e.key === "Enter" && (!multi || e.metaKey || e.ctrlKey)) { e.preventDefault(); apply(); }
      });

      function apply() {
        var raw = field.value.trim();
        var out = raw;
        var problem = "";
        if (kind === "url" && raw && !/^https?:\/\/\S+$/.test(raw)) {
          problem = "Enter a full link starting with https://";
        }
        if (kind === "urls") {
          var urls = raw.split(/\s+/).filter(Boolean);
          if (urls.some(function (u) { return !/^https?:\/\/\S+$/.test(u); })) {
            problem = "Enter full links starting with https://";
          }
          out = urls.length > 1 ? urls : urls[0] || "";
        }
        if (kind === "year" && raw) {
          out = Number(raw);
          if (!/^\d{4}$/.test(raw)) { problem = "Enter a four-digit year"; }
        }
        if (kind === "count" && raw) {
          out = Number(raw);
          if (!/^\d+$/.test(raw)) { problem = "Enter a whole number"; }
        }
        if (path === "short_name" && !raw) { problem = "A short name is required"; }
        if (path === "id") { problem = idProblem(raw); }
        if (problem) {
          err.textContent = problem;
          err.hidden = false;
          field.setAttribute("aria-invalid", "true");
          field.focus();
          return;
        }
        closePop();
        if (key(out) !== key(get(doc, path))) { commit(path, out); }
      }
    }

    function toggleChip(text, on) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "sed-chip";
      b.setAttribute("aria-pressed", on ? "true" : "false");
      b.innerHTML = '<span class="sed-chip__ck">' + ICON.check + "</span><span>" + esc(text) +
        "</span>";
      b.addEventListener("click", function () {
        b.setAttribute("aria-pressed", b.getAttribute("aria-pressed") === "true" ? "false" : "true");
      });
      return b;
    }

    function modesEditor(path, from) {
      var p = makePop(path, from, true);
      var current = get(doc, path) || [];
      var wrap = document.createElement("div");
      wrap.className = "sed-chips";
      cfg.modes.forEach(function (m) {
        var b = toggleChip(m.label, current.indexOf(m.id) !== -1);
        b.setAttribute("data-value", m.id);
        wrap.appendChild(b);
      });
      p.appendChild(wrap);
      p.appendChild(footer(function () {
        var out = Array.prototype.filter.call(wrap.children, function (b) {
          return b.getAttribute("aria-pressed") === "true";
        }).map(function (b) { return b.getAttribute("data-value"); });
        closePop();
        if (key(out) !== key(current)) { commit(path, out); }
      }));
      place();
      wrap.firstChild.focus();
    }

    /* A search box over a list, used to pick a licence or an organization.
       `items` are {value, text, html, group}; `other` offers a value that is
       not in the list, built from what was typed. */
    function picker(items, opts) {
      var box = document.createElement("div");
      box.className = "sed-pick";
      box.innerHTML = '<label class="sed-find">' + ICON.magnify +
        '<input type="search" autocomplete="off" placeholder="' + esc(opts.placeholder) +
        '" aria-label="' + esc(opts.placeholder) + '"></label><ul class="sed-list sed-list--pick" ' +
        'role="listbox"></ul>';
      var input = box.querySelector("input");
      var ul = box.querySelector("ul");
      var shown = [];
      var active = 0;

      function draw() {
        var q = input.value.trim().toLowerCase();
        shown = items.filter(function (it) {
          return !q || it.text.toLowerCase().indexOf(q) !== -1;
        }).slice(0, 60);
        if (opts.other && q && !items.some(function (it) { return it.text.toLowerCase() === q; })) {
          shown.push({ value: null, other: input.value.trim(),
            html: '<span class="sed-opt__t">' + ICON.plus + " " + esc(opts.otherLabel) +
              ' "' + esc(input.value.trim()) + '"</span>' });
        }
        var group = null;
        ul.innerHTML = "";
        shown.forEach(function (it, i) {
          if (it.group && it.group !== group && !q) {
            group = it.group;
            var g = document.createElement("li");
            g.className = "sed-group";
            g.setAttribute("role", "presentation");
            g.textContent = group;
            ul.appendChild(g);
          }
          var li = document.createElement("li");
          li.className = "sed-opt";
          li.setAttribute("role", "option");
          li.setAttribute("data-i", i);
          li.innerHTML = '<span class="sed-opt__v">' + it.html + "</span>";
          li.addEventListener("mousedown", function (e) { e.preventDefault(); });
          li.addEventListener("click", function () { choose(i); });
          ul.appendChild(li);
        });
        if (!shown.length) {
          ul.innerHTML = '<li class="sed-group" role="presentation">No match</li>';
        }
        setActive(0);
      }

      function setActive(i) {
        active = i;
        Array.prototype.forEach.call(ul.querySelectorAll(".sed-opt"), function (li) {
          var on = Number(li.getAttribute("data-i")) === i;
          li.classList.toggle("is-active", on);
          if (on && li.scrollIntoView) { li.scrollIntoView({ block: "nearest" }); }
        });
      }

      function choose(i) {
        var it = shown[i];
        if (!it) { return; }
        opts.onPick(it.other !== undefined ? { other: it.other } : { value: it.value });
      }

      input.addEventListener("input", draw);
      input.addEventListener("keydown", function (e) {
        if (e.key === "ArrowDown") { e.preventDefault(); setActive(Math.min(active + 1, shown.length - 1)); }
        else if (e.key === "ArrowUp") { e.preventDefault(); setActive(Math.max(active - 1, 0)); }
        else if (e.key === "Enter") { e.preventDefault(); choose(active); }
      });
      draw();
      box.focusInput = function () { input.focus(); };
      return box;
    }

    function licencesEditor(path, from) {
      var p = makePop(path, from, true);
      var rows = clone(get(doc, path) || []).map(function (l) {
        var m = LICENCES[l.id];
        return { id: l.id, scopes: l.scopes || [], other: !m && !!l.id, url: l.url || "" };
      });
      var list = document.createElement("div");
      list.className = "sed-lics";
      var add = document.createElement("button");
      add.type = "button";
      add.className = "ghost sed-add";
      add.innerHTML = ICON.plus + "<span>Add a licence</span>";
      add.addEventListener("click", function () {
        rows.push({ id: "", scopes: [], other: false, url: "" });
        drawRows(rows.length - 1);
      });
      p.appendChild(list);
      p.appendChild(add);
      p.appendChild(footer(apply));

      var cats = {};
      cfg.licence_categories.forEach(function (c) { cats[c.id] = c.label; });
      var items = cfg.licence_categories.reduce(function (acc, c) {
        return acc.concat(cfg.licences.filter(function (l) { return l.category === c.id; })
          .map(function (l) {
            return { value: l.id, text: l.id + " " + l.name, group: c.label,
              html: '<span class="sed-dot sed-dot--' + l.category + '"></span>' +
                '<span class="sed-opt__t">' + esc(l.id) + '</span><span class="sed-opt__h">' +
                esc(l.name) + "</span>" };
          }));
      }, []);

      function drawRows(openIndex) {
        list.innerHTML = "";
        rows.forEach(function (row, i) {
          var el = document.createElement("div");
          el.className = "sed-lic";
          var m = LICENCES[row.id];
          var name = row.other ? row.id || "Other licence" : m ? m.id : "Choose a licence";
          var sub = row.other ? "Not in the list yet" : m ? m.name : "";
          var combo = document.createElement("button");
          combo.type = "button";
          combo.className = "sed-combo";
          combo.setAttribute("aria-expanded", "false");
          combo.innerHTML = '<span class="sed-dot sed-dot--' + (m ? m.category : "unknown") +
            '"></span><span class="sed-combo__t"><span>' + esc(name) + "</span>" +
            (sub ? "<small>" + esc(sub) + "</small>" : "") + "</span>" + ICON["chevron-down"];
          var del = document.createElement("button");
          del.type = "button";
          del.className = "sed-icon";
          del.setAttribute("aria-label", "Remove " + name);
          del.innerHTML = ICON["delete-outline"];
          del.addEventListener("click", function () {
            rows.splice(i, 1);
            drawRows();
          });
          var top = document.createElement("div");
          top.className = "sed-lic__top";
          top.appendChild(combo);
          top.appendChild(del);
          el.appendChild(top);

          if (row.other) {
            var o = document.createElement("div");
            o.className = "sed-other";
            o.innerHTML = '<input class="sed-input" type="text" placeholder="Licence name" ' +
              'aria-label="Licence name"><input class="sed-input" type="url" ' +
              'placeholder="Link to the licence text" aria-label="Link to the licence text">';
            var ins = o.querySelectorAll("input");
            ins[0].value = row.id;
            ins[1].value = row.url;
            ins[0].addEventListener("input", function () { row.id = ins[0].value.trim(); });
            ins[1].addEventListener("input", function () { row.url = ins[1].value.trim(); });
            el.appendChild(o);
          }

          var scopes = document.createElement("div");
          scopes.className = "sed-chips sed-chips--sm";
          cfg.scopes.forEach(function (s) {
            var b = toggleChip(s.label, row.scopes.indexOf(s.id) !== -1);
            b.addEventListener("click", function () {
              var at = row.scopes.indexOf(s.id);
              if (at === -1) { row.scopes.push(s.id); } else { row.scopes.splice(at, 1); }
            });
            scopes.appendChild(b);
          });
          el.appendChild(scopes);

          var pick = null;
          combo.addEventListener("click", function () {
            if (pick) {
              pick.remove();
              pick = null;
              combo.setAttribute("aria-expanded", "false");
              return;
            }
            pick = picker(items, {
              placeholder: "Search licences",
              other: true,
              otherLabel: "Other licence",
              onPick: function (r) {
                if (r.other !== undefined) {
                  row.id = r.other;
                  row.other = true;
                } else {
                  row.id = r.value;
                  row.other = false;
                  row.url = "";
                }
                drawRows();
              }
            });
            top.insertAdjacentElement("afterend", pick);
            combo.setAttribute("aria-expanded", "true");
            pick.focusInput();
          });
          list.appendChild(el);
          if (openIndex === i) { combo.click(); }
        });
        place();
      }

      function apply() {
        var out = rows.filter(function (r) { return r.id; }).map(function (r) {
          var l = { id: r.id, scopes: r.scopes.slice() };
          if (r.other && r.url) { l.url = r.url; }
          return l;
        });
        closePop();
        if (key(out) !== key(get(doc, path))) { commit(path, out); }
      }

      if (rows.length) {
        drawRows(-1);
        list.querySelector(".sed-combo").focus();
      } else {
        rows.push({ id: "", scopes: [], other: false, url: "" });
        drawRows(0);
      }
    }

    function orgsEditor(path, from) {
      var p = makePop(path, from, true);
      var chosen = (get(doc, path) || []).slice();
      var chips = document.createElement("div");
      chips.className = "sed-picked";
      p.appendChild(chips);
      var holder = document.createElement("div");
      p.appendChild(holder);
      p.appendChild(footer(function () {
        closePop();
        if (key(chosen) !== key(get(doc, path))) { commit(path, chosen); }
      }));

      function drawChips() {
        chips.innerHTML = "";
        chosen.forEach(function (id, i) {
          var o = orgOf(id);
          var c = document.createElement("span");
          c.className = "sed-picked__c";
          c.innerHTML = orgLogo(o) + "<span>" + esc(o.name) + "</span>";
          var x = document.createElement("button");
          x.type = "button";
          x.className = "sed-icon sed-icon--sm";
          x.setAttribute("aria-label", "Remove " + o.name);
          x.innerHTML = ICON.close;
          x.addEventListener("click", function () {
            chosen.splice(i, 1);
            redraw();
          });
          c.appendChild(x);
          chips.appendChild(c);
        });
      }

      function redraw() {
        drawChips();
        holder.innerHTML = "";
        var items = cfg.organizations.filter(function (o) { return chosen.indexOf(o.id) === -1; })
          .map(function (o) {
            return { value: o.id, text: o.name + " " + o.short + " " + o.id,
              html: orgLogo(o) + '<span class="sed-opt__t">' + esc(o.name) + "</span>" };
          });
        var pk = picker(items, {
          placeholder: "Search organizations",
          other: true,
          otherLabel: "Add",
          onPick: function (r) {
            chosen.push(r.other !== undefined ? r.other : r.value);
            redraw();
          }
        });
        holder.appendChild(pk);
        place();
        pk.focusInput();
      }
      redraw();
    }

    /* ============================================================ edit bar */

    function showBar() {
      bar = document.createElement("div");
      bar.className = "sed-bar";
      bar.setAttribute("role", "region");
      bar.setAttribute("aria-label", "Suggest a change");
      bar.innerHTML = '<div class="sed-bar__in"><span class="sed-bar__t">' + ICON["pencil-outline"] +
        "<span>" + (isNew ? "New specification" : "Editing <strong>" + esc(cfg.name) + "</strong>") +
        "</span></span>" +
        '<span class="sed-bar__n" data-n></span>' +
        '<button type="button" class="ghost" data-discard>' + ICON.close +
        "<span>Discard</span></button>" +
        '<button type="button" class="btn btn--primary" data-review>' + ICON.check +
        "<span>Review</span></button></div>";
      root.appendChild(bar);
      document.body.classList.add("sed-has-bar");
      var discard = bar.querySelector("[data-discard]");
      var armed = null;
      discard.addEventListener("click", function () {
        if (!changes().length || armed) {
          clearTimeout(armed);
          clearDraft();
          stop();
          return;
        }
        discard.querySelector("span").textContent = "Discard " + plural(changes().length) + "?";
        armed = setTimeout(function () {
          armed = null;
          if (discard.isConnected) { discard.querySelector("span").textContent = "Discard"; }
        }, 3500);
      });
      bar.querySelector("[data-review]").addEventListener("click", review);
      updateBar();
    }

    function plural(n) { return n + (n === 1 ? " change" : " changes"); }

    function updateBar() {
      if (!bar) { return; }
      var n = changes().length;
      bar.querySelector("[data-n]").textContent = n ? plural(n) : "";
      bar.querySelector("[data-review]").disabled = n === 0 ||
        (isNew && (empty(get(doc, "short_name")) || !!idProblem(get(doc, "id") || "")));
    }

    /* ============================================================== drafts */

    function storeKey() { return STORE + (isNew ? "+new" : cfg.id); }

    function saveDraft() {
      var values = {};
      changes().forEach(function (p) {
        var v = get(doc, p);
        values[p] = v === undefined ? null : v;
      });
      try {
        if (Object.keys(values).length) {
          localStorage.setItem(storeKey(), JSON.stringify({ t: Date.now(), values: values,
            idByHand: idByHand }));
        } else {
          localStorage.removeItem(storeKey());
        }
      } catch (e) { /* storage off: the change lives as long as the tab */ }
    }

    function readDraft() {
      try {
        var d = JSON.parse(localStorage.getItem(storeKey()));
        return d && d.values && Object.keys(d.values).length ? d : null;
      } catch (e) { return null; }
    }

    function clearDraft() {
      try { localStorage.removeItem(storeKey()); } catch (e) { /* nothing kept */ }
    }

    function showDraftNotice() {
      hideDraftNotice();
      var d = readDraft();
      var box = root.querySelector(".contribute");
      if (!d || !box) { return; }
      var n = Object.keys(d.values).length;
      var note = document.createElement("div");
      note.className = "sed-draft";
      note.innerHTML = ICON["progress-clock"] + "<span>Your suggestion (" + plural(n) +
        ") has not been sent yet.</span>" +
        '<button type="button" class="btn btn--primary" data-resume>' + ICON["pencil-outline"] +
        "<span>Resume</span></button>" +
        '<button type="button" class="ghost" data-drop>Discard</button>';
      note.querySelector("[data-resume]").addEventListener("click", function () { start(true); });
      note.querySelector("[data-drop]").addEventListener("click", function () {
        clearDraft();
        hideDraftNotice();
      });
      box.insertBefore(note, box.firstChild);
    }

    function hideDraftNotice() {
      var n = root.querySelector(".sed-draft");
      if (n) { n.remove(); }
    }

    /* ======================================================== review + send */

    function shown(path, v) {
      if (empty(v)) { return ""; }
      if (path === "status") { return vocab(cfg.status, v).label; }
      if (/\.verdict$/.test(path)) { return vocab(cfg.verdict, v).label; }
      if (path === "adoption.lifecycle") { return vocab(cfg.lifecycle, v).label; }
      if (path === "adoption.tier") { return vocab(cfg.tier, v).label; }
      if (path === "adoption.confirmed_by_maintainer") { return v === true ? "Yes" : "No"; }
      if (path === "modes") { return v.map(function (m) { return vocab(cfg.modes, m).label; }).join(", "); }
      if (path === "maintainers") { return v.map(function (id) { return orgOf(id).name; }).join(", "); }
      if (path === "licences") {
        return v.map(function (l) {
          return l.id + (l.scopes && l.scopes.length ? " (" + l.scopes.join(", ") + ")" : "");
        }).join(", ");
      }
      if (path === "adoption.adopters_count") { return Number(v).toLocaleString("en-US"); }
      return Array.isArray(v) ? v.join(", ") : String(v);
    }

    function rows() {
      return changes().map(function (p) {
        return { path: p, label: label(p), before: shown(p, get(orig, p)), after: shown(p, get(doc, p)) };
      });
    }

    /* The change as it would be written in the file: only the keys that
       change, nested the way the file nests them. */
    function patch() {
      var out = {};
      changes().forEach(function (p) {
        if (p === "description" || p === "id") { return; }
        var v = get(doc, p);
        if (p === "licences") {
          v = (v || []).map(function (l) {
            var o = { id: l.id };
            if (l.scopes && l.scopes.length) { o.scopes = l.scopes; }
            return o;
          });
        }
        var parts = p.split(".");
        var at = out;
        for (var i = 0; i < parts.length - 1; i++) {
          at[parts[i]] = at[parts[i]] || {};
          at = at[parts[i]];
        }
        at[parts[parts.length - 1]] = empty(v) ? null : v;
      });
      return out;
    }

    function yamlOf(obj) {
      if (!Object.keys(obj).length) { return ""; }
      return window.jsyaml.dump(obj, { lineWidth: -1, noRefs: true, flowLevel: -1 })
        .replace(/: null$/gm, ":")
        .trim();
    }

    function cellText(s) {
      s = String(s || "").replace(/\s+/g, " ").trim();
      if (s.length > 120) { s = s.slice(0, 117).replace(/\s+\S*$/, "") + "..."; }
      return s ? s.replace(/\|/g, "\\|") : "_not set_";
    }

    /* The whole file for a new specification, laid out like the others, with
       every field present so the reviewer sees what is still empty. */
    function newFile() {
      var a = doc.adoption || {};
      var f = {
        short_name: doc.short_name || null,
        full_name: doc.full_name || null,
        homepage_url: doc.homepage_url || null,
        status: doc.status || "under_review",
        modes: doc.modes || [],
        maintainers: doc.maintainers || [],
        licences: (doc.licences || []).map(function (l) {
          var o = { id: l.id };
          if (l.scopes && l.scopes.length) { o.scopes = l.scopes; }
          return o;
        })
      };
      if (!empty(doc.licence_evidence_url)) { f.licence_evidence_url = doc.licence_evidence_url; }
      f.first_release_year = empty(doc.first_release_year) ? null : doc.first_release_year;
      f.adoption = { lifecycle: a.lifecycle || null, tier: a.tier || null };
      ["adopters_count", "adopters_count_updated", "adopters_registry_url",
        "confirmed_by_maintainer"].forEach(function (k) {
        if (!empty(a[k])) { f.adoption[k] = a[k]; }
      });
      f.principles = {};
      CRITERIA.forEach(function (k) {
        var c = doc.principles[k] || {};
        f.principles[k] = { verdict: c.verdict || "not_assessed", rationale: c.rationale || null,
          evidence_url: c.evidence_url || null };
      });
      return "---\n" + yamlOf(f) + "\n---\n\n# Description\n\n" +
        (doc.description || "").trim() + "\n";
    }

    function filePath() {
      return isNew ? "data/specifications/" + (doc.id || "new-specification") + ".md" : cfg.path;
    }

    function proposal(withTable) {
      var parts = [];
      if (withTable) {
        parts.push("| Field | Now | Suggested |\n| --- | --- | --- |\n" + rows().map(function (r) {
          return "| " + cellText(r.label) + " | " + cellText(r.before) + " | " + cellText(r.after) + " |";
        }).join("\n"));
      }
      if (isNew) {
        parts.push("New file `" + filePath() + "`:\n\n````markdown\n" + newFile() + "````");
      }
      var y = isNew ? "" : yamlOf(patch());
      if (y) { parts.push("In `" + cfg.path + "`:\n\n```yaml\n" + y + "\n```"); }
      if (!isNew && changed("description")) {
        parts.push("`# Description`:\n\n```markdown\n" + (doc.description || "") + "\n```");
      }
      var extra = [];
      (doc.licences || []).forEach(function (l) {
        if (l.id && !LICENCES[l.id]) {
          extra.push("- New licence, not yet in `data/licences.csv`: " + l.id + (l.url ? " (" + l.url + ")" : ""));
        }
      });
      (doc.maintainers || []).forEach(function (id) {
        if (!ORGS[id]) { extra.push("- New maintainer, not yet in `data/organizations/`: " + id); }
      });
      if (extra.length) { parts.push(extra.join("\n")); }
      return parts.join("\n\n");
    }

    function issueUrl(sources) {
      var base = "https://github.com/" + cfg.repo + "/issues/new";
      var params = function (change) {
        return "?template=" + encodeURIComponent(cfg.template) +
          "&title=" + encodeURIComponent(isNew ? "New specification: " + (doc.short_name || "")
            : "Suggested change: " + cfg.name) +
          "&spec_id=" + encodeURIComponent(isNew ? doc.id || "" : cfg.id) +
          "&change=" + encodeURIComponent(change) +
          (sources ? "&evidence=" + encodeURIComponent(sources) : "");
      };
      var url = base + params(proposal(true));
      if (url.length > URL_MAX) { url = base + params(proposal(false)); }
      if (url.length > URL_MAX) {
        url = base + params("Paste the suggestion copied from the registry page here.");
        return { url: url, paste: true };
      }
      return { url: url, paste: false };
    }

    function review() {
      closePop();
      loadYaml().then(openDialog, function () { openDialog(); });
    }

    function openDialog() {
      var dlg = document.createElement("dialog");
      dlg.className = "sed-dialog";
      dlg.setAttribute("aria-labelledby", "sed-dialog-title");
      var table = rows().map(function (r) {
        return '<tr><th scope="row">' + esc(r.label) + "</th>" + cell(r.before, "old") +
          cell(r.after, "new") + "</tr>";
      }).join("");
      dlg.innerHTML =
        '<form method="dialog" class="sed-dialog__in">' +
        '<div class="sed-step" data-step="review">' +
        '<h2 id="sed-dialog-title">' + (isNew ? "Review your proposal" : "Review your suggestion") +
        "</h2>" +
        '<div class="hist__scroll"><table class="hist__t"><thead><tr><th scope="col">Field</th>' +
        '<th scope="col">Now</th><th scope="col">Suggested</th></tr></thead><tbody>' + table +
        "</tbody></table></div>" +
        '<label class="sed-label" for="sed-sources">Sources</label>' +
        '<textarea id="sed-sources" class="sed-input" rows="3" placeholder="Links that support ' +
        'this change"></textarea>' +
        '<div class="sed-gh">' + ICON.github + "<p>Suggestions are sent and discussed on GitHub. " +
        'No account? <a href="#" data-signup>Create one for free</a>, your suggestion stays ' +
        "saved here meanwhile.</p></div>" +
        '<div class="sed-dialog__foot"><button type="button" class="ghost" data-back>' +
        "Back to editing</button>" +
        '<button type="button" class="btn btn--primary" data-send>' + ICON.github +
        "<span>Continue on GitHub</span>" + ICON["open-in-new"] + "</button></div></div>" +
        '<div class="sed-step" data-step="sent" hidden>' +
        '<h2>Finish on GitHub</h2>' +
        "<p>Submit the issue that opened in a new tab. Until you do, your suggestion stays " +
        "saved on this page.</p>" +
        '<p class="sed-paste" hidden>' + ICON["information-outline"] + "<span>It was too long " +
        "for a link: it is copied, paste it into the form.</span></p>" +
        '<div class="sed-dialog__foot"><button type="button" class="ghost" data-copy>' +
        ICON["content-copy"] + "<span>Copy suggestion</span></button>" +
        '<button type="button" class="ghost" data-again>' + ICON["open-in-new"] +
        "<span>Open GitHub again</span></button>" +
        '<button type="button" class="btn btn--primary" data-done>' + ICON.check +
        "<span>I submitted it</span></button></div></div>" +
        "</form>";
      root.appendChild(dlg);
      var sources = dlg.querySelector("#sed-sources");
      var target = null;

      function go(viaSignup) {
        target = issueUrl(sources.value.trim());
        if (target.paste) { copy(proposal(true)); }
        /* After signing up, GitHub returns to the pre-filled form. */
        var url = viaSignup
          ? "https://github.com/signup?return_to=" +
            encodeURIComponent(target.url.replace("https://github.com", ""))
          : target.url;
        window.open(url, "_blank", "noopener");
        dlg.querySelector('[data-step="review"]').hidden = true;
        dlg.querySelector('[data-step="sent"]').hidden = false;
        dlg.querySelector(".sed-paste").hidden = !target.paste;
      }

      dlg.querySelector("[data-send]").addEventListener("click", function () { go(false); });
      dlg.querySelector("[data-signup]").addEventListener("click", function (e) {
        e.preventDefault();
        go(true);
      });
      dlg.querySelector("[data-back]").addEventListener("click", function () { dlg.close(); });
      dlg.querySelector("[data-again]").addEventListener("click", function () {
        window.open(target.url, "_blank", "noopener");
      });
      dlg.querySelector("[data-copy]").addEventListener("click", function (e) {
        var b = e.currentTarget;
        copy(proposal(true)).then(function () {
          b.querySelector("span").textContent = "Copied";
          setTimeout(function () { b.querySelector("span").textContent = "Copy suggestion"; }, 2000);
        });
      });
      dlg.querySelector("[data-done]").addEventListener("click", function () {
        clearDraft();
        dlg.close();
        if (isNew) { location.href = "../"; } else { stop(); }
      });
      dlg.addEventListener("close", function () { dlg.remove(); });
      dlg.showModal();
    }

    function cell(value, kind) {
      if (!value) { return '<td class="hist__' + kind + ' is-empty">Not set</td>'; }
      var short = value.length > 160 ? value.slice(0, 158).replace(/\s+\S*$/, "") + "..." : value;
      return '<td class="hist__' + kind + '">' + esc(short) + "</td>";
    }

    function copy(text) {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        return navigator.clipboard.writeText(text).catch(function () { return legacyCopy(text); });
      }
      return Promise.resolve(legacyCopy(text));
    }

    function legacyCopy(text) {
      var t = document.createElement("textarea");
      t.value = text;
      t.style.position = "fixed";
      t.style.opacity = "0";
      document.body.appendChild(t);
      t.select();
      try { document.execCommand("copy"); } catch (e) { /* nothing more to try */ }
      t.remove();
    }
  }

  /* js-yaml, served next to this script, to write the change as YAML. */
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

  function isObj(v) { return v && typeof v === "object" && !Array.isArray(v); }

  function esc(s) {
    return String(s === undefined || s === null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
})();
