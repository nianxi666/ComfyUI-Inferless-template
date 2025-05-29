import json
import time
import subprocess
import os
import requests
import psutil
import threading
import base64

# from websocket import create_connection

def start_comfyui(comfyui_path):
    try:
        print(f"Attempting to start ComfyUI from: {comfyui_path}")
        command = f"comfy --skip-prompt --workspace={comfyui_path} launch -- --listen 127.0.0.1 --port 8188"
        print(f"Running command: {command}")
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        time.sleep(10) # Increase initial wait time

        if process.poll() is None:
            print("ComfyUI process started successfully.")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"ComfyUI server failed to start with exit code {process.returncode}")
            print(f"STDOUT:\n{stdout}")
            print(f"STDERR:\n{stderr}")
            raise Exception("ComfyUI server failed to start")
    except Exception as e:
        print(f"Exception during ComfyUI startup: {e}")
        raise Exception("Error setting up ComfyUI repo") from e

def run_comfyui_in_background(comfyui_path):
    def run_server():
        start_comfyui(comfyui_path)

    server_thread = threading.Thread(target=run_server)
    server_thread.start()

def check_comfyui(server_address, client_id):
    url = f"http://{server_address}/prompt"
    # Increase timeout to 120 seconds
    for _ in range(120):
        try:
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                print("ComfyUI server is running.")
                return True
        except requests.exceptions.ConnectionError:
            print("Waiting for ComfyUI server to start...")
        time.sleep(1)
    raise Exception("ComfyUI server did not start in time.")

def load_workflow(workflow_path):
    with open(workflow_path, 'r') as file:
        workflow = json.load(file)
    return workflow

def prompt_update_workflow(workflow_filename, workflow, prompt, negative_prompt=None):
    workflow["6"]["inputs"]["text"] = prompt
    if negative_prompt:
        workflow["7"]["inputs"]["text"] = negative_prompt
    return workflow

def send_comfyui_request(ws, prompt, server_address, client_id):
    url = f"http://{server_address}/prompt"
    headers = {'Content-Type': 'application/json'}
    payload = {"prompt": prompt, "client_id": client_id}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    response.raise_for_status() # Raise an exception for HTTP errors
    return response.json()['prompt_id']

def get_img_file_path(server_address, prompt_id):
    with requests.get(f"http://{server_address}/history/{prompt_id}", timeout=10) as response:
        output = response.json()
    outputs = output[prompt_id]["outputs"]
    for node_id in outputs:
        node_output = outputs[node_id]
    if "images" in node_output:
        image_outputs = []
        for image in node_output["images"]:
            image_outputs.append({"filename": image.get("filename")})
    for node_id in image_outputs:
        file_path = f"/output/{node_id.get('filename')}"
    return file_path

def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
        return encoded_string.decode('utf-8')

def stop_server_on_port(port):
    for connection in psutil.net_connections():
        if connection.laddr.port == port:
            process = psutil.Process(connection.pid)
            process.terminate()

def is_comfyui_running(server_address="127.0.0.1:8188"):
    try:
        response = requests.get(f"http://{server_address}/", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False
