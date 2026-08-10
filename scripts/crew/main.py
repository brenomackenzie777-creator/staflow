"""
StaFlow — Orquestrador principal: roteia por loop conforme o dia da semana
Uso: python -m scripts.crew.main
Override manual: LOOP=produto python -m scripts.crew.main
Log detalhado (debug):  VERBOSE=1 python -m scripts.crew.main
"""
import sys
import os
import time
import logging
import datetime
from crewai import Crew, Process

from .config import MAX_RPM
from .agents import build_loop_agents, build_meta_agent, build_meta_relator
from .tasks import build_loop_tasks, build_meta_task, build_meta_relatorio_task
from .tools import ler_gasto_do_dia, salvar_gasto_do_dia
from . import uso

MAX_RETRIES = 5
BASE_WAIT   = 30   # segundos iniciais; dobra a cada tentativa

# O log verboso do CrewAI estoura o limite do Railway (500 linhas/seg) e
# derruba justamente as linhas de erro que importam. Ligue só para depurar.
VERBOSE = os.environ.get("VERBOSE", "").strip() in ("1", "true", "True")

# Silencia o ruído das bibliotecas; mantém avisos e erros.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
for _lib in ("httpx", "httpcore", "LiteLLM", "litellm", "openai", "urllib3"):
    logging.getLogger(_lib).setLevel(logging.WARNING)

log = logging.getLogger("staflow")

# ★ 08/08/2026 — a pedido do Breno: em vez de UM loop por dia útil, roda
# quantos loops de negócio couberem por dia, TODOS OS DIAS (inclusive fim
# de semana), até usar 70% da cota diária do Groq (100.000 tokens/dia no
# free tier — ver scripts/crew/config.py). Os outros 30% ficam de reserva
# pra retries, o Meta-Agente de sexta e qualquer chamada manual (LOOP=x).
# (Histórico: começou em 50%, foi pra 90%, o log de 08/08 mostrou um loop
# sozinho consumindo quase a cota inteira do dia — voltou pra 70% até
# entendermos o motivo real do consumo alto. Ver nota sobre gatilho
# duplicado logo abaixo.)
#
# Ordem de execução gira por dia (dia do ano % 4) pra nenhuma área ficar
# sempre em último — se o orçamento acabar no meio, quem tomava o corte
# antes era sempre "suporte"; agora o corte roda entre as 4 áreas.
LOOPS_DE_NEGOCIO = ["marketing", "produto", "financeiro", "suporte"]

COTA_DIARIA_TOKENS   = int(os.environ.get("COTA_DIARIA_TOKENS", "100000"))
FRACAO_ORCAMENTO     = float(os.environ.get("FRACAO_ORCAMENTO_DIARIO", "0.7"))
ORCAMENTO_DIARIO     = int(COTA_DIARIA_TOKENS * FRACAO_ORCAMENTO)

# Limite de tokens POR MINUTO do free tier do Groq (llama-3.3-70b).
# Usado como teto de sanidade do contador — ver _tokens_do_crew().
TPM_GROQ = int(os.environ.get("TPM_GROQ", "12000"))

ORDEM_AGENTES = ["coletor", "pesquisador", "analista", "estrategista",
                  "decisor", "executor", "observador", "relator"]
ORDEM_TAREFAS = ["coletar", "pesquisar", "analisar", "propor",
                  "decidir", "executar", "aprender", "relatar"]


