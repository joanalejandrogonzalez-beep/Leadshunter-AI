"""Plantillas gratuitas (sin IA externa). Solo generan texto: tú lo revisas y lo envías personalmente."""

# Frases de gancho: solo se usan si la evidencia observada las respalda.
HOOKS = {
    "Novus Ops": {
        "es": {"no_form": "vi que su web no tiene un formulario o vía directa para cotizar o agendar",
               "no_mobile": "noté que su web no está adaptada a móviles",
               "ops": "por el volumen de proyectos/productos que manejan, imagino que hay procesos repetitivos que consumen tiempo",
               "default": "estuve revisando la presencia digital de {name}"},
        "en": {"no_form": "I noticed your site has no quote or booking form",
               "no_mobile": "I noticed your site isn't mobile-friendly",
               "ops": "given the volume of projects/products you handle, I imagine there are repetitive processes eating up time",
               "default": "I was reviewing {name}'s online presence"},
    },
    "NTO Productions": {
        "es": {"no_video": "vi que sus propiedades/proyectos se presentan sin video profesional en la web",
               "listings": "vi el catálogo de propiedades y proyectos que promocionan",
               "default": "estuve revisando la presencia digital de {name}"},
        "en": {"no_video": "I noticed your listings/projects are shown without professional video on your site",
               "listings": "I saw the portfolio of properties and projects you promote",
               "default": "I was reviewing {name}'s online presence"},
    },
}

BODY = {
    ("Novus Ops", "es"): ("Hola {contact}, soy {sender} de Novus Ops. {hook}. Nos dedicamos a crear software a medida, "
                          "automatizaciones y páginas web para empresas del sector {sector_l}. ¿Te parece si conversamos "
                          "15 minutos esta semana para ver si podemos ayudarles a ahorrar tiempo y captar más clientes?\n\nSaludos,\n{sender}"),
    ("Novus Ops", "en"): ("Hi {contact}, I'm {sender} from Novus Ops. {hook}. We build custom software, automations and "
                          "websites for companies in the {sector_l} sector. Would you be open to a 15-minute chat this week "
                          "to see if we can help you save time and win more clients?\n\nBest,\n{sender}"),
    ("NTO Productions", "es"): ("Hola {contact}, soy {sender} de NTO Productions. {hook}. Producimos videos profesionales "
                                "para apartamentos, villas y proyectos inmobiliarios que ayudan a vender y alquilar más rápido. "
                                "Puedo enviarte ejemplos y proponerte un video piloto para una de sus propiedades. ¿Te interesa?\n\nSaludos,\n{sender}"),
    ("NTO Productions", "en"): ("Hi {contact}, I'm {sender} from NTO Productions. {hook}. We produce professional videos for "
                                "apartments, villas and real-estate projects that help them sell and rent faster. I can send "
                                "examples and propose a pilot video for one of your properties. Interested?\n\nBest,\n{sender}"),
}


def build_message(business, lead, signals, lang="es", sender="[Tu nombre]", contact="equipo de"):
    h = HOOKS[business][lang]
    s = signals or {}
    key = "default"
    if business == "Novus Ops":
        if s and not s.get("has_form") and not s.get("has_quote_cta"):
            key = "no_form"
        elif s and not s.get("has_viewport"):
            key = "no_mobile"
        elif s and (s.get("catalog_mentions", 0) >= 5 or s.get("project_mentions", 0) >= 5):
            key = "ops"
    else:
        if s and not s.get("has_video"):
            key = "no_video"
        elif s and s.get("listing_mentions", 0) >= 5:
            key = "listings"
    hook = h[key].format(name=lead.get("name", "su empresa"))
    hook = hook[0].upper() + hook[1:]
    return BODY[(business, lang)].format(contact=f"{contact} {lead.get('name', '')}".strip() if contact == "equipo de" else contact,
                                         sender=sender, hook=hook, sector_l=(lead.get("sector") or "su").lower())
