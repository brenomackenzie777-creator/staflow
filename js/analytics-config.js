/* ============================================================
   StaFlow — Configuração do Google Analytics 4 (FRONTEND)
   ------------------------------------------------------------
   ★ 18/08/2026 — a pedido do Breno, pra medir visitas, cliques e
   cadastros no site (complementa a atribuição gravada no banco —
   ver js/attribution.js e sql/029_atribuicao_marketing.sql).

   PENDENTE PRO BRENO — 3 passos, ~3 minutos:
   1. Acesse https://analytics.google.com
   2. Admin (ícone de engrenagem) → Criar propriedade → dê um nome
      (ex: "StaFlow") → fuso horário Brasil → moeda BRL.
   3. Em "Fluxos de dados" → Web → adicione o site
      https://staflow.app.br → copie o "ID de mensuração"
      (começa com "G-") e cole abaixo, substituindo null.

   Sem o ID preenchido, js/analytics.js simplesmente não carrega o
   Google Analytics — o site continua funcionando normalmente, só
   não fica sendo medido ainda.
   ============================================================ */

window.STAFLOW_GA4_MEASUREMENT_ID = null; // ← cole aqui o "G-XXXXXXXXXX"
