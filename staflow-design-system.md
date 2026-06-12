# StaFlow — Design System Enterprise v2.0

> Identidade visual aprovada em Jun 2026. Baseada na direção enterprise B2B.  
> Referência visual: dashboard aprovado no Figma → https://www.figma.com/design/bZzjk2gn2JD5pjNO1XN7an

---

## 1. Paleta de Cores

### Cores base (backgrounds)

| Token            | Hex       | Uso                                          |
|------------------|-----------|----------------------------------------------|
| `--color-bg`     | `#111827` | Background principal de todas as páginas     |
| `--color-surface`| `#1F2937` | Cards, sidebar, modais, painéis              |
| `--color-surface-2`| `#374151`| Bordas, divisores, header de tabelas        |
| `--color-surface-hover`| `#243040`| Hover state de rows e items de lista   |

### Cores de texto

| Token               | Hex       | Uso                                      |
|---------------------|-----------|------------------------------------------|
| `--color-text`      | `#F9FAFB` | Texto principal                          |
| `--color-text-muted`| `#9CA3AF` | Texto secundário, labels, subtítulos     |
| `--color-text-faint`| `#6B7280` | Placeholders, texto desativado, captions |

### Cores de acento

| Token              | Hex       | Uso                                              |
|--------------------|-----------|--------------------------------------------------|
| `--color-blue`     | `#3B82F6` | CTA principal, links, active state, progress     |
| `--color-blue-dark`| `#1D4ED8` | Hover de botão primário                          |
| `--color-blue-dim` | `rgba(59,130,246,0.12)` | Background de badge/active nav  |
| `--color-green`    | `#10B981` | Sucesso, status Presente, trend positivo         |
| `--color-red`      | `#EF4444` | Erro, status Ausente, trend negativo             |
| `--color-amber`    | `#F59E0B` | Aviso, status Férias, atenção                    |
| `--color-purple`   | `#8B5CF6` | Variação de avatar, feature destaque             |

### Bordas

| Token              | Valor                    | Uso                           |
|--------------------|--------------------------|-------------------------------|
| `--color-border`   | `rgba(55,65,81,1)`       | Bordas de cards e inputs      |
| `--color-border-subtle` | `rgba(55,65,81,0.5)` | Divisores de tabela, rows    |

---

## 2. Tipografia

### Família

```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
```

Importar via Google Fonts:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
```

### Escala tipográfica

| Token          | Size  | Weight | Line-height | Letter-spacing | Uso                        |
|----------------|-------|--------|-------------|----------------|----------------------------|
| `--text-hero`  | 52px  | 800    | 1.1         | -1.5px         | H1 da landing page         |
| `--text-h1`    | 36px  | 700    | 1.15        | -0.8px         | Títulos de seção           |
| `--text-h2`    | 28px  | 700    | 1.2         | -0.5px         | Subtítulos de seção        |
| `--text-h3`    | 20px  | 600    | 1.3         | -0.3px         | Títulos de card/painel     |
| `--text-h4`    | 16px  | 600    | 1.4         | -0.2px         | Labels de seção            |
| `--text-body`  | 15px  | 400    | 1.6         | 0              | Corpo de texto padrão      |
| `--text-small` | 13px  | 400    | 1.5         | 0              | Texto secundário           |
| `--text-xs`    | 11px  | 500    | 1.4         | 0.8px          | Labels uppercase, badges   |
| `--text-mono`  | 13px  | 500    | 1.4         | 0              | Dados numéricos, códigos   |

**Regra:** Labels de categorias/colunas sempre `uppercase` + `letter-spacing: 1.2px` + peso 500.

---

## 3. Espaçamento e Grid

### Escala base (múltiplos de 4px)

```
4 · 8 · 12 · 16 · 20 · 24 · 32 · 40 · 48 · 64 · 80 · 96 · 128
```

### Aplicação

| Contexto                     | Valor    |
|------------------------------|----------|
| Padding interno de card      | 20–24px  |
| Gap entre cards              | 16px     |
| Padding lateral de seção     | 28–32px  |
| Gap entre seções (vertical)  | 48–80px  |
| Padding de botão (h / v)     | 14px / 10px |
| Padding de input (h / v)     | 14px / 10px |
| Altura de row de tabela      | 42–48px  |
| Altura de top bar            | 64px     |
| Largura de sidebar           | 220px    |

### Layout desktop (dashboard)

```
Sidebar: 220px fixo (esquerda)
Conteúdo: calc(100% - 220px)
Content padding: 28px
Max-width conteúdo: 1440px
```

### Layout landing page

```
Max-width: 1200px
Padding horizontal: clamp(24px, 5vw, 80px)
Seções: padding vertical 80–120px
```

---

## 4. Border Radius

| Token          | Valor | Uso                                    |
|----------------|-------|----------------------------------------|
| `--radius-sm`  | 4px   | Badges, pequenos elementos             |
| `--radius-md`  | 6px   | Inputs, botões, nav items              |
| `--radius-lg`  | 8px   | Cards, painéis, tabelas                |
| `--radius-xl`  | 12px  | Modais, dropdowns grandes              |
| `--radius-2xl` | 16px  | Seções de destaque, hero cards         |
| `--radius-full`| 9999px| Avatars, chips de status              |

---

## 5. Sombras

```css
--shadow-sm:  0 1px 3px rgba(0,0,0,0.3);
--shadow-md:  0 4px 12px rgba(0,0,0,0.4);
--shadow-lg:  0 8px 32px rgba(0,0,0,0.5);
--shadow-blue: 0 4px 20px rgba(59,130,246,0.25);
--shadow-glow: 0 0 40px rgba(59,130,246,0.12);
```

---

## 6. Componentes

### 6.1 Botões

#### Botão Primário (CTA)
```css
background: #3B82F6;
color: #F9FAFB;
font-size: 15px;
font-weight: 600;
padding: 10px 20px;
border-radius: 6px;
border: none;
cursor: pointer;
transition: background 0.15s, transform 0.1s;
box-shadow: 0 4px 14px rgba(59,130,246,0.3);

