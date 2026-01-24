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
    def __init__(self, token, name):
        self.token = token
        self.name = name
        self.states = ["WAITING_FOR_HEN", "HEN_INSIDE", "EGGS_DEPOSITED", "PERSON_COLLECTING"]
        self.current_state_idx = 0
        self.current_weight = 0.0
        self.current_uid = "None"
        self.telemetry_interval = 10 
        self.door_status = "open"
        self.led_rgb = "off"
        
        self.state_counter = 0
        self.target_repeats = random.randint(5, 30)

    def update_logic(self):
        """Cyclic logic with door blocking and random persistence"""
        
        # LOGIC: Check if we are trying to transition into the "HEN_INSIDE" state
        # current_state_idx 0 is WAITING, 1 is HEN_INSIDE. 
        # If we reached the target repeats and the next state is HEN_INSIDE, check the door.
        if self.state_counter >= self.target_repeats:
            next_state_idx = (self.current_state_idx + 1) % len(self.states)
            
            # BLOCKING LOGIC: If door is closed, we cannot move to HEN_INSIDE or PERSON_COLLECTING
            # (Assuming the person also needs the door open to reach the eggs)
            if self.door_status.lower() == "closed" and next_state_idx in [1, 3]:
                return # Stay in current state, don't reset counter, don't transition
            
            # If door is open (or state doesn't require open door), transition:
            self.current_state_idx = next_state_idx
            self.state_counter = 0 
            self.target_repeats = random.randint(5, 30)
            print(f"[{self.name}] - Transitioning to: {self.states[self.current_state_idx]}")

        self.state_counter += 1
        
        # State Data Generation
        if self.state_counter == 1:
            state = self.states[self.current_state_idx]
            if state == "WAITING_FOR_HEN":
                self.current_uid = "None"
                self.current_weight = 0.0
            elif state == "HEN_INSIDE":
                self.current_uid = "9104EE5D"
                self.current_weight = round(random.uniform(2000, 3500), 2)
            elif state == "EGGS_DEPOSITED": # Fixed name to match self.states
                self.current_uid = "None"
                self.current_weight = (random.randint(1, 3) * 65)
            elif state == "PERSON_COLLECTING":
                self.current_uid = "11580C5D"
                self.current_weight = 0.0

def on_message(client, userdata, msg):
    nest = userdata['nest']
    token = userdata['token'] # Fixed KeyError
    try:
        data = json.loads(msg.payload)
        params = data.get("params", data)
        if "door" in params:
            nest.door_status = params["door"]
            print(f"[{nest.name}] - COMMAND Door: {nest.door_status.upper()}")
        if "rgb" in params:
            nest.led_rgb = params["rgb"]
            print(f"[{nest.name}] - COMMAND LED Color: {nest.led_rgb.upper()}")
        if "period" in params:
            nest.telemetry_interval = int(params["period"]) / 1000
            print(f"[{nest.name}] - COMMAND Period: {nest.telemetry_interval}s")
    except Exception as e:
        print(f"[{nest.name}] - Error parsing command: {e}")

def run():
    if len(sys.argv) < 3:
        print("Usage: python nest_sim.py <token> <name>")
        return

    token = sys.argv[1]
    name = sys.argv[2]
    
    nest = SmartNest(token, name)
    # Fixed userdata dictionary to include 'token'
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, userdata={'nest': nest, 'token': token})
    client.username_pw_set(token)
    client.tls_set_context(ssl.create_default_context())
    client.on_message = on_message
    
    try:
        client.connect(THINGSBOARD_HOST, PORT, 60)
        client.subscribe("v1/devices/me/attributes")
        client.loop_start()

        print(f"--- {name} Simulation Started ---")

        while True:
            nest.update_logic()
            payload = {
                "temperature": round(random.uniform(21, 24), 2),
                "humidity": round(random.uniform(40, 60), 2),
                "weight": nest.current_weight,
                "uid": nest.current_uid
            }
            client.publish("v1/devices/me/telemetry", json.dumps(payload))
            print(f"[{name}] - T: {payload['temperature']} | H: {payload['humidity']} | W: {payload['weight']}g | UID: {payload['uid']}")
            time.sleep(nest.telemetry_interval)
            
    except KeyboardInterrupt:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    run()