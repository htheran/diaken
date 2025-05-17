import os
import ssl
import winrm

# Deshabilitar verificación SSL
os.environ['PYTHONHTTPSVERIFY'] = '0'
ssl._create_default_https_context = ssl._create_unverified_context

# Configurar sesión
try:
    session = winrm.Session(
        'https://10.104.10.20:5986/wsman',
        auth=('Administrator', 'Windows2022'),
        transport='ntlm',
        server_cert_validation='ignore'
    )
    result = session.run_cmd('whoami')
    print("Conexión exitosa!")
    print("Salida:", result.std_out.decode('utf-8'))
except Exception as e:
    print("Error en la conexión:", str(e))
