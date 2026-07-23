#!/usr/bin/env python3
"""
Exporta la base de datos SQLite a CSV
Ubicación: ~/Estudios/Python/Proyectos/AutoVulnerabilities/exportar_csv.py
"""

import sqlite3
import csv
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "verificaciones.db")
CSV_DIR = os.path.join(os.path.dirname(__file__), "backups")

# Crear directorio de backups si no existe
os.makedirs(CSV_DIR, exist_ok=True)

# Nombre del archivo con timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_file = os.path.join(CSV_DIR, f"export_usuarios_{timestamp}.csv")

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Exportar todos los usuarios
    cursor.execute('''
        SELECT id, email, nombre, apellido, dominio, codigo, 
               fecha_registro, verificado, pagado, fecha_verificacion, fecha_pago 
        FROM usuarios
    ''')
    
    rows = cursor.fetchall()
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'email', 'nombre', 'apellido', 'dominio', 'codigo', 
                        'fecha_registro', 'verificado', 'pagado', 'fecha_verificacion', 'fecha_pago'])
        writer.writerows(rows)
    
    conn.close()
    
    print(f"✅ Exportación completada: {csv_file}")
    print(f"📊 Total registros exportados: {len(rows)}")
    
except Exception as e:
    print(f"❌ Error en exportación: {e}")
