#!/usr/bin/env python
import sys
from inventory.update_interpreter import update_python_interpreter

def main():
    if len(sys.argv) != 3:
        print("Uso: python update_host_interpreter.py <host_id> <new_interpreter_path>")
        sys.exit(1)
    
    host_id = int(sys.argv[1])
    new_interpreter_path = sys.argv[2]
    
    success = update_python_interpreter(host_id, new_interpreter_path)
    
    if success:
        print(f"Intérprete de Python actualizado exitosamente para el host {host_id} a {new_interpreter_path}")
    else:
        print(f"Error al actualizar el intérprete de Python para el host {host_id}")
        sys.exit(1)

if __name__ == "__main__":
    main()
