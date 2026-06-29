/* ============================================================
   StaFlow — Funções de Autenticação
   Tradução amigável de erros, helpers, proteção de rota.
   Depende de: window.staflowSupabase (ver supabase-client.js)
   ============================================================ */

(function () {
  'use strict';

  const sb = window.staflowSupabase;
  if (!sb) {
    console.error('[StaFlow auth] Supabase client não inicializado.');
    return;
  }

  // ---------- Tradução de erros do Supabase para PT-BR ----------
  function traduzirErro(err) {
    if (!err) return 'Algo deu errado. Tente novamente.';
    const msg = (err.message || String(err)).toLowerCase();

    if (msg.includes('invalid login credentials'))     return 'E-mail ou senha incorretos.';
    if (msg.includes('email not confirmed'))           return 'Confirme seu e-mail antes de entrar. Verifique sua caixa de entrada.';
    if (msg.includes('user already registered'))       return 'Esse e-mail já está cadastrado. Tente entrar ou recuperar a senha.';
    if (msg.includes('password should be at least'))   return 'A senha deve ter pelo menos 8 caracteres.';
    if (msg.includes('rate limit'))                    return 'Muitas tentativas. Aguarde um minuto e tente novamente.';
    if (msg.includes('over_email_send_rate_limit'))    return 'Aguarde alguns segundos antes de pedir outro e-mail.';
    if (msg.includes('security purposes') ||
        msg.includes('only request this after'))       return 'Aguarde alguns instantes antes de solicitar outro e-mail.';
    if (msg.includes('token has expired') ||
        msg.includes('invalid token'))                 return 'Link expirado. Solicite um novo.';
    if (msg.includes('network'))                       return 'Sem conexão. Verifique sua internet.';
    if (msg.includes('user not found'))                return 'Conta não encontrada.';
    return 'Não foi possível concluir. Tente novamente em instantes.';
  }

  // ---------- Sanitização básica ----------
  function clean(str) {
    if (typeof str !== 'string') return '';
    return str.trim().replace(/[<>]/g, '');
  }

  // ---------- AUTH ----------
  async function signIn(email, password) {
    try {
      const { data, error } = await sb.auth.signInWithPassword({
        email: clean(email).toLowerCase(),
        password
      });
      if (error) throw error;
      return { ok: true, data };
    } catch (err) {
      return { ok: false, error: traduzirErro(err) };
    }
  }

  async function signUp(email, password, metadata) {
    try {
      const { data, error } = await sb.auth.signUp({
        email: clean(email).toLowerCase(),
        password,
        options: {
          data: metadata || {},
          emailRedirectTo: `${location.origin}/auth/callback`
        }
      });
      if (error) throw error;
      return { ok: true, data };
    } catch (err) {
      return { ok: false, error: traduzirErro(err) };
    }
  }

  async function signOut() {
    try {
      const { error } = await sb.auth.signOut();
      if (error) throw error;
      return { ok: true };
    } catch (err) {
      return { ok: false, error: traduzirErro(err) };
    }
  }

  async function resetPassword(email) {
    try {
      const { error } = await sb.auth.resetPasswordForEmail(clean(email).toLowerCase(), {
        redirectTo: `${location.origin}/auth/callback` // callback troca o code PKCE e redireciona para nova-senha
      });
      if (error) throw error;
      return { ok: true };
    } catch (err) {
      return { ok: false, error: traduzirErro(err) };
    }
  }

  async function updatePassword(newPassword) {
    try {
      const { data, error } = await sb.auth.updateUser({ password: newPassword });
      if (error) throw error;
      return { ok: true, data };
    } catch (err) {
      return { ok: false, error: traduzirErro(err) };
    }
  }

  async function resendConfirmation(email) {
    try {
      const { error } = await sb.auth.resend({
        type: 'signup',
        email: clean(email).toLowerCase(),
        options: { emailRedirectTo: `${location.origin}/auth/callback` }
      });
      if (error) throw error;
      return { ok: true };
    } catch (err) {
      return { ok: false, error: traduzirErro(err) };
    }
  }

  async function getCurrentUser() {
    const { data } = await sb.auth.getUser();
    return data?.user || null;
  }

  async function getCurrentSession() {
    const { data } = await sb.auth.getSession();
    return data?.session || null;
  }

  function onAuthStateChange(cb) {
    return sb.auth.onAuthStateChange((event, session) => cb(event, session));
  }

  // ---------- PROFILES ----------
  async function getProfile(userId) {
    try {
      const id = userId || (await getCurrentUser())?.id;
      if (!id) return { ok: false, error: 'Sessão inválida.' };
      const { data, error } = await sb.from('profiles').select('*').eq('id', id).single();
      if (error) throw error;
      return { ok: true, data };
    } catch (err) {
      return { ok: false, error: traduzirErro(err) };
    }
  }

  async function updateProfile(userId, patch) {
    try {
      const id = userId || (await getCurrentUser())?.id;
      if (!id) return { ok: false, error: 'Sessão inválida.' };
      const { data, error } = await sb.from('profiles')
        .update(patch).eq('id', id).select().single();
      if (error) throw error;
      return { ok: true, data };
    } catch (err) {
      return { ok: false, error: traduzirErro(err) };
    }
  }

  // ---------- ROUTE GUARD ----------
  // Use em páginas protegidas no topo do <body> ou antes do conteúdo:
  //   <script>staflowAuth.checkAuth();</script>
  async function checkAuth(redirectTo) {
    const session = await getCurrentSession();
    if (!session) {
      const target = redirectTo || '/auth/login.html';
      location.replace(target);
      return null;
    }
    return session;
  }

  // ---------- SUBSCRIPTION ----------
  // Considera "vigente" apenas status active OU trialing E ainda dentro
  // do período atual. Bloqueia past_due, canceled, pending e expirados.
  //
  // Retorna o objeto da assinatura se vigente, ou:
  //   null                      → sem assinatura nenhuma (precisa /planos.html)
  //   { _blocked: true, ... }   → tem assinatura mas inadimplente/expirada
  async function checkSubscription() {
    try {
      const user = await getCurrentUser();
      if (!user) return null;

      const { data, error } = await sb
        .from('subscriptions')
        .select('*')
        .eq('profile_id', user.id)
        .maybeSingle();

      if (error || !data) return null;

      const statusValido = data.status === 'active' || data.status === 'trialing';
      const periodoValido =
        data.current_period_end == null ||
        new Date(data.current_period_end) > new Date();

      if (statusValido && periodoValido) {
        return data;
      }

      // Tem registro mas não está vigente — sinaliza para UI
      return {
        ...data,
        _blocked: true,
        _reason: !statusValido
          ? (data.status === 'past_due' ? 'past_due'
            : data.status === 'canceled' ? 'canceled'
            : 'inactive')
          : 'expired'
      };
    } catch {
      return null;
    }
  }

  // ---------- LOAD FULL SESSION (consumido pelo route-guard) ----------
  // Carrega em uma chamada: session, profile, claim funcionário, subscription.
  // Idempotente — pode ser chamado múltiplas vezes sem efeitos colaterais
  // adicionais (claim retorna o mesmo vínculo existente).
  //
  // Retorna:
  //   { user, profile, subscription, claimed }
  //   - user: { id, email } | null
  //   - profile: row da tabela profiles | null
  //   - subscription: row da tabela subscriptions | null
  //     (pode vir com _blocked=true e _reason; ver checkSubscription)
  //   - claimed: true se o claim_funcionario_by_email() vinculou nesta chamada
  async function loadFullSession() {
    const session = await getCurrentSession();
    if (!session?.user) {
      return { user: null, profile: null, subscription: null, claimed: false };
    }
    const user = session.user;

    // ★ TRAVA — E-MAIL NÃO CONFIRMADO
    // Se chegou aqui sem email_confirmed_at, é bypass via callback PKCE
    // mal configurado ou alguém forçando session via SDK admin. Força
    // signOut + sinaliza o login pra mostrar mensagem amigável.
    // (Quando 'Confirm email' está ON no Supabase Auth, signInWithPassword
    // já bloqueia. Esta verificação é defense in depth no nível do client.)
    if (!user.email_confirmed_at) {
      try { await sb.auth.signOut(); } catch (_) {}
      const path = location.pathname || '';
      const isPublic = ['/auth/login', '/auth/cadastro', '/auth/callback',
                        '/auth/recuperar-senha', '/auth/nova-senha',
                        '/staflow-landing', '/', '/404']
        .some(p => path === p || path === p + '.html');
      if (!isPublic) {
        location.replace('/auth/login.html?reason=email_not_confirmed');
      }
      return { user: null, profile: null, subscription: null, claimed: false };
    }

    // 1. Tenta vincular funcionário (idempotente — não faz nada se já estiver
    //    vinculado, e não cria nada se o email não bater)
    let claimed = false;
    try {
      const claim = await sb.rpc('claim_funcionario_by_email').single();
      if (claim?.data?.vinculado) claimed = true;
    } catch (_) { /* RPC pode falhar; profile será carregado mesmo assim */ }

    // 2. Carrega profile (depois do claim — pega role atualizada)
    const profRes = await getProfile();
    const profile = profRes.ok ? profRes.data : null;

    // 3. ★ MULTI-CNPJ — Lista condomínios do user (alimenta o switcher)
    //    e resolve o "ativo" persistido em localStorage.
    let condominios = [];
    let condominioAtualId = null;
    if (profile && (profile.role === 'sindico' || profile.role === 'admin')) {
      try {
        const r = await sb.rpc('meus_condominios');
        condominios = r?.data || [];
        // Lê seleção persistida; valida se ainda é membro
        const persisted = (() => { try { return localStorage.getItem('staflow_condo_atual'); } catch(_) { return null; }})();
        if (persisted && condominios.some(c => c.condominio_id === persisted)) {
          condominioAtualId = persisted;
        } else if (condominios.length > 0) {
          condominioAtualId = condominios[0].condominio_id;
          try { localStorage.setItem('staflow_condo_atual', condominioAtualId); } catch(_) {}
        }
      } catch (_) { /* RPC pode falhar — segue com lista vazia */ }
    }

    // 3b. Propaga o condomínio ativo no header HTTP do cliente Supabase
    //    pra que my_condominio_id() leia do contexto correto.
    if (condominioAtualId && sb.rest?.headers) {
      sb.rest.headers['x-condominio-id'] = condominioAtualId;
    }

    // 4. Subscription do condomínio ATIVO (não mais do user)
    let subscription = null;
    if (profile && (profile.role === 'sindico' || profile.role === 'admin') && condominioAtualId) {
      subscription = await checkSubscriptionPorCondo(condominioAtualId);
    }

    return { user, profile, subscription, claimed, condominios, condominioAtualId };
  }

  // ---------- MULTI-CNPJ HELPERS ----------
  // Subscription do condomínio específico (não mais do user).
  async function checkSubscriptionPorCondo(condoId) {
    try {
      const { data, error } = await sb
        .from('subscriptions')
        .select('*')
        .eq('condominio_id', condoId)
        .maybeSingle();
      if (error || !data) return null;
      const statusValido  = data.status === 'active' || data.status === 'trialing';
      const periodoValido = data.current_period_end == null ||
                            new Date(data.current_period_end) > new Date();
      if (statusValido && periodoValido) return data;
      return {
        ...data,
        _blocked: true,
        _reason: !statusValido
          ? (data.status === 'past_due' ? 'past_due'
            : data.status === 'canceled' ? 'canceled' : 'inactive')
          : 'expired'
      };
    } catch { return null; }
  }

  // Troca o condomínio ativo. Persiste, propaga no header e dispara reload.
  function switchCondominio(condoId) {
    if (!condoId) return;
    try { localStorage.setItem('staflow_condo_atual', condoId); } catch(_) {}
    if (sb.rest?.headers) sb.rest.headers['x-condominio-id'] = condoId;
    // Reload para reidratar todo o estado da página com o novo contexto
    location.reload();
  }

  function getCondominioAtualId() {
    try { return localStorage.getItem('staflow_condo_atual'); } catch(_) { return null; }
  }

  // ---------- API GLOBAL ----------
  window.staflowAuth = {
    signIn, signUp, signOut,
    resetPassword, updatePassword, resendConfirmation,
    getCurrentUser, getCurrentSession, onAuthStateChange,
    getProfile, updateProfile,
    checkAuth, checkSubscription, checkSubscriptionPorCondo,
    loadFullSession, traduzirErro,
    switchCondominio, getCondominioAtualId
  };
})();
