from pymongo import MongoClient
from datetime import datetime

MONGO_URI = "mongodb://admin:captaPassword123@localhost:27017/"
client = MongoClient(MONGO_URI)
db = client["capta_tickets"]


def calcular_reaperturas(history):
    count = 0
    for action in history:
        if (
            action.get("action") == "state_change"
            and action.get("from") == "closed"
            and action.get("to") != "closed"
        ):
            count += 1
    return count


def calcular_cambios_estado(history):
    count = 0
    for action in history:
        if action.get("action") == "state_change":
            count += 1
    return count


def calcular_comentarios(history):
    count = 0
    for action in history:
        if action.get("action") == "comment":
            count += 1
    return count


def obtener_fecha_cierre(history, current_state):
    if current_state != "closed":
        return None

    for action in reversed(history):
        if action.get("action") == "state_change" and action.get("to") == "closed":
            return action.get("timestamp")

    return None


def obtener_ultimo_cambio_estado(history):
    for action in reversed(history):
        if action.get("action") == "state_change":
            return action.get("timestamp")

    return None


def obtener_ultima_modificacion(history):
    if history:
        return history[-1].get("timestamp")
    return None


def actualizar_ticket(ticket):
    ticket_id = ticket["_id"]
    history = ticket.get("history", [])
    current_state = ticket.get("currentState")

    reopen_count = calcular_reaperturas(history)
    state_change_count = calcular_cambios_estado(history)
    comment_count = calcular_comentarios(history)
    closed_at = obtener_fecha_cierre(history, current_state)
    last_state_change_at = obtener_ultimo_cambio_estado(history)
    last_modified_at = obtener_ultima_modificacion(history)

    update_fields = {
        "reopenCount": reopen_count,
        "stateChangeCount": state_change_count,
        "commentCount": comment_count,
        "lastModifiedAt": last_modified_at or ticket.get("createdAt"),
    }

    if closed_at:
        update_fields["closedAt"] = closed_at

    if last_state_change_at:
        update_fields["lastStateChangeAt"] = last_state_change_at

    result = db.tickets.update_one({"_id": ticket_id}, {"$set": update_fields})

    return result.modified_count > 0


def actualizar_todos_los_tickets():
    print("=" * 60)
    print("🔄 ACTUALIZANDO TICKETS CON CAMPOS DESNORMALIZADOS")
    print("=" * 60)

    tickets = list(db.tickets.find({}))
    total_tickets = len(tickets)

    print(f"\n📊 Encontrados {total_tickets} tickets para actualizar")
    print("\nProcesando...")

    actualizados = 0
    errores = 0

    for i, ticket in enumerate(tickets, 1):
        try:
            if actualizar_ticket(ticket):
                actualizados += 1

            if i % 10 == 0:
                print(f"  Procesados {i}/{total_tickets} tickets...")
        except Exception as e:
            errores += 1
            print(f"  ❌ Error en ticket {ticket['_id']}: {e}")

    print("\n" + "=" * 60)
    print("✅ PROCESO COMPLETADO")
    print("=" * 60)
    print(f"\nTotal procesados: {total_tickets}")
    print(f"Actualizados exitosamente: {actualizados}")
    print(f"Errores: {errores}")

    generar_estadisticas()


