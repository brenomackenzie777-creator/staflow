# StaFlow — Memória Compartilhada dos Agentes
<!-- Este arquivo é lido por todos os agentes antes de agir.
     É atualizado automaticamente após cada execução.
     Não editar manualmente — deixe os agentes gerenciarem. -->

## Contexto do Produto
- **Produto:** StaFlow — controle de presença para condomínios
- **URL produção:** https://staflow.app.br
- **Stack:** HTML/CSS/JS estático + Supabase + Stripe LIVE + Vercel
- **Status:** Em produção com usuários reais
- **Mercado e concorrência:** ver `mercado-concorrencia.md` (pesquisa breve de
  07/08/2026 — 327 mil condomínios ativos no Brasil, dois tipos de concorrente:
  ERPs condominiais completos como Superlógica/TownSq/MyCond, e SaaS de ponto
  genérico como Ahgora/Tangerino/Pontotel. StaFlow é nicho: ponto feito
  especificamente pra condomínio, preço mais simples e direto). Os agentes de
  marketing e financeiro têm a ferramenta `read_market_context` pra ler isso.

## Planos e Preços (DEFINITIVOS — não alterar)
| Plano     | Mensal    | Funcionários |
|-----------|-----------|--------------|
| Starter   | R$ 0      | até 3        |
| Pro       | R$ 99/mês | até 15       |
| Advanced  | R$ 159/mês| até 35       |
| Scale     | R$ 279/mês| até 100      |

## Identidade Visual
- Logo: variante I — dois blocos azuis geométricos em S
- Cor primária: #3B82F6 (azul)
- Fundo principal: #111827
- Superfícies: #1F2937
- Texto: #F9FAFB
- Fonte: Inter

## ★ Ciclo CEO — o único loop automático (Railway, todo dia 08:00 BRT)

**Ordem do Breno em 10/08/2026:** um loop só, para a operação inteira,
funcionando como CEO da empresa. Os 4 loops por área saíram do automático.

**A conta que explica por que nada funcionava até aqui:** cada loop de 8
agentes custava ~26 mil tokens. Quatro por dia = 105 mil, contra uma cota
diária de 100 mil do Groq no plano gratuito. **Nunca coube — era impossível
desde o primeiro dia**, e ninguém tinha feito essa conta antes de agendar.

O ciclo CEO tem **4 agentes** e custa ~13 mil tokens (≈13% da cota),
deixando folga de verdade para retry, erro e execução manual.

| Etapa | Papel | O que faz |
|-------|-------|-----------|
| 1 | **Analista-Chefe** | Lê `panorama_negocio` + memória. Diz onde a empresa está hoje, com número real. |
| 2 | **CEO (Estrategista)** | Escolhe **UMA** prioridade para o dia e justifica com dado. Recado do Breno vira prioridade automaticamente. |
| 3 | **Executor** | Entrega o trabalho pronto, responde os recados, registra o ciclo e atualiza a memória. |
| 4 | **Relator** | Escreve o e-mail do dia para o Breno, em português de gente. |

Prompts em `scripts/crew/prompts/ceo.json`. Ferramenta principal:
`panorama_negocio` (em `tools.py`) — retrato do funil inteiro, que
**separa dado de teste de dado real** (contas `@staflow.test`, `+teste` e
condomínio órfão são descartadas; só conta como receita quem tem assinatura
confirmada no Stripe).

Os 4 loops antigos por área continuam no código e podem ser rodados na mão:
`LOOP=marketing python -m scripts.crew.main`. Não rodam mais sozinhos.

---

### Histórico dos 4 loops por área (arquivado)
Mantido porque explica decisões e bugs antigos.

Rodava quantos loops de negócio coubessem no dia, até usar **70% da cota
diária do Groq** (a fração passou por 50% → 90% → 70% no mesmo dia).

