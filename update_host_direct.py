#!/usr/bin/env python
import sqlite3
import sys

def update_host(host_id, field, value):
    """
    Actualiza un campo específico de un host directamente en la base de datos SQLite.
    
    Args:
        host_id (int): ID del host a actualizar
        field (str): Nombre del campo a actualizar
        value (str): Nuevo valor para el campo
    
    Returns:
        bool: True si la actualización fue exitosa, False en caso contrario
    """
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect('/opt/www/db.sqlite3')
        cursor = conn.cursor()
        
        # Construir la consulta SQL
        query = f"UPDATE inventory_host SET {field} = ? WHERE id = ?"
        
        # Ejecutar la consulta
        cursor.execute(query, (value, host_id))
        
        # Confirmar los cambios
        conn.commit()
        
        # Verificar si se actualizó alguna fila
        rows_affected = cursor.rowcount
        
        # Cerrar la conexión
        conn.close()
        
        return rows_affected > 0
    except Exception as e:
        print(f"Error al actualizar el host: {e}")
        return False

def main():
    if len(sys.argv) != 4:
        print("Uso: python update_host_direct.py <host_id> <field> <value>")
        sys.exit(1)
    
    host_id = int(sys.argv[1])
    field = sys.argv[2]
    value = sys.argv[3]
    
    # Validar que el campo sea válido
    valid_fields = [
        'name', 'ip', 'operating_system', 'ansible_python_interpreter',
        'status', 'tags', 'notes'
    ]
    
    if field not in valid_fields:
        print(f"Error: Campo inválido. Campos válidos: {', '.join(valid_fields)}")
        sys.exit(1)
    
    success = update_host(host_id, field, value)
    
    if success:
        print(f"Host {host_id} actualizado exitosamente. Campo '{field}' establecido a '{value}'")
    else:
        print(f"Error al actualizar el host {host_id}")
        sys.exit(1)

if __name__ == "__main__":
    main()
