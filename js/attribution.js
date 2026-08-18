/* ============================================================
   StaFlow — Captura de atribuição de marketing (primeiro toque)
   ------------------------------------------------------------
   ★ 18/08/2026 — a pedido do Breno, pra ele conseguir ver de onde
   vêm os cadastros (e-mail, campanha específica, etc.) e não só
   "quantos cadastros" no vácuo.

   Como funciona:
   - Roda em toda página pública (landing, planos, cadastro, login).
   - Na PRIMEIRA visita, lê utm_source/utm_medium/utm_campaign/
     utm_content da URL (se vieram de um link com essas tags) e o
     document.referrer, e guarda no localStorage por 90 dias.
   - Se a pessoa já tem uma atribuição salva, NÃO sobrescreve —
     é "primeiro toque" (first-touch): o que trouxe a pessoa da
     primeira vez continua valendo, mesmo que ela feche a aba e
     volte depois direto pela barra de endereço.
   - auth/cadastro.html lê isso na hora do cadastro e manda junto
     no signUp() (metadata) — o banco grava em condominios via
     ensure_condominio() (ver sql/029_atribuicao_marketing.sql).

   Uso de link em campanha: staflow.app.br/?utm_source=email&utm_campaign=leads-agosto-2026
   ============================================================ */
(function () {
  'use strict';

  var KEY      = 'staflow_attribution';
  var TTL_DIAS = 90;

  function lerSalva() {
    try {
      var raw = localStorage.getItem(KEY);
      if (!raw) return null;
      var obj = JSON.parse(raw);
      if (!obj.ts || (Date.now() - obj.ts) > TTL_DIAS * 24 * 60 * 60 * 1000) return null;
      return obj;
    } catch (_) { return null; }
  }

  function salvar(obj) {
    try { localStorage.setItem(KEY, JSON.stringify(obj)); } catch (_) { /* storage bloqueado — segue sem atribuição */ }
  }

  function capturar() {
    if (lerSalva()) return; // já tem primeiro-toque salvo — não sobrescreve

    var qs = new URLSearchParams(location.search);
    var utm_source   = qs.get('utm_source');
    var utm_medium   = qs.get('utm_medium');
    var utm_campaign = qs.get('utm_campaign');
    var utm_content  = qs.get('utm_content');
    var referrer     = document.referrer || null;

    // Sem UTM e sem referrer: navegação direta (digitou a URL, favoritos
    // etc.) — não há nada útil pra guardar.
    if (!utm_source && !referrer) return;

    salvar({
      ts: Date.now(),
      utm_source:   utm_source   || null,
      utm_medium:   utm_medium   || null,
      utm_campaign: utm_campaign || null,
      utm_content:  utm_content  || null,
      referrer:     referrer,
      landing_page: location.pathname
    });
  }

  capturar();

  window.staflowAttribution = { get: lerSalva };
})();
