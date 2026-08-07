/* ============================================================
   StaFlow — Motor de cálculo de ponto (FONTE ÚNICA DA VERDADE)
   ------------------------------------------------------------
   Todo cálculo de horas, agrupamento por dia e janela de consulta
   passa por aqui. Nenhuma tela deve reimplementar essa conta.

   POR QUE ESTE ARQUIVO EXISTE
   ---------------------------
   Antes, cada tela calculava do seu jeito e os números divergiam
   entre si. Dois defeitos reais foram encontrados em produção:

   1) HORAS INFLADAS PELO ALMOÇO
      A tela de Ponto (e o CSV "Exportar dia") pegava a PRIMEIRA
      entrada e a ÚLTIMA saída do dia e subtraía uma da outra.
      Num dia 08:00→12:00 (almoço) 13:00→17:00 isso dava 9h,
      quando o trabalhado real é 8h. Já o Espelho legal e o
      Relatório Excel pareavam corretamente e davam 8h. Ou seja:
      o mesmo dia saía com números diferentes em documentos
      diferentes — inaceitável para prestação de contas.

   2) BATIDA NO DIA ERRADO (fuso horário)
      A janela do dia era montada em UTC ('2026-06-18T00:00:00Z').
      Como o Brasil é UTC-3, toda batida after 21:00 no horário
      local cai no dia seguinte em UTC e sumia do dia correto.
      Caso real no banco: batida de 18/06 às 21:38 local aparecia
      em 19/06. Para porteiro noturno isso corrompe o mês inteiro.

   REGRAS DE NEGÓCIO
   -----------------
   - O "dia" é sempre o dia no fuso LOCAL do navegador (horário do
     condomínio), nunca em UTC.
   - Horas trabalhadas = soma dos pares entrada→saída em sequência.
     Intervalos (almoço) ficam de fora por construção.
   - Batida ímpar (entrada sem saída) não entra no total e é
     sinalizada como pendência — não se inventa horário de saída.
   - Hora noturna reduzida: CLT Art. 73 §1º (52min30s = 1 hora).
   ============================================================ */

