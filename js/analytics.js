/* ============================================================
   StaFlow — Loader do Google Analytics 4 + helper de eventos
   ------------------------------------------------------------
   ★ 18/08/2026 — a pedido do Breno.

   Carrega o gtag.js só se window.STAFLOW_GA4_MEASUREMENT_ID estiver
   configurado (ver js/analytics-config.js). Expõe window.staflowTrack()
   pras páginas dispararem eventos de conversão sem se preocupar se o
   GA carregou ou não (no-op silencioso se não tiver ID configurado).
   ============================================================ */
(function () {
  'use strict';

  var GA_ID = window.STAFLOW_GA4_MEASUREMENT_ID;

  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }
  window.gtag = window.gtag || gtag;

  if (GA_ID) {
    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(GA_ID);
    document.head.appendChild(s);

    gtag('js', new Date());
    // anonymize_ip: LGPD — não guarda o IP completo do visitante.
    gtag('config', GA_ID, { anonymize_ip: true });
  }

  // ---------- Helper de eventos de conversão ----------
  // Uso: window.staflowTrack('sign_up', { role: 'sindico' })
  // Se o GA não estiver configurado ainda, isso só não faz nada —
  // nunca quebra a página por falta de GA4_MEASUREMENT_ID.
  window.staflowTrack = function (eventName, params) {
    try {
      if (!GA_ID) return;
      gtag('event', eventName, params || {});
    } catch (_) { /* nunca deixa um erro de tracking quebrar o fluxo real */ }
  };
})();