/* Hover */
background: #1D4ED8;
transform: translateY(-1px);
box-shadow: 0 6px 20px rgba(59,130,246,0.4);

/* Tamanhos */
/* SM */  padding: 7px 14px; font-size: 13px;
/* MD */  padding: 10px 20px; font-size: 14px;   /* padrão */
/* LG */  padding: 13px 28px; font-size: 15px;
/* XL */  padding: 16px 36px; font-size: 16px;   /* hero CTA */
```

#### Botão Secundário (Ghost)
```css
background: transparent;
color: #F9FAFB;
border: 1px solid #374151;
padding: 10px 20px;
border-radius: 6px;
font-size: 14px;
font-weight: 500;
transition: border-color 0.15s, background 0.15s;

/* Hover */
background: rgba(55,65,81,0.4);
border-color: #6B7280;
```

#### Botão Outline Blue
```css
background: transparent;
color: #3B82F6;
border: 1px solid rgba(59,130,246,0.4);
padding: 10px 20px;
border-radius: 6px;

/* Hover */
background: rgba(59,130,246,0.08);
border-color: #3B82F6;
```

#### Botão de Texto (link)
```css
background: transparent;
border: none;
color: #9CA3AF;
font-size: 13px;
font-weight: 500;
padding: 4px 8px;
cursor: pointer;

/* Hover */
color: #F9FAFB;
```

---

### 6.2 Cards

#### Card Padrão
```css
background: #1F2937;
border: 1px solid #374151;
border-radius: 8px;
padding: 20px 24px;
```

#### Card KPI / Métrica
```css
background: #1F2937;
border: 1px solid #374151;
border-radius: 8px;
padding: 20px;
/* Estrutura interna:
   - Ícone 36x36px (background colorido com opacity 0.15, dot colorido)
   - Label: 12px, #9CA3AF
   - Valor: 28px, Bold, #F9FAFB, letter-spacing -0.5px
   - Trend: 11px, cor de acento (verde/vermelho)
*/
```

#### Card Hero (landing)
```css
background: rgba(31,41,55,0.8);
border: 1px solid rgba(55,65,81,0.8);
border-radius: 12px;
padding: 24px;
backdrop-filter: blur(8px);
box-shadow: 0 8px 32px rgba(0,0,0,0.4);
```

---

### 6.3 Inputs / Formulários

```css
/* Container de campo */
.field { margin-bottom: 18px; }

/* Label */
.field label {
  display: block;
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 1.2px;
  text-transform: uppercase;
  color: #6B7280;
  margin-bottom: 7px;
}

