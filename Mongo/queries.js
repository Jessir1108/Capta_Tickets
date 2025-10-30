use capta_tickets

print("\n" + "=".repeat(80))
print("🔍 CONSULTAS PRINCIPALES - SISTEMA CAPTA TICKETS")
print("=".repeat(80))

const startDate = new Date("2025-09-01T00:00:00Z")
const endDate = new Date("2025-10-28T00:00:00Z")
const estadoFiltro = "open"
const clasificadorFiltro = "altos_palmas_torre1"

print("\n📅 PARÁMETROS DE PRUEBA:")
print(`   Fecha inicio: ${startDate.toISOString()}`)
print(`   Fecha fin: ${endDate.toISOString()}`)
print(`   Estado filtro: ${estadoFiltro}`)
print(`   Clasificador filtro: ${clasificadorFiltro}`)

print("\n" + "=".repeat(80))
print("CONSULTA 1: LISTA DE CASOS")
print("=".repeat(80))

print("\n📖 SEMÁNTICA:")
print("   Retorna tickets que cumplan TODOS los filtros aplicables:")
print("   - Estuvieron ACTIVOS (no cerrados) durante [startDate, endDate)")
print("   - Tienen el estado especificado al final del período (endDate)")
print("   - Están clasificados en el nodo especificado o sus descendientes")

print("\n🔧 IMPLEMENTACIÓN:")

function getDescendantClassifiers(nodeId) {
    const node = db.classifiers.findOne({ _id: nodeId })
    if (!node) return [nodeId]

    const descendants = db.classifiers.find({
        ancestors: nodeId
    }).toArray().map(c => c._id)

    return [nodeId, ...descendants]
}

function getStateAtEndDate(ticket, endDate) {
    const history = ticket.history || []

    for (let i = history.length - 1; i >= 0; i--) {
        const action = history[i]
        if (action.action === 'state_change' && action.timestamp < endDate) {
            return action.to
        }
    }

    return ticket.history[0]?.details?.initialState || ticket.currentState
}

const descendientes = getDescendantClassifiers(clasificadorFiltro)
print(`\n   Nodos incluidos en filtro jerárquico: ${JSON.stringify(descendientes)}`)

const pipeline1 = [
    {
        $match: {
            createdAt: { $lt: endDate },
            $or: [
                { closedAt: { $exists: false } },
                { closedAt: { $gte: startDate } }
            ],
            "currentClassifications.tipo_solicitud": { $in: descendientes }
        }
    },
    {
        $project: {
            _id: 1,
            title: 1,
            currentState: 1,
            currentClassifications: 1,
            createdAt: 1,
            closedAt: 1,
            history: 1
        }
    }
]

let resultadosQ1 = db.tickets.aggregate(pipeline1).toArray()

resultadosQ1 = resultadosQ1.filter(ticket => {
    const stateAtEnd = getStateAtEndDate(ticket, endDate)
    return stateAtEnd === estadoFiltro
})

print(`\n✅ RESULTADO: ${resultadosQ1.length} tickets encontrados`)

print("\n📋 Primeros 3 tickets:")
resultadosQ1.slice(0, 3).forEach((ticket, idx) => {
    const stateAtEnd = getStateAtEndDate(ticket, endDate)
    print(`\n   ${idx + 1}. ID: ${ticket._id}`)
    print(`      Título: ${ticket.title}`)
    print(`      Estado actual: ${ticket.currentState}`)
    print(`      Estado al ${endDate.toISOString().split('T')[0]}: ${stateAtEnd}`)
    print(`      Clasificación: ${ticket.currentClassifications.tipo_solicitud}`)
    print(`      Creado: ${ticket.createdAt.toISOString().split('T')[0]}`)
})

print("\n" + "=".repeat(80))
print("CONSULTA 2: CANTIDAD DE REAPERTURAS")
print("=".repeat(80))

print("\n📖 SEMÁNTICA:")
print("   Cuenta el TOTAL de reaperturas en el sistema")
print("   Una reapertura = transición de 'closed' a cualquier estado activo")
print("   Un ticket puede tener múltiples reaperturas")

print("\n🔧 IMPLEMENTACIÓN:")
print("   Método 1: Usando campo desnormalizado 'reopenCount'")

const pipeline2a = [
    {
        $group: {
            _id: null,
            totalReaperturas: { $sum: "$reopenCount" }
        }
    }
]

const resultado2a = db.tickets.aggregate(pipeline2a).toArray()
const totalReaperturas = resultado2a[0]?.totalReaperturas || 0

print(`\n✅ RESULTADO (Método 1 - Desnormalizado): ${totalReaperturas} reaperturas`)

