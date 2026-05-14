// Google Analytics 4 (GA4) bootstrap for static site.
// Measurement ID: G-NYDT6H7XR8
(function () {
  var MID = "G-NYDT6H7XR8";
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

