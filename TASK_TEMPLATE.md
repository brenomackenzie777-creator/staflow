# Task — [TÍTULO CURTO E CLARO]
<!-- Template padrão StaFlow. Claude Code lê este arquivo e executa.
     Copie, preencha e salve como TASK_YYYY-MM-DD_slug.md em /tasks/ -->

## Meta
<!-- O que precisa estar funcionando ao final. Uma frase. -->
> Ex: O botão "Exportar CSV" na página /ponto deve gerar um arquivo válido

## Contexto
<!-- Por que essa task existe? De onde veio? (feedback de usuário, bug, feature request) -->
- Origem: [ ] Bug reportado  [ ] Feedback de usuário  [ ] Decisão interna
- Urgência: [ ] Crítico (produção quebrada)  [ ] Alta  [ ] Normal  [ ] Baixa
- Página(s) afetada(s): `________`
- Arquivo(s) envolvido(s): `________`

## Critérios de aceitação
<!-- O que "pronto" significa. Claude Code usa para validar. -->
- [ ] 
- [ ]
- [ ]

## Comportamento esperado
```
// Descreva aqui o que deve acontecer step-by-step
// Ex:
// 1. Usuário clica em "Exportar CSV"
// 2. Arquivo baixa com nome ponto_YYYY-MM.csv
// 3. Colunas: nome, data, entrada, saída, total_horas
```

## Comportamento atual (se bug)
```
// O que está acontecendo de errado agora
```

## Restrições técnicas
- Stack: HTML/CSS/JS estático (sem frameworks)
- Auth: Supabase (`window.staflowSupabase`)
- Design: seguir `staflow-design-system.md`
- Não quebrar funcionalidades existentes
- Testar offline (service worker ativo)

## Testes mínimos
<!-- Rafael vai rodar isso depois do deploy -->
- [ ] Funciona no Chrome desktop
- [ ] Funciona no Safari iOS (se página mobile)
- [ ] Funciona offline (se usa dados do Supabase com queue)
- [ ] Não há erros no console

## Estimativa
- Complexidade: [ ] Simples (<30min)  [ ] Médio (2h)  [ ] Complexo (>1 dia)

---
*Criada em: YYYY-MM-DD | Por: [humano/agente]*
