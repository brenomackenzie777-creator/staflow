/* ============================================================
   StaFlow — Cliente Supabase
   Inicializa o cliente único usado em toda a aplicação.
   ============================================================
   COMO USAR:
   1. Antes deste script, inclua o SDK do Supabase via CDN:
      <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
   2. Em seguida inclua este arquivo:
      <script src="/js/supabase-client.js"></script>
   3. Disponibiliza globalmente: window.staflowSupabase
   ============================================================ */

(function () {
  'use strict';

  // ⚠️ SUBSTITUIR pelos valores do projeto StaFlow no painel Supabase
  // Painel → Settings → API → Project URL e anon public key
  const SUPABASE_URL      = 'https://wsxpskrrzqtdoodpoofx.supabase.co';
  const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndzeHBza3JyenF0ZG9vZHBvb2Z4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzg4NDExNzksImV4cCI6MjA5NDQxNzE3OX0.GOJgWFpm9vIPuTCrhCK4TWriLrcjxXP9VGSMekI4Tfs';

  if (!window.supabase || typeof window.supabase.createClient !== 'function') {
    console.error('[StaFlow] SDK do Supabase não carregado. Adicione o <script> do CDN antes deste arquivo.');
    return;
  }

  // Alerta dev quando rodando sem HTTPS em produção
  if (location.hostname !== 'localhost' && location.protocol !== 'https:') {
    console.warn('[StaFlow] Atenção: aplicação rodando sem HTTPS. Auth tokens podem ser interceptados.');
  }

  // Multi-CNPJ: header customizado lido por my_condominio_id() no Postgres.
  // Lido aqui ANTES do cliente subir; switchCondominio() atualiza em runtime.
  const condoAtual = (() => {
    try { return localStorage.getItem('staflow_condo_atual'); } catch(_) { return null; }
  })();

  const globalHeaders = {};
  if (condoAtual) globalHeaders['x-condominio-id'] = condoAtual;

  const client = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
    auth: {
      autoRefreshToken:   true,
      persistSession:     true,
      detectSessionInUrl: true,
      storage:            window.localStorage,
      flowType:           'pkce'
    },
    global: { headers: globalHeaders }
  });

  window.staflowSupabase = client;
})();
