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
    Class representing a Smart Nest node (NEST).
    
    Manages internal state, weight simulation logic, and user identification 
    through a Finite State Machine (FSM). 
    """
    def __init__(self, token, name):
        """
        Initializes the nest with credentials and default values.

        :param token: ThingsBoard access token for the device. 
        :param name: Identifiable name for logs. 
        """
        self.token = token
        self.name = name
        # Simulation states 
        self.states = ["WAITING_FOR_HEN", "HEN_INSIDE", "EGGS_DEPOSITED", "PERSON_COLLECTING"]
        self.current_state_idx = 0
        self.current_weight = 0.0
        self.current_uid = "None"
        self.telemetry_interval = 10 
        self.door_status = "open"
        self.led_rgb = "off"
        
        # Persistence control for each state in the simulation
        self.state_counter = 0
        self.target_repeats = random.randint(3, 10)

    def update_logic(self):
        """
        Updates the cyclic logic. The farmer UID is sent once, 
        while the hen UID persists while she is inside.
        """
        # 1. Transition logic
        if self.state_counter >= self.target_repeats:
            next_state_idx = (self.current_state_idx + 1) % len(self.states)
            
            if self.door_status.lower() == "closed" and self.states[self.current_state_idx] == "WAITING_FOR_HEN":
                return 
            
            self.current_state_idx = next_state_idx
            self.state_counter = 0 
            self.target_repeats = random.randint(5, 30)
            print(f"[{self.name}] - Transitioning to: {self.states[self.current_state_idx]}")

        self.state_counter += 1
        state = self.states[self.current_state_idx]
        
        # 2. State Initialization (runs on the first tick of every state)
        if self.state_counter == 1:
            if state == "WAITING_FOR_HEN":
                self.current_uid = "None"
                self.current_weight = 0.0
            elif state == "HEN_INSIDE":
                self.current_uid = "9104EE5D" 
                self.current_weight = round(random.uniform(2000, 3500), 2)
            elif state == "EGGS_DEPOSITED":
                self.current_uid = "None"
                self.current_weight = (random.randint(1, 3) * 65)
            elif state == "PERSON_COLLECTING":
                self.current_uid = "11580C5D" # Farmer UID
                self.current_weight = 0.0 
        
        # 3. Specific Reset Logic (runs on every tick AFTER the first one)
        else:
            if state == "PERSON_COLLECTING":
                # Clear the farmer UID after the first transmission
                self.current_uid = "None"

def on_message(client, userdata, msg):
    """
    Callback executed when an MQTT message (Shared Attributes) is received. 
    
    Enables remote control of telemetry frequency, door status, and 
    LED color from the ThingsBoard dashboard. 
    """
    nest = userdata['nest']
    try:
        data = json.loads(msg.payload)
        params = data.get("params", data) # Supports attribute updates 
        
        # Remote door control 
        if "door" in params:
            nest.door_status = params["door"]
            print(f"[{nest.name}] - COMMAND Door: {nest.door_status.upper()}")
        
        # Remote LED color control 
        if "rgb" in params:
            nest.led_rgb = params["rgb"]
            print(f"[{nest.name}] - COMMAND LED Color: {nest.led_rgb.upper()}")
            
        # Remote interval control (in milliseconds)
        if "period" in params:
            nest.telemetry_interval = int(params["period"]) / 1000
            print(f"[{nest.name}] - COMMAND Period: {nest.telemetry_interval}s")
    except Exception as e:
        print(f"[{nest.name}] - Error parsing command: {e}")

def run():
    """
    Main function to start the MQTT client and the simulation loop. 
    """
    if len(sys.argv) < 3:
        print("Usage: python nest_sim.py <token> <name>")
        return

    token = sys.argv[1]
    name = sys.argv[2]
    
    nest = SmartNest(token, name)
    
    # MQTT client configuration using protocol v2 
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, userdata={'nest': nest, 'token': token})
    client.username_pw_set(token)
    
    # TLS security configuration 
    client.tls_set_context(ssl.create_default_context())
    client.on_message = on_message
    
    try:
        # Connection to the IoT server
        client.connect(THINGSBOARD_HOST, PORT, 60)
        # Subscribe to attributes to receive real-time commands
        client.subscribe("v1/devices/me/attributes")
        client.loop_start()
        
        # Initial diagnostic message
        init_payload = {"init": "started"}
        client.publish("v1/devices/me/telemetry", json.dumps(init_payload))
        
        print(f"--- {name} Simulation Started ---")

        # Infinite telemetry loop 
        while True:
            nest.update_logic()
            payload = {
                "temperature": round(random.uniform(5, 20), 2),
                "humidity": round(random.uniform(60, 90), 2),
                "weight": nest.current_weight, 
                "uid": nest.current_uid 
            }
            # Publish data to the standard ThingsBoard telemetry topic 
            client.publish("v1/devices/me/telemetry", json.dumps(payload))
            print(f"[{name}] - T: {payload['temperature']} | H: {payload['humidity']} | W: {payload['weight']}g | UID: {payload['uid']}")
            time.sleep(nest.telemetry_interval)
            
    except KeyboardInterrupt:
        # Clean exit on manual interruption (Ctrl+C)
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    run()