def _tokens_do_crew(crew: Crew, segundos: float = 0) -> int:
    """Lê o total de tokens gastos num crew.kickoff() já concluído.

    ★ 09/08/2026 — o número cru do CrewAI veio ABSURDO num log real:
    631.320 tokens num ciclo de 6min19s. Isso é fisicamente impossível:
    o Groq corta em 12.000 tokens/minuto, então 6min19s comportam no
    MÁXIMO ~76.000. O usage_metrics do CrewAI soma a conversa inteira
    de novo a cada rodada de ferramenta, inflando o total.

    Como o orçamento diário depende desse número, um valor inflado faz
    o freio disparar cedo demais (ou tarde demais).

    ★ 09/08/2026 (2ª correção) — em vez de tentar consertar o número do
    CrewAI, agora medimos na fonte: um callback do litellm soma cada
    chamada de verdade (é a mesma origem das linhas "OpenAI API usage"
    do log). Somando essas linhas no ciclo de 6min19s dá 26.336 tokens,
    não 631.320. O teto físico por tempo fica como segunda rede."""
    medido = uso.consumir()

    # Teto físico: 12.000 tokens/min é o limite do free tier do Groq.
    # Nenhum ciclo pode ter gasto mais do que o relógio permitia.
    if segundos > 0:
        teto = int((segundos / 60.0) * TPM_GROQ) + TPM_GROQ  # +1min de folga
        if medido > teto:
            log.warning(
                "Contador reportou %d tokens em %ds — acima do teto físico "
                "(~%d). Usando o teto para o controle de orçamento.",
                medido, int(segundos), teto
            )
            return teto
    return medido


def _registrar_execucao(loop_key: str, sucesso: bool, tokens: int,
                        segundos: int, detalhe: str = "") -> None:
    """Grava no Supabase que este ciclo rodou — SEMPRE, dando certo ou não.

    ★ 09/08/2026 — antes isso dependia do agente Executor lembrar de
    chamar a ferramenta supabase_write_agent_run. Num ciclo real que
    completou inteiro (loop 'produto', 6min19s), ele simplesmente não
    chamou: a tabela agent_runs ficou vazia e o trabalho evaporou sem
    deixar rastro. Registro de execução não pode depender do modelo
    lembrar — agora o próprio orquestrador grava."""
    try:
        from supabase import create_client
        from .config import SUPABASE_URL, SUPABASE_KEY
        sb = create_client(SUPABASE_URL, SUPABASE_KEY)
        resumo = (
            f"Ciclo de {loop_key} "
            f"{'concluído' if sucesso else 'interrompido'} em "
            f"{segundos // 60}min{segundos % 60:02d}s (~{tokens} tokens)."
        )
        if detalhe:
            resumo += f" {detalhe}"
        sb.table("agent_runs").insert({
            "agent_name":     "orquestrador",
            "loop_name":      loop_key,
            "output_summary": resumo[:500],
            "status":         "pending" if sucesso else "failed",
            "created_at":     datetime.datetime.utcnow().isoformat(),
        }).execute()
    except Exception as e:
        log.warning("Não consegui registrar a execução no Supabase: %s",
                     str(e)[:200])


def _ordem_do_dia() -> list:
    """Gira a ordem das 4 áreas conforme o dia do ano, pra distribuir
    igualmente quem corre risco de ficar de fora quando o orçamento
    aperta."""
    giro = datetime.date.today().timetuple().tm_yday % len(LOOPS_DE_NEGOCIO)
    return LOOPS_DE_NEGOCIO[giro:] + LOOPS_DE_NEGOCIO[:giro]


def montar_crew(loop_key: str) -> Crew:
    if loop_key == "meta":
        meta_agente   = build_meta_agent()
        meta_relator  = build_meta_relator()
        tarefa_meta   = build_meta_task(meta_agente)
        tarefa_relato = build_meta_relatorio_task(meta_relator, tarefa_meta)
        return Crew(agents=[meta_agente, meta_relator],
                    tasks=[tarefa_meta, tarefa_relato],
                    process=Process.sequential, verbose=VERBOSE, memory=False,
                    max_rpm=MAX_RPM)

    agents = build_loop_agents(loop_key)
    tasks  = build_loop_tasks(loop_key, agents)
    return Crew(
        agents=[agents[k] for k in ORDEM_AGENTES],
        tasks=[tasks[k] for k in ORDEM_TAREFAS],
        process=Process.sequential,
        verbose=VERBOSE,
        memory=False,
        max_rpm=MAX_RPM,
    )


