/* ============================================================
   StaFlow — App Shell
   Funções compartilhadas pelas páginas internas (dashboard,
   funcionarios, configuracoes, etc.):
   - Proteção de rota (checkAuth)
   - Carregamento de perfil + ensure_condominio
   - Toast helper
   - Sidebar (menu do usuário, mobile drawer, logout)
   - Highlight do link ativo
   ============================================================ */

window.staflowApp = window.staflowApp || {};

(function () {
  'use strict';

  // ---------- Toast (success | error | warning | info) ----------
  const TOAST_ICONS = {
    success: '✓',
    error:   '✕',
    warning: '!',
    info:    'i'
  };
  function showToast(msg, type = 'success', durationMs) {
    const t = ensureToast();
    const safeType = TOAST_ICONS[type] ? type : 'info';
    t.className = 'toast show ' + safeType;
    t.querySelector('.ico').textContent = TOAST_ICONS[safeType];
    t.querySelector('.msg').textContent = msg;
    clearTimeout(window.__tt);
    window.__tt = setTimeout(() => t.className = 'toast', durationMs || 4000);
  }
  function ensureToast() {
    let t = document.getElementById('toast');
    if (!t) {
      t = document.createElement('div');
      t.id = 'toast';
      t.className = 'toast';
      t.innerHTML = '<span class="ico"></span><span class="msg"></span>';
      document.body.appendChild(t);
    } else if (!t.querySelector('.ico')) {
      // Página tem o elemento mas sem markup interno — normaliza
      t.innerHTML = '<span class="ico"></span><span class="msg"></span>';
    }
    return t;
  }
  // Alias para compatibilidade com chamadas existentes
  const toast = showToast;

  // ---------- Skeleton loaders ----------
  // skeletonRows(tbodyId, cols, rowCount) — preenche o <tbody> com linhas
  // de skeleton enquanto a Promise de carga ainda está pendente.
  function skeletonRows(tbodyOrId, cols = 5, rowCount = 5) {
    const tbody = typeof tbodyOrId === 'string'
      ? document.getElementById(tbodyOrId)
      : tbodyOrId;
    if (!tbody) return;
    const widths = ['w-80', 'w-60', 'w-50', 'w-30', 'w-60', 'w-50'];
    let html = '';
    for (let r = 0; r < rowCount; r++) {
      let tds = '';
      for (let c = 0; c < cols; c++) {
        if (c === 0) {
          // Primeira coluna: avatar/círculo + bloco de texto
          tds += `<td>
            <span class="sk-circle"></span>
            <span class="sk-text-block">
              <span class="sk-bar w-60"></span>
              <span class="sk-bar sm w-30"></span>
            </span>
          </td>`;
        } else {
          tds += `<td><span class="sk-bar ${widths[c % widths.length]}"></span></td>`;
        }
      }
      html += `<tr class="sk-row">${tds}</tr>`;
    }
    tbody.innerHTML = html;
  }

  // skeletonStats(ids) — substitui o conteúdo de cada elemento por uma sk-bar
  function skeletonStats(ids = []) {
    ids.forEach(id => {
      const el = document.getElementById(id);
      if (el) el.innerHTML = '<span class="sk-bar lg w-50"></span>';
    });
  }

  // ---------- Helpers ----------
  function iniciais(nome) {
    if (!nome) return '?';
    const parts = nome.trim().split(/\s+/);
    return ((parts[0]?.[0] || '') + (parts[parts.length - 1]?.[0] || '')).toUpperCase();
  }
  function saudacao() {
    const h = new Date().getHours();
    if (h < 12) return 'Bom dia';
    if (h < 18) return 'Boa tarde';
    return 'Boa noite';
  }
  function roleLabel(r) {
    return ({ sindico: 'Síndico', admin: 'Administrador', funcionario: 'Funcionário' })[r] || '—';
  }

  // ---------- Sidebar bootstrap ----------
  // Espera o DOM ter os elementos #u-name, #u-role, #u-avatar, .sb-link[data-route]
  async function bootstrapShell(opts = {}) {
    const route = opts.route || 'dashboard';

    // 1. Proteger
    const session = await window.staflowAuth.checkAuth('/auth/login.html');
    if (!session) return null;

    // 2. Verificar assinatura vigente — bloqueia se inexistente, expirada,
    //    past_due ou canceled. Em todos os casos redireciona para /planos.html.
    const sub = await window.staflowAuth.checkSubscription();
    if (!sub || sub._blocked) {
      const motivo = sub?._reason;
      if (motivo) {
        // Sinaliza o motivo via query string para a tela de planos exibir o toast
        const params = new URLSearchParams({ reason: motivo });
        location.replace('/planos.html?' + params.toString());
      } else {
        location.replace('/planos.html');
      }
      return null;
    }

    // 3a. Tenta vincular como funcionário primeiro (auto-claim por e-mail).
    //     Se o usuário foi pré-cadastrado em /funcionarios pelo síndico, esta
    //     RPC rebaixa role para 'funcionario' e seta condominio_id correto.
    let isFuncionario = false;
    try {
      const claim = await window.staflowSupabase.rpc('claim_funcionario_by_email').single();
      if (claim.data && claim.data.vinculado) isFuncionario = true;
    } catch (e) { /* RPC pode não existir em ambientes antigos — silencioso */ }

    // 3a-bis. Se o user marcou "Sou Colaborador" no cadastro e o claim
    //         falhou, redireciona para /colaborador.html que tem UI
    //         própria explicando que o e-mail não foi cadastrado.
    let pendingColabClaim = null;
    try { pendingColabClaim = localStorage.getItem('staflow_pending_colab_claim'); } catch(_) {}
    if (pendingColabClaim && !isFuncionario) {
      // Mantém a flag — colaborador.html mostra a tela "Conta não vinculada"
      location.replace('/colaborador.html');
      return null;
    }
    if (isFuncionario) {
      // Vínculo deu certo — limpa a flag
      try { localStorage.removeItem('staflow_pending_colab_claim'); } catch(_) {}
    }

    // 3b. Garante condomínio APENAS para síndicos/admins (evita criar
    //     condomínio órfão para funcionários recém-cadastrados).
    if (!isFuncionario) {
      try {
        await window.staflowSupabase.rpc('ensure_condominio');
      } catch (e) { /* silencioso */ }
    }

    // 4. Perfil
    const { ok, data: profile, error } = await window.staflowAuth.getProfile();
    if (!ok) {
      toast(error, 'error');
      hideSplash();
      return null;
    }

    // 4b. ROUTE GUARD POR ROLE — funcionário não acessa páginas admin.
    //     Síndico/admin não acessa /colaborador.html. bootstrapShell é
    //     chamado pelas páginas admin; se chegou aqui com role=funcionario
    //     redireciona para o app de bolso.
    if (profile.role === 'funcionario') {
      location.replace('/colaborador.html');
      return null;
    }

    // 4c. Preencher sidebar
    const elName   = document.getElementById('u-name');
    const elRole   = document.getElementById('u-role');
    const elAvatar = document.getElementById('u-avatar');
    if (elName)   elName.textContent   = profile.full_name || profile.email;
    if (elRole)   elRole.textContent   = roleLabel(profile.role);
    if (elAvatar) elAvatar.textContent = iniciais(profile.full_name);

    // 5. Highlight do link ativo
    document.querySelectorAll('.sb-link').forEach(a => {
      a.classList.toggle('active', a.dataset.route === route);
    });

    // 6. Menu do usuário
    const menu    = document.getElementById('user-menu');
    const btnMenu = document.getElementById('btn-menu');
    if (btnMenu && menu) {
      btnMenu.addEventListener('click', (e) => { e.stopPropagation(); menu.classList.toggle('show'); });
      document.addEventListener('click', (e) => { if (!menu.contains(e.target)) menu.classList.remove('show'); });
    }

    // Ajuda (placeholder)
    const btnHelp = document.getElementById('btn-help');
    if (btnHelp) btnHelp.addEventListener('click', () => toast('Central de ajuda em breve. Por enquanto: brenomackenzie777@gmail.com', 'success'));

    // 7. Logout
    const btnLogout = document.getElementById('btn-logout');
    if (btnLogout) {
      btnLogout.addEventListener('click', async () => {
        const res = await window.staflowAuth.signOut();
        if (!res.ok) { toast(res.error, 'error'); return; }
        location.replace('/auth/login.html');
      });
    }

    // 8. Mobile drawer + backdrop
    const tgl = document.getElementById('menu-toggle');
    const sb  = document.getElementById('sidebar');
    if (tgl && sb) {
      // Cria backdrop sob demanda
      let bd = document.querySelector('.sidebar-backdrop');
      if (!bd) {
        bd = document.createElement('div');
        bd.className = 'sidebar-backdrop';
        document.body.appendChild(bd);
      }
      const closeDrawer = () => {
        sb.classList.remove('open');
        bd.classList.remove('show');
      };
      tgl.addEventListener('click', () => {
        const open = sb.classList.toggle('open');
        bd.classList.toggle('show', open);
      });
      bd.addEventListener('click', closeDrawer);
      // Fecha ao navegar dentro do drawer
      sb.querySelectorAll('a.sb-link').forEach(a => a.addEventListener('click', closeDrawer));
      // Fecha com Esc
      document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeDrawer(); });
    }

    // 9. Auto-logout na expiração
    window.staflowAuth.onAuthStateChange((event) => {
      if (event === 'SIGNED_OUT') location.replace('/auth/login.html');
    });

    hideSplash();
    return profile;
  }

  function hideSplash() {
    const s = document.getElementById('splash');
    if (s) s.classList.add('hide');
  }

  // ---------- HTML do Sidebar (injetado para evitar duplicação) ----------
  function sidebarHTML() {
    return `
      <a href="/dashboard.html" class="sb-brand">
        <img src="/assets/logo-mark.svg" alt="StaFlow">
        <div class="wm"><span class="sta">STA</span><span class="flow">FLOW</span></div>
      </a>

      <div class="sb-section">Geral</div>
      <a class="sb-link" data-route="dashboard"    href="/dashboard.html"><span class="ico">▦</span> Dashboard</a>
      <a class="sb-link" data-route="ponto"        href="/ponto.html"><span class="ico">●</span> Ponto</a>
      <a class="sb-link" data-route="tarefas"      href="/tarefas.html"><span class="ico">✓</span> Tarefas</a>
      <a class="sb-link" data-route="faltas"       href="/faltas.html"><span class="ico">⚠</span> Faltas</a>

      <div class="sb-section">Equipe</div>
      <a class="sb-link" data-route="funcionarios" href="/funcionarios.html"><span class="ico">◐</span> Funcionários</a>

      <div class="sb-section">Conta</div>
      <a class="sb-link" data-route="configuracoes" href="/configuracoes.html"><span class="ico">⚙</span> Configurações</a>

      <div class="sb-spacer"></div>

      <div class="user-menu" id="user-menu">
        <button onclick="location.href='/configuracoes.html'">⚙ Meu perfil</button>
        <button id="btn-help">？ Ajuda</button>
        <hr>
        <button id="btn-logout" class="danger">⏻ Sair</button>
      </div>

      <div class="sb-user">
        <div class="avatar" id="u-avatar">—</div>
        <div class="info">
          <div class="name" id="u-name">…</div>
          <div class="role" id="u-role">…</div>
        </div>
        <button class="menu-btn" id="btn-menu" aria-label="Menu">⋯</button>
      </div>
    `;
  }

  function renderSidebar(targetId = 'sidebar') {
    const el = document.getElementById(targetId);
    if (el) el.innerHTML = sidebarHTML();
  }

  // ---------- CSV helper (BOM UTF-8 para abrir corretamente no Excel) ----------
  // header: ['Coluna A', 'Coluna B', ...]
  // rows:   [[v1, v2, ...], [v1, v2, ...], ...]   (valores brutos; serão escapados)
  // filename: 'relatorio_2026-05.csv'
  function csvEscape(v) {
    if (v == null) return '';
    const s = String(v);
    // Se contém vírgula, aspa, quebra de linha → cerca com aspas e escapa "
    if (/[",\n\r;]/.test(s)) return '"' + s.replace(/"/g, '""') + '"';
    return s;
  }
  function exportCSV(header, rows, filename) {
    const lines = [
      header.map(csvEscape).join(','),
      ...rows.map(r => r.map(csvEscape).join(','))
    ];
    // BOM UTF-8 (﻿) garante acentos corretos no Excel/Numbers
    const csv  = '﻿' + lines.join('\r\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  // ---------- API global ----------
  window.staflowApp.toast          = toast;
  window.staflowApp.iniciais       = iniciais;
  window.staflowApp.saudacao       = saudacao;
  window.staflowApp.roleLabel      = roleLabel;
  window.staflowApp.bootstrapShell = bootstrapShell;
  window.staflowApp.renderSidebar  = renderSidebar;
  window.staflowApp.hideSplash     = hideSplash;
  window.staflowApp.exportCSV      = exportCSV;
  window.staflowApp.showToast      = showToast;
  window.staflowApp.skeletonRows   = skeletonRows;
  window.staflowApp.skeletonStats  = skeletonStats;
})();
