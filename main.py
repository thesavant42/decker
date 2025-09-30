# T-Deck LLM Chat Application

import board
import displayio
import terminalio
from adafruit_display_text import label
from adafruit_st7789 import ST7789
import json
import time
import adafruit_requests
import wifi, os
import socketpool
from lilygo_tdeck import TDeck  # Uncommented to test after I2C scan
import config
import audiobusio
import audiocore
import traceback

wifi.radio.connect(ssid=os.getenv('CIRCUITPY_WIFI_SSID'),
                   password=os.getenv('CIRCUITPY_WIFI_PASSWORD'))
print("Assigned IP address:", wifi.radio.ipv4_address)

# Add delay for WiFi to fully initialize
time.sleep(2)  # Wait 2 seconds for connection stability
dns_servers = wifi.radio.ipv4_dns

# Initialize socket pool for requests
pool = socketpool.SocketPool(wifi.radio)
print("Socket pool initialized.")

if dns_servers is None:
    print("DNS servers: No DNS servers configured")
else:
    # Handle single Address or list
    if hasattr(dns_servers, '__iter__') and not isinstance(dns_servers, (str, bytes)):
        dns_str = ', '.join(str(d) for d in dns_servers)
    else:
        dns_str = str(dns_servers)
    print(f"DNS servers: {dns_str}")

# Initialize the display
displayio.release_displays()

spi = board.SPI()
tft_cs = board.IO12  # GPIO12 for TFT CS
tft_dc = board.IO11  # GPIO11 for TFT DC

from fourwire import FourWire
display_bus = FourWire(spi, command=tft_dc, chip_select=tft_cs, reset=board.IO9)  # GPIO9 for RST

display = ST7789(display_bus, width=320, height=240, rotation=270)  # Rotation 270 for upright (flip if needed)

# Create a group for the display
display_group = displayio.Group()
display.root_group = display_group

# Add a label to the display
welcome_label = label.Label(terminalio.FONT, text="T-Deck LLM Chat", color=0xFFFFFF, x=10, y=10)
display_group.append(welcome_label)

# Create status bar for model information
## BUG This says Model: None in the label. It should be updated based upon which model is being loaded.
model_label = label.Label(terminalio.FONT, text="Model: None", color=0xFFFFFF, x=10, y=30)
display_group.append(model_label)

######### Load configuration on startup
config_instance = config.Config()
config_instance.load_config()
print(f"Config loaded successfully. Using base URL: {config_instance.lm_studio_base_url} | Using API key: {config_instance.api_key[:5]}...")

# Load system prompt from file
system_prompt = ""
try:
    with open("prompt.txt", "r") as f:
        system_prompt = f.read().strip()
    print(f"System prompt loaded from prompt.txt ({len(system_prompt)} chars)")
except OSError as e:
    print(f"Warning: Could not load prompt.txt: {e}. Using empty system prompt.")

# Check to see if URL needs HTTPS libraries
if config_instance.lm_studio_base_url.startswith("https://"):
    import ssl
    context = ssl.create_default_context()
    requests = adafruit_requests.Session(pool, context)
else:
    requests = adafruit_requests.Session(pool, None)
    # Initialize TTS requests session (assume HTTP for TTS-WebUI)
    tts_requests = adafruit_requests.Session(pool, None)
    print("TTS HTTP session initialized.")

# Test HTTP request to configured API (basic health check)
test_url = f"{config_instance.lm_studio_base_url}/models"
# LOOK HERE Is this why it fails?
# Conditional auth header if api_key provided
headers = {}
if config_instance.api_key and config_instance.api_key.strip():
    headers["Authorization"] = f"Bearer {config_instance.api_key}"
# Fails after this print
print(f"Testing URL: {test_url}")  # Log the configured URL for validation
try:
    print(f"Before GET: requests object: {requests}")
    test_response = requests.get(test_url) #, headers=headers)
    print(f"After GET: response type: {type(test_response)}")
    if test_response is not None:
        print(f"API test status: {test_response.status_code}")
    else:
        print("Response is None - potential Session init issue")
    if test_response.status_code in [200, 401]:  # 401 ok if auth fails, still reachable
        print("API connectivity confirmed.")
    else:
        print(f"API test failed: {test_response.text}")
except Exception as net_e:
    print(f"Network test error: {net_e}")
    print("Network test details:")
    # CircuitPython traceback limited; print exception directly
    import sys
    sys.print_exception(net_e)

