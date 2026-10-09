"""Everything the player reads that is not a sentence built on the fly.

Names follow the Spanish OGame naming used in the research. They are kept in
one place so they can be renamed later without touching the engine.
"""
from __future__ import annotations

import html
from datetime import datetime, timezone

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None  # type: ignore

NAMES: dict[int, str] = {
    1: "Mina de metal", 2: "Mina de cristal", 3: "Sintetizador de deuterio", 4: "Planta de energía solar",
    12: "Planta de fusión", 14: "Fábrica de robots", 15: "Fábrica de nanobots", 21: "Hangar",
    22: "Almacén de metal", 23: "Almacén de cristal", 24: "Contenedor de deuterio", 31: "Laboratorio",
    33: "Terraformador", 34: "Depósito de alianza", 41: "Base lunar", 42: "Sensor phalanx",
    43: "Salto cuántico", 44: "Silo de misiles",
    106: "Espionaje", 108: "Computación", 109: "Militar", 110: "Defensa", 111: "Blindaje", 113: "Energía",
    114: "Hiperespacio", 115: "Motor de combustión", 117: "Motor de impulso", 118: "Propulsor hiperespacial",
    120: "Láser", 121: "Iónica", 122: "Plasma", 123: "Red de investigación intergaláctica",
    124: "Expediciones", 199: "Gravitón",
    202: "Nave pequeña de carga", 203: "Nave grande de carga", 204: "Cazador ligero", 205: "Cazador pesado",
    206: "Crucero", 207: "Nave de batalla", 208: "Colonizador", 209: "Reciclador", 210: "Sonda de espionaje",
    211: "Bombardero", 212: "Satélite solar", 213: "Destructor", 214: "Estrella de la muerte",
    215: "Acorazado",
    401: "Lanzamisiles", 402: "Láser pequeño", 403: "Láser grande", 404: "Cañón gauss", 405: "Cañón iónico",
    406: "Cañón de plasma", 407: "Cúpula pequeña de protección", 408: "Cúpula grande de protección",
    502: "Misil de intercepción", 503: "Misil interplanetario",
}

SHORT: dict[int, str] = {
    202: "P. carga", 203: "G. carga", 204: "C. ligero", 205: "C. pesado", 206: "Crucero", 207: "N. batalla",
    208: "Colonizador", 209: "Reciclador", 210: "Sonda", 211: "Bombardero", 212: "Satélite",
    213: "Destructor", 214: "E. muerte", 215: "Acorazado",
}

DESCRIPTIONS: dict[int, str] = {
    1: "Produce metal, lo más usado.", 2: "Produce cristal.", 3: "Produce deuterio (combustible).",
    4: "Da energía a las minas.", 12: "Da mucha energía, pero gasta deuterio.",
    14: "Construye más rápido los edificios.", 15: "Divide a la mitad los tiempos por nivel.",
    21: "Construye naves y defensas.", 22: "Guarda más metal.", 23: "Guarda más cristal.",
    24: "Guarda más deuterio.", 31: "Permite investigar.", 33: "Agrega 5 campos al planeta.",
    34: "Abastece a las flotas aliadas.", 41: "Agrega 3 campos a la luna.",
    42: "Deja ver flotas cercanas (próximamente).", 43: "Mueve flotas entre lunas (próximamente).",
    44: "Guarda misiles (los misiles llegan en una próxima versión).",
    106: "Informes más completos y menos riesgo al espiar.", 108: "+1 flota en vuelo por nivel.",
    109: "+10 % de ataque por nivel.", 110: "+10 % de escudo por nivel.", 111: "+10 % de casco por nivel.",
    113: "Abre otras tecnologías.", 114: "Abre naves grandes.", 115: "+10 % de velocidad (motor de combustión).",
    117: "+20 % de velocidad (motor de impulso).", 118: "+30 % de velocidad (propulsor hiperespacial).",
    120: "Abre armas láser.", 121: "Abre armas iónicas.", 122: "Abre armas de plasma.",
    123: "Suma laboratorios de otros planetas.", 124: "Abre las expediciones.",
    199: "Abre la Estrella de la muerte. Pide 300.000 de energía.",
}

OFFICER_NAMES: dict[int, str] = {
    601: "Geólogo", 602: "Almirante", 603: "Ingeniero", 604: "Tecnócrata", 605: "Constructor",
    606: "Científico", 607: "Almacenista", 608: "Defensor", 610: "Espía", 611: "Comandante", 613: "General",
}

OFFICER_EFFECTS: dict[int, str] = {
    601: "+5 % de producción por nivel", 602: "+5 % de ataque, escudo y casco por nivel",
    603: "+5 % de energía por nivel", 604: "−5 % de tiempo al construir naves por nivel",
    605: "−10 % de tiempo al construir edificios por nivel", 606: "−10 % de tiempo al investigar por nivel",
    607: "+50 % de almacén por nivel", 608: "−37,5 % de tiempo al construir defensas por nivel",
    610: "+5 niveles de espionaje por nivel", 611: "+3 flotas en vuelo por nivel",
    613: "+25 % de velocidad de las naves por nivel",
}

