// Google Analytics 4 (GA4) bootstrap for static site.
// 1) index.html で window.__GA4_MEASUREMENT_ID__ を宣言するとそれを優先
// 2) 未設定のときは下記の既定 ID（GitHub Actions の GA4_MEASUREMENT_ID または index の window 行で上書き可能）
(function () {
  var raw = "";
  try {
    if (typeof window !== "undefined" && window.__GA4_MEASUREMENT_ID__) {
      raw = String(window.__GA4_MEASUREMENT_ID__).trim();
    }
  } catch (_e) {}
  var MID = /^G-[A-Z0-9]+$/.test(raw) ? raw : "G-2WG5ES7LVQ";
  if (!MID || !/^G-[A-Z0-9]+$/.test(MID)) return;

  if (window.gtag && window.dataLayer) {
    try {
      window.gtag("config", MID);
    } catch (_e) {}
    return;
  }

  window.dataLayer = window.dataLayer || [];
  function gtag() {
    window.dataLayer.push(arguments);
  }
  window.gtag = gtag;
  gtag("js", new Date());

  var s = document.createElement("script");
  s.async = true;
  s.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(MID);
  document.head.appendChild(s);

  gtag("config", MID);
})();

