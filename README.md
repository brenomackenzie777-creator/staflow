# StaFlow

SaaS de gestão de funcionários para condomínios brasileiros — ponto digital, tarefas e faltas em tempo real.

🌐 **Produção:** https://staflow.vercel.app

## Stack

- **Frontend:** HTML / CSS / Vanilla JS (sem build)
- **Auth + DB:** Supabase (Postgres + RLS + Auth)
- **Hosting:** Vercel (CDN global, HTTPS automático)
- **Fontes:** Syne (display) + DM Sans (body) + DM Mono (mono) — Google Fonts

## Estrutura

```
.
├── staflow-landing.html      # Landing page pública
├── dashboard.html            # Painel principal (protegido)
├── funcionarios.html         # CRUD de funcionários
├── configuracoes.html        # Perfil + condomínio
├── auth/                     # Login, cadastro, reset de senha
├── js/                       # Cliente Supabase, auth e app-shell
├── assets/                   # Logos SVG
├── sql/                      # Migrações Postgres (apply em ordem)
├── app.css                   # Design system do app (sidebar, tabela, modal)
└── vercel.json               # Config de roteamento + security headers
```

## Rodar local

```bash
npx serve .
# Acesse: http://localhost:3000
```

## Deploy

Auto-deploy via Vercel conectado a este repo. Push em `main` publica automaticamente.

## Migrações

As migrações em `sql/` devem ser executadas em ordem no Supabase SQL Editor (ou via MCP).

---

© 2026 StaFlow Tecnologia — v1.0
