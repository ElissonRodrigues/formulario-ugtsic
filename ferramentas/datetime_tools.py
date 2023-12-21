
from datetime import timedelta

def formatar_tempo(tempo: timedelta):
    dias = tempo.days
    anos, dias = divmod(dias, 365)
    meses, dias = divmod(dias, 30)
    horas, resto = divmod(tempo.seconds, 3600)
    minutos, segundos = divmod(resto, 60)
    partes = []
    if anos:
        partes.append(f"{anos} ano" + ("s" if anos > 1 else ""))
    if meses:
        partes.append(f"{meses} mês" + ("es" if meses > 1 else ""))
    if dias:
        partes.append(f"{dias} dia" + ("s" if dias > 1 else ""))
    partes.append(f"{horas:02}:{minutos:02}:{segundos:02}")
    return ", ".join(partes)
