# Prompt Rafael — Sprint 5: Teste iOS PWA

**Data:** 26/06/2026  
**Status:** Sprints 1–4 concluídos · 10/10 bugs resolvidos  
**Objetivo:** Validar que o PWA funciona perfeitamente no iPhone

---

## Contexto

Decisão do Breno: **PWA melhorado** (sem app store por agora). O `colaborador.html` precisa funcionar como app na home screen do iPhone, tanto quanto no Android. Não há necessidade de Play Store ou App Store — a prioridade é a experiência ser fluida nos dois sistemas.

---

## Checklist de teste — iPhone (Safari iOS 16.4+)

Testa em dispositivo real. Emulador não vale para PWA no iOS.

### 1. Instalação como PWA

- [ ] Abrir `staflow.app.br/colaborador` no Safari
- [ ] Compartilhar → "Adicionar à Tela de Início"
- [ ] Ícone aparece corretamente (logo I — blocos azuis, não o bolt nem SF)
- [ ] App abre em modo standalone (sem barra de URL do Safari)
- [ ] `theme_color` aparece na status bar (deve ser `#0d0f12` ou similar escuro)

### 2. Autenticação

- [ ] Login com email funciona no webview Safari
- [ ] Magic link abre no app (não redireciona para o Safari externo)
- [ ] Sessão persiste ao fechar e reabrir o app

### 3. Fluxo de ponto

- [ ] Botão de ponto visível sem scroll no iPhone SE (menor tela suportada)
- [ ] Botão de ponto visível sem scroll no iPhone 14
- [ ] GPS captura corretamente (pede permissão na primeira vez)
- [ ] Batida de entrada registra com `audit_status: OK`
- [ ] Batida de saída registra corretamente (par entrada/saída)
- [ ] Dashboard do síndico atualiza em realtime após batida

### 4. Modo offline

- [ ] Desligar WiFi + dados no iPhone
- [ ] Bater ponto offline → toast "salvo offline"
- [ ] Reconectar → fila sincroniza automaticamente
- [ ] Verificar que GPS status foi preservado (não apenas `OFFLINE_PENDENTE`)

### 5. Upload de atestado

- [ ] Toque em "Enviar atestado" abre câmera ou galeria (não só galeria)
- [ ] Upload de JPG/PNG/PDF funciona
- [ ] Arquivo > 10MB exibe erro amigável

### 6. Zoom e acessibilidade

- [ ] Pinch-to-zoom funciona (não está mais bloqueado — BUG-007 corrigido)
- [ ] Interface legível com zoom a 150%
- [ ] Botão de ponto ainda visível com zoom a 200%

---

## Itens específicos do iOS a verificar

| Item | Esperado | Status |
|------|----------|--------|
| `apple-touch-icon` | Logo I em 180×180px | |
| SW cache no Safari | Funciona em iOS 16.4+ | |
| Push notifications | **Não funciona** — comportamento esperado e aceito | |
| Scroll com momentum | Suave (iOS native scroll) | |
| Input focus zoom | Sem zoom automático em inputs (font-size ≥ 16px?) | |

**Nota sobre inputs:** iOS faz zoom automático em `<input>` com `font-size < 16px`. Se algum campo de login ou formulário causar zoom indesejado ao tocar, aumenta o font-size desse input para 16px.

---

## Entrega

Arquivo `_reports/SPRINT5_IOS.md` com:
- Resultado de cada item do checklist (✅ / ❌ / ⚠️)
- Screenshots dos bugs encontrados (se houver)
- Lista de correções aplicadas + commits

Se encontrar bugs: corrige, commita e marca no relatório. Não entrega checklist com ❌ sem correção.

---

## Após o Sprint 5

Quando o PWA estiver validado em iOS, o StaFlow estará **pronto para o primeiro cliente**. O Marcos já está em campo com os prospects.

---

*Cérebro · StaFlow · 26/06/2026*