**Bug encontrado e corrigido em 08/08/2026 (log real analisado pelo Claude):**
a causa real era MAIOR do que o agendamento duplicado do GitHub Actions
(que também foi desligado — ver abaixo). O Breno tinha **DOIS projetos
Railway diferentes conectados ao mesmo repositório GitHub** (um chamado
"adequate-dream", outro "terrific-celebration"), os dois com cron nas
11:00 UTC e os dois rodando o loop inteiro a cada `git push` — ou seja,
todo commit do dia disparava o time de agentes DUAS VEZES em paralelo,
os dois gastando da mesma chave/cota do Groq sem se enxergar. Foi assim
que a cota de 100.000 tokens/dia sumia mesmo com o orçamento interno
ainda achando que tinha gasto 0%. Resolvido pelo Breno: projeto
"adequate-dream" **excluído**, "terrific-celebration" **renomeado para
"staflow"** — esse é o único projeto Railway que resta rodando o time.
Também foi desligado o agendamento automático do GitHub Actions (ver
`.github/workflows/agentes.yml`); **Railway (projeto "staflow") é agora
o único agendador**. O workflow do GitHub continua disponível pra rodar
manualmente (Actions → Run workflow) se o Railway cair.

A ordem das 4 áreas gira dia a dia (dia do ano % 4) pra nenhuma ficar
sempre por último quando o orçamento aperta.

| Loop | Foco |
|------|------|
| Marketing / Crescimento | Aquisição, conversão, campanhas, copy |
| Produto / Desenvolvimento | Bugs, UX, funcionalidades, qualidade técnica |
| Financeiro / Assinaturas | Churn, conversão entre planos, receita |
| Suporte / Sucesso do Cliente | Feedbacks, onboarding, atendimento |

Toda sexta-feira, se ainda sobrar orçamento depois da rotação do dia, roda
também o **Meta-Agente Evolutivo**, que avalia a semana inteira nos 4 loops.

Cada loop tem os mesmos 8 papéis (Coletor → Pesquisador → Analista →
Estrategista → Decisor → Executor → Observador → **Relator**), mas com prompts
próprios em `scripts/crew/prompts/<loop>.json`. O Meta-Agente é compartilhado
entre todos os loops (`scripts/crew/prompts/meta.json`) e lê o histórico de
aprovações/rejeições de qualquer loop antes de propor uma mudança de prompt.

Lógica de orçamento: `scripts/crew/main.py`. Ajustável por variável de
ambiente no Railway: `FRACAO_ORCAMENTO_DIARIO` (padrão 0.7) e
`COTA_DIARIA_TOKENS` (padrão 100000).

**O Relator** é o último agente de cada ciclo e o único que fala com o Breno.
Ele traduz tudo para português leigo (o Breno é CEO, não programador) e envia
por email via Resend. Na sexta-feira há um Relator Semanal que fecha a semana
consolidando os 4 loops. Termos técnicos são proibidos nos relatórios.

Configuração de cada loop (foco e queries de pesquisa) fica em
`scripts/crew/loops.json`. Execuções ficam marcadas no Supabase
(`agent_runs.loop_name`) para não misturar histórico entre áreas.

## Canal único com o Breno ("Time de IA")
**Criado em 08/08/2026, a pedido do Breno:** ele quer o time como uma
empresa — trabalha sozinho, mas ele pode comentar/pedir a qualquer
momento por UM canal só, em vez de precisar saber qual dos 4 loops (ou
qual dos 3 agentes antigos Camila/Marcos/Rafael) procurar.

Mecanismo (não é chat ao vivo — os loops só rodam 1x/dia):
1. Página `/agentes.html` ("Time de IA" no menu) **ou o Telegram** (ver
   seção seguinte) — o Breno escreve um recado (texto livre + área
   opcional) que grava em `public.time_recados` (status inicial
   `pendente`). As duas portas caem na mesma tabela — é o mesmo canal.
2. O **Analista** do ciclo CEO lê os recados pendentes no início (vêm
   dentro de `panorama_negocio`) e lista cada um COM O ID.
3. O **CEO** trata recado do Breno como PRIORIDADE AUTOMÁTICA do dia —
   acima de qualquer coisa que o time escolheria sozinho.
