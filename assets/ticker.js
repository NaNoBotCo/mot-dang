/* ticker.js — last week's traffic, one slow line above the footer.
   Reads ticker.json beside this file (written weekly by ~/.claude/traffic-scripts/ticker.py).
   <script src="ticker.js" defer></script>; data-base="/carolina-barbecue" when the site lives under a path.
   Tap or hover stops it; reduced motion gets a still line that scrolls sideways. */
(function () {
  var me = document.currentScript;
  if (!me || !window.fetch) return;
  var base = me.getAttribute("data-base") || "";
  var src = me.src.replace(/ticker\.js(\?.*)?$/, "ticker.json");

  function norm(p) {
    if (base && p.indexOf(base) === 0) p = p.slice(base.length);
    p = p.replace(/index\.html$/, "").replace(/\.html$/, "").replace(/\/+$/, "");
    return p || "/";
  }
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  var root = document.documentElement;
  // motdang: the site's own language toggle hides .th / .en; Thai leads, as everywhere there
  var siteLang = /\blang-(both|th|en)\b/.test(root.className);
  function pair(x) {
    if (siteLang)
      return '<span class="th" lang="th">' + esc(x.th) + '</span><span class="en" lang="en"><span class="th"> · </span>' + esc(x.en) + "</span>";
    return '<span lang="en">' + esc(x.en) + '</span> · <span lang="th">' + esc(x.th) + "</span>";
  }

  fetch(src, { cache: "no-cache" }).then(function (r) { return r.ok ? r.json() : null; }).then(function (d) {
    if (!d || !d.fleet) return;
    var items = [].concat((d.pages && d.pages[norm(location.pathname)]) || [], d.site || [], d.fleet);
    var line = '<b class="tk-head">' + pair(d.head) + "</b>" +
      items.map(function (x) { return '<span class="tk-i">' + pair(x) + "</span>"; }).join("");

    var css = document.createElement("style");
    css.textContent =
      ".tk{overflow:hidden;white-space:nowrap;font-size:.74rem;line-height:1.9;opacity:.72;" +
      "border-top:1px solid rgba(127,127,127,.25);border-bottom:1px solid rgba(127,127,127,.25);" +
      "margin:1.2rem 0 0;cursor:pointer;-webkit-user-select:none;user-select:none}" +
      ".tk-run{display:inline-block;animation:tk-go var(--tk-s,90s) linear infinite}" +
      ".tk:hover .tk-run,.tk.tk-stop .tk-run,.tk:focus-within .tk-run{animation-play-state:paused}" +
      ".tk-set{display:inline-block;padding-right:3rem}" +
      ".tk-head{font-weight:600;margin-right:1.4rem}" +
      ".tk-i{margin-right:1.4rem}.tk-i:before{content:'•';margin-right:1.4rem;opacity:.5}" +
      "@keyframes tk-go{from{transform:translateX(0)}to{transform:translateX(-50%)}}" +
      "@media (prefers-reduced-motion:reduce){.tk{overflow-x:auto;cursor:auto}.tk-run{animation:none}.tk-run .tk-set+.tk-set{display:none}}";
    document.head.appendChild(css);

    var box = document.createElement("aside");
    box.className = "tk";
    box.setAttribute("aria-label", d.head.en);
    box.innerHTML = '<div class="tk-run"><span class="tk-set">' + line + '</span><span class="tk-set" aria-hidden="true">' + line + "</span></div>";
    box.addEventListener("click", function () { box.classList.toggle("tk-stop"); });

    var foot = document.querySelector("main footer, body > footer, footer");
    if (foot && foot.parentNode) foot.parentNode.insertBefore(box, foot);
    else document.body.appendChild(box);

    var w = box.querySelector(".tk-set").offsetWidth;
    if (w) box.style.setProperty("--tk-s", Math.max(30, Math.round(w / 45)) + "s");
  }).catch(function () {});
})();
