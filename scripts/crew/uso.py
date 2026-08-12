"""
StaFlow — Medição real de consumo de tokens

★ 09/08/2026 — criado depois de um log real mostrar o problema:
o `crew.usage_metrics` do CrewAI reportou 631.320 tokens para um ciclo
que, somando as chamadas de verdade registradas no mesmo log, gastou
26.336. Um exagero de ~24x (o CrewAI registra o contador uma vez por
agente e acaba multiplicando o total). Como o orçamento diário é
calculado em cima desse número, o time achava que tinha estourado
902% da cota logo no primeiro loop e pulava os outros três — todo dia.

Aqui a gente mede o consumo na fonte: um callback do litellm (a
biblioteca que o CrewAI usa por baixo pra falar com o Groq), que é
exatamente de onde saem as linhas "OpenAI API usage: {...}" do log.
"""
import logging

log = logging.getLogger("staflow")

# Acumulador do processo. Zerado a cada loop via `zerar()`.
_ACUMULADO = {"tokens": 0}
_CALLBACK_REGISTRADO = {"ok": False}

# Se a medição real não funcionar (mudança de versão do litellm, por
# exemplo), assumimos este custo por ciclo em vez de achar que gastou
# zero — zero faria o time rodar sem freio nenhum.
#
# Medições reais somando as chamadas do log:
#   09/08/2026 · loop 'produto' (8 agentes) ... 26.336 tokens
#   12/08/2026 · ciclo 'ceo'    (4 agentes) ... 13.013 tokens
# O valor abaixo é o do ciclo CEO com folga de ~15%.
ESTIMATIVA_POR_LOOP = 15000


def _extrair_total(response_obj) -> int:
    """Pega total_tokens da resposta, seja ela dict ou objeto."""
    try:
        if isinstance(response_obj, dict):
            usage = response_obj.get("usage")
        else:
            usage = getattr(response_obj, "usage", None)
        if usage is None:
            return 0
        if isinstance(usage, dict):
            return int(usage.get("total_tokens") or 0)
        return int(getattr(usage, "total_tokens", 0) or 0)
    except Exception:
        return 0


def _callback(kwargs, response_obj, start_time, end_time):
    _ACUMULADO["tokens"] += _extrair_total(response_obj)


def registrar_callback() -> None:
    """Liga a medição. Pode ser chamada várias vezes sem problema.

    ★ 12/08/2026 — no primeiro ciclo CEO o callback não disparou e a
    contagem caiu na estimativa. Provável causa: o CrewAI monta o objeto
    LLM na importação e mexe nas listas de callback do litellm depois de
    nós. Por isso agora registramos nas DUAS listas que o litellm usa e
    reregistramos antes de cada ciclo, em vez de uma vez só no começo."""
    try:
        import litellm
        for atributo in ("success_callback", "callbacks"):
            atuais = list(getattr(litellm, atributo, []) or [])
            if _callback not in atuais:
                atuais.append(_callback)
                setattr(litellm, atributo, atuais)
        _CALLBACK_REGISTRADO["ok"] = True
    except Exception as e:
        log.warning("Não foi possível medir tokens com precisão (%s). "
                    "Vou usar a estimativa de %d por ciclo.",
                    str(e)[:120], ESTIMATIVA_POR_LOOP)


def zerar() -> None:
    _ACUMULADO["tokens"] = 0


def consumir() -> int:
    """Devolve quantos tokens foram gastos desde o último `zerar()` e
    reinicia a contagem. Se a medição real falhou, devolve a estimativa."""
    medido = _ACUMULADO["tokens"]
    zerar()
    if medido > 0:
        return medido
    return ESTIMATIVA_POR_LOOP
