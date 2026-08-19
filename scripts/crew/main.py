"""
StaFlow — Orquestrador do ciclo diário

Roda UM ciclo por dia: o time-CEO, que olha a operação inteira e escolhe
a única prioridade do dia.

Uso normal:            python -m scripts.crew.main
Rodar loop antigo:     LOOP=marketing python -m scripts.crew.main
Log detalhado (debug): VERBOSE=1 python -m scripts.crew.main
"""
import sys
import os
import time
import logging
import datetime
from crewai import Crew, Process

from .config import MAX_RPM
from .agents import (build_loop_agents, build_ceo_agents, ORDEM_CEO,
                     build_meta_agent, build_meta_relator)
from .tasks import (build_loop_tasks, build_ceo_tasks,
                    build_meta_task, build_meta_relatorio_task)
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

# ★ 10/08/2026 — ordem do Breno: UM ciclo pra operação inteira, funcionando
# como CEO. Os 4 loops por área saíram do automático.
#
# A conta que ninguém tinha feito e que explica meses de falha: cada loop
# de 8 agentes custava ~26 mil tokens. Quatro por dia = 105 mil, contra
# cota diária de 100 mil do Groq. Nunca coube. O ciclo CEO tem 4 agentes
# (~13 mil tokens) e usa ~13% da cota — sobra folga real pra retry e erro.
#
# Os loops por área seguem existindo pra rodar na mão: LOOP=marketing.
LOOPS_DE_NEGOCIO = ["marketing", "produto", "financeiro", "suporte"]

# ★ 19/08/2026 — números atualizados junto com a troca de modelo
# (llama-3.3-70b desativado pela Groq em 16/08 — ver config.py).
# Free tier do openai/gpt-oss-120b: 8.000 tokens/min · 200.000/dia.
COTA_DIARIA_TOKENS   = int(os.environ.get("COTA_DIARIA_TOKENS", "200000"))
FRACAO_ORCAMENTO     = float(os.environ.get("FRACAO_ORCAMENTO_DIARIO", "0.7"))
ORCAMENTO_DIARIO     = int(COTA_DIARIA_TOKENS * FRACAO_ORCAMENTO)

# Limite de tokens POR MINUTO do free tier do Groq (openai/gpt-oss-120b).
# Usado como teto de sanidade do contador — ver _tokens_do_crew().
# Apertou em relação ao modelo antigo (era 12.000 no llama-3.3-70b).
TPM_GROQ = int(os.environ.get("TPM_GROQ", "8000"))

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

    # Teto físico: TPM_GROQ tokens/min é o limite do free tier do Groq
    # (8.000 no openai/gpt-oss-120b desde 19/08/2026).
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
    # ★ 19/08/2026 — importado FORA do try. Antes ficava dentro, e o
    # próprio except tentava ler SUPABASE_URL pra montar o diagnóstico:
    # se o import falhasse, o handler de erro estourava um NameError em
    # cima do erro original e escondia os dois.
    from .config import SUPABASE_URL, SUPABASE_KEY
    try:
        from supabase import create_client
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
        url_ok = isinstance(SUPABASE_URL, str) and SUPABASE_URL.startswith("http")
        log.warning(
            "Não consegui registrar a execução no Supabase: %s: %s | "
            "SUPABASE_URL parece válida: %s (%d chars, começa com '%s')",
            type(e).__name__, str(e)[:200], url_ok,
            len(str(SUPABASE_URL)), str(SUPABASE_URL)[:12]
        )


def _ordem_do_dia() -> list:
    """Gira a ordem das 4 áreas conforme o dia do ano, pra distribuir
    igualmente quem corre risco de ficar de fora quando o orçamento
    aperta."""
    giro = datetime.date.today().timetuple().tm_yday % len(LOOPS_DE_NEGOCIO)
    return LOOPS_DE_NEGOCIO[giro:] + LOOPS_DE_NEGOCIO[:giro]