print("\n   Método 2: Calculando desde el histórico (para verificación)")

const pipeline2b = [
    { $unwind: "$history" },
    {
        $match: {
            "history.action": "state_change",
            "history.from": "closed",
            "history.to": { $ne: "closed" }
        }
    },
    { $count: "totalReaperturas" }
]

const resultado2b = db.tickets.aggregate(pipeline2b).toArray()
const totalReaperturasVerificado = resultado2b[0]?.totalReaperturas || 0

print(`\n✅ RESULTADO (Método 2 - Histórico): ${totalReaperturasVerificado} reaperturas`)

if (totalReaperturas === totalReaperturasVerificado) {
    print("\n   ✓ Ambos métodos coinciden (datos consistentes)")
} else {
    print("\n   ⚠ Los métodos NO coinciden (revisar consistencia)")
}

const ticketsConReaperturas = db.tickets.countDocuments({ reopenCount: { $gt: 0 } })
print(`\n   📊 Tickets con al menos 1 reapertura: ${ticketsConReaperturas}`)

const maxReaperturas = db.tickets.findOne({}, { sort: { reopenCount: -1 } })
print(`   📊 Máximo de reaperturas en un ticket: ${maxReaperturas?.reopenCount || 0}`)

print("\n" + "=".repeat(80))
print("CONSULTA 3: CANTIDAD DE INGRESOS")
print("=".repeat(80))

print("\n📖 SEMÁNTICA:")
print("   Cuenta tickets CREADOS durante [startDate, endDate)")
print("   Es el número de tickets nuevos que entraron al sistema en ese período")

print("\n🔧 IMPLEMENTACIÓN:")

const matchQ3 = {
    createdAt: {
        $gte: startDate,
        $lt: endDate
    }
}

if (estadoFiltro) {
    matchQ3.currentState = estadoFiltro
}

if (clasificadorFiltro) {
    const descendientesQ3 = getDescendantClassifiers(clasificadorFiltro)
    matchQ3["currentClassifications.tipo_solicitud"] = { $in: descendientesQ3 }
}

const totalIngresos = db.tickets.countDocuments(matchQ3)

print(`\n✅ RESULTADO: ${totalIngresos} tickets creados en el período`)

const ejemplosIngresos = db.tickets.find(
    { createdAt: { $gte: startDate, $lt: endDate } }
).sort({ createdAt: 1 }).limit(3).toArray()

print("\n📋 Primeros 3 tickets creados:")
ejemplosIngresos.forEach((ticket, idx) => {
    print(`\n   ${idx + 1}. ID: ${ticket._id}`)
    print(`      Título: ${ticket.title}`)
    print(`      Fecha creación: ${ticket.createdAt.toISOString()}`)
    print(`      Estado actual: ${ticket.currentState}`)
})

print("\n" + "=".repeat(80))
print("CONSULTA 4: CANTIDAD DE CIERRES")
print("=".repeat(80))

print("\n📖 SEMÁNTICA:")
print("   Cuenta TRANSICIONES hacia estado 'closed' durante [startDate, endDate)")
print("   Un ticket puede tener múltiples cierres si fue reabierto")
print("   Solo cuenta cierres que ocurrieron dentro del período especificado")

print("\n🔧 IMPLEMENTACIÓN:")

const pipeline4 = [
    { $unwind: "$history" },
    {
        $match: {
            "history.action": "state_change",
            "history.to": "closed",
            "history.timestamp": {
                $gte: startDate,
                $lt: endDate
            }
        }
    },
    { $count: "totalCierres" }
]

const resultado4 = db.tickets.aggregate(pipeline4).toArray()
const totalCierres = resultado4[0]?.totalCierres || 0

print(`\n✅ RESULTADO: ${totalCierres} cierres en el período`)

const pipeline4detalle = [
    { $unwind: "$history" },
    {
        $match: {
            "history.action": "state_change",
            "history.to": "closed",
            "history.timestamp": {
                $gte: startDate,
                $lt: endDate
            }
        }
    },
    {
        $project: {
            _id: 1,
            title: 1,
            "history.timestamp": 1,
            "history.from": 1,
            "history.comment": 1
        }
    },
    { $limit: 3 }
]

const ejemplosCierres = db.tickets.aggregate(pipeline4detalle).toArray()

print("\n📋 Primeros 3 cierres:")
ejemplosCierres.forEach((item, idx) => {
    print(`\n   ${idx + 1}. Ticket: ${item._id} - ${item.title}`)
    print(`      Fecha cierre: ${item.history.timestamp.toISOString()}`)
    print(`      Estado anterior: ${item.history.from}`)
    if (item.history.comment) {
        print(`      Comentario: ${item.history.comment}`)
    }
})