def generar_estadisticas():
    print("\n" + "=" * 60)
    print("📊 ESTADÍSTICAS DE LOS CAMPOS AGREGADOS")
    print("=" * 60)

    pipeline_reaperturas = [
        {
            "$group": {
                "_id": None,
                "totalReaperturas": {"$sum": "$reopenCount"},
                "ticketsConReaperturas": {
                    "$sum": {"$cond": [{"$gt": ["$reopenCount", 0]}, 1, 0]}
                },
                "maxReaperturas": {"$max": "$reopenCount"},
            }
        }
    ]

    resultado = list(db.tickets.aggregate(pipeline_reaperturas))
    if resultado:
        stats = resultado[0]
        print(f"\n🔄 Reaperturas:")
        print(f"  Total de reaperturas: {stats.get('totalReaperturas', 0)}")
        print(f"  Tickets con reaperturas: {stats.get('ticketsConReaperturas', 0)}")
        print(f"  Máximo de reaperturas en un ticket: {stats.get('maxReaperturas', 0)}")

    tickets_cerrados = db.tickets.count_documents({"currentState": "closed"})
    tickets_con_fecha_cierre = db.tickets.count_documents(
        {"closedAt": {"$exists": True}}
    )
    print(f"\n📅 Fechas de cierre:")
    print(f"  Tickets cerrados: {tickets_cerrados}")
    print(f"  Tickets con closedAt: {tickets_con_fecha_cierre}")

    pipeline_comentarios = [
        {
            "$group": {
                "_id": None,
                "totalComentarios": {"$sum": "$commentCount"},
                "promedioComentarios": {"$avg": "$commentCount"},
                "maxComentarios": {"$max": "$commentCount"},
            }
        }
    ]

    resultado = list(db.tickets.aggregate(pipeline_comentarios))
    if resultado:
        stats = resultado[0]
        print(f"\n💬 Comentarios:")
        print(f"  Total de comentarios: {stats.get('totalComentarios', 0)}")
        print(f"  Promedio por ticket: {stats.get('promedioComentarios', 0):.2f}")
        print(f"  Máximo en un ticket: {stats.get('maxComentarios', 0)}")

    pipeline_cambios = [
        {
            "$group": {
                "_id": None,
                "totalCambios": {"$sum": "$stateChangeCount"},
                "promedioCambios": {"$avg": "$stateChangeCount"},
                "maxCambios": {"$max": "$stateChangeCount"},
            }
        }
    ]

    resultado = list(db.tickets.aggregate(pipeline_cambios))
    if resultado:
        stats = resultado[0]
        print(f"\n🔄 Cambios de estado:")
        print(f"  Total de cambios: {stats.get('totalCambios', 0)}")
        print(f"  Promedio por ticket: {stats.get('promedioCambios', 0):.2f}")
        print(f"  Máximo en un ticket: {stats.get('maxCambios', 0)}")

    print("\n" + "=" * 60)
    print("📋 EJEMPLO DE TICKET ACTUALIZADO")
    print("=" * 60)

    ticket_ejemplo = db.tickets.find_one({"reopenCount": {"$gt": 0}})
    if not ticket_ejemplo:
        ticket_ejemplo = db.tickets.find_one()

    if ticket_ejemplo:
        print(f"\n🎫 Ticket ID: {ticket_ejemplo['_id']}")
        print(f"  Título: {ticket_ejemplo.get('title', 'N/A')}")
        print(f"  Estado actual: {ticket_ejemplo.get('currentState', 'N/A')}")
        print(f"  Fecha creación: {ticket_ejemplo.get('createdAt', 'N/A')}")
        print(f"  Última modificación: {ticket_ejemplo.get('lastModifiedAt', 'N/A')}")

        if ticket_ejemplo.get("closedAt"):
            print(f"  Fecha cierre: {ticket_ejemplo.get('closedAt')}")

        print(f"\n  📊 Métricas:")
        print(f"    Reaperturas: {ticket_ejemplo.get('reopenCount', 0)}")
        print(f"    Cambios de estado: {ticket_ejemplo.get('stateChangeCount', 0)}")
        print(f"    Comentarios: {ticket_ejemplo.get('commentCount', 0)}")

        print(f"\n  📜 Histórico ({len(ticket_ejemplo.get('history', []))} acciones):")
        for i, action in enumerate(ticket_ejemplo.get("history", [])[:5], 1):
            print(f"    {i}. {action.get('action')} - {action.get('timestamp')}")
        if len(ticket_ejemplo.get("history", [])) > 5:
            print(
                f"    ... y {len(ticket_ejemplo.get('history', [])) - 5} acciones más"
            )


def verificar_campos_existentes():
    print("\n🔍 Verificando si los campos ya existen...")

    sample = db.tickets.find_one({})
    if not sample:
        print("  ⚠️  No hay tickets en la base de datos")
        return False

    campos_nuevos = [
        "reopenCount",
        "stateChangeCount",
        "commentCount",
        "lastModifiedAt",
    ]
    campos_existentes = [campo for campo in campos_nuevos if campo in sample]

    if campos_existentes:
        print(f"  ⚠️  Algunos campos ya existen: {', '.join(campos_existentes)}")
        respuesta = input("\n¿Deseas recalcular y sobrescribir estos campos? (s/n): ")
        return respuesta.lower() == "s"
    else:
        print("  ✅ Los campos no existen, procediendo con la actualización...")
        return True


def main():
    print("\n" + "=" * 60)
    print("🚀 SCRIPT DE ACTUALIZACIÓN DE TICKETS")
    print("=" * 60)
    print("\nEste script agregará los siguientes campos a cada ticket:")
    print("  • reopenCount: Contador de reaperturas")
    print("  • stateChangeCount: Total de cambios de estado")
    print("  • commentCount: Total de comentarios")
    print("  • closedAt: Fecha de cierre (si aplica)")
    print("  • lastStateChangeAt: Fecha del último cambio de estado")
    print("  • lastModifiedAt: Fecha de última modificación")

    if not verificar_campos_existentes():
        print("\n❌ Operación cancelada por el usuario")
        return

    actualizar_todos_los_tickets()

    print("\n✅ Script completado exitosamente")
    print("\n💡 Ahora tus tickets tienen todos los campos necesarios")
    print("   para consultas optimizadas!")


if __name__ == "__main__":
    main()