# Auto-load default model if none set
print("Checking for auto-load model...")
if config_instance.last_used_model is None:
    default_model = "phi-4-mini-instruct"
    print(f"Setting default model: {default_model}")
    config_instance.last_used_model = default_model
    print("Loading default model...")
    try:
        url = f"{config_instance.lm_studio_base_url}/models"
        print(f"Auto-load URL: {url}")
        headers = {"Authorization": f"Bearer {config_instance.api_key}", "Content-Type": "application/json"}
        payload = {"model": default_model}
        response = requests.post(url, json=payload, headers=headers)
        print(f"After POST (autoload): response type: {type(response)}")
        if response is not None:
            print(f"Auto-load response status: {response.status_code}")
        else:
            print("Autoload response is None")
        if response.status_code == 200:
            print(f"Default model {default_model} loaded successfully.")
            config_instance.save_config()
            model_label.text = f"Model: {default_model}"
        else:
            print(f"Failed to auto-load model. Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        import traceback
        print(f"Error auto-loading model: {e}")
        print("Auto-load traceback:")
        print(traceback.format_exc())
else:
    print(f"Using existing model: {config_instance.last_used_model}")
    model_label.text = f"Model: {config_instance.last_used_model}"


# Initialize the T-Deck
tdeck = TDeck()
print("T-Deck library initialized.")

# TTS Functions
import random  # For seed generation


def tts_generate_audio(text, config_instance):
    """Generate TTS audio bytes from text using OpenAI-compatible API."""
    print("=== TTS GENERATE START ===")
    print(f"TTS base_url from config: {getattr(config_instance, 'tts_base_url', 'NOT SET')}")
    try:
        if not config_instance.tts_base_url:
            print("TTS base_url not configured - skipping TTS")
            return None
        url = f"{config_instance.tts_base_url}/v1/audio/speech"
        import json
        headers = {
            "Content-Type": "application/json",
            "Accept": "*/*"
        }
        if config_instance.api_key and config_instance.api_key.strip():
            headers["Authorization"] = f"Bearer {config_instance.api_key}"
        
        # Use config values, fallback to task defaults
        model = config_instance.tts_model_name or "chatterbox"
        voice = config_instance.tts_voice or "voices/chatterbox/whywishnotfar.wav"
        exaggeration = config_instance.tts_exaggeration or 0.4
        cfg_weight = config_instance.tts_cfg_weight or 0.5
        temperature = config_instance.tts_temperature or 0.6
        device = config_instance.tts_device or "auto"
        dtype = config_instance.tts_dtype or "float16"
        seed = config_instance.tts_seed or -1
        chunked = getattr(config_instance, 'tts_chunked', True)
        
        params = {
            "desired_length": 100,
            "max_length": 300,
            "halve_first_chunk": True,
            "exaggeration": exaggeration,
            "cfg_weight": cfg_weight,
            "temperature": temperature,
            "device": device,
            "dtype": dtype,
            "cpu_offload": False,
            "chunked": chunked,
            "cache_voice": False,
            "tokens_per_slice": None,
            "remove_milliseconds": None,
            "remove_milliseconds_start": None,
            "chunk_overlap_method": "undefined",
            "seed": seed,
            "use_compilation": True,
            "max_new_tokens": 1000,
            "max_cache_len": 1500
        }
        
        payload = {
            "model": model,
            "voice": voice,
            "input": text,
            "response_format": "wav",
            "speed": 1,
            "stream": True,
            "params": params
        }
        print(f"TTS payload: {json.dumps(payload)}")
        print(f"POST URL: {url}")
        print(f"Headers: {headers}")
        response = tts_requests.post(url, json=payload, headers=headers)
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        if response.status_code == 200:
            audio_bytes = response.content
            print(f"TTS audio bytes generated: {len(audio_bytes)} bytes")
            return audio_bytes
        else:
            print(f"TTS generation failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"TTS generation error: {e}")
        import traceback
        print("TTS traceback:")
        print(traceback.format_exc())
        return None
    print("=== TTS GENERATE END ===")


def play_audio(tdeck, filepath):
    """Play WAV file via TDeck's speaker."""
    try:
        if tdeck.speaker is None:
            print("TDeck speaker not available")
            return
        print("Using TDeck speaker for playback")
        with open(filepath, "rb") as audio_file:
            wave = audiocore.WaveFile(audio_file)
            print("Starting audio playback")
            tdeck.speaker.play(wave)
            while tdeck.speaker.playing:
                pass
            print("Playback loop completed")
        print("Audio playback completed.")
    except Exception as e:
        print(f"Audio playback error: {e}")

# No separate keyboard object; use tdeck directly for get_keypress() (bypassed)

# Create scrollable chat history area
print("Before chat_history init.")
chat_history = []  # Will store (text, height) tuples
print("After chat_history init.")
chat_history_group = displayio.Group()
chat_history_group.y = 50  # Position below model_label
print("Created chat_history_group.")
display_group.append(chat_history_group)
print("Appended chat_history_group.")

# Create text input bar
input_label = label.Label(terminalio.FONT, text="> ", color=0xFFFFFF, x=10, y=220)
display_group.append(input_label)

# Helper function to create multi-line labels for long messages
def create_multi_line_label(text, x, start_y, color, max_chars=50):
    """Split text into lines and create stacked labels."""
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = current_line + (word + " " if current_line else word)
        if len(test_line) <= max_chars:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line.strip())
            current_line = word + " "
    if current_line:
        lines.append(current_line.strip())
    
    labels = []
    y_offset = start_y
    for line in lines:
        label_obj = label.Label(terminalio.FONT, text=line, color=color, x=x, y=y_offset)
        labels.append(label_obj)
        y_offset += 15  # line_height
    print(f"Created {len(lines)} lines for message: {text[:50]}...")
    return labels, y_offset - start_y  # Return labels and total height

# Main loop
input_text = ""
print("time already imported earlier.")
import time  # Ensure time is imported for sleep

print("Entering main loop...")
while True:
    keypress = tdeck.get_keypress()
    # print("After get_keypress.")
    if keypress:
        print(f"Keypress detected: {repr(keypress)}")
        print(f"Key pressed: {repr(keypress)}")
        if keypress == "\n":  # Enter key
            print("Enter key pressed, processing input.")
            print(f"User input: {input_text}")
            if input_text:
                print("Input is not empty, checking for slash command.")
            else:
                print("Input is empty, ignoring.")
            if input_text.startswith("/"):
                print("Input starts with /, parsing command.")
                # Parse slash command
                command = input_text[1:].split()
                print(f"Command split: {command}")
                if command and command[0] == "models":
                    try:
                        url = f"{config_instance.lm_studio_base_url}/models"
                        # Conditional auth header if api_key provided
                        headers = {}
                        if config_instance.api_key and config_instance.api_key.strip():
                            headers["Authorization"] = f"Bearer {config_instance.api_key}"
                        print("Headers created.")
                        response = requests.get(url, headers=headers)
                        print(f"GET response received, status: {response.status_code}")
                        if response.status_code == 200:
                            print("Status 200, parsing JSON.")
                            models = response.json()
                            print("JSON parsed successfully.")
                            print("Available models:")
                            print(f"Models data: {models}")
                            print("Before iterating models.")
                            for model in models["data"]:
                                print(f"Model ID: {model['id']}")
                                print(model["id"])
                            print("Finished iterating models.")
                        else:
                            print(f"Failed to fetch models. Status code: {response.status_code}")
                            print(f"Response text: {response.text}")
                    except Exception as e:
                        print(f"Error fetching models: {e}")
                elif command and command[0] == "load":
                    print("Processing /load command.")
                    if len(command) > 1:
                        print("Command has model name.")
                        model_name = command[1]
                        try:
                            url = f"{config_instance.lm_studio_base_url}/models"
                            # Conditional auth header if api_key provided
                            headers = {"Content-Type": "application/json"}
                            if config_instance.api_key and config_instance.api_key.strip():
                                headers["Authorization"] = f"Bearer {config_instance.api_key}"
                            print("Load headers created.")
                            print("Before POST request for load.")
                            response = requests.post(url, json={"model": model_name}, headers=headers)
                            print(f"POST response status: {response.status_code}")
                            if response.status_code == 200:
                                print("Load successful, status 200.")
                                print(f"Model {model_name} loaded successfully.")
                                print("Before setting last_used_model.")
                                config_instance.last_used_model = model_name
                                print("Last used model set.")
                                print("Before save_config.")
                                config_instance.save_config()
                                print("Config saved.")
                                # Update the model label
                                print("Before updating model_label.")
                                model_label.text = f"Model: {model_name}"
                                print("Model label updated.")
                            else:
                                print(f"Failed to load model. Status code: {response.status_code}")
                                print(f"Response text: {response.text}")
                        except Exception as e:
                            print(f"Error loading model: {e}")
                            import traceback
                            print("Load traceback:")
                            print(traceback.format_exc())
                    else:
                        print("Please specify a model name.")
                    print("Finished /load processing.")
                else:
                    print(f"Unknown command: {command[0] if command else 'empty'}")
                print("Finished slash command processing.")
            else:
                print("Regular chat message, not a command.")
                print("Before appending user input to history.")
                user_message = f"User: {input_text}"
                line_height = 15
                base_y = 50 + sum(prev_height for _, prev_height in chat_history)  # Sum prior heights
                user_labels, user_height = create_multi_line_label(user_message, 10, base_y, 0xFFFFFF)
                for lbl in user_labels:
                    chat_history_group.append(lbl)
                chat_history.append((user_message, user_height))  # Store text and height
                print(f"Displayed user message at base_y={base_y}, height={user_height}")
                
                # Basic scrolling for chat history
                visible_height = 170
                total_y = base_y + user_height
                if total_y > visible_height:
                    scroll_amount = total_y - visible_height
                    chat_history_group.y -= scroll_amount
                    print(f"Scrolled chat history up by {scroll_amount}px")
                try:
                    print("Inside chat try.")
                    model = config_instance.last_used_model or "phi-4-mini-instruct"
                    print(f"Selected model: {model}")
                    url = f"{config_instance.lm_studio_base_url}/chat/completions"
                    print(f"Chat URL: {url}")
                    print(f"Sending chat request to {url} with model {model}")
                    print("Before chat headers.")
                    # Conditional auth header if api_key provided
                    headers = {"Content-Type": "application/json"}
                    if config_instance.api_key and config_instance.api_key.strip():
                        headers["Authorization"] = f"Bearer {config_instance.api_key}"
                    print("Chat headers created.")
                    print("Before chat POST request.")
                    messages = [{"role": "user", "content": input_text}]
                    if system_prompt:
                        messages.insert(0, {"role": "system", "content": system_prompt})
                    payload = {"model": model, "messages": messages}
                    print(f"Request payload: {payload}")
                    response = requests.post(url, json=payload, headers=headers)
                    print(f"Chat response status: {response.status_code}")
                    if response.status_code == 200:
                        assistant_response = response.json()
                        print(f"YoYo:: {assistant_response['choices'][0]['message']['content']}")
                        # Display assistant's message
                        assistant_message = f"YoYo:: {assistant_response['choices'][0]['message']['content']}"
                        print(f"Assistant message created: {assistant_message[:50]}...")
                        line_height = 15
                        base_y = 50 + sum(prev_height for _, prev_height in chat_history)  # Sum prior heights
                        assistant_labels, assistant_height = create_multi_line_label(assistant_message, 10, base_y, 0x00FF00)
                        for lbl in assistant_labels:
                            chat_history_group.append(lbl)
                        chat_history.append((assistant_message, assistant_height))  # Store text and height
                        print(f"Displayed assistant message at base_y={base_y}, height={assistant_height}")
                        
                        # TTS Integration: Generate and play audio for assistant response
                        try:
                            # Debug config TTS attributes
                            print(f"Config TTS base_url: {getattr(config_instance, 'tts_base_url', 'NOT SET')}")
                            print(f"Config TTS model: {getattr(config_instance, 'tts_model_name', 'NOT SET')}")
                            print("=== TTS INTEGRATION START ===")
                            
                            response_text = assistant_response['choices'][0]['message']['content']
                            print(f"TTS input text length: {len(response_text)} chars")
                            audio_bytes = tts_generate_audio(response_text, config_instance)
                            print(f"TTS returned audio_bytes length: {len(audio_bytes) if audio_bytes else 'None'}")
                            if audio_bytes:
                                temp_file = f"{config_instance.sd_card_path}/temp_audio.wav"
                                with open(temp_file, "wb") as f:
                                    f.write(audio_bytes)
                                print(f"Audio bytes written to {temp_file}")
                                play_audio(tdeck, temp_file)
                                # Cleanup temp file
                                try:
                                    os.remove(temp_file)
                                    print("Temp audio file deleted.")
                                except OSError as e:
                                    print(f"Failed to delete temp file: {e}")
                        except Exception as tts_e:
                            print(f"TTS integration error: {tts_e}")
                            print("=== TTS INTEGRATION END ===")
                        
                        # Basic scrolling for chat history
                        visible_height = 170
                        total_y = base_y + assistant_height
                        if total_y > visible_height:
                            scroll_amount = total_y - visible_height
                            chat_history_group.y -= scroll_amount
                            print(f"Scrolled chat history up by {scroll_amount}px")
                    else:
                        print(f"Failed to send chat request. Status code: {response.status_code}")
                        print(f"Chat response text: {response.text}")
                except Exception as e:
                    print(f"Error sending chat request: {e}")
                    print("After chat try block.")
            print("Resetting input_text.")
            input_text = ""
            input_label.text = "> "
        elif keypress == "\b":  # Backspace key
            input_text = input_text[:-1]
            input_label.text = f"> {input_text}"
        else:
            input_text += keypress
            input_label.text = f"> {input_text}"
        print("Finished keypress handling.")
        
    # print("No keypress or handled, before sleep.")
    # print("Before sleep.")
    time.sleep(0.1)  # Sleep to avoid busy-waiting
    # print("After sleep.")

# Use the provided API endpoints to fetch available models and send chat requests
# TODO: Implement using the provided API endpoints to fetch available models and send chat requests

# Handle API responses and errors gracefully
# TODO: Implement handling API responses and errors gracefully

# Debug and fix any issues encountered during testing
# TODO: Implement debugging and fixing any issues encountered during testing

# Ensure the application is stable and responsive
# TODO: Implement ensuring the application is stable and responsive
