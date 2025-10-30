use capta_tickets

db.tickets.createIndex({ "createdAt": 1 }, { name: "idx_createdAt" })

db.tickets.createIndex({ "currentState": 1 }, { name: "idx_currentState" })

db.tickets.createIndex({ "closedAt": 1 }, { name: "idx_closedAt" })

db.tickets.createIndex(
  { "currentClassifications.tipo_solicitud": 1 },
  { name: "idx_classification_tipo_solicitud" }
)

db.tickets.createIndex(
  { "createdAt": 1, "currentState": 1 },
  { name: "idx_createdAt_currentState" }
)

db.tickets.createIndex(
  { "createdAt": 1, "closedAt": 1 },
  { name: "idx_createdAt_closedAt" }
)

db.tickets.createIndex(
  { "currentState": 1, "currentClassifications.tipo_solicitud": 1 },
  { name: "idx_currentState_classification" }
)

db.tickets.createIndex(
  { "createdAt": 1, "currentState": 1, "currentClassifications.tipo_solicitud": 1 },
  { name: "idx_complex_filter" }
)

db.tickets.createIndex(
  { "history.timestamp": 1 },
  { name: "idx_history_timestamp" }
)

db.tickets.createIndex(
  { "history.action": 1, "history.timestamp": 1 },
  { name: "idx_history_action_timestamp" }
)

db.tickets.createIndex(
  { "lastModifiedAt": -1 },
  { name: "idx_lastModifiedAt_desc" }
)

db.tickets.createIndex(
  { "assignedTo": 1, "currentState": 1 },
  { name: "idx_assignedTo_currentState" }
)

db.classifiers.createIndex({ "rootId": 1 }, { name: "idx_rootId" })

db.classifiers.createIndex({ "parentId": 1 }, { name: "idx_parentId" })

db.classifiers.createIndex({ "ancestors": 1 }, { name: "idx_ancestors" })

db.classifiers.createIndex({ "path": 1 }, { name: "idx_path" })

db.classifiers.createIndex(
  { "rootId": 1, "level": 1 },
  { name: "idx_rootId_level" }
)

print("\n" + "=".repeat(60))
print("✅ ÍNDICES CREADOS EXITOSAMENTE")
print("=".repeat(60))

print("\n📊 Verificando índices creados...\n")

var ticketIndexes = db.tickets.getIndexes()
print("Colección 'tickets' - " + ticketIndexes.length + " índices:")
ticketIndexes.forEach(function(idx) {
    print("  • " + idx.name + ": " + JSON.stringify(idx.key))
})

var classifierIndexes = db.classifiers.getIndexes()
print("\nColección 'classifiers' - " + classifierIndexes.length + " índices:")
classifierIndexes.forEach(function(idx) {
    print("  • " + idx.name + ": " + JSON.stringify(idx.key))
})

print("\n" + "=".repeat(60))
print("📈 ANÁLISIS DE COBERTURA DE CONSULTAS")
print("=".repeat(60))

print("\n✅ CONSULTA 1: Lista de Casos")
print("   Filtros: rango de fechas + estado + clasificador")
print("   Índice usado: idx_complex_filter")
print("   Performance: O(log n)")

print("\n✅ CONSULTA 2: Cantidad de Reaperturas")
print("   Filtros: ninguno (usa reopenCount desnormalizado)")
print("   Índice usado: ninguno necesario")
print("   Performance: O(n) - scan completo pero rápido")

print("\n✅ CONSULTA 3: Cantidad de Ingresos")
print("   Filtros: rango de fechas + filtros opcionales")
print("   Índice usado: idx_createdAt o idx_createdAt_currentState")
print("   Performance: O(log n)")

print("\n✅ CONSULTA 4: Cantidad de Cierres")
print("   Filtros: history.action + history.timestamp")
print("   Índice usado: idx_history_action_timestamp")
print("   Performance: O(log n * m) donde m = acciones por ticket")

print("\n✅ CONSULTA 5: Lista de Acciones")
print("   Filtros: rango de fechas en history")
print("   Índice usado: idx_history_timestamp")
print("   Performance: O(log n * m)")

print("\n" + "=".repeat(60))
print("💡 RECOMENDACIONES")
print("=".repeat(60))

print("\n1. Monitorear uso de índices:")
print("   db.tickets.find({...}).explain('executionStats')")

print("\n2. Índices compuestos se usan de izquierda a derecha:")
print("   idx_createdAt_currentState sirve para:")
print("     ✓ { createdAt: ... }")
print("     ✓ { createdAt: ..., currentState: ... }")
print("     ✗ { currentState: ... } (no lo usa)")

print("\n3. Tamaño aproximado de índices:")
var stats = db.tickets.stats()
print("   Documentos: " + stats.count)
print("   Tamaño total: " + (stats.size / 1024 / 1024).toFixed(2) + " MB")
print("   Tamaño índices: " + (stats.totalIndexSize / 1024 / 1024).toFixed(2) + " MB")

print("\n4. Si los datos crecen >100K tickets:")
print("   - Considerar particionar por fecha")
print("   - Archivar tickets antiguos")
print("   - Revisar índices no utilizados")

print("\n" + "=".repeat(60))