const ticketsCerrados = db.tickets.countDocuments({
    closedAt: {
        $gte: startDate,
        $lt: endDate
    }
})
print(`\n   📊 Tickets actualmente cerrados que se cerraron en el período: ${ticketsCerrados}`)

print("\n" + "=".repeat(80))
print("CONSULTA 5: LISTA DE ACCIONES")
print("=".repeat(80))

print("\n📖 SEMÁNTICA:")
print("   Retorna todas las acciones del histórico que ocurrieron durante [startDate, endDate)")
print("   Incluye: cambios de estado, comentarios, asignaciones, etc.")
print("   Las acciones pueden ser de cualquier ticket que cumpla los filtros base")

print("\n🔧 IMPLEMENTACIÓN:")

const pipeline5 = [
    {
        $match: {
            "history.timestamp": {
                $gte: startDate,
                $lt: endDate
            }
        }
    },
    { $unwind: "$history" },
    {
        $match: {
            "history.timestamp": {
                $gte: startDate,
                $lt: endDate
            }
        }
    },
    {
        $project: {
            ticketId: "$_id",
            ticketTitle: "$title",
            action: "$history.action",
            timestamp: "$history.timestamp",
            userId: "$history.userId",
            from: "$history.from",
            to: "$history.to",
            comment: "$history.comment",
            assignedTo: "$history.assignedTo"
        }
    },
    { $sort: { timestamp: -1 } },
    { $limit: 50 }
]

const acciones = db.tickets.aggregate(pipeline5).toArray()

print(`\n✅ RESULTADO: ${acciones.length} acciones encontradas (mostrando últimas 50)`)

const accionesPorTipo = {}
acciones.forEach(a => {
    accionesPorTipo[a.action] = (accionesPorTipo[a.action] || 0) + 1
})

print("\n📊 Distribución por tipo de acción:")
Object.entries(accionesPorTipo).forEach(([tipo, count]) => {
    print(`   • ${tipo}: ${count}`)
})

print("\n📋 Últimas 5 acciones:")
acciones.slice(0, 5).forEach((accion, idx) => {
    print(`\n   ${idx + 1}. ${accion.action.toUpperCase()}`)
    print(`      Ticket: ${accion.ticketId} - ${accion.ticketTitle}`)
    print(`      Fecha: ${accion.timestamp.toISOString()}`)
    print(`      Usuario: ${accion.userId}`)

    if (accion.action === 'state_change') {
        print(`      Cambio: ${accion.from} → ${accion.to}`)
    }

    if (accion.action === 'assignment') {
        print(`      Asignado a: ${accion.assignedTo}`)
    }

    if (accion.comment) {
        print(`      Comentario: ${accion.comment}`)
    }
})

print("\n" + "=".repeat(80))
print("📊 RESUMEN EJECUTIVO")
print("=".repeat(80))

const totalTickets = db.tickets.countDocuments({})
const ticketsAbiertos = db.tickets.countDocuments({ currentState: "open" })
const ticketsEnProgreso = db.tickets.countDocuments({ currentState: "in_progress" })
const ticketsActualmenteCerrados = db.tickets.countDocuments({ currentState: "closed" })

print(`\n🎫 TICKETS:`)
print(`   Total en sistema: ${totalTickets}`)
print(`   Abiertos: ${ticketsAbiertos} (${(ticketsAbiertos / totalTickets * 100).toFixed(1)}%)`)
print(`   En progreso: ${ticketsEnProgreso} (${(ticketsEnProgreso / totalTickets * 100).toFixed(1)}%)`)
print(`   Cerrados: ${ticketsActualmenteCerrados} (${(ticketsActualmenteCerrados / totalTickets * 100).toFixed(1)}%)`)

print(`\n📊 MÉTRICAS DEL PERÍODO:`)
print(`   Ingresos: ${totalIngresos} tickets`)
print(`   Cierres: ${totalCierres} transiciones`)
print(`   Reaperturas: ${totalReaperturas} transiciones`)
print(`   Acciones registradas: ${acciones.length}`)

const tasaReapertura = ticketsCerrados > 0 ? (totalReaperturas / ticketsCerrados * 100) : 0
print(`\n📈 INDICADORES:`)
print(`   Tasa de reapertura: ${tasaReapertura.toFixed(1)}%`)
print(`   Tickets con reaperturas: ${ticketsConReaperturas}`)

print("\n" + "=".repeat(80))
print("✅ TODAS LAS CONSULTAS COMPLETADAS EXITOSAMENTE")
print("=".repeat(80) + "\n")