# Pagamentos — o que já está pronto e o que falta

## Resposta curta

**O Stripe já está conectado e em modo LIVE.** Não precisa conectar nada — foi
feito antes. O que você precisa é **verificar** se está tudo de pé e resolver
duas coisas que não são o Stripe.

O que já existe no seu produto, funcionando:

| Peça | Estado |
|---|---|
| Checkout hospedado do Stripe (`create-checkout-session`) | ✅ ativo |
| Webhook do Stripe (`stripe-webhook`) | ✅ ativo |
| Cancelamento de assinatura (`cancel-subscription`) | ✅ ativo |
| Price IDs de produção (Pro, Advanced, Scale — mensal e anual) | ✅ LIVE |
| Assinatura separada por condomínio (multi-CNPJ) | ✅ |
| Limpeza de checkout abandonado | ✅ |

O webhook já trata: `checkout.session.completed`, `checkout.session.expired`,
`customer.subscription.created/updated/deleted`, `invoice.paid` e
`invoice.payment_failed`.

---

## Verificação de 15 minutos (faça antes da primeira venda)

### 1. No painel do Stripe, em modo LIVE (chave "Test mode" desligada)

- [ ] **Developers → Webhooks:** existe um endpoint apontando para
      `https://wsxpskrrzqtdoodpoofx.supabase.co/functions/v1/stripe-webhook`?
- [ ] Esse endpoint tem os 7 eventos acima marcados?
- [ ] Últimas entregas estão verdes (sem falha)?

### 2. Nos secrets do Supabase (Settings → Edge Functions → Secrets)

- [ ] `STRIPE_SECRET_KEY` começa com `sk_live_`
- [ ] `STRIPE_WEBHOOK_SECRET` é o do endpoint **LIVE** (não o de teste)

> Se o `STRIPE_WEBHOOK_SECRET` for o de teste, o pagamento passa mas o
> condomínio **não sobe de plano** — e você só descobre com o cliente
> reclamando. É a falha mais comum e mais silenciosa.

### 3. O único teste que vale de verdade

Compre você mesmo. Sério:

1. Crie um condomínio novo na sua conta
2. Assine o **Pro** com seu cartão real (R$99)
3. Confirme: o condomínio virou Pro no painel? O limite de funcionários subiu?
4. Cancele e peça reembolso no Stripe (Payments → clique → Refund)

R$99 que voltam em alguns dias. É o único jeito de saber que o fluxo inteiro
funciona antes de um cliente descobrir por você.

---

## Os dois problemas que o Stripe não resolve

Aqui é onde eu acho que você tem risco real na venda — e não tem a ver com
estar conectado ou não.

### Problema 1 — Nota fiscal (NFS-e)

Todo SaaS com CNPJ ativo é obrigado a emitir NFS-e para cada receita recebida,
incluindo assinatura mensal e recorrência.

Isso é mais grave do que parece no seu caso específico: **condomínio é uma
entidade que presta contas em assembleia.** O contador do condomínio não
consegue lançar uma despesa sem nota. Você vai fechar a venda, e na hora de
pagar o síndico vai perguntar "e a nota fiscal?" — e se não tiver, a compra
trava ali.

**O Stripe não emite NFS-e.** Isso é obrigação sua, na prefeitura da sua cidade.

Caminhos:
- **Hoje, manual:** emitir pelo portal da sua prefeitura a cada pagamento. Dá
  conta tranquilamente dos 10 primeiros clientes.
- **Depois, automático:** serviços como NFE.io ou Spedy se conectam por webhook
  ao Stripe e emitem sozinhos a cada cobrança paga.

**Ação de hoje:** confirme que seu CNPJ tem inscrição municipal e acesso ao
emissor de NFS-e da prefeitura. Se não tiver, resolva isso antes de cobrar o
primeiro cliente — não depois.

### Problema 2 — Condomínio muitas vezes não paga no cartão

O comprador B2B brasileiro ainda paga muita coisa por boleto, principalmente
empresas com processo de contas a pagar rígido — e SaaS que só aceita cartão
perde contrato de empresa que não paga assinatura no cartão corporativo.

Condomínio é exatamente esse perfil: dinheiro do condomínio, conta do
condomínio, prestação de contas em assembleia. Muito síndico **não vai passar
no cartão dele** uma despesa que é do prédio.

**Sobre Pix no Stripe:** o Stripe aceita Pix, mas para empresas sediadas no
Brasil ele está disponível apenas por convite. Ou seja: pode não estar liberado
pra você agora. Vale checar no seu painel.

---

## Devo trocar de plataforma? Minha recomendação: não hoje.

**Não migre nada hoje.** Você está LIVE, funcionando, e quer vender hoje.
Trocar de plataforma de pagamento é projeto de dias, não de horas — e o risco
de quebrar o que funciona é alto.

O plano que eu faria:

**Hoje até os 5 primeiros clientes:**
- Vende com o Stripe no cartão, que já funciona
- Se o cliente disser "só posso boleto": faz manual. Você emite um boleto ou
  cobra por Pix direto, emite a nota, e libera o plano na mão no banco. Feio,
  mas fecha a venda — e nos primeiros clientes fechar vale mais que automatizar.
- **Anote quantos pediram boleto.** Esse número decide o próximo passo.

**Depois dos 5 primeiros:**

Se **a maioria pediu boleto/Pix**, aí vale integrar uma plataforma brasileira:

| Plataforma | Quando faz sentido |
|---|---|
| **Asaas** | O mais direto pra pequena empresa: boleto, Pix e cartão recorrente com cobrança e régua de inadimplência nativas. Seria minha escolha se boleto virar essencial. |
| **Vindi** | Mais robusto em gestão de assinatura, integra com vários gateways. Faz sentido com volume maior. |
| **Iugu** | Concorrente direto do Asaas, perfil parecido. |

Se **quase todos pagaram no cartão sem reclamar**, fica no Stripe e só resolve a
nota fiscal automática. Menos peça, menos coisa pra quebrar.

> Repare que a decisão depende de um dado que você ainda não tem. Por isso não
> dá pra decidir hoje sem chutar — e trocar de plataforma por chute é o tipo de
> retrabalho que custa uma semana.

---

## Resumo do que fazer agora

1. Verificar o webhook LIVE e os secrets (15 min)
2. Comprar seu próprio Pro e reembolsar (10 min)
3. Confirmar que consegue emitir NFS-e pela prefeitura (30 min)
4. Sair pra vender — com uma resposta pronta pra "aceita boleto?":
   *"Aceito. Hoje faço a cobrança direto por boleto ou Pix e emito a nota
   normalmente — me passa o CNPJ do condomínio que eu já preparo."*

Sources:
- [Receba pagamentos por Pix | Stripe](https://stripe.com/br/payment-method/pix)
- [Pagamento de SaaS no Brasil: Pix, boleto e cartão no B2B](https://blog.b2bstack.com.br/pagamento-de-saas-no-brasil-pix-boleto-cartao/)
- [Nota Fiscal Automática para SaaS | Spedy](https://lp.spedy.com.br/saas)
- [Preços e taxas Asaas](https://www.asaas.com/precos-e-taxas)
- [SaaS B2B no Brasil: compliance, cobrança e vendas | Logik Digital](https://logikdigital.com.br/blog/saas-b2b-brasil-compliance-cobranca)
