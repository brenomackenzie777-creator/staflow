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
  //
  // ARQUITETURA: toda decisão de "pode renderizar aqui?" é delegada ao
  // window.staflowGuard.executarRoteamentoSeguro (tronco superior de
  // roteamento). bootstrapShell só faz a parte VISUAL e de DOM depois
  // que o guard autoriza.
  async function bootstrapShell(opts = {}) {
    const route = opts.route || 'dashboard';

    // 1. Carrega sessão completa: user + claim + profile + subscription + condominios
    const { user, profile, subscription, claimed, condominios, condominioAtualId } =
      await window.staflowAuth.loadFullSession();

    // 2. Se o claim vinculou, limpa a flag de pending (cadastro como colab)
    if (claimed) window.staflowGuard.limparPendingColabClaim();

    // 3. ★ TRONCO SUPERIOR DE ROTEAMENTO — única decisão autoritativa
    const g = window.staflowGuard.executarRoteamentoSeguro(user, profile, {
      hasActiveSubscription: !!subscription && !subscription._blocked,
      isBlockedSubscription: !!subscription?._blocked,
      blockReason: subscription?._reason
    });
    if (!g.allow) return null;   // guard já redirecionou ou bloqueou

    // 4. Daqui pra baixo: sindico/admin autorizado em página admin.
    //    Garante condomínio vinculado (síndico recém-criado pode não ter).
    try {
      await window.staflowSupabase.rpc('ensure_condominio');
    } catch (_) { /* silencioso */ }

    // 5. Preencher sidebar
    const elName   = document.getElementById('u-name');
    const elRole   = document.getElementById('u-role');
    const elAvatar = document.getElementById('u-avatar');
    if (elName)   elName.textContent   = profile.full_name || profile.email;
    if (elRole)   elRole.textContent   = roleLabel(profile.role);
    if (elAvatar) elAvatar.textContent = iniciais(profile.full_name);

    // 5b. ★ MULTI-CNPJ — monta o switcher de condomínios no topo
    renderCondoSwitcher(condominios || [], condominioAtualId);

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
    if (btnHelp) btnHelp.addEventListener('click', () => toast('Central de ajuda em breve. Por enquanto: contato@staflow.com.br', 'success'));

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

  // ---------- Switcher de Condomínios (Multi-CNPJ) ----------
  // Injeta um dropdown no topo da .main + botão "Novo condomínio".
  // Idempotente: se já existe, só atualiza o conteúdo.
  function renderCondoSwitcher(condos, ativoId) {
    if (!condos || condos.length === 0) return;
    const main = document.querySelector('.main');
    if (!main) return;

    // CSS injetado uma vez
    if (!document.getElementById('condo-switcher-styles')) {
      const style = document.createElement('style');
      style.id = 'condo-switcher-styles';
      style.textContent = `
        .condo-switcher { position: relative; display: inline-flex; align-items: center; gap: 8px;
          background: var(--navy); border: 1px solid var(--border); border-radius: var(--radius-card, 12px);
          padding: 6px 10px 6px 14px; font-family: var(--font-body); margin-bottom: 14px; }
        .condo-switcher .label { font-family: var(--font-mono); font-size: 9px; letter-spacing: 1.5px;
          color: var(--white-muted); text-transform: uppercase; }
        .condo-switcher select { background: transparent; border: none; color: var(--white);
          font-family: inherit; font-size: 13px; font-weight: 600; padding: 6px 24px 6px 6px;
          appearance: none; -webkit-appearance: none; cursor: pointer; outline: none; max-width: 220px; }
        .condo-switcher::after { content: '▾'; position: absolute; right: 36px; pointer-events: none;
          color: var(--teal); font-size: 11px; }
        .condo-switcher .badge-plano { font-family: var(--font-mono); font-size: 9px; letter-spacing: 1px;
          padding: 2px 7px; border-radius: var(--radius-btn, 8px); background: var(--teal-dim);
          color: var(--teal); border: 1px solid var(--teal-border); text-transform: uppercase; }
        .condo-switcher .badge-plano.warn { background: rgba(255,209,102,0.10); color: var(--amber);
          border-color: rgba(255,209,102,0.25); }
        .condo-switcher .btn-novo { margin-left: 6px; background: transparent; border: 1px solid var(--border);
          color: var(--white-dim); border-radius: var(--radius-btn, 8px); padding: 5px 10px; font-size: 12px;
          font-family: inherit; cursor: pointer; transition: all 0.2s ease; }
        .condo-switcher .btn-novo:hover { color: var(--teal); border-color: var(--teal); }
      `;
      document.head.appendChild(style);
    }

    let wrap = document.getElementById('condo-switcher');
    const ativo = condos.find(c => c.condominio_id === ativoId) || condos[0];
    const planoLabel = (ativo?.plano || 'starter').toUpperCase();
    const isBlocked = ativo?.status_assinatura === 'past_due' ||
                       ativo?.status_assinatura === 'canceled' ||
                       ativo?.status_assinatura === 'inactive';

    const optionsHtml = condos.map(c =>
      `<option value="${c.condominio_id}" ${c.condominio_id === ativoId ? 'selected' : ''}>${escapeHtml(c.nome || '—')}</option>`
    ).join('');

    const html = `
      <span class="label">Condomínio</span>
      <select id="condo-switcher-select">${optionsHtml}</select>
      <span class="badge-plano ${isBlocked ? 'warn' : ''}">${escapeHtml(planoLabel)}</span>
      <button type="button" class="btn-novo" id="btn-novo-condo" title="Cadastrar novo condomínio">+ Novo</button>
    `;

    if (!wrap) {
      wrap = document.createElement('div');
      wrap.id = 'condo-switcher';
      wrap.className = 'condo-switcher';
      wrap.innerHTML = html;
      // Insere no topo da .main, antes do topbar
      const topbar = main.querySelector('.topbar');
      if (topbar) main.insertBefore(wrap, topbar);
      else main.insertBefore(wrap, main.firstChild);
    } else {
      wrap.innerHTML = html;
    }

    document.getElementById('condo-switcher-select').addEventListener('change', (e) => {
      window.staflowAuth.switchCondominio(e.target.value);
    });
    document.getElementById('btn-novo-condo').addEventListener('click', () => {
      // Política comercial: 2º+ condomínio sempre exige plano pago
      location.href = '/planos.html?novo=1';
    });
  }

  function escapeHtml(s) {
    return String(s || '').replace(/[&<>"']/g,
      c => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]));
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
  // Prefixos perigosos que Excel/Sheets interpretam como fórmula.
  // CVE clássica (CWE-1236): nome de funcionário '=cmd|/c calc' pode
  // executar código no Excel da contabilidade. Prefixamos com aspas
  // simples (tratamento oficial recomendado pelo OWASP).
  function neutralizeFormula(s) {
    if (typeof s !== 'string' || s.length === 0) return s;
    const first = s.charAt(0);
    if (first === '=' || first === '+' || first === '-' || first === '@' || first === '\t' || first === '\r') {
      return "'" + s;
    }
    return s;
  }
  function csvEscape(v) {
    if (v == null) return '';
    let s = neutralizeFormula(String(v));
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
  /* ────────────────────────────────────────────────────────────────
     EXPORT XLS — Relatório Executivo Visual (HTML table → .xls)
     ────────────────────────────────────────────────────────────────
     Gera uma planilha .xls usando HTML table com CSS inline.
     Excel/LibreOffice/Sheets abrem nativamente. Zero dependência
     externa (sem CDN, sem biblioteca).

     opts = {
       titulo:       'Espelho de Ponto',                       // título do relatório
       condominio:   { nome, cnpj, endereco },                 // cabeçalho corporativo
       periodo:      'Maio/2026',                              // string de período
       resumo:       [{label, value}, ...],                    // metadados rápidos
       colunas:      [{ label, key, width?, type? }],          // type: 'text'|'mono'|'status'
       rows:         [{key1:..., key2:...}, ...],              // dados
       statusKey:    'auditStatus',                            // qual key disparar cor
       statusColors: { 'OK': 'green', 'FRAUDE_SUSPECT': 'red' } // map valor → 'green'|'red'|'yellow'
     }
  ──────────────────────────────────────────────────────────── */
  const XLS_COLORS = {
    navy:        '#1A2238',
    white:       '#FFFFFF',
    zebra:       '#F5F7FB',
    softGreen:   '#E6F7F1',
    softGreenTx: '#0E8C66',
    softRed:     '#FCEAEA',
    softRedTx:   '#A82121',
    softYellow:  '#FFF4DA',
    softYellowTx:'#8A6100',
    border:      '#D7DCE4',
    textMuted:   '#5F6B7A',
    headerBg:    '#1A2238',
    titleAccent: '#06D6A0'
  };

  function xlsEscape(v) {
    if (v == null) return '';
    // Aplica neutralizeFormula ANTES do escape HTML — defesa contra
    // CSV/XLS formula injection mesmo em planilhas abertas no Excel.
    const safe = neutralizeFormula(String(v));
    return safe
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function cellStyleFor(type, statusColor) {
    const base = 'border:1px solid ' + XLS_COLORS.border + ';padding:6px 10px;vertical-align:middle;';
    let extra = '';
    if (type === 'mono') extra += 'font-family:Consolas,monospace;text-align:center;';
    if (statusColor === 'green')  extra += 'background:' + XLS_COLORS.softGreen  + ';color:' + XLS_COLORS.softGreenTx  + ';font-weight:600;';
    if (statusColor === 'red')    extra += 'background:' + XLS_COLORS.softRed    + ';color:' + XLS_COLORS.softRedTx    + ';font-weight:600;';
    if (statusColor === 'yellow') extra += 'background:' + XLS_COLORS.softYellow + ';color:' + XLS_COLORS.softYellowTx + ';font-weight:600;';
    return base + extra;
  }

  function exportXLS(filename, opts) {
    opts = opts || {};
    const cols       = opts.colunas || [];
    const rows       = opts.rows    || [];
    const condo      = opts.condominio || {};
    const resumo     = opts.resumo  || [];
    const statusKey  = opts.statusKey;
    const statusMap  = opts.statusColors || {};
    const totalCols  = cols.length || 1;

    // ── Bloco de cabeçalho corporativo ──
    const headerHtml = `
      <table style="border-collapse:collapse;width:100%;font-family:Arial,sans-serif;margin-bottom:14px;">
        <tr>
          <td colspan="${totalCols}" style="padding:14px 12px;background:${XLS_COLORS.headerBg};color:${XLS_COLORS.white};border:1px solid ${XLS_COLORS.headerBg};">
            <div style="font-size:18px;font-weight:bold;letter-spacing:0.5px;">
              ${xlsEscape(opts.titulo || 'Relatório')}
              <span style="color:${XLS_COLORS.titleAccent};margin-left:8px;font-size:12px;font-weight:normal;">· STAFLOW</span>
            </div>
            <div style="font-size:11px;color:#B8C2D1;margin-top:4px;">
              ${xlsEscape(opts.periodo || '')}
              ${opts.periodo && condo.nome ? ' · ' : ''}
              ${xlsEscape(condo.nome || '')}
            </div>
          </td>
        </tr>
        ${condo.cnpj || condo.endereco ? `
        <tr>
          <td colspan="${totalCols}" style="padding:8px 12px;background:${XLS_COLORS.zebra};color:${XLS_COLORS.textMuted};border:1px solid ${XLS_COLORS.border};font-size:10px;">
            ${condo.cnpj     ? '<strong>CNPJ:</strong> ' + xlsEscape(condo.cnpj)       : ''}
            ${condo.cnpj && condo.endereco ? ' &nbsp;·&nbsp; ' : ''}
            ${condo.endereco ? '<strong>Endereço:</strong> ' + xlsEscape(condo.endereco) : ''}
          </td>
        </tr>` : ''}
      </table>
    `;

    // ── Bloco de resumo (cards horizontais) ──
    let resumoHtml = '';
    if (resumo.length > 0) {
      resumoHtml = `
        <table style="border-collapse:collapse;width:100%;font-family:Arial,sans-serif;margin-bottom:14px;">
          <tr>
            ${resumo.map(m => `
              <td style="padding:10px 14px;border:1px solid ${XLS_COLORS.border};background:${XLS_COLORS.white};vertical-align:top;">
                <div style="font-size:9px;color:${XLS_COLORS.textMuted};letter-spacing:1.5px;text-transform:uppercase;">${xlsEscape(m.label)}</div>
                <div style="font-size:15px;font-weight:bold;color:${XLS_COLORS.headerBg};margin-top:4px;">${xlsEscape(m.value)}</div>
              </td>
            `).join('')}
          </tr>
        </table>
      `;
    }

    // ── Tabela de dados (cabeçalho navy + zebra + cor condicional) ──
    const colgroup = cols.map(c =>
      `<col style="width:${c.width || 100}px;">`).join('');

    const theadHtml = `
      <thead>
        <tr>
          ${cols.map(c => `
            <th style="background:${XLS_COLORS.headerBg};color:${XLS_COLORS.white};font-weight:bold;padding:8px 10px;border:1px solid ${XLS_COLORS.headerBg};text-align:left;font-size:11px;letter-spacing:0.3px;">
              ${xlsEscape(c.label)}
            </th>`).join('')}
        </tr>
      </thead>
    `;

    const tbodyHtml = '<tbody>' + rows.map((r, i) => {
      const zebraBg = i % 2 === 1 ? `background:${XLS_COLORS.zebra};` : '';
      return '<tr>' + cols.map(c => {
        const raw = r[c.key];
        const isStatus = statusKey && c.key === statusKey;
        const statusColor = isStatus ? statusMap[raw] || null : null;
        const style = cellStyleFor(c.type, statusColor) + (statusColor ? '' : zebraBg);
        return `<td style="${style}">${xlsEscape(raw == null ? '' : raw)}</td>`;
      }).join('') + '</tr>';
    }).join('') + '</tbody>';

    const tableHtml = `
      <table style="border-collapse:collapse;width:100%;font-family:Arial,sans-serif;font-size:11px;">
        <colgroup>${colgroup}</colgroup>
        ${theadHtml}
        ${tbodyHtml}
      </table>
    `;

    // Rodapé
    const gerado = new Date();
    const ger = gerado.toLocaleString('pt-BR', { dateStyle:'short', timeStyle:'short' });
    const footerHtml = `
      <table style="border-collapse:collapse;width:100%;font-family:Arial,sans-serif;margin-top:14px;">
        <tr>
          <td style="padding:6px 10px;color:${XLS_COLORS.textMuted};font-size:9px;border-top:1px solid ${XLS_COLORS.border};">
            Gerado por StaFlow em ${ger} · staflow.app.br
          </td>
        </tr>
      </table>
    `;

    // ExcelWorkbook XML — força o Excel a usar 1 sheet sem prompt + auto-fit
    const wbXml = `
      <xml>
        <x:ExcelWorkbook>
          <x:ExcelWorksheets>
            <x:ExcelWorksheet>
              <x:Name>Relatório</x:Name>
              <x:WorksheetOptions>
                <x:DisplayGridlines/>
              </x:WorksheetOptions>
            </x:ExcelWorksheet>
          </x:ExcelWorksheets>
        </x:ExcelWorkbook>
      </xml>
    `;

    const fullHtml =
      '<html xmlns:o="urn:schemas-microsoft-com:office:office" ' +
      'xmlns:x="urn:schemas-microsoft-com:office:excel" ' +
      'xmlns="http://www.w3.org/TR/REC-html40">' +
      '<head><meta charset="UTF-8">' + wbXml + '</head>' +
      '<body>' + headerHtml + resumoHtml + tableHtml + footerHtml + '</body></html>';

    // BOM UTF-8 garante acentos OK no Excel pt-BR
    const blob = new Blob(['﻿' + fullHtml],
      { type: 'application/vnd.ms-excel;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a   = document.createElement('a');
    a.href     = url;
    a.download = filename.replace(/\.(csv|xlsx|xls)$/i, '') + '.xls';
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  window.staflowApp.toast          = toast;
  window.staflowApp.iniciais       = iniciais;
  window.staflowApp.saudacao       = saudacao;
  window.staflowApp.roleLabel      = roleLabel;
  window.staflowApp.bootstrapShell = bootstrapShell;
  window.staflowApp.renderSidebar  = renderSidebar;
  window.staflowApp.hideSplash     = hideSplash;
  window.staflowApp.exportCSV      = exportCSV;
  window.staflowApp.exportXLS      = exportXLS;
  window.staflowApp.showToast      = showToast;
  window.staflowApp.skeletonRows   = skeletonRows;
  window.staflowApp.skeletonStats  = skeletonStats;
})();