def montar_crew(loop_key: str) -> Crew:
    if loop_key == "ceo":
        agents = build_ceo_agents()
        tasks  = build_ceo_tasks(agents)
        return Crew(
            agents=[agents[k] for k in ORDEM_CEO],
            tasks=[tasks[k] for k in ["entender", "decidir", "fazer", "contar"]],
            process=Process.sequential, verbose=VERBOSE, memory=False,
            max_rpm=MAX_RPM,
        )

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
    uso.registrar_callback()   # o CrewAI pode ter sobrescrito a lista
    uso.zerar()                # começa a contar os tokens deste ciclo do zero
    log.info("=" * 50)
    log.info("StaFlow — Loop: %s", loop_key.upper())
    log.info("=" * 50)

    crew = None

    def _falhou(detalhe: str, parar_o_dia: bool = False):
        """Fecha o loop como falha: mede, registra no Supabase e devolve
        a tripla que o orquestrador espera."""
        dur    = int(time.time() - inicio)
        tokens = _tokens_do_crew(crew, dur)
        _registrar_execucao(loop_key, False, tokens, dur, detalhe)
        return False, tokens, parar_o_dia

    # ★ 19/08/2026 — montar_crew() ficava FORA de qualquer try. Se ela
    # falhasse (prompt quebrado no banco, modelo inválido, credencial
    # faltando), a exceção subia direto e o ciclo morria sem registrar
    # nada em agent_runs. Agora até a montagem do time vira falha
    # registrada, não sumiço.
    try:
        crew = montar_crew(loop_key)
    except Exception as e:
        log.error("Não consegui nem montar o time do loop %s: %s: %s",
                  loop_key, type(e).__name__, str(e)[:300])
        return _falhou(f"Falha ao montar o time: {type(e).__name__}: {str(e)[:120]}")

    wait = BASE_WAIT

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
    """★ 10/08/2026 — ordem do Breno: UM loop só, pra operação inteira,
    trabalhando como CEO. Nada de 4 loops por área.

    Por que isso também conserta o sistema, e não só simplifica:
    os 4 loops de 8 agentes custavam ~26 mil tokens CADA. Quatro por dia
    = 105 mil, contra uma cota diária de 100 mil do Groq. Nunca coube —
    era matematicamente impossível desde o primeiro dia. O ciclo CEO tem
    4 agentes (~13 mil tokens), roda uma vez por dia e usa ~13% da cota.
    Sobra folga de verdade pra retry, erro e execução manual.

    Os loops antigos por área continuam disponíveis pra rodar na mão
    (LOOP=marketing python -m scripts.crew.main), mas não são mais o
    comportamento automático.
    """
    uso.registrar_callback()   # liga a medição real de tokens

    hoje_iso = datetime.date.today().isoformat()

    # Override manual: LOOP=marketing (ou produto/financeiro/suporte/meta)
    loop_key = os.environ.get("LOOP", "").strip().lower() or "ceo"

    # ★ 09/08/2026 — o gasto do dia vem do banco, não da memória deste
    # processo. O Railway sobe container novo a cada cron E a cada deploy;
    # antes, toda subida zerava o contador e o time rodava de novo achando
    # que tinha a cota inteira. Era assim que 100 mil tokens sumiam sem
    # aparecer em lugar nenhum.
    gasto_anterior = ler_gasto_do_dia(hoje_iso)

    log.info("=" * 50)
    log.info("StaFlow — ciclo do dia: %s", loop_key.upper())
    log.info("Orçamento: %d tokens (%.0f%% de %d/dia). Já gastos hoje: %d.",
             ORCAMENTO_DIARIO, FRACAO_ORCAMENTO * 100,
             COTA_DIARIA_TOKENS, gasto_anterior)
    log.info("=" * 50)

    if gasto_anterior >= ORCAMENTO_DIARIO:
        log.warning("Orçamento do dia já esgotado (%d/%d tokens) por uma "
                    "execução anterior. Ciclo de hoje não roda.",
                    gasto_anterior, ORCAMENTO_DIARIO)
        return

    sucesso, tokens, _ = _rodar_um_loop(loop_key)
    gasto = gasto_anterior + tokens
    salvar_gasto_do_dia(hoje_iso, gasto)

    log.info("=" * 50)
    log.info("Ciclo %s: %s · %d tokens neste ciclo · %d/%d no dia (%.0f%%)",
             loop_key, "concluído" if sucesso else "INTERROMPIDO",
             tokens, gasto, ORCAMENTO_DIARIO,
             (gasto / ORCAMENTO_DIARIO * 100) if ORCAMENTO_DIARIO else 0)
    log.info("=" * 50)


if __name__ == "__main__":
    try:
        executar_loop()
    except Exception as e:
        log.error("ERRO CRÍTICO: %s", str(e)[:500])
        sys.exit(1)