4. O **Executor** responde cada recado (`responder_recado_breno`):
   `atendido` (com o que foi feito) ou `nao_prioridade` (com o motivo).
   Nunca fica sem resposta. Isso também dispara mensagem no Telegram.
5. O Breno vê a resposta na página `/agentes.html`, no histórico, e
   também recebe no Telegram na hora que o Executor responde.

Para pedidos que precisam de resposta NA HORA (não no próximo ciclo de
até 24h), o canal continua sendo esta conversa com o Claude/Cowork.

## ★ Canal Telegram (18/08/2026, a pedido do Breno)

Ele pediu pra conversar com o time em vez de só deixar recado numa
página e esperar. Sem VPS nem servidor sempre ligado (ainda não faz
sentido pro estágio da empresa — ver decisão abaixo), a solução ficou
toda na infra que já existe:

- **Bot do Telegram** (`@BotFather`) → webhook aponta pra uma Edge
  Function nova, `supabase/functions/telegram-webhook/`.
- O Breno manda mensagem no Telegram a qualquer hora → a function grava
  em `time_recados` (autor_id = o dele, via secret `BRENO_USER_ID`) e
  responde na hora "recebido, trato no próximo ciclo".
- Segurança: a function só aceita mensagem de `TELEGRAM_CHAT_ID` — vem
  de outro chat, ignora silenciosamente. O bot não vira caixa pública.
- Quando o Executor do ciclo do dia seguinte responde o recado
  (`responder_recado_breno`), a resposta de verdade chega no Telegram
  também — não só na página. O Relator também manda um aviso curto no
  Telegram quando o email do dia sai ("📬 relatório no seu email").

