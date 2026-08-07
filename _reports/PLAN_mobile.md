# PLAN_mobile.md — Plano App Mobile Fase 2 StaFlow
**Status:** DECIDIDO — aguarda o loop de Produto/Desenvolvimento transformar em tasks
**Data:** 26/06/2026 | **Metodologia:** writing-plans + grill-me
**Decisão registrada em:** 07/08/2026 (revisão com o Breno)

---

## ✅ Decisão do Breno (07/08/2026)

Respostas às 7 perguntas abaixo:

1. **Motivo do app nativo:** nenhum — não há necessidade técnica que o PWA atual não resolva. Não é prioridade ir pra loja de app agora.
2. **Usuários:** funcionários **e síndicos** — diferente do escopo original deste doc (que previa só funcionário). O painel do síndico também precisa de uma experiência mobile melhor, não só responsiva.
3. **Caminho escolhido: Opção C — PWA Melhorado.** Sem app nativo por enquanto. Foco em corrigir bugs e melhorar a experiência do PWA existente (`colaborador.html`) e estender atenção mobile ao painel do síndico.

**Consequência pro escopo original:** a seção "Won't Have no MVP" deste doc listava "Dashboard do síndico (mantém versão web)" — isso muda. O próximo passo do loop de Produto/Desenvolvimento é desenhar o que "PWA melhorado para o síndico" significa na prática (ainda web responsivo, ou um shell mobile dedicado como o do colaborador?).

---

## ⚠️ Este documento precisa de aprovação

Antes de qualquer linha de código, Breno deve responder às perguntas da seção "Requisitos a Confirmar". As respostas determinam a tecnologia, o escopo e o custo do projeto.

---

## Contexto

O StaFlow já tem um PWA funcional em `colaborador.html` com:
- Ponto online e offline (SW + IndexedDB)
- GPS antifraude
- Tarefas e justificativas
- Funciona na home screen como app standalone

A questão é: **por que um app nativo?** O PWA não supre alguma necessidade real, ou é uma demanda de percepção de valor ("síndico quer ver na App Store")?

---

## Requisitos a Confirmar (perguntas do grill-me)

**Breno, responder antes de aprovar:**

1. **Qual problema o PWA atual não resolve?**
   - Há funcionalidade técnica que exige nativo (acesso a NFC, Bluetooth, biometria nativa)?
   - Ou é percepção de valor para o cliente síndico ("meu app na App Store")?

2. **Quem são os usuários do app mobile?**
   - Apenas funcionários (porteiros) — como o PWA atual?
   - Ou síndicos também terão app mobile?

3. **Plataformas:**
   - Apenas Android (90%+ dos porteiros)?
   - iOS também (síndicos e porteiros premium)?
   - Ambos obrigatoriamente?

4. **Tecnologia — qual é a restrição?**
   - Opção A: **React Native** (uma codebase, Android + iOS, ~6 semanas)
   - Opção B: **Capacitor.js** (wrapping do PWA existente em nativo, ~2 semanas, menor retrabalho)
   - Opção C: **Flutter** (Dart, melhor performance, ~8 semanas, nova linguagem)
   - Opção D: **PWA melhorado** (sem app nativo — apenas melhorar o colaborador.html, ~1 semana)
   - Sem preferência técnica, escolha baseada em timeline e custo.

5. **Timeline:**
   - Quando precisa estar na Play Store / App Store?
   - Há evento, divulgação ou cliente específico aguardando?

6. **Orçamento de tempo:**
   - Quantas horas/semana Rafael pode dedicar ao mobile?
   - É o único projeto ou há entregas paralelas?

7. **Backend:**
   - API atual (Supabase) é suficiente, ou o mobile precisa de endpoints novos?
   - Push notifications são obrigatórias no MVP?

---

## Análise de Opções (para informar a decisão)

### Opção A — React Native (Recomendada se iOS é obrigatório)

**Prós:**
- Uma codebase → Android + iOS
- Reutiliza lógica JS/TypeScript da web
- Comunidade enorme, Expo facilita build
- Supabase SDK nativo disponível
- Push via Expo Notifications

**Contras:**
- Reescrever toda a UI em componentes RN (não reutiliza HTML/CSS)
- Bridge nativo pode ter quirks de performance
- Publicação na App Store (iOS) requer conta Apple Developer ($99/ano)
- Tempo: 6–8 semanas para MVP funcional

**MVP estimado:** autenticação + ponto + GPS + offline

### Opção B — Capacitor.js (Recomendada para prazo curto)

**Prós:**
- Wrapping do PWA existente — aproveita todo o HTML/CSS/JS atual
- Android + iOS
- Acesso a APIs nativas via plugins (GPS nativo, biometria)
- Push notifications via Capacitor Push Notifications
- Tempo: **2–3 semanas** para MVP na Play Store

**Contras:**
- Performance levemente inferior ao nativo
- UI não tem "feel" 100% nativo (usa webview)
- Debugging mais complexo

**MVP estimado:** `colaborador.html` como app Capacitor + push + biometria

### Opção C — PWA Melhorado (Recomendada se Play Store não é obrigatório)

**Prós:**
- Zero retrabalho — melhora o que existe
- Funciona hoje na home screen sem app store
- Tempo: **1 semana**
- Corrige os bugs identificados (GPS offline, performance)

