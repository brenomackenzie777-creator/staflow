/* ====================================================================
   StaFlow — Route Guard Autoritativo (Tronco Superior de Roteamento)
   --------------------------------------------------------------------
   ÚNICO ponto do sistema que decide para onde o usuário pode ir.
   Toda página privada chama executarRoteamentoSeguro() no boot e
   só renderiza o conteúdo se a função autorizar.

   Princípios:
   - decideRota() é PURA → auditável e testável (sem side-effects)
   - ejetar() é o único lugar que faz location.replace()
   - idempotência: chamadas repetidas produzem o mesmo veredito
   - anti-loop: se o destino é a página atual, NÃO redireciona
   - whitelist de paths para classificar e bloquear acessos cruzados

   Regras de bifurcação (autoritativas):
   - profile.role === 'funcionario' ou flag pending → /colaborador
   - profile.role in ('sindico','admin'):
       sem subscription ativa → /planos
       em /colaborador → ejetar para /dashboard
       caso contrário → autoriza
   - sem user → /auth/login
   ==================================================================== */

(function () {
  'use strict';

  // ─── Whitelist de rotas conhecidas ─────────────────────────────────
  const PAGES = {
    PUBLIC: [
      '/', '/staflow-landing', '/404',
      '/auth/login', '/auth/cadastro', '/auth/callback',
      '/auth/recuperar-senha', '/auth/nova-senha'
    ],
    FUNCIONARIO: ['/colaborador'],
    ADMIN:       ['/dashboard','/funcionarios','/ponto','/tarefas','/faltas','/configuracoes'],
    PLANOS:      ['/planos']
  };

  // ─── Helpers de path ───────────────────────────────────────────────
  function normalizarPath(p) {
    if (!p) return '/';
    p = p.split('?')[0].split('#')[0];
    p = p.replace(/\.html$/i, '');
    if (p.length > 1 && p.endsWith('/')) p = p.slice(0, -1);
    return p.toLowerCase();
  }

  function classificarPath(path) {
    const p = normalizarPath(path);
    if (PAGES.FUNCIONARIO.includes(p)) return 'funcionario';
    if (PAGES.ADMIN.includes(p))       return 'admin';
    if (PAGES.PLANOS.includes(p))      return 'planos';
    if (PAGES.PUBLIC.includes(p))      return 'public';
    return 'unknown';
  }

  // ─── Flag de cadastro pendente (do fluxo /auth/cadastro como colab) ─
  function temFlagPendingColab() {
    try { return !!localStorage.getItem('staflow_pending_colab_claim'); }
    catch (_) { return false; }
  }

  // ─── DECISÃO PURA (testável sem DOM) ───────────────────────────────
  // Inputs:
  //   user     : { id, email } | null
  //   profile  : { id, role, condominio_id, ... } | null
  //   pathname : string  (location.pathname)
  //   opts     : {
  //     hasActiveSubscription?: boolean,
  //     isBlockedSubscription?: boolean,
  //     blockReason?: string  // 'past_due'|'canceled'|'expired'|'inactive'
  //   }
  // Output:
  //   { redirectTo: string|null, allow: boolean, reason: string }
  function decideRota(user, profile, pathname, opts) {
    opts = opts || {};
    const path = normalizarPath(pathname);
    const kind = classificarPath(pathname);
    const pendingColab = temFlagPendingColab();

    // 1) Não autenticado
    if (!user) {
      if (kind === 'public') return { redirectTo: null, allow: true, reason: 'public_anon' };
      return { redirectTo: '/auth/login.html', allow: false, reason: 'not_authenticated' };
    }

    // 2) Autenticado em página de auth (exceto callback) → ejeta
    const authPages = ['/auth/login','/auth/cadastro','/auth/recuperar-senha','/auth/nova-senha'];
    if (authPages.includes(path)) {
      if ((profile && profile.role === 'funcionario') || pendingColab) {
        return { redirectTo: '/colaborador.html', allow: false, reason: 'authed_on_auth_page_to_colab' };
      }
      // sindico/admin sem subscription → planos
      if (profile && (profile.role === 'sindico' || profile.role === 'admin')) {
        if (opts.isBlockedSubscription || opts.hasActiveSubscription === false) {
          const r = opts.blockReason || 'inactive';
          return { redirectTo: '/planos.html?reason=' + encodeURIComponent(r), allow: false, reason: 'authed_on_auth_page_no_sub' };
        }
      }
      return { redirectTo: '/dashboard.html', allow: false, reason: 'authed_on_auth_page_to_dash' };
    }

    // 3) Páginas públicas: sempre passa (mesmo autenticado pode ver landing)
    if (kind === 'public') {
      return { redirectTo: null, allow: true, reason: 'public_authed' };
    }

    // 4) Sem profile carregado em página privada → defensivo: login
    if (!profile) {
      return { redirectTo: '/auth/login.html', allow: false, reason: 'no_profile' };
    }

    // 5) ★ REGRA AUTORITATIVA — FUNCIONÁRIO
    //    profile.role === 'funcionario' OU flag pending de cadastro
    //    como colaborador → SÓ pode acessar /colaborador.
    if (profile.role === 'funcionario' || pendingColab) {
      if (kind === 'funcionario') {
        return { redirectTo: null, allow: true, reason: 'funcionario_in_colab' };
      }
      // Tentou qualquer outra coisa → eject para /colaborador
      return { redirectTo: '/colaborador.html', allow: false, reason: 'funcionario_ejected_from_' + kind };
    }

    // 6) ★ REGRA AUTORITATIVA — SINDICO/ADMIN
    if (profile.role === 'sindico' || profile.role === 'admin') {
      // Admin tentando entrar em /colaborador → eject para /dashboard
      if (kind === 'funcionario') {
        return { redirectTo: '/dashboard.html', allow: false, reason: 'admin_ejected_from_colab' };
      }
      // Páginas admin exigem subscription ativa
      if (kind === 'admin') {
        if (opts.isBlockedSubscription || opts.hasActiveSubscription === false) {
          const r = opts.blockReason || 'inactive';
          return { redirectTo: '/planos.html?reason=' + encodeURIComponent(r), allow: false, reason: 'admin_no_sub' };
        }
        return { redirectTo: null, allow: true, reason: 'admin_with_sub' };
      }
      // Página de planos: sempre permitida pra admin (precisa pra contratar/regularizar)
      if (kind === 'planos') {
        return { redirectTo: null, allow: true, reason: 'admin_in_planos' };
      }
      // Rota desconhecida (mas autenticado) — permite render (será 404.html)
      return { redirectTo: null, allow: true, reason: 'admin_unknown_path' };
    }

    // 7) Role desconhecida (defensivo) — desloga e manda pro login
    return { redirectTo: '/auth/login.html', allow: false, reason: 'unknown_role' };
  }

  // ─── Detector anti-reconhecimento ──────────────────────────────────
  // Se um funcionário tenta acessar 3+ rotas admin em 60s (sintoma
  // de tentativa de enumeração), forçamos signOut + destruição do
  // token de sessão. Falso positivo é raro: usuário legítimo não
  // navega por bookmarks errados em sequência rápida.
  const RECON_KEY    = 'staflow_recon_attempts';
  const RECON_WINDOW = 60 * 1000;   // 60s
  const RECON_THRESHOLD = 3;
  function registrarTentativaSuspeita(reason) {
    if (!reason || !reason.startsWith('funcionario_ejected_from_')) return;
    try {
      const now = Date.now();
      const raw = sessionStorage.getItem(RECON_KEY);
      let arr = raw ? JSON.parse(raw) : [];
      arr = arr.filter(t => now - t < RECON_WINDOW);
      arr.push(now);
      sessionStorage.setItem(RECON_KEY, JSON.stringify(arr));
      if (arr.length >= RECON_THRESHOLD) {
        // Destrói token e força login
        sessionStorage.removeItem(RECON_KEY);
        try { localStorage.removeItem('staflow_pending_colab_claim'); } catch(_) {}
        if (window.staflowSupabase?.auth?.signOut) {
          window.staflowSupabase.auth.signOut().finally(() => {
            location.replace('/auth/login.html?reason=suspicious_activity');
          });
        } else {
          location.replace('/auth/login.html?reason=suspicious_activity');
        }
        return true;
      }
    } catch(_) { /* sessionStorage bloqueado → segue normal */ }
    return false;
  }

  // ─── EFEITO COLATERAL ÚNICO: location.replace ──────────────────────
  function ejetar(redirectTo, currentPath, reason) {
    const targetNorm  = normalizarPath(redirectTo);
    const currentNorm = normalizarPath(currentPath);
    if (targetNorm === currentNorm) {
      // Anti-loop: já estamos no destino — não redireciona
      console.warn('[guard] ejetar() para mesma rota suprimido:', redirectTo);
      return false;
    }
    // Hardening: detecta padrão de reconhecimento e força signOut
    if (registrarTentativaSuspeita(reason)) return true;
    location.replace(redirectTo);
    return true;
  }

  // ─── API PÚBLICA ───────────────────────────────────────────────────
  // Decide e executa o redirect. O caller deve checar { allow } antes de seguir.
  function executarRoteamentoSeguro(user, profile, opts) {
    const dec = decideRota(user, profile, location.pathname, opts);
    if (dec.allow) return { allow: true, decision: dec };
    if (dec.redirectTo) {
      const ejected = ejetar(dec.redirectTo, location.pathname, dec.reason);
      // Se NÃO ejetou (loop), permite render — caso degenerado, melhor mostrar
      // a página do que travar.
      return { allow: !ejected, decision: dec };
    }
    return { allow: false, decision: dec };
  }

  // Helper: limpa flag de pending claim (chamado quando o vínculo dá certo)
  function limparPendingColabClaim() {
    try { localStorage.removeItem('staflow_pending_colab_claim'); } catch (_) {}
  }

  window.staflowGuard = {
    executarRoteamentoSeguro,
    decideRota,
    classificarPath,
    normalizarPath,
    temFlagPendingColab,
    limparPendingColabClaim
  };
})();
