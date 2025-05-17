import os
import ssl
import winrm

# Deshabilitar verificación de certificado
os.environ['PYTHONHTTPSVERIFY'] = '0'
ssl._create_default_https_context = ssl._create_unverified_context

# Configurar sesión
session = winrm.Session(
    'https://10.104.10.20:5986/wsman',
    auth=('Administrator', 'TU_PASSWORD'),
    transport='ntlm',
    server_cert_validation='ignore'
)

# Ejecutar comando
result = session.run_cmd('whoami')
print(result.std_out)
