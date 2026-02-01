import time
import json
import random
import sys
import paho.mqtt.client as mqtt
import ssl

# --- CONFIGURATION ---
THINGSBOARD_HOST = "srv-iot.diatel.upm.es"
PORT = 8883 

class SmartNest:
    """
    Clase que representa un nodo inteligente de nido (NEST).
    
    Gestiona el estado interno, la lógica de simulación de peso y la 
    identificación de usuarios mediante una Máquina de Estados Finatarios (FSM).
    """
    def __init__(self, token, name):
        """
        Inicializa el nido con credenciales y valores por defecto.

        :param token: Token de acceso de ThingsBoard para el dispositivo.
        :param name: Nombre identificativo del nido para logs.
        """
        self.token = token
        self.name = name
        # Estados de la simulación
        self.states = ["WAITING_FOR_HEN", "HEN_INSIDE", "EGGS_DEPOSITED", "PERSON_COLLECTING"]
        self.current_state_idx = 0
        self.current_weight = 0.0
        self.current_uid = "None"
        self.telemetry_interval = 10 
        self.door_status = "open"
        self.led_rgb = "off"
        
        # Control de persistencia en cada estado para la simulación
        self.state_counter = 0
        self.target_repeats = random.randint(5, 20)

    def update_logic(self):
        """
        Actualiza la lógica cíclica del nido.
        
        Controla las transiciones entre estados basándose en contadores aleatorios
        y verifica si la puerta está bloqueada para impedir cambios de estado físicos.
        """
        
        # Lógica de transición: Si se alcanza el tiempo de permanencia aleatorio
        if self.state_counter >= self.target_repeats:
            next_state_idx = (self.current_state_idx + 1) % len(self.states)
            
            # Lógica de bloqueo: Si la puerta está cerrada, la gallina o persona no pueden entrar
            if self.door_status.lower() == "closed" and self.states[self.current_state_idx] == "WAITING_FOR_HEN":
                return # Mantiene el estado actual si la puerta impide el paso
            
            # Realiza la transición de estado
            self.current_state_idx = next_state_idx
            self.state_counter = 0 
            self.target_repeats = random.randint(5, 30)
            print(f"[{self.name}] - Transitioning to: {self.states[self.current_state_idx]}")

        self.state_counter += 1
        
        # Generación de datos sintéticos según el estado actual
        if self.state_counter == 1:
            state = self.states[self.current_state_idx]
            if state == "WAITING_FOR_HEN":
                self.current_uid = "None"
                self.current_weight = 0.0
            elif state == "HEN_INSIDE":
                self.current_uid = "9104EE5D" # UID de ejemplo para una gallina
                self.current_weight = round(random.uniform(2000, 3500), 2)
            elif state == "EGGS_DEPOSITED":
                self.current_uid = "None"
                # Peso proporcional a 1-3 huevos (aprox 65g cada uno)
                self.current_weight = (random.randint(1, 3) * 65)
            elif state == "PERSON_COLLECTING":
                self.current_uid = "11580C5D" # UID de ejemplo para el granjero
                self.current_weight = 0.0

def on_message(client, userdata, msg):
    """
    Callback que se ejecuta cuando se recibe un mensaje MQTT (Atributos Compartidos).
    
    Permite el control remoto de la frecuencia de telemetría, el estado de la puerta
    y el color del LED desde el dashboard de ThingsBoard.
    """
    nest = userdata['nest']
    try:
        data = json.loads(msg.payload)
        params = data.get("params", data) # Soporta tanto actualizaciones de atributos como RPC
        
        # Control remoto de la puerta
        if "door" in params:
            nest.door_status = params["door"]
            print(f"[{nest.name}] - COMMAND Door: {nest.door_status.upper()}")
        
        # Control remoto del color del LED
        if "rgb" in params:
            nest.led_rgb = params["rgb"]
            print(f"[{nest.name}] - COMMAND LED Color: {nest.led_rgb.upper()}")
            
        # Control remoto del intervalo de envío (en milisegundos)
        if "period" in params:
            nest.telemetry_interval = int(params["period"]) / 1000
            print(f"[{nest.name}] - COMMAND Period: {nest.telemetry_interval}s")
    except Exception as e:
        print(f"[{nest.name}] - Error parsing command: {e}")

def run():
    """
    Función principal para arrancar el cliente MQTT y el bucle de simulación.
    """
    if len(sys.argv) < 3:
        print("Usage: python nest_sim.py <token> <name>")
        return

    token = sys.argv[1]
    name = sys.argv[2]
    
    nest = SmartNest(token, name)
    
    # Configuración del cliente MQTT con protocolo v2
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, userdata={'nest': nest, 'token': token})
    client.username_pw_set(token)
    
    # Configuración de seguridad TLS
    client.tls_set_context(ssl.create_default_context())
    client.on_message = on_message
    
    try:
        # Conexión al servidor IoT
        client.connect(THINGSBOARD_HOST, PORT, 60)
        # Suscripción a atributos para recibir comandos en tiempo real
        client.subscribe("v1/devices/me/attributes")
        client.loop_start()
        
        # Mensaje inicial de diagnóstico
        init_payload = {"init": "started"}
        client.publish("v1/devices/me/telemetry", json.dumps(init_payload))
        
        print(f"--- {name} Simulation Started ---")

        # Bucle infinito de envío de telemetría
        while True:
            nest.update_logic()
            payload = {
                "temperature": round(random.uniform(21, 24), 2),
                "humidity": round(random.uniform(40, 60), 2),
                "weight": nest.current_weight,
                "uid": nest.current_uid
            }
            # Publicación de datos en el tópico estándar de ThingsBoard
            client.publish("v1/devices/me/telemetry", json.dumps(payload))
            print(f"[{name}] - T: {payload['temperature']} | H: {payload['humidity']} | W: {payload['weight']}g | UID: {payload['uid']}")
            time.sleep(nest.telemetry_interval)
            
    except KeyboardInterrupt:
        # Cierre limpio en caso de interrupción manual (Ctrl+C)
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    run()