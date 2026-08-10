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

# Se por algum motivo a medição real não funcionar (mudança de versão
# do litellm, por exemplo), assumimos este custo por ciclo em vez de
# achar que gastou zero — zero faria o time rodar sem freio nenhum.
# Base: 26.336 tokens medidos no ciclo de produto em 09/08/2026,
# arredondado pra cima com folga.
ESTIMATIVA_POR_LOOP = 30000


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
    """Liga a medição. Chamar uma vez, no início do programa.
    Nunca derruba o processo: se o litellm mudar de API, a gente cai
    na estimativa fixa e segue rodando."""
    if _CALLBACK_REGISTRADO["ok"]:
        return
    try:
        import litellm
        atuais = list(getattr(litellm, "success_callback", []) or [])
        if _callback not in atuais:
            atuais.append(_callback)
        litellm.success_callback = atuais
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
