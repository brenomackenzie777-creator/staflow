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
        redirectTo: `${location.origin}/auth/nova-senha`
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

  // ---------- API GLOBAL ----------
  window.staflowAuth = {
    signIn, signUp, signOut,
    resetPassword, updatePassword, resendConfirmation,
    getCurrentUser, getCurrentSession, onAuthStateChange,
    getProfile, updateProfile,
    checkAuth, checkSubscription, traduzirErro
  };
})();
