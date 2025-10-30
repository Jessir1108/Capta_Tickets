from pymongo import MongoClient
from datetime import datetime, timedelta
import random
from faker import Faker

fake = Faker(["es_ES"])

MONGO_URI = "mongodb://admin:captaPassword123@localhost:27017/"
client = MongoClient(MONGO_URI)
db = client["capta_tickets"]

ESTADOS = ["open", "in_progress", "closed", "pending", "cancelled"]

CLASIFICADORES = [
    "altos_palmas_torre1",
    "altos_palmas_torre2",
    "altos_palmas_torre3",
    "zonas_comunes",
    "hungria_reservado",
    "mirador_horizonte",
    "senderos_cerro",
]

TIPOS_PROBLEMA = [
    ("Sin suministro de agua", "No hay agua en el apartamento"),
    ("Fuga de agua", "Hay una fuga en {ubicacion}"),
    ("Problema eléctrico", "Se va la luz constantemente"),
    ("Ascensor averiado", "El ascensor no funciona"),
    ("Ruido excesivo", "Vecinos generando ruido"),
    ("Basura acumulada", "No se ha recogido la basura"),
    ("Portón dañado", "El portón principal no cierra"),
    ("Aire acondicionado", "El AC no enfría correctamente"),
    ("Plaga", "Presencia de plagas en el apartamento"),
    ("Pintura deteriorada", "Pintura descascarada en paredes"),
    ("Filtración", "Filtración de agua por el techo"),
    ("Cerradura dañada", "La cerradura de la puerta está rota"),
    ("Vidrio roto", "Ventana con vidrio roto"),
    ("Tubería rota", "Tubería con escape de agua"),
    ("Iluminación", "Luces del pasillo no funcionan"),
]

USUARIOS = [f"user_{i:03d}" for i in range(1, 51)]
AGENTES = [f"agent_{i:03d}" for i in range(1, 11)]
SUPERVISORES = [f"supervisor_{i:03d}" for i in range(1, 4)]


def generar_fecha_aleatoria(inicio, fin):
    delta = fin - inicio
    random_days = random.randint(0, delta.days)
    random_seconds = random.randint(0, 86400)
    return inicio + timedelta(days=random_days, seconds=random_seconds)


def generar_ticket(ticket_id, fecha_base):
    titulo, descripcion_template = random.choice(TIPOS_PROBLEMA)
    ubicaciones = ["baño", "cocina", "sala", "habitación", "balcón"]
    descripcion = descripcion_template.format(ubicacion=random.choice(ubicaciones))

    clasificador = random.choice(CLASIFICADORES)
    usuario = random.choice(USUARIOS)

    fecha_creacion = generar_fecha_aleatoria(
        fecha_base - timedelta(days=90), fecha_base
    )

    history = [
        {
            "action": "created",
            "timestamp": fecha_creacion,
            "userId": usuario,
            "details": {"initialState": "open", "initialClassification": clasificador},
        }
    ]

    estado_actual = "open"
    fecha_ultima_accion = fecha_creacion
    asignado_a = None
    fecha_cierre = None

    probabilidad_progreso = random.random()

    if probabilidad_progreso > 0.3:
        agente = random.choice(AGENTES)
        fecha_asignacion = fecha_ultima_accion + timedelta(hours=random.randint(1, 24))

        history.append(
            {
                "action": "assignment",
                "timestamp": fecha_asignacion,
                "userId": random.choice(SUPERVISORES),
                "assignedTo": agente,
            }
        )

        history.append(
            {
                "action": "state_change",
                "timestamp": fecha_asignacion + timedelta(minutes=5),
                "userId": agente,
                "from": "open",
                "to": "in_progress",
                "comment": "Caso en revisión",
            }
        )

        estado_actual = "in_progress"
        asignado_a = agente
        fecha_ultima_accion = fecha_asignacion

        if random.random() > 0.4:
            dias_resolucion = random.randint(1, 15)
            fecha_cierre = fecha_ultima_accion + timedelta(days=dias_resolucion)

            history.append(
                {
                    "action": "comment",
                    "timestamp": fecha_cierre - timedelta(hours=2),
                    "userId": agente,
                    "comment": "Trabajo completado, esperando verificación",
                }
            )

            history.append(
                {
                    "action": "state_change",
                    "timestamp": fecha_cierre,
                    "userId": agente,
                    "from": "in_progress",
                    "to": "closed",
                    "comment": "Problema resuelto satisfactoriamente",
                }
            )

            estado_actual = "closed"
            fecha_ultima_accion = fecha_cierre

            if random.random() > 0.85:
                dias_reapertura = random.randint(1, 10)
                fecha_reapertura = fecha_cierre + timedelta(days=dias_reapertura)

                history.append(
                    {
                        "action": "state_change",
                        "timestamp": fecha_reapertura,
                        "userId": usuario,
                        "from": "closed",
                        "to": "open",
                        "comment": "El problema persiste o ha vuelto a ocurrir",
                    }
                )

                estado_actual = "open"
                fecha_ultima_accion = fecha_reapertura
                fecha_cierre = None

                if random.random() > 0.5:
                    nuevo_agente = random.choice(AGENTES)
                    fecha_reasignacion = fecha_reapertura + timedelta(
                        hours=random.randint(2, 12)
                    )

                    history.append(
                        {
                            "action": "assignment",
                            "timestamp": fecha_reasignacion,
                            "userId": random.choice(SUPERVISORES),
                            "assignedTo": nuevo_agente,
                        }
                    )

                    history.append(
                        {
                            "action": "state_change",
                            "timestamp": fecha_reasignacion + timedelta(minutes=10),
                            "userId": nuevo_agente,
                            "from": "open",
                            "to": "in_progress",
                            "comment": "Reabierto, investigando causa raíz",
                        }
                    )

                    estado_actual = "in_progress"
                    asignado_a = nuevo_agente

    ticket = {
        "_id": f"ticket_{ticket_id:04d}",
        "title": titulo,
        "description": descripcion,
        "currentState": estado_actual,
        "currentClassifications": {"tipo_solicitud": clasificador},
        "createdAt": fecha_creacion,
        "createdBy": usuario,
        "assignedTo": asignado_a,
        "history": history,
    }

    if fecha_cierre and estado_actual == "closed":
        ticket["closedAt"] = fecha_cierre

    return ticket


