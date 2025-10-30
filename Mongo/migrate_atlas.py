from pymongo import MongoClient
from datetime import datetime

SOURCE_URI = "SOURCE"
TARGET_URI = "TARGET"

print("=" * 70)
print("🚀 MIGRACIÓN DE DATOS: Docker Local → MongoDB Atlas")
print("=" * 70)

print("\n⚠️  IMPORTANTE:")
print("   1. Reemplaza <PASSWORD> en TARGET_URI con tu contraseña de Atlas")
print("   2. Reemplaza 'capta-tickets-prod.xxxxx' con tu cluster de Atlas")
print("   3. Asegúrate de tener el cluster Atlas creado y configurado")

continuar = input("\n¿Continuar con la migración? (s/n): ")
if continuar.lower() != 's':
    print("❌ Migración cancelada")
    exit()

try:
    print("\n📡 Conectando a MongoDB Local (Docker)...")
    source_client = MongoClient(SOURCE_URI)
    source_db = source_client['capta_tickets']
    
    source_client.server_info()
    print("✅ Conectado a MongoDB Local")
    
except Exception as e:
    print(f"❌ Error conectando a MongoDB Local: {e}")
    exit()

try:
    print("\n☁️  Conectando a MongoDB Atlas...")
    target_client = MongoClient(TARGET_URI)
    target_db = target_client['capta_tickets']
    
    target_client.server_info()
    print("✅ Conectado a MongoDB Atlas")
    
except Exception as e:
    print(f"❌ Error conectando a MongoDB Atlas: {e}")
    print("\n💡 Verifica:")
    print("   - El connection string es correcto")
    print("   - La contraseña está reemplazada")
    print("   - La IP 0.0.0.0/0 está en la whitelist")
    exit()

print("\n" + "=" * 70)
print("📊 ANÁLISIS DE DATOS A MIGRAR")
print("=" * 70)

colecciones = ['tickets', 'classifiers']

for coleccion in colecciones:
    count = source_db[coleccion].count_documents({})
    print(f"\n📁 Colección: {coleccion}")
    print(f"   Documentos: {count}")
    
    if count > 0:
        ejemplo = source_db[coleccion].find_one()
        print(f"   Tamaño ejemplo: ~{len(str(ejemplo))} bytes")

print("\n" + "=" * 70)

confirmar = input("\n¿Proceder con la migración? (s/n): ")
if confirmar.lower() != 's':
    print("❌ Migración cancelada")
    exit()

print("\n" + "=" * 70)
print("🔄 INICIANDO MIGRACIÓN")
print("=" * 70)

for coleccion in colecciones:
    print(f"\n📦 Migrando colección: {coleccion}")
    
    source_count = source_db[coleccion].count_documents({})
    
    if source_count == 0:
        print(f"   ⚠️  Colección vacía, saltando...")
        continue
    
    target_db[coleccion].drop()
    print(f"   🗑️  Colección destino limpiada")
    
    documentos = list(source_db[coleccion].find({}))
    
    if documentos:
        result = target_db[coleccion].insert_many(documentos)
        print(f"   ✅ {len(result.inserted_ids)} documentos migrados")
    
    indices_source = source_db[coleccion].list_indexes()
    
    print(f"   📊 Migrando índices...")
    indices_migrados = 0
    
    for index in indices_source:
        if index['name'] != '_id_':
            try:
                keys = list(index['key'].items())
                opciones = {}
                
                if 'name' in index:
                    opciones['name'] = index['name']
                
                target_db[coleccion].create_index(keys, **opciones)
                indices_migrados += 1
                
            except Exception as e:
                print(f"   ⚠️  Error creando índice {index['name']}: {e}")
    
    print(f"   ✅ {indices_migrados} índices migrados")

print("\n" + "=" * 70)
print("✅ VERIFICACIÓN POST-MIGRACIÓN")
print("=" * 70)

todo_correcto = True

for coleccion in colecciones:
    source_count = source_db[coleccion].count_documents({})
    target_count = target_db[coleccion].count_documents({})
    
    print(f"\n📁 {coleccion}:")
    print(f"   Origen: {source_count} documentos")
    print(f"   Destino: {target_count} documentos")
    
    if source_count == target_count:
        print(f"   ✅ Coinciden")
    else:
        print(f"   ❌ NO COINCIDEN")
        todo_correcto = False

print("\n" + "=" * 70)

if todo_correcto:
    print("✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
    print("\n💡 Próximos pasos:")
    print("   1. Actualiza el MONGO_URI en app.py con el de Atlas")
    print("   2. Despliega en Vercel")
    print("   3. Configura el secret MONGO_URI en Vercel")
else:
    print("⚠️  MIGRACIÓN COMPLETADA CON ADVERTENCIAS")
    print("   Verifica los conteos que no coinciden")

print("\n📝 Connection String para Vercel:")
print(f"   {TARGET_URI}")

print("\n" + "=" * 70)