def _rodar_um_loop(loop_key: str):
    """Roda um loop (com retries). Retorna (sucesso, tokens_gastos, parar_o_dia).
    parar_o_dia=True só quando a COTA DIÁRIA acabou — aí não adianta tentar
    os outros loops de hoje, todos vão bater na mesma parede."""
    inicio = time.time()
    uso.zerar()          # começa a contar os tokens deste ciclo do zero
    log.info("=" * 50)
    log.info("StaFlow — Loop: %s", loop_key.upper())
    log.info("=" * 50)

    crew = montar_crew(loop_key)
    wait = BASE_WAIT

    def _falhou(detalhe: str, parar_o_dia: bool = False):
        """Fecha o loop como falha: mede, registra no Supabase e devolve
        a tripla que o orquestrador espera."""
        dur    = int(time.time() - inicio)
        tokens = _tokens_do_crew(crew, dur)
        _registrar_execucao(loop_key, False, tokens, dur, detalhe)
        return False, tokens, parar_o_dia

    for tentativa in range(1, MAX_RETRIES + 1):
        try:
            crew.kickoff()
            dur    = int(time.time() - inicio)
            tokens = _tokens_do_crew(crew, dur)
            log.info("=" * 50)
            log.info("Loop %s concluído em %dmin%02ds (~%d tokens)",
                      loop_key, dur // 60, dur % 60, tokens)
            log.info("=" * 50)
            _registrar_execucao(loop_key, True, tokens, dur)
            return True, tokens, False

        except Exception as e:
            msg = str(e)

            # 413 = pedido grande demais. Esperar não resolve, mas encolher a
            # memória resolve: cada tentativa aperta o teto de leitura e
            # remonta o crew do zero, com conversa limpa.
            if "413" in msg or "Request too large" in msg:
                from . import tools
                if tentativa < 3:
                    tools.LIMITE_MEMORIA = max(1200, tools.LIMITE_MEMORIA // 2)
                    tools.LIMITE_PROMPTS = max(1000, tools.LIMITE_PROMPTS // 2)
                    log.warning(
                        "Pedido grande demais. Reduzindo a memória lida "
                        "(agora %d caracteres) e tentando de novo (%d/3).",
                        tools.LIMITE_MEMORIA, tentativa
                    )
                    time.sleep(65)          # zera a janela de tokens/minuto
                    crew = montar_crew(loop_key)   # conversa limpa
                    continue

                log.error(
                    "Pedido segue grande demais mesmo com a memória mínima "
                    "para o loop %s. Pulando pra o próximo. Detalhe: %s",
                    loop_key, msg[:250]
                )
                return _falhou("Pedido grande demais mesmo com memória mínima.")

            # Cota DIÁRIA esgotada: esperar minutos não resolve, só vira o dia.
            # Isso encerra a rotação inteira de hoje, não só este loop.
            if "tokens per day" in msg or "TPD" in msg:
                log.error(
                    "Cota diária de IA esgotada (100.000 tokens/dia do plano "
                    "gratuito) durante o loop %s. Os loops restantes de hoje "
                    "ficam pra amanhã.", loop_key
                )
                return _falhou("Cota diária do Groq esgotada.", parar_o_dia=True)

            # Chamada de ferramenta malformada pelo modelo. É falha de geração,
            # não de código — outra tentativa normalmente sai correta.
            # O Groq manda essa falha com pelo menos 3 textos diferentes;
            # os três precisam cair aqui, senão o loop inteiro trava.
            if ("tool_use_failed" in msg
                    or "Failed to call a function" in msg
                    or "tool call validation failed" in msg
                    or "which was not in request.tools" in msg):
                if tentativa < MAX_RETRIES:
                    log.warning("O modelo gerou uma chamada de ferramenta "
                                "inválida (tentativa %d/%d). Refazendo em 10s.",
                                tentativa, MAX_RETRIES)
                    time.sleep(10)
                    crew = montar_crew(loop_key)   # conversa limpa
                    continue
                log.error("O modelo falhou em chamar as ferramentas "
                          "corretamente no loop %s após %d tentativas. "
                          "Pulando pra o próximo.", loop_key, MAX_RETRIES)
                return _falhou("Modelo não conseguiu usar as ferramentas.")

            if "429" in msg or "rate_limit" in msg.lower() or "RESOURCE_EXHAUSTED" in msg:
                if tentativa < MAX_RETRIES:
                    log.warning("Limite da IA atingido (tentativa %d/%d). "
                                "Aguardando %ds...", tentativa, MAX_RETRIES, wait)
                    time.sleep(wait)
                    wait = min(wait * 2, 300)
                else:
                    log.error("Limite da IA esgotado no loop %s após %d "
                              "tentativas. Pulando pra o próximo.",
                              loop_key, MAX_RETRIES)
                    return _falhou("Limite por minuto da IA esgotado.")
            else:
                log.error("Falha no loop %s: %s. Pulando pra o próximo.",
                           loop_key, msg[:500])
                return _falhou(f"Erro: {msg[:150]}")

    return False, 0, False


def executar_loop():
    uso.registrar_callback()   # liga a medição real de tokens

    # Override manual (LOOP=marketing python -m scripts.crew.main) — roda
    # só esse loop, ignora rotação e orçamento diário.
    loop_manual = os.environ.get("LOOP")
    if loop_manual:
        _rodar_um_loop(loop_manual)
        return

    hoje     = datetime.date.today()
    hoje_iso = hoje.isoformat()
    eh_sexta = hoje.weekday() == 4   # 0=segunda ... 4=sexta

    ordem = _ordem_do_dia()

    # ★ 09/08/2026 — o gasto do dia agora vem do banco, não da memória
    # deste processo. O Railway sobe um container novo a cada cron E a
    # cada deploy; antes, toda subida zerava o contador e o time rodava
    # de novo achando que tinha a cota inteira disponível. Foi assim que
    # os 100 mil tokens/dia sumiam sem aparecer em lugar nenhum: num
    # mesmo dia teve execução às 11:04, às 15:05 e à meia-noite, cada
    # uma se achando a primeira.
    gasto = ler_gasto_do_dia(hoje_iso)
    log.info("Orçamento de hoje: %d tokens (%.0f%% de %d/dia). "
              "Já gastos hoje por execuções anteriores: %d. Ordem: %s",
              ORCAMENTO_DIARIO, FRACAO_ORCAMENTO * 100, COTA_DIARIA_TOKENS,
              gasto, " → ".join(ordem))

    concluidos, pulados = [], []

    for i, loop_key in enumerate(ordem):
        if gasto >= ORCAMENTO_DIARIO:
            restante = ordem[i:]
            pulados.extend(restante)
            log.info("Orçamento diário atingido (%d/%d tokens). Loops "
                      "restantes de hoje (%s) ficam pra amanhã.",
                      gasto, ORCAMENTO_DIARIO, ", ".join(restante))
            break

        sucesso, tokens, parar_o_dia = _rodar_um_loop(loop_key)
        gasto += tokens
        salvar_gasto_do_dia(hoje_iso, gasto)
        (concluidos if sucesso else pulados).append(loop_key)

        if parar_o_dia:
            restante = ordem[i + 1:]
            pulados.extend(restante)
            if restante:
                log.warning("Loops restantes de hoje (%s) ficam pra amanhã "
                            "— cota diária esgotada.", ", ".join(restante))
            break

    # Sexta-feira: se ainda sobrar orçamento, fecha a semana com o
    # Meta-Agente (avalia os 4 loops e propõe ajuste de prompt).
    if eh_sexta:
        if gasto < ORCAMENTO_DIARIO:
            log.info("Sexta-feira — rodando o Meta-Agente (avaliação da semana).")
            sucesso, tokens, _ = _rodar_um_loop("meta")
            gasto += tokens
            salvar_gasto_do_dia(hoje_iso, gasto)
            (concluidos if sucesso else pulados).append("meta")
        else:
            log.warning("Sexta-feira, mas o orçamento diário já esgotou — "
                        "o Meta-Agente fica pra próxima sexta.")

    log.info("=" * 50)
    log.info("Dia concluído: %d loop(s) rodados (%s) · %d/%d tokens (%.0f%%)",
              len(concluidos), ", ".join(concluidos) or "nenhum",
              gasto, ORCAMENTO_DIARIO,
              (gasto / ORCAMENTO_DIARIO * 100) if ORCAMENTO_DIARIO else 0)
    if pulados:
        log.info("Ficaram de fora hoje: %s", ", ".join(pulados))
    log.info("=" * 50)


if __name__ == "__main__":
    try:
        executar_loop()
    except Exception as e:
        log.error("ERRO CRÍTICO: %s", str(e)[:500])
        sys.exit(1)
