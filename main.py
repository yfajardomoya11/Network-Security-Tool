import os
from dotenv import load_dotenv

# 1. CARGAR CONFIGURACIÓN (Siempre al inicio)
load_dotenv()

# 2. ASIGNAR VARIABLES
usuario = os.getenv('NET_USER')
password = os.getenv('NET_PASS')

# 3. LÓGICA DEL PROGRAMA
def conectar_dispositivos():
    # Aquí es donde usarás 'usuario' y 'password'
    # para leer tu archivo dispositivos.txt y conectarte
    print(f"Iniciando sesión con el usuario: {usuario}")
    
    with open("dispositivos.txt", "r") as archivo:
        for linea in archivo:
            ip = linea.strip()
            print(f"Conectando a la IP: {ip}...")

# 4. PUNTO DE ENTRADA
if __name__ == "__main__":
    conectar_dispositivos()
import getpass
import time
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException

def create_backup(connection, hostname):
    """Genera un respaldo de la configuración actual."""
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"backup_{hostname}_{timestamp}.txt"
    config_data = connection.send_command('show running-config')
    with open(filename, "w") as f:
        f.write(config_data)
    return filename

def apply_security_to_all():
    # Pedir credenciales una sola vez para todos los equipos
    username = input("Introduce el usuario SSH: ")
    password = getpass.getpass("Introduce la contraseña SSH: ")
    secret = getpass.getpass("Introduce la contraseña Enable (Privilegiada): ")

    # Comandos de Hardening
    security_commands = [
        'no ip http server',
        'no ip http secure-server',
        'service password-encryption',
        'banner motd ^C ALERTA: Acceso Monitoreado. Propiedad Privada. ^C',
        'line vty 0 4',
        'exec-timeout 5 0',
        'transport input ssh',
        'exit'
    ]

    # Leer las IPs desde el archivo .txt
    try:
        with open("dispositivos.txt", "r") as f:
            ips = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("❌ Error: No se encontró el archivo 'dispositivos.txt'")
        return

    print(f"🔍 Se han detectado {len(ips)} dispositivos para procesar.\n")

    for ip in ips:
        device = {
            'device_type': 'cisco_ios',
            'host': ip,
            'username': username,
            'password': password,
            'secret': secret,
        }

        try:
            print(f"🌐 Conectando a {ip}...")
            connection = ConnectHandler(**device)
            connection.enable()
            
            hostname = connection.find_prompt().replace("#", "").replace(">", "")
            
            # 1. Backup
            backup_file = create_backup(connection, hostname)
            print(f"  ✅ Backup creado: {backup_file}")

            # 2. Hardening
            connection.send_config_set(security_commands)
            print(f"  🛡️  Seguridad aplicada en {hostname}")

            # 3. Guardar
            connection.send_command('write memory')
            print(f"  💾 Configuración guardada en {ip}")
            
            connection.disconnect()
            print("-" * 30)

        except (NetmikoAuthenticationException, NetmikoTimeoutException) as e:
            print(f"⚠️  Error en {ip}: No se pudo conectar o autenticar.")
        except Exception as e:
            print(f"❌ Error inesperado en {ip}: {e}")

    print("\n🚀 Tarea masiva finalizada.")

if __name__ == "__main__":
    apply_security_to_all()