**Contras:**
- Não aparece na Play Store / App Store
- iOS tem limitações de PWA (push notifications não funcionam no Safari)
- Percepção de valor menor para alguns clientes

---

## Escopo do MVP (para qualquer opção)

### Must Have (lançamento)
- [ ] Autenticação (login com email + magic link)
- [ ] Bater ponto (entrada, almoço, volta, saída)
- [ ] GPS capturado por batida
- [ ] Modo offline com fila de sincronização
- [ ] Ver histórico do dia atual
- [ ] Logout

### Should Have (sprint 2)
- [ ] Push notification quando síndico atribui tarefa
- [ ] Ver tarefas atribuídas + marcar concluída
- [ ] Enviar justificativa de falta
- [ ] Upload de atestado médico (câmera nativa)

### Won't Have no MVP
- Dashboard do síndico (mantém versão web)
- Gestão de funcionários
- Relatórios
- Checkout/planos
- Configurações do condomínio

---

## Plano de Execução (Opção B — Capacitor, sujeito a aprovação)

### Semana 1 — Setup e base

**Objetivo:** App rodando no emulador Android com autenticação funcional.

```
Dia 1: Setup Capacitor + Android Studio
  - npm init @capacitor/app
  - npx cap add android
  - Configurar capacitor.config.ts apontando para /colaborador

Dia 2: Ajustes de compatibilidade
  - Testar colaborador.html em webview Capacitor
  - Corrigir BUG-004 (route-guard defer) — impacto direto no app
  - Corrigir BUG-007 (maximum-scale) — zoom no webview

Dia 3: GPS nativo
  - Instalar @capacitor/geolocation
  - Substituir navigator.geolocation por Capacitor Geolocation
  - Testar em device real (emulador tem GPS mockado por padrão)

Dia 4: Biometria (nice to have)
  - Instalar @capacitor/biometrics
  - Login com impressão digital (fallback para email)

Dia 5: Build e teste em device real
  - npx cap sync && npx cap open android
  - Testar fluxo completo em celular Android básico
```

### Semana 2 — Offline + Push + Build

```
Dia 1: Offline mode validation
  - Testar fila offline no device real (não no emulador)
  - Verificar comportamento ao matar e reabrir o app

Dia 2: Push Notifications
  - Instalar @capacitor/push-notifications
  - Firebase Cloud Messaging para Android
  - Endpoint no Supabase Edge Function para disparar push

Dia 3: Upload de câmera
  - Instalar @capacitor/camera
  - Substituir input[type=file] pelo camera nativa para atestados
  - Manter fallback para galeria

Dia 4: Build de release
  - Gerar APK de release assinado
  - Testar em 3+ devices reais (Samsung básico, Motorola, Xiaomi)
  - Corrigir quirks de cada fabricante

Dia 5: Play Store
  - Criar conta Google Play Developer ($25 único)
  - Criar listing: screenshots, descrição, categoria
  - Submeter para revisão (3–7 dias úteis)
```

### Semana 3 — Buffer + iOS (opcional)

```
Se iOS obrigatório:
  - npx cap add ios
  - Xcode setup
  - Conta Apple Developer ($99/ano)
  - Testar em iPhone simulator + device real
  - Submeter App Store (revisão 1–3 dias)

Se iOS não obrigatório:
  - Semana de buffer para correções pós-Play Store
  - Início da sprint 2 (push, tarefas, câmera)
```

---

## Dependências e Pré-requisitos

| Requisito | Responsável | Status |
|-----------|-------------|--------|
| Conta Google Play Developer ($25) | Breno | Pendente |
| Conta Apple Developer ($99/ano) — se iOS | Breno | Pendente |
| Android Studio instalado | Rafael | Pendente |
| Device Android real para teste | Rafael/Breno | Pendente |
| Correção BUG-001/002 (GPS offline) | Rafael | Prioridade |
| Firebase project para push | Rafael | Pendente |

---

## Riscos

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Supabase SDK com quirks no webview Capacitor | Média | Alto | Testar auth na semana 1, dia 1 |
| Revisão Play Store rejeitar por falta de screenshots/política de privacidade | Alta | Médio | Ter política de privacidade (já existe) e screenshots prontos |
| GPS nativo diferente entre fabricantes Android | Alta | Médio | Testar em 3 devices antes do lançamento |
| iOS rejeição App Store por política de pagamento (Stripe) | Média | Alto | Não incluir checkout in-app no iOS — deep link para web |
| PWA atual ser suficiente (decisão de fazer app nativo desnecessária) | Média | Baixo | Validar com Breno antes de iniciar |

---

## Decisão Recomendada

**Se o prazo é < 3 semanas:** Opção C (PWA melhorado) — entrega mais valor real por menos esforço. Corrigir os 10 bugs identificados, otimizar performance, e o PWA vira um produto excelente sem a complexidade de app stores.

**Se Play Store é obrigatório e prazo é 3–6 semanas:** Opção B (Capacitor) — menor retrabalho, aproveita o PWA existente.

**Se iOS é obrigatório e prazo é > 6 semanas:** Opção A (React Native com Expo) — produto mais polido a longo prazo.

---

**Próximo passo:** Breno responde as 7 perguntas da seção "Requisitos a Confirmar". Rafael aguarda aprovação antes de iniciar qualquer desenvolvimento.

---

*PLAN_mobile.md — StaFlow · 26/06/2026 · AGUARDA APROVAÇÃO*
