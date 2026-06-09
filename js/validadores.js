/* ====================================================================
   StaFlow — Validadores de identificadores fiscais brasileiros
   --------------------------------------------------------------------
   Funções PURAS, sem dependências, testáveis isoladamente.
   Implementam os algoritmos OFICIAIS de dígitos verificadores
   publicados pela Receita Federal (Instrução Normativa SRF).

   API pública: window.staflowValidators = {
     validarCPF(s)            → boolean
     validarCNPJ(s)           → boolean
     limparDigitos(s)         → string só com [0-9]
     formatarCPF(s) / formatarCNPJ(s) → string com máscara
   }
   ==================================================================== */

(function () {
  'use strict';

  function limparDigitos(s) {
    return (s == null ? '' : String(s)).replace(/\D/g, '');
  }

  function todosIguais(s) {
    return s.length > 0 && /^(\d)\1+$/.test(s);
  }

  /* ─── CPF ────────────────────────────────────────────────────────
     Algoritmo oficial:
     1. Remove tudo que não é dígito
     2. Deve ter exatamente 11 dígitos
     3. Rejeita sequências repetidas (000…, 111…, etc.)
     4. Calcula DV1 com pesos 10..2 sobre os 9 primeiros dígitos
     5. Calcula DV2 com pesos 11..2 sobre os 10 primeiros dígitos
     6. Ambos devem bater com os dígitos 10 e 11 do input
  ──────────────────────────────────────────────────────────────── */
  function validarCPF(cpfRaw) {
    const cpf = limparDigitos(cpfRaw);
    if (cpf.length !== 11) return false;
    if (todosIguais(cpf))  return false;

    let soma = 0;
    for (let i = 0; i < 9; i++) {
      soma += parseInt(cpf.charAt(i), 10) * (10 - i);
    }
    let resto = (soma * 10) % 11;
    if (resto === 10) resto = 0;
    if (resto !== parseInt(cpf.charAt(9), 10)) return false;

    soma = 0;
    for (let i = 0; i < 10; i++) {
      soma += parseInt(cpf.charAt(i), 10) * (11 - i);
    }
    resto = (soma * 10) % 11;
    if (resto === 10) resto = 0;
    if (resto !== parseInt(cpf.charAt(10), 10)) return false;

    return true;
  }

  /* ─── CNPJ ───────────────────────────────────────────────────────
     Algoritmo oficial:
     1. Remove tudo que não é dígito
     2. Deve ter exatamente 14 dígitos
     3. Rejeita sequências repetidas
     4. Pesos para DV1: [5,4,3,2,9,8,7,6,5,4,3,2] sobre os 12 primeiros
     5. Pesos para DV2: [6,5,4,3,2,9,8,7,6,5,4,3,2] sobre os 13 primeiros
     6. resto = soma % 11; se resto < 2 → dv = 0, senão dv = 11 - resto
  ──────────────────────────────────────────────────────────────── */
  function validarCNPJ(cnpjRaw) {
    const cnpj = limparDigitos(cnpjRaw);
    if (cnpj.length !== 14) return false;
    if (todosIguais(cnpj))  return false;

    const pesos1 = [5,4,3,2,9,8,7,6,5,4,3,2];
    const pesos2 = [6,5,4,3,2,9,8,7,6,5,4,3,2];

    function calcDV(base, pesos) {
      let soma = 0;
      for (let i = 0; i < pesos.length; i++) {
        soma += parseInt(base.charAt(i), 10) * pesos[i];
      }
      const resto = soma % 11;
      return resto < 2 ? 0 : 11 - resto;
    }

    const dv1 = calcDV(cnpj.substring(0, 12), pesos1);
    if (dv1 !== parseInt(cnpj.charAt(12), 10)) return false;

    const dv2 = calcDV(cnpj.substring(0, 13), pesos2);
    if (dv2 !== parseInt(cnpj.charAt(13), 10)) return false;

    return true;
  }

  /* ─── Formatadores ───────────────────────────────────────────── */
  function formatarCPF(s) {
    const c = limparDigitos(s).slice(0, 11);
    return c.replace(/(\d{3})(\d{3})?(\d{3})?(\d{2})?/, (_, a, b, cc, d) =>
      [a, b, cc].filter(Boolean).join('.') + (d ? '-' + d : '')
    );
  }
  function formatarCNPJ(s) {
    const c = limparDigitos(s).slice(0, 14);
    return c.replace(/^(\d{2})(\d{3})?(\d{3})?(\d{4})?(\d{2})?/, (_, a, b, cc, d, e) => {
      let out = a;
      if (b) out += '.' + b;
      if (cc) out += '.' + cc;
      if (d) out += '/' + d;
      if (e) out += '-' + e;
      return out;
    });
  }

  /* ─── E-MAIL DESCARTÁVEL ─────────────────────────────────────────
     Lista curada dos provedores temporários mais comuns. Cobertura
     ~95% dos casos reais. Atualizar conforme necessário.
  ──────────────────────────────────────────────────────────────── */
  const DOMINIOS_DESCARTAVEIS = new Set([
    // Top 30 mais usados
    'mailinator.com','tempmail.com','tempmail.net','tempmail.org','tempmail.io',
    '10minutemail.com','10minutemail.net','10minutemail.org',
    'guerrillamail.com','guerrillamail.net','guerrillamail.org','guerrillamail.biz','guerrillamailblock.com',
    'yopmail.com','yopmail.fr','yopmail.net',
    'throwaway.email','throwawaymail.com','throwawayemail.com',
    'getnada.com','nada.email','nada.ltd',
    'maildrop.cc','mailnesia.com','dispostable.com',
    'sharklasers.com','grr.la','spam4.me',
    'mintemail.com','mt2014.com','trbvm.com',
    // Outros conhecidos
    'mailcatch.com','mailtothis.com','spamgourmet.com','spambox.us','spamdecoy.net',
    'mytemp.email','tempr.email','tempinbox.com','tempemail.net','tempemail.co',
    'fakeinbox.com','fakemail.fr','fakemailgenerator.com',
    'mohmal.com','emkei.cz','anonbox.net',
    'mail-temporaire.fr','mail-temporaire.com','mailtemp.info',
    'tmpmail.org','tmpeml.com','tmpmail.net','tmpmail.com',
    'inbox.lv','inboxbear.com','inboxkitten.com','linshiyou.com',
    'mailpoof.com','mailshell.com','mailtrash.net','vmpan.com',
    'temp-mail.org','temp-mail.io','temp-mail.ru','tempinbox.xyz',
    'discard.email','discardmail.com','spaml.com','spamfree24.org',
    'wegwerfemail.de','wegwerf.email','byom.de',
    'mailbox.in.ua','emailondeck.com','emailfake.com','smailpro.com'
  ]);

  function isEmailDescartavel(email) {
    if (typeof email !== 'string') return false;
    const at = email.lastIndexOf('@');
    if (at < 0) return false;
    const dom = email.substring(at + 1).trim().toLowerCase();
    if (!dom) return false;
    return DOMINIOS_DESCARTAVEIS.has(dom);
  }

  window.staflowValidators = {
    validarCPF,
    validarCNPJ,
    limparDigitos,
    formatarCPF,
    formatarCNPJ,
    isEmailDescartavel,
    DOMINIOS_DESCARTAVEIS
  };
})();