/* Input */
.field input, .field select, .field textarea {
  width: 100%;
  background: #111827;
  border: 1px solid #374151;
  border-radius: 6px;
  padding: 11px 14px;
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  color: #F9FAFB;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}

input::placeholder { color: #374151; }

/* Focus */
input:focus {
  border-color: rgba(59,130,246,0.6);
  box-shadow: 0 0 0 3px rgba(59,130,246,0.12);
}
```

---

### 6.4 Badges / Pills de Status

```css
/* Base */
.badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.3px;
}

/* Variantes */
.badge-green  { background: rgba(16,185,129,0.12); color: #10B981; border: 1px solid rgba(16,185,129,0.3); }
.badge-blue   { background: rgba(59,130,246,0.12); color: #3B82F6; border: 1px solid rgba(59,130,246,0.3); }
.badge-red    { background: rgba(239,68,68,0.12);  color: #EF4444; border: 1px solid rgba(239,68,68,0.3); }
.badge-amber  { background: rgba(245,158,11,0.12); color: #F59E0B; border: 1px solid rgba(245,158,11,0.3); }
.badge-gray   { background: rgba(107,114,128,0.15); color: #9CA3AF; border: 1px solid rgba(107,114,128,0.3); }
```

---

### 6.5 Tabela

```css
.table-container {
  background: #1F2937;
  border: 1px solid #374151;
  border-radius: 8px;
  overflow: hidden;
}

.table-header {
  background: #171F2E;
  padding: 14px 20px;
  border-bottom: 1px solid #374151;
  font-size: 14px;
  font-weight: 600;
  color: #F9FAFB;
}

.table-col-header {
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 1.2px;
  text-transform: uppercase;
  color: #6B7280;
  padding: 10px 20px;
  background: #121B2E;
  border-bottom: 1px solid #374151;
}

.table-row {
  padding: 0 20px;
  height: 48px;
  display: flex;
  align-items: center;
  border-bottom: 1px solid rgba(55,65,81,0.5);
  transition: background 0.1s;
}

.table-row:hover { background: rgba(55,65,81,0.3); }
.table-row:nth-child(even) { background: rgba(24,32,48,0.4); }
```

---

### 6.6 Sidebar (dashboard)

```css
.sidebar {
  width: 220px;
  height: 100vh;
  background: #1F2937;
  border-right: 1px solid #374151;
  display: flex;
  flex-direction: column;
  position: fixed;
  left: 0; top: 0;
}

/* Logo */
.sidebar-logo {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.5px;
  color: #F9FAFB;
  padding: 20px;
  border-bottom: 1px solid #374151;
}

/* Nav item */
.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  margin: 2px 12px;
  border-radius: 6px;
  font-size: 13px;
  color: #9CA3AF;
  cursor: pointer;
  transition: background 0.12s, color 0.12s;
  text-decoration: none;
}

.nav-item:hover {
  background: rgba(55,65,81,0.5);
  color: #F9FAFB;
}

.nav-item.active {
  background: rgba(59,130,246,0.12);
  color: #3B82F6;
  font-weight: 600;
}
```

---

### 6.7 Navbar da Landing Page

```css
.navbar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(17,24,39,0.92);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(55,65,81,0.6);
  padding: 0 clamp(24px, 5vw, 80px);
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.navbar-logo {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.5px;
  color: #F9FAFB;
}
/* "Flow" em azul: color: #3B82F6 */

.navbar-links {
  display: flex;
  gap: 32px;
  list-style: none;
}

.navbar-links a {
  font-size: 14px;
  font-weight: 500;
  color: #9CA3AF;
  text-decoration: none;
  transition: color 0.15s;
}

.navbar-links a:hover { color: #F9FAFB; }

.navbar-cta {
  display: flex;
  gap: 10px;
  align-items: center;
}
```

---

## 7. CSS Custom Properties (para usar nos arquivos)

```css
:root {
  /* Backgrounds */
  --bg:           #111827;
  --surface:      #1F2937;
  --surface-2:    #374151;
  --surface-hover:#243040;

  /* Texto */
  --text:         #F9FAFB;
  --text-muted:   #9CA3AF;
  --text-faint:   #6B7280;

  /* Acentos */
  --blue:         #3B82F6;
  --blue-dark:    #1D4ED8;
  --blue-dim:     rgba(59,130,246,0.12);
  --blue-border:  rgba(59,130,246,0.35);
  --green:        #10B981;
  --red:          #EF4444;
  --amber:        #F59E0B;
  --purple:       #8B5CF6;

  /* Bordas */
  --border:       #374151;
  --border-subtle:rgba(55,65,81,0.5);

  /* Raios */
  --radius-sm:    4px;
  --radius-md:    6px;
  --radius-lg:    8px;
  --radius-xl:    12px;

  /* Sombras */
  --shadow-sm:    0 1px 3px rgba(0,0,0,0.3);
  --shadow-md:    0 4px 12px rgba(0,0,0,0.4);
  --shadow-lg:    0 8px 32px rgba(0,0,0,0.5);
  --shadow-blue:  0 4px 20px rgba(59,130,246,0.25);

  /* Fonte */
  --font:         'Inter', -apple-system, sans-serif;
}
```

---

## 8. Regras Visuais Gerais

1. **Sem gradientes chamativos** — fundo sempre sólido escuro, sem rainbow, sem glows coloridos
2. **Bordas finas e discretas** — sempre 1px, cor `#374151`
3. **Hierarquia por peso** — `Bold` para valores, `Semi Bold` para títulos, `Regular` para corpo, `Medium` para labels
4. **Espaçamento generoso** — nunca comprimir; usar no mínimo 16px de gap entre elementos relacionados
5. **Hover states sutis** — fundo `rgba(55,65,81,0.4)`, não outline; transições `0.12–0.15s`
6. **Texto em caps** — apenas para labels de coluna, badges de status e tags de categoria
7. **Sem border-radius excessivo** — máximo `12px` para cards; `6px` para botões/inputs
8. **Fundo da página** — sempre `#111827`, nunca preto puro `#000`
9. **Cor de CTA única** — `#3B82F6`; não misturar com teal, verde ou laranja em botões principais
10. **Logo StaFlow** — "Sta" em `#F9FAFB`, "Flow" em `#3B82F6`, sempre Inter Bold

---

*StaFlow Design System v2.0 — Enterprise Edition*  
*Criado por Camila (Design & Identity Visual) — Jun 2026*