Secrets necessários (Supabase Edge Functions **e** Railway, são dois
lugares diferentes que precisam do mesmo token):
`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, e só na Edge Function
`BRENO_USER_ID` (`41c002e3-c256-43c1-9e31-a938fc31e15a`).

**Decisão consciente de não ir mais longe agora:** dá pra ter servidor
sempre ligado, múltiplos provedores de LLM, VPS — isso existe em
referências de mercado que o Breno trouxe (ver conversa de 18/08). Não
foi escolhido pré-receita: custo e manutenção que não se pagam ainda
com a empresa nesse estágio. Isso é revisitável depois que houver
receita de verdade sustentando.

## ★ Autoevolução (ligada em 12/08/2026, a pedido do Breno)

O time **se ajusta sozinho**, sem depender de aprovação. Os prompts vivem
na tabela `public.agent_prompts` (não mais só no arquivo `ceo.json`) —
porque o container do Railway é descartável: reescrever arquivo não
persistiria, e fazer commit pra persistir dispararia um novo deploy, que
dispararia outro ciclo, num loop infinito queimando a cota.

No fim de cada ciclo o **Executor** avalia o próprio time. Se identificar
um padrão de falha que já apareceu mais de uma vez, chama `evoluir_prompt`
e reescreve o `goal` ou o `backstory` do agente responsável. Vale a partir
do ciclo seguinte.

**Travas (não são burocracia — são o que separa evoluir de oscilar):**
- Só `goal` e `backstory`. O `role` é a identidade do agente e não muda.
- Máximo **1 mudança por agente a cada 7 dias**.
- Motivo obrigatório, com o padrão observado.
- Toda versão anterior fica guardada — dá pra reverter a qualquer momento.

**Como o Breno reverte:** na tabela `agent_prompts`, marcar `ativo=false`
na versão nova e `ativo=true` na anterior. Ou pedir ao Claude.

## Regras de Ouro (todos os agentes devem seguir)
1. Nunca inventar dados ou métricas — sempre ler do Supabase
2. Preços são os da tabela acima — nunca outros valores
3. Output sempre em Markdown estruturado
4. Primeira linha do output = resumo de 1 linha (vai para o log)
5. Se houver dúvida, registrar no output e sinalizar para o Breno
6. **O time evolui a si mesmo, mas não toca no produto.** O que os agentes
   podem mudar sozinhos: os próprios prompts, a memória, o conteúdo que
   produzem. O que continua exigindo o Breno, sem exceção:
   - código do site, banco de dados, login, Stripe
   - qualquer coisa que apague dado (**registro de ponto é documento de
     valor legal do condomínio** — corromper isso é passivo jurídico do
     cliente, não bug)
   - preços
   - mandar mensagem em nome da empresa para cliente
   - gastar dinheiro

## Últimas Execuções
<!-- Preenchido automaticamente pelos agentes -->
**09/08/2026 — primeiro ciclo que completou de verdade.** Loop `produto`
rodou inteiro em 6min19s (11:04–11:11 UTC). Nos dias anteriores nenhum
ciclo chegou ao fim: todos morriam de cota esgotada no meio.

Três problemas encontrados analisando esse log e corrigidos no mesmo dia:

1. **Contador de tokens inflado ~24x.** O `crew.usage_metrics` do CrewAI
   reportou 631.320 tokens para um ciclo que, somando as chamadas reais
   do log, gastou 26.336. Com isso o orçamento "estourava" (902%) logo
   no primeiro loop e os outros três eram pulados todo dia. Agora a
   medição vem de um callback do litellm (`scripts/crew/uso.py`), com o
   teto físico por tempo (12 mil tokens/min do Groq) como segunda rede.
2. **Orçamento diário zerava a cada execução.** O Railway sobe container
   novo a cada cron E a cada deploy — no dia 09/08 rodou às 11:04, 15:05
   e 00:00, cada execução se achando a primeira e liberando os 70 mil
   tokens de novo. Agora o gasto fica em `public.agent_budget_diario`,
   compartilhado entre execuções.
3. **Nada era registrado no banco.** A tabela `agent_runs` não tinha a
   coluna `loop_name` que o código usa, então toda gravação falhava em
   silêncio — e o registro ainda dependia do Executor lembrar de chamar
   a ferramenta. Coluna criada e o próprio orquestrador agora grava cada
   ciclo (`_registrar_execucao`), dando certo ou não.

Em aberto: o Breno ainda não recebeu nenhum relatório por email. O
`NotifyTool` agora loga sucesso/falha do envio no Railway pra descobrir
se é o Resend recusando o remetente, spam, ou o Relator nem chamando a
ferramenta.

**09/08/2026, mesmo dia — bug novo na correção nº 2 (orçamento no banco).**
Um log mostrou `ler_gasto_do_dia`/`salvar_gasto_do_dia`/`_registrar_execucao`
falhando com "Invalid URL" ao tentar falar com o Supabase, bem na hora de
um loop bater na cota diária esgotada. Não deu pra confirmar a causa raiz
ainda (a mensagem de erro vinha curta demais). O sistema não quebrou por
causa disso — a estimativa de segurança (30.000 tokens) segurou o freio de
orçamento mesmo sem conseguir salvar no banco — mas o valor não fica
persistido pra próxima execução aproveitar. Log foi enriquecido (tipo do
erro + diagnóstico da URL/chave configurada) pra próxima falha apontar a
causa exata.

**18/08/2026 — conferência de 4 dias de ciclo real (13 a 16/08) + bug de dado sério encontrado.**
Ciclo rodou de ponta a ponta em 13, 14, 15 e 16/08 (registro completo no
`agent_runs`, com o orquestrador confirmando sucesso nos três últimos). A
autoevolução JÁ disparou de verdade uma vez: no dia 13, logo após entregar
a "chapa" pedida pelo Breno, o time reescreveu o próprio prompt do
Executor (`agent_prompts`, versão 2, motivo registrado). Recado da
"chapa" foi lido e respondido nesse mesmo ciclo.

Dois problemas achados nessa conferência:

1. **17 e 18/08: gasto de token sem nenhum registro.** `agent_budget_diario`
   mostra 12.200 tokens gastos nos dois dias, mas `agent_runs` não tem
   nenhuma linha nesse intervalo — nem sucesso, nem a falha de segurança
   do orquestrador. Falha silenciosa nova, causa ainda não identificada
   (precisa do log do Railway desses dois dias).
2. **MRR e "cliente pagante" estavam errados.** O `panorama_negocio`
   reportou "1 condomínio pagando, R$99 MRR" — mas esse condomínio
   ("Ed. Teste StaFlow") é um teste do próprio Breno, cadastrado com o
   e-mail dele mesmo, que tinha assinatura Stripe de verdade e passava
   batido pelo filtro de teste (que só olhava padrão de e-mail tipo
   `+teste`/`@staflow.test`). Número real de cliente pagante era ZERO.
   Corrigido em `tools.py`: `eh_teste()` agora também exclui o e-mail do
   fundador (`NOTIFY_EMAIL`) e qualquer condomínio com "teste"/"demo" no
   nome. Lição: filtro de teste por padrão de e-mail sozinho não basta.

Também notado (não é bug, é ponto de atenção): 3 dos 4 ciclos bateram na
mesma prioridade — reativar condomínios cadastrados que nunca usaram o
produto — sem entregar mais que a recomendação em texto. Faz sentido,
já que o time não pode mandar mensagem pro cliente sem autorização do
Breno (Regra de Ouro), mas vale olhar se travou aí ou se está evoluindo
o texto a cada dia.

## ★ Gateway de pagamento Asaas (18/08/2026, em construção)

A pedido do Breno, rodando em **paralelo à Stripe** (que continua ativa,
nada foi desligado). Motivo: Asaas resolve Pix nativo e boleto que a
Stripe não resolve bem no Brasil — ver `vendas/pagamentos-checklist.md`.

**Detalhe importante:** a conta Asaas do Breno é **pessoa física**
(ele desativou o MEI) — por isso **não emite nota fiscal automática**.
Isso é uma limitação aceita por enquanto, não um bug a corrigir.

O que existe:
- `supabase/functions/create-asaas-checkout/` — cria um Checkout Asaas
  (Pix + cartão, assinatura mensal recorrente) e devolve o link.
  Detecta sandbox x produção sozinho pelo prefixo da API Key
  (`$aact_hmlg_` = sandbox, `$aact_prod_` = produção).
- `supabase/functions/asaas-webhook/` — recebe eventos de assinatura e
  pagamento, atualiza `status_assinatura`/`plano`/`plano_ativo`/
  `asaas_subscription_id`/`asaas_customer_id` no condomínio. Identifica
  o condomínio pelo `externalReference` (`condominioId:plano`).
- `condominios.asaas_customer_id` / `asaas_subscription_id` — colunas
  novas, paralelas às `stripe_*`.
- `planos.html` — cada plano pago (Pro/Advanced/Scale) ganhou um link
  "ou pagar com Pix" abaixo do botão principal (Stripe continua sendo
  o botão principal). Só aparece pra condomínio já existente e plano
  mensal — cadastro de condomínio novo e plano anual ainda só na
  Stripe (não implementado no Asaas ainda).

**18/08/2026, mesmo dia — Pix escondido antes da campanha de vendas.**
Breno ia mandar e-mail de venda pros leads e perguntou se estava tudo
pronto. Sinalizei que a chave `ASAAS_API_KEY` ativa ainda é a de
**sandbox** — se um lead real clicasse em "ou pagar com Pix", cairia
num ambiente de teste que não processa pagamento de verdade. Ele
escolheu esconder o botão até trocar pra chave de produção (o cartão
via Stripe continua funcionando normal, não foi afetado). Escondido
via CSS em `planos.html` (`.pagar-pix-link { display:none }`, com
comentário explicando como reativar). **Pendente pro Breno**: gerar a
chave de API de produção na Asaas (`$aact_prod_...`, precisa de SMS,
mesmo processo da sandbox) + criar o Webhook de produção no painel
Asaas (separado do de sandbox) apontando pra
`asaas-webhook` com um token novo. Quando tiver os dois, troco os
secrets `ASAAS_API_KEY`/`ASAAS_WEBHOOK_TOKEN` e reativo o botão.

**Pendente pro Breno (fora do alcance do Claude):**
1. Secret `ASAAS_API_KEY` no Supabase (Edge Functions → Secrets) —
   valor da chave sandbox já gerada. ✅ feito em 18/08.
2. Criar o Webhook no painel Asaas (Integrações → Webhooks) apontando
   pra `https://wsxpskrrzqtdoodpoofx.supabase.co/functions/v1/asaas-webhook`,
   escolhendo um token de autenticação e cadastrando esse MESMO valor
   como secret `ASAAS_WEBHOOK_TOKEN` no Supabase. ✅ feito em 18/08.
