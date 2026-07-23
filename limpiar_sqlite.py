#!/usr/bin/env python3
"""
Limpia la base de datos SQLite pero conserva:
- Dominio
- Código TXT asociado
- (para que no se generen códigos nuevos a dominios ya registrados)
Ubicación: ~/Estudios/Python/Proyectos/AutoVulnerabilities/limpiar_sqlite.py
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "verificaciones.db")

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Guardar los dominios y códigos existentes (para no perderlos)
    cursor.execute('SELECT DISTINCT dominio, codigo FROM usuarios')
    dominios_codigos = cursor.fetchall()
    
    print(f"📋 Dominios únicos encontrados: {len(dominios_codigos)}")
    
    # 2. Eliminar todos los registros
    cursor.execute('DELETE FROM usuarios')
    
    # 3. Reinsertar solo dominio y código (sin datos personales)
    for dominio, codigo in dominios_codigos:
        cursor.execute('''
            INSERT INTO usuarios (dominio, codigo, email, nombre, apellido, fecha_registro)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (dominio, codigo, f"backup@{dominio}", "Backup", "Auto", datetime.now().isoformat()))
    
    conn.commit()
    
    # Verificar resultados
    cursor.execute('SELECT COUNT(*) FROM usuarios')
    count = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"✅ Limpieza completada")
    print(f"📊 Registros conservados (dominio + código): {count}")
    print(f"💡 Estos registros evitan que se generen nuevos códigos para dominios existentes")
    
except Exception as e:
    print(f"❌ Error en limpieza: {e}")
