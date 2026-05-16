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

  // ---------- Toast ----------
  function toast(msg, type = 'success') {
    let t = document.getElementById('toast');
    if (!t) {
      t = document.createElement('div');
      t.id = 'toast';
      t.className = 'toast';
      t.innerHTML = '<span class="ico"></span><span class="msg"></span>';
      document.body.appendChild(t);
    }
    t.className = 'toast show ' + type;
    t.querySelector('.ico').textContent = type === 'success' ? '✓' : '⚠';
    t.querySelector('.msg').textContent = msg;
    clearTimeout(window.__tt);
    window.__tt = setTimeout(() => t.className = 'toast', 4000);
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

    // 2. Garante condomínio vinculado ao perfil (RPC)
    try {
      await window.staflowSupabase.rpc('ensure_condominio');
    } catch (e) { /* silencioso — usuário pode não ser sindico/admin */ }

    // 3. Perfil
    const { ok, data: profile, error } = await window.staflowAuth.getProfile();
    if (!ok) {
      toast(error, 'error');
      hideSplash();
      return null;
    }

    // 4. Preencher sidebar
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

    // 8. Mobile drawer
    const tgl = document.getElementById('menu-toggle');
    const sb  = document.getElementById('sidebar');
    if (tgl && sb) tgl.addEventListener('click', () => sb.classList.toggle('open'));

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
      <a class="sb-link" data-route="ponto"        href="#"><span class="ico">●</span> Ponto</a>
      <a class="sb-link" data-route="tarefas"      href="#"><span class="ico">✓</span> Tarefas</a>
      <a class="sb-link" data-route="faltas"       href="#"><span class="ico">⚠</span> Faltas</a>

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

  // ---------- API global ----------
  window.staflowApp.toast          = toast;
  window.staflowApp.iniciais       = iniciais;
  window.staflowApp.saudacao       = saudacao;
  window.staflowApp.roleLabel      = roleLabel;
  window.staflowApp.bootstrapShell = bootstrapShell;
  window.staflowApp.renderSidebar  = renderSidebar;
  window.staflowApp.hideSplash     = hideSplash;
})();