3. Testar uma assinatura de teste no sandbox de ponta a ponta antes de
   trocar pra chave de produção. ⚠️ parcialmente feito — ver abaixo.

**18/08/2026, mesmo dia — teste ao vivo do botão "ou pagar com Pix"
achou e corrigiu 2 bugs reais antes de qualquer cliente usar:**

1. **CORS bloqueava a chamada de verdade.** `js/supabase-client.js`
   manda um header custom `x-condominio-id` em toda chamada de
   function (usado pro contexto multi-CNPJ). `create-checkout-session`
   (Stripe) já liberava esse header; `create-asaas-checkout` não. O
   navegador aceitava o preflight OPTIONS (200) mas recusava mandar o
   POST de verdade — aparecia só como "Failed to send a request to the
   Edge Function" no toast, sem chegar no log da function nem no painel
   do Supabase. Achado testando fetch direto no console do navegador
   (via Claude in Chrome), comparando com o `x-condominio-id` já
   liberado em `create-checkout-session`. Corrigido.
2. **A Asaas recusa Pix recorrente misturado com cartão.** A primeira
   versão usava o endpoint `/v3/checkouts` com
   `billingTypes:["PIX","CREDIT_CARD"]` + `chargeTypes:["RECURRENT"]`.
   A Asaas retornava 502: "PIX exige tipo de cobrança DETACHED" / "só
   CREDIT_CARD pode ser RECURRENT". Corrigido trocando pro endpoint de
   Assinatura direto (`/v3/subscriptions`), que aceita
   `billingType:"PIX"` recorrente nativamente. O botão "ou pagar com
   Pix" agora cria cliente Asaas (por `externalReference` =
   condominio_id) + assinatura mensal Pix + devolve o link da primeira
   fatura (QR code/copia-e-cola).