ATTACK, ACS, TRANSPORT, DEPLOY, HOLD, SPY, COLONIZE, RECYCLE, DESTROY, EXPEDITION = 1, 2, 3, 4, 5, 6, 7, 8, 9, 15

MISSIONS: dict[int, str] = {
    ATTACK: "Atacar", TRANSPORT: "Transportar", DEPLOY: "Desplegar", SPY: "Espiar", COLONIZE: "Colonizar",
    RECYCLE: "Reciclar", EXPEDITION: "Expedición",
}

MISSION_ICONS: dict[int, str] = {
    ATTACK: "⚔️", TRANSPORT: "📦", DEPLOY: "🛬", SPY: "🔭", COLONIZE: "🌱", RECYCLE: "♻️", EXPEDITION: "🌠",
}

RES_ICONS = ("🔩", "💎", "🧪")
RES_NAMES = ("Metal", "Cristal", "Deuterio")


def esc(text: object) -> str:
    return html.escape(str(text), quote=False)


def num(value: float) -> str:
    """1234567 -> 1.234.567"""
    n = int(round(value))
    sign = "-" if n < 0 else ""
    return sign + f"{abs(n):,}".replace(",", ".")


def short_num(value: float) -> str:
    """Compact numbers for buttons: 1.2k, 3.4M."""
    v = abs(value)
    if v >= 1_000_000_000:
        return f"{value / 1e9:.1f}B".replace(".0B", "B")
    if v >= 1_000_000:
        return f"{value / 1e6:.1f}M".replace(".0M", "M")
    if v >= 10_000:
        return f"{value / 1e3:.0f}k"
    return num(value)


def duration(seconds: float) -> str:
    s = max(0, int(round(seconds)))
    days, s = divmod(s, 86_400)
    hours, s = divmod(s, 3600)
    minutes, s = divmod(s, 60)
    if days:
        return f"{days} d {hours} h" if hours else f"{days} d"
    if hours:
        return f"{hours} h {minutes} min" if minutes else f"{hours} h"
    if minutes:
        return f"{minutes} min {s} s" if s and minutes < 10 else f"{minutes} min"
    return f"{s} s"


def clock(ts: float, tz_name: str = "UTC") -> str:
    tz = timezone.utc
    if ZoneInfo is not None and tz_name and tz_name != "UTC":
        try:
            tz = ZoneInfo(tz_name)
        except Exception:  # unknown zone: fall back to UTC
            tz = timezone.utc
    return datetime.fromtimestamp(ts, tz).strftime("%d/%m %H:%M")


def coords(galaxy: int, system: int, position: int, moon: bool = False) -> str:
    return f"[{galaxy}:{system}:{position}]" + (" 🌙" if moon else "")


def cost_line(cost: tuple[float, float, float], energy: float = 0) -> str:
    parts = [f"{RES_ICONS[i]} {num(c)}" for i, c in enumerate(cost) if c]
    if energy:
        parts.append(f"⚡ {num(energy)}")
    return " · ".join(parts) if parts else "gratis"


def units_line(units: dict[int, int], short: bool = False) -> str:
    names = SHORT if short else NAMES
    items = [f"{num(n)} {names.get(eid, NAMES.get(eid, str(eid)))}" for eid, n in units.items() if n > 0]
    return ", ".join(items) if items else "nada"


HELP = """<b>Cómo se juega</b>

Eres el dueño de un planeta. Todo avanza con el tiempo, aunque no estés conectado.

🔩 <b>Recursos.</b> Las minas producen metal, cristal y deuterio cada hora. Necesitan energía: sube la planta solar a la par de las minas.
🏗 <b>Edificios.</b> Un edificio a la vez por planeta. Cada nivel cuesta más y tarda más.
🔬 <b>Investigación.</b> Una a la vez. Vale para todos tus planetas.
🚀 <b>Hangar y defensa.</b> Construye naves para atacar y llevar carga, y defensas para proteger el planeta.
🛰 <b>Flota.</b> Envía naves a otras coordenadas: atacar, espiar, transportar, desplegar, colonizar, reciclar escombros o expediciones.
🌌 <b>Galaxia.</b> Mira tus vecinos. Los marcados (i) llevan 7 días sin entrar y (I) 28 días: son la presa más segura.

⚔️ <b>Farmear.</b> Espía, ataca y te llevas la mitad de los recursos que haya, si te cabe en la bodega. Lo destruido deja escombros que se recogen con recicladores.

🛡 <b>Protección.</b> No puedes atacar a quien tiene 5 veces menos puntos (ni él a ti). Máximo 6 ataques al mismo planeta cada 24 horas. El modo vacaciones te protege, pero detiene tu producción.

🎖 <b>Oficiales.</b> Ganas experiencia de minero al subir minas y almacenes, y de saqueador al atacar. Cada nivel te da un punto para contratar oficiales.

Consejo: gasta tus recursos antes de desconectarte. Lo que se gasta no se puede robar."""