def generar_tickets(cantidad=100):
    print(f"Generando {cantidad} tickets...")

    fecha_base = datetime.now()
    tickets = []

    for i in range(1, cantidad + 1):
        ticket = generar_ticket(i, fecha_base)
        tickets.append(ticket)

        if i % 10 == 0:
            print(f"  Generados {i}/{cantidad} tickets...")

    return tickets


def insertar_tickets(tickets):
    print(f"\nInsertando {len(tickets)} tickets en MongoDB...")

    try:
        db.tickets.drop()
        print("  Colección 'tickets' limpiada")

        result = db.tickets.insert_many(tickets)
        print(f"  ✅ {len(result.inserted_ids)} tickets insertados correctamente")

        return True
    except Exception as e:
        print(f"  ❌ Error al insertar tickets: {e}")
        return False


def generar_estadisticas():
    print("\n📊 Estadísticas de los datos generados:")

    total_tickets = db.tickets.count_documents({})
    print(f"  Total de tickets: {total_tickets}")

    por_estado = db.tickets.aggregate(
        [
            {"$group": {"_id": "$currentState", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
    )
    print("\n  Tickets por estado:")
    for item in por_estado:
        print(f"    - {item['_id']}: {item['count']}")

    por_clasificador = db.tickets.aggregate(
        [
            {
                "$group": {
                    "_id": "$currentClassifications.tipo_solicitud",
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"count": -1}},
        ]
    )
    print("\n  Tickets por clasificador:")
    for item in por_clasificador:
        print(f"    - {item['_id']}: {item['count']}")

    pipeline_reaperturas = [
        {"$unwind": "$history"},
        {
            "$match": {
                "history.action": "state_change",
                "history.from": "closed",
                "history.to": {"$ne": "closed"},
            }
        },
        {"$count": "total_reaperturas"},
    ]
    resultado_reaperturas = list(db.tickets.aggregate(pipeline_reaperturas))
    total_reaperturas = (
        resultado_reaperturas[0]["total_reaperturas"] if resultado_reaperturas else 0
    )
    print(f"\n  Total de reaperturas: {total_reaperturas}")

    pipeline_cierres = [
        {"$unwind": "$history"},
        {"$match": {"history.action": "state_change", "history.to": "closed"}},
        {"$count": "total_cierres"},
    ]
    resultado_cierres = list(db.tickets.aggregate(pipeline_cierres))
    total_cierres = resultado_cierres[0]["total_cierres"] if resultado_cierres else 0
    print(f"  Total de cierres: {total_cierres}")


def main():
    print("=" * 60)
    print("🎲 GENERADOR DE DATOS - CAPTA TICKETS")
    print("=" * 60)

    cantidad = int(
        input("\n¿Cuántos tickets quieres generar? (recomendado: 100): ") or "100"
    )

    tickets = generar_tickets(cantidad)

    if insertar_tickets(tickets):
        generar_estadisticas()
        print("\n✅ ¡Proceso completado exitosamente!")
    else:
        print("\n❌ Hubo errores durante el proceso")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
