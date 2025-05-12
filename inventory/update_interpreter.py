import sqlite3

def update_python_interpreter(host_id, new_interpreter_path):
    """
    Actualiza directamente el intérprete de Python para un host específico en la base de datos.
    
    Args:
        host_id (int): ID del host a actualizar
        new_interpreter_path (str): Nueva ruta al intérprete de Python
    
    Returns:
        bool: True si la actualización fue exitosa, False en caso contrario
    """
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect('/opt/www/db.sqlite3')
        cursor = conn.cursor()
        
        # Actualizar el intérprete de Python
        cursor.execute(
            "UPDATE inventory_host SET ansible_python_interpreter = ? WHERE id = ?",
            (new_interpreter_path, host_id)
        )
        
        # Confirmar los cambios
        conn.commit()
        
        # Cerrar la conexión
        conn.close()
        
        return True
    except Exception as e:
        print(f"Error al actualizar el intérprete de Python: {e}")
        return False