**Achado no mesmo teste:** a Asaas exige CPF/CNPJ do pagador pra
cadastrar o cliente. A function agora recusa com mensagem clara
("Cadastre o CNPJ... antes de pagar com Pix") em vez do erro genérico —
isso significa que **nenhum condomínio sem CNPJ cadastrado consegue
pagar via Pix**. Fluxo por cartão (Stripe) não é afetado.

**Caminho feliz confirmado no mesmo dia, com autorização do Breno:**
CNPJ de teste (válido, dígito verificador correto) colocado
temporariamente no condomínio "sola" só pra fechar o teste — revertido
pra `null` logo depois. Resultado: `create-asaas-checkout` criou
cliente na Asaas, criou a assinatura mensal Pix, devolveu o link da
fatura (`sandbox.asaas.com/i/...`), e o `asaas-webhook` gravou sozinho
`asaas_subscription_id`, `asaas_customer_id`, `plano` e `plano_ativo`
no condomínio via `SUBSCRIPTION_CREATED` — sem eu precisar tocar no
banco de novo. `status_assinatura` ficou `inactive` (correto: a
cobrança Pix ainda não foi paga). Fluxo ponta a ponta validado — falta
só alguém efetivamente pagar o Pix no sandbox pra confirmar que
`PAYMENT_CONFIRMED` também vira `status_assinatura='active'` (mesma
lógica já usada pelo webhook da Stripe, não é código novo).

---
*Última atualização: 18/08/2026*
