# decker
t-deck llm chat

## Goal
User wish: I want to use my lilygo T-Deck to chat with my LLMs hosted in LM Studio (OpenAI Compatible API)

Solution: ESP32-based chat application using REST APIs (and websockets?)
- MVP: Support LM Studio (no API key used, but should support them)
- Stretch goal: Support Openrouter.ai API

### Needs to:
- Configure Endpoint Server(s)
  -- Name, Address, [edit/save]
  -- Load Model Names into dropdown selection text input
  -- save configurations to a text file for editing elsewhere if desired
- Text input box at bottom of screen, the width of the display and the height of 1-2 rows of typed user input
- Area above that should be reserved for text from chat responses

##  Plan (Rough Outline)

 - Use https://github.com/bayeggex/Arduino-AI-Chat-Library?tab=readme-ov-file
  -- Set up as a PlatformIO project
     -- Configure PlaformIO for T-Deck (libraries, pinmaps, platformio.ini)

### Config Variables

LM Studio API Endpoint: http://192.168.1.98:1234/v1  # OpenAI v1 compatible
API Key: None at this time, but can use sk-1234 as a temp
Model: qwen3-4b-instruct-2507
Wifi: Read/Write configuration via text file
-- fall back to AP configuration

### T-Deck Hardware

https://github.com/Xinyuan-LilyGO/T-Deck



| Setting | Value |
|---:|---|
| __Board:__ | ESP32S3 Dev Module |
| __USB CDC On Boot:__ | Enabled |
| __Flash Mode:__ | QIO 120MHz |
| __Flash Size:__ | 16MB(128Mb) |
| __Partition Scheme:__ | 16M Flash(2M APP/12.5MB FATFS) |
| __PSRAM:__ | OPI PSRAM |





### Lilygo default examples, for reference only
docs/examples 
├─Keyboard_ESP32C3       # ESP32C3 keyboard I2C slave
├─Keyboard_T_Deck_Master # T-Deck read from keyboard
├─LoRaWAN_Starter        # LoRaWAN example
├─Microphone             # Noise detection  
├─Touchpad               # Read touch coordinates 
├─GPSShield              # GPS Shield example
├─lvgl_example           # lvgl example
└─UnitTest               # Factory hardware unit testing           