window.staflowPonto = (function () {
  'use strict';

  // Fator da hora noturna reduzida — CLT Art.73 §1º (60 / 52.5)
  const FATOR_HORA_NOTURNA = 60 / 52.5;

  // ---------- Datas no fuso LOCAL ----------

  /* 'YYYY-MM-DD' do dia local de um timestamp */
  function diaLocal(ts) {
    const d = ts instanceof Date ? ts : new Date(ts);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  }

  /* 'YYYY-MM-DD' de hoje, local */
  function hojeLocal() {
    return diaLocal(new Date());
  }

  /* Janela [início, fim) de um dia local, em ISO/UTC pronto pra consulta.
     Ex: '2026-06-18' no Brasil → 2026-06-18T03:00Z até 2026-06-19T03:00Z */
  function limitesDoDia(dataStr) {
    const [a, m, d] = dataStr.split('-').map(Number);
    const inicio = new Date(a, m - 1, d, 0, 0, 0, 0);
    const fim    = new Date(a, m - 1, d + 1, 0, 0, 0, 0);
    return { inicioISO: inicio.toISOString(), fimISO: fim.toISOString() };
  }

  /* Janela [início, fim) de um mês local. mes = 1..12 */
  function limitesDoMes(ano, mes) {
    const inicio = new Date(ano, mes - 1, 1, 0, 0, 0, 0);
    const fim    = new Date(ano, mes, 1, 0, 0, 0, 0);
    return { inicioISO: inicio.toISOString(), fimISO: fim.toISOString() };
  }

  /* Janela [início, fim) entre dois dias locais, ambos inclusivos */
  function limitesDoPeriodo(dataInicio, dataFim) {
    const [a1, m1, d1] = dataInicio.split('-').map(Number);
    const [a2, m2, d2] = dataFim.split('-').map(Number);
    const inicio = new Date(a1, m1 - 1, d1, 0, 0, 0, 0);
    const fim    = new Date(a2, m2 - 1, d2 + 1, 0, 0, 0, 0);
    return { inicioISO: inicio.toISOString(), fimISO: fim.toISOString() };
  }

  // ---------- Formatação ----------

  /* 'HH:MM' local */
  function hhmm(ts) {
    if (!ts) return '—';
    const d = ts instanceof Date ? ts : new Date(ts);
    return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
  }

  /* 'DD/MM/AAAA' local */
  function ddmmaaaa(ts) {
    if (!ts) return '—';
    const d = ts instanceof Date ? ts : new Date(ts);
    return d.toLocaleDateString('pt-BR');
  }

  /* milissegundos → '8h05m' (ou '—' se zero) */
  function fmtDuracao(ms) {
    if (!ms || ms <= 0) return '—';
    const h = Math.floor(ms / 3600000);
    const m = Math.round((ms % 3600000) / 60000);
    return `${h}h${String(m).padStart(2, '0')}m`;
  }

  /* milissegundos → 8.25 (decimal, pra planilha somar) */
  function horasDecimais(ms) {
    if (!ms || ms <= 0) return 0;
    return Math.round((ms / 3600000) * 100) / 100;
  }

  // ---------- Pareamento entrada → saída ----------

  /* Ordena eventos por horário e pareia sequencialmente.
     Retorna { pares: [{entrada, saida}], pendente: <evento|null> }
     `pendente` = entrada sem saída correspondente (turno em aberto). */
  function parear(eventos) {
    const ordenados = [...(eventos || [])].sort(
      (a, b) => new Date(a.registrado_em) - new Date(b.registrado_em)
    );
    const pares = [];
    let aberta = null;
    for (const e of ordenados) {
      if (e.tipo === 'entrada') {
        // Duas entradas seguidas: a anterior fica órfã (não inventa saída)
        if (!aberta) aberta = e;
      } else if (e.tipo === 'saida' && aberta) {
        pares.push({ entrada: aberta, saida: e });
        aberta = null;
      }
      // saída sem entrada aberta é ignorada no cálculo (dado inconsistente)
    }
    return { pares, pendente: aberta };
  }

  /* Milissegundos efetivamente trabalhados num conjunto de batidas.
     Intervalos (almoço) ficam de fora porque só somamos os pares. */
  function msTrabalhados(eventos) {
    const { pares } = parear(eventos);
    return pares.reduce(
      (acc, p) => acc + (new Date(p.saida.registrado_em) - new Date(p.entrada.registrado_em)),
      0
    );
  }

  /* Resumo de um dia: primeira entrada, última saída, total real e flags */
  function resumoDoDia(eventos) {
    const { pares, pendente } = parear(eventos);
    const ordenados = [...(eventos || [])].sort(
      (a, b) => new Date(a.registrado_em) - new Date(b.registrado_em)
    );
    const primeiraEntrada = ordenados.find(e => e.tipo === 'entrada') || null;
    const ultimaSaida     = [...ordenados].reverse().find(e => e.tipo === 'saida') || null;
    const ms              = msTrabalhados(eventos);

    // Intervalo = tempo entre a 1ª entrada e a última saída MENOS o trabalhado.
    // É o almoço/pausas. Só faz sentido com o turno fechado.
    let msIntervalo = 0;
    if (primeiraEntrada && ultimaSaida && !pendente) {
      const bruto = new Date(ultimaSaida.registrado_em) - new Date(primeiraEntrada.registrado_em);
      msIntervalo = Math.max(0, bruto - ms);
    }

    return {
      primeiraEntrada,
      ultimaSaida,
      pares,
      pendente,                       // entrada sem saída = turno em aberto
      totalMs: ms,
      totalFmt: fmtDuracao(ms),
      totalDecimal: horasDecimais(ms),
      intervaloMs: msIntervalo,
      intervaloFmt: fmtDuracao(msIntervalo),
      qtdBatidas: (eventos || []).length,
      // Nº ímpar de batidas = alguém esqueceu de bater; sinaliza pra auditoria
      batidaImpar: (eventos || []).length % 2 !== 0
    };
  }

  /* Agrupa uma lista de batidas por dia LOCAL → { 'YYYY-MM-DD': [batidas] } */
  function agruparPorDia(eventos) {
    const mapa = {};
    (eventos || []).forEach(e => {
      const k = diaLocal(e.registrado_em);
      (mapa[k] ||= []).push(e);
    });
    return mapa;
  }

  // ---------- Hora noturna (CLT Art.73 §1º) ----------

  /* Minutos de relógio dentro da janela legal noturna [22h, 05h) */
  function minutosNoturnos(entradaTs, saidaTs) {
    const inicio = new Date(entradaTs);
    const fim    = new Date(saidaTs);
    if (fim <= inicio) return 0;

    let total = 0;
    const cursor = new Date(inicio);
    cursor.setHours(0, 0, 0, 0);

    while (cursor < fim) {
      const diaInicio = new Date(cursor);
      const fim5h     = new Date(cursor); fim5h.setHours(5, 0, 0, 0);
      const inicio22h = new Date(cursor); inicio22h.setHours(22, 0, 0, 0);
      const diaFim    = new Date(cursor); diaFim.setDate(diaFim.getDate() + 1);

      // [00h, 05h)
      const s1 = Math.max(inicio.getTime(), diaInicio.getTime());
      const e1 = Math.min(fim.getTime(),    fim5h.getTime());
      if (e1 > s1) total += (e1 - s1) / 60000;

      // [22h, 24h)
      const s2 = Math.max(inicio.getTime(), inicio22h.getTime());
      const e2 = Math.min(fim.getTime(),    diaFim.getTime());
      if (e2 > s2) total += (e2 - s2) / 60000;

      cursor.setDate(cursor.getDate() + 1);
    }
    return total;
  }

  /* Minutos noturnos cronológicos de um conjunto de batidas */
  function minutosNoturnosDe(eventos) {
    const { pares } = parear(eventos);
    return pares.reduce(
      (acc, p) => acc + minutosNoturnos(p.entrada.registrado_em, p.saida.registrado_em),
      0
    );
  }

  /* Converte minutos noturnos cronológicos em minutos de jornada legal */
  function minutosNoturnosLegais(minutosCronologicos) {
    return minutosCronologicos * FATOR_HORA_NOTURNA;
  }

  // ---------- Atraso ----------

  /* Minutos de atraso da entrada vs. horário previsto + tolerância.
     Retorna null se não dá pra calcular ou se está dentro da tolerância. */
  function minutosAtraso(horarioInicio, entradaTs, toleranciaMin) {
    if (!horarioInicio || !entradaTs) return null;
    const [hh, mm] = String(horarioInicio).split(':').map(Number);
    if (Number.isNaN(hh) || Number.isNaN(mm)) return null;
    const real = new Date(entradaTs);
    const esperado = new Date(real);
    esperado.setHours(hh, mm, 0, 0);
    const diff = Math.round((real - esperado) / 60000);
    return diff > (toleranciaMin ?? 0) ? diff : null;
  }

  // ---------- API ----------
  return {
    FATOR_HORA_NOTURNA,
    diaLocal, hojeLocal,
    limitesDoDia, limitesDoMes, limitesDoPeriodo,
    hhmm, ddmmaaaa, fmtDuracao, horasDecimais,
    parear, msTrabalhados, resumoDoDia, agruparPorDia,
    minutosNoturnos, minutosNoturnosDe, minutosNoturnosLegais,
    minutosAtraso
  };
})();
