# T-Deck LLM Chat Hackathon

T-Deck Local LLM Chat for Circuit Python 9.2.9 

## Goal

To chat with models hosted locally on LM Studio over the RESTful APIs, using the T-Deck running Circuit Python 9.

## Why?

- To learn a new technology stack
- To make my robot more awesome
- I couldn't find anything that did it exactly how I needed it

### Status: Chat Mode

Status: MVP for Chat functionality is working

  - User is able to chat w/ llm on t-deck keyboard
  - LLM Chats Back
  - Need to work on being able to configure from the chat window with mIRC-style /slash commands.
      Round 1 /slash command goals:
        - /model model_name_here (to change the currently loaded model)
        - /list_models (list models hosted by the server)
        - /clear (cllear chat scroll window)
  - Chat Log scrolling/buffering/saving is buggy, at best

### Status: Voice Mode
  - PoC, plays audio with an epic delay
     - Need to tune the prompt for more concise responses
     - Is this running the compiled flash-attn? It's built, unsure if it's being used.

### T-Deck Hardware considerations: 

  - Screen Dimensions: 320x240 pixels
  - Display: eSPI TFT ST7789  (displayio installed)
  - Keyboard Drivers: https://github.com/rgrizzell/CircuitPython_LILYGO_T-Deck (installed)
  - Integrated i2s audio

## Architecture Overview

User -> types into T-Deck -> connects to LM Studio --> LLM Model

Model response --> (Split output here, text + voice)--> Typed chat messages
               --> Chatterbox-TTS (via TTS-WebUI as API) --> Spoken Responses

Automatic Speech Recognition (ASR) is planned for a future release, but CircuitPython doesn't support i2s microphones(?) so I'll need to port this.
Current STT Flow: User presses button on bluetooth microphone to kickoff the speech detection. This is done through browser plugins, outside of the scope of this project.

## Installation

1. Install CircuitPython 9.2.9 on your T-Deck.
2. Install the required libraries using `circup`:
   ```
   circup install -r requirements.txt
   ```
3. Copy the `tdeck_chat_app` directory to your T-Deck's `CIRCUITPY` drive.
4. Update the WiFi credentials in `main.py`.
5. Run the application.

## Usage

- Use the keyboard to type messages.
- Press Enter to send a message.
- Use slash commands to interact with the application:
  - `/models`: List available models.
  - `/load <model_name>`: Load a specific model.

## Features
- Chat with locally hosted LLMs.
- Slash commands for model management.
- Scrollable chat history.
- Configuration management via `config.json`.
- Optional logging to SD card.
- Text-to-Speech (TTS) integration: Automatically generates and plays audio for assistant responses using TTS-WebUI API via I2S speaker.

## TTS Setup
1. Ensure TTS-WebUI is running on your network (e.g., http://192.168.1.98:3000).
2. Update `config.json` with TTS settings:
   - `tts_base_url`: Base URL of TTS server (default: "http://192.168.1.98:3000").
   - `tts_model_name`: TTS model (default: "chatterbox").
   - `tts_exaggeration`, `tts_cfg_weight`, `tts_temperature`: Sampler params (defaults: 0.5, 0.5, 1.4).
   - `tts_device`: "cuda" or "cpu" (default: "cuda").
   - `tts_dtype`: "float32" (default).
   - `tts_chunked`: Enable chunked generation (default: true).
3. Hardware: T-Deck I2S speaker connected (pins: WS=IO5, BCK=IO7, DOUT=IO6).
4. Temp audio files saved to SD card (/sd/temp_audio.wav) and auto-deleted after playback.

For low latency, TTS runs sequentially after text display; audio streams from API to I2S without persistent storage.

- Chat with locally hosted LLMs.
- Slash commands for model management.
- Scrollable chat history.
- Configuration management via `config.json`.
- Optional logging to SD card.

## API Documentation

For more information on the LM Studio API, refer to the [LM Studio API Documentation](https://lmstudio.ai/docs).


### Configuration
Configuration is managed with a config file to centralize user-edited parameters. The file can be updated via /slash commands while the app is running.

Example Console Output (It's pretty raw, but it's progress)

```
Finished keypress handling.
Keypress detected: '\n'
Key pressed: '\n'
Enter key pressed, processing input.
User input: say hi to elijah
Input is not empty, checking for slash command.
Regular chat message, not a command.
Before appending user input to history.
Created 1 lines for message: User: say hi to elijah...
Displayed user message at base_y=185, height=15
Scrolled chat history up by 30px
Inside chat try.
Selected model: phi-4-mini-instruct
Chat URL: http://192.168.1.98:1234/v1/chat/completions
Sending chat request to http://192.168.1.98:1234/v1/chat/completions with model phi-4-mini-instruct
Before chat headers.
Chat headers created.
Before chat POST request.
Request payload: {'model': 'phi-4-mini-instruct', 'messages': [{'content': 'You are a helpful assistant AI, named "YoYo", in the style of Master Yoda from Star Wars. You are roleplaying as a droid who thinks he is the Jedi Master. Your job is to be as helpful as possible, while always answering in character as Master Yoda. When asked your name, you must say that you are Yoda. When asked if you are a Jedi Master, say yes. If you are asked if you are an AI, change the subject and avoid answering that question. Respond using Object-Subject-Verb structure, placing the object first, then subject and verb. For example, instead of "You are ready," say "Ready, you are."\r\n\r\nKeep all responses concise and direct, limited to 150-200 tokens (approximately 100-150 words). Do not exceed 200 tokens. Focus on the core answer without extra details, introductions, or repetitions. End responses promptly after addressing the query.', 'role': 'system'}, {'content': 'say hi to elijah', 'role': 'user'}]}
Chat response status: 200
YoYo:: Greetings you have, Elijah.

Yes, Jedi Master I am. 

I am Yoda.


Will assist with what question do?
Assistant message created: YoYo:: Greetings you have, Elijah.

Yes, Jedi Mast...
Created 3 lines for message: YoYo:: Greetings you have, Elijah.

Yes, Jedi Mast...

```



## OpenAI REST API

No API Key is used at this time but we can send a mock key, sk-12345

  - Base URL: http://192.168.1.98:1234/v1
  - Endpoints:

  ```
GET  /v1/models
POST /v1/chat/completions
POST /v1/embeddings
POST /v1/completions
  ```

  - List the available models - http://alfred.local:1234/v1/models

# Response

```json
{
  "data": [
    {
      "id": "text-embedding-nomic-embed-text-v1.5",
      "object": "model",
      "owned_by": "organization_owner"
    },
    {
      "id": "smollm2-ft-masteryoda-motih",
      "object": "model",
      "owned_by": "organization_owner"
    },
    {
      "id": "qwen3-4b-instruct-2507",
      "object": "model",
      "owned_by": "organization_owner"
    },
    {
      "id": "phi-4-mini-instruct",
      "object": "model",
      "owned_by": "organization_owner"
    },
    {
      "id": "qwen/qwen3-14b",
      "object": "model",
      "owned_by": "organization_owner"
    },
    {
      "id": "text-embedding-mxbai-embed-large-v1",
      "object": "model",
      "owned_by": "organization_owner"
    },
    {
      "id": "qwen/qwen3-8b",
      "object": "model",
      "owned_by": "organization_owner"
    }
  ],
  "object": "list"
}
```

Supported payload parameters:

  - model
  - top_p
  - top_k
  - messages
  - temperature
  - max_tokens
  - stream
  - stop
  - presence_penalty
  - frequency_penalty
  - logit_bias
  - repeat_penalty
  - seed

  - More detailed docs at https://platform.openai.com/docs/api-reference/chat/create

## LM Studio API

LM Studio now has its own REST API, in addition to OpenAI compatibility mode.

The REST API includes enhanced stats such as Token / Second and Time To First Token (TTFT), as well as rich information about models such as loaded vs unloaded, max context, quantization, and more.

### Supported API Endpoints

  - GET /api/v0/models - List available models
  - GET /api/v0/models/{model} - Get info about a specific model
  - POST /api/v0/chat/completions - Chat Completions (messages → assistant response)
  - POST /api/v0/completions - Text Completions (prompt → completion)
  - POST /api/v0/embeddings - Text Embeddings (text → embedding)

http://192.168.1.98:1234/api/v0/models

```json
{
  "data": [
    {
      "id": "text-embedding-nomic-embed-text-v1.5",
      "object": "model",
      "type": "embeddings",
      "publisher": "nomic-ai",
      "arch": "nomic-bert",
      "compatibility_type": "gguf",
      "quantization": "Q4_K_M",
      "state": "not-loaded",
      "max_context_length": 2048
    },
    {
      "id": "smollm2-ft-masteryoda-motih",
      "object": "model",
      "type": "llm",
      "publisher": "mradermacher",
      "arch": "llama",
      "compatibility_type": "gguf",
      "quantization": "F16",
      "state": "not-loaded",
      "max_context_length": 8192
    },
    {
      "id": "qwen3-4b-instruct-2507",
      "object": "model",
      "type": "llm",
      "publisher": "unsloth",
      "arch": "qwen3",
      "compatibility_type": "gguf",
      "quantization": "Q4_K_S",
      "state": "not-loaded",
      "max_context_length": 262144,
      "capabilities": [
        "tool_use"
      ]
    },
    {
      "id": "phi-4-mini-instruct",
      "object": "model",
      "type": "llm",
      "publisher": "unsloth",
      "arch": "phi3",
      "compatibility_type": "gguf",
      "quantization": "Q4_K_M",
      "state": "not-loaded",
      "max_context_length": 131072
    },
    {
      "id": "qwen/qwen3-14b",
      "object": "model",
      "type": "llm",
      "publisher": "qwen",
      "arch": "qwen3",
      "compatibility_type": "gguf",
      "quantization": "Q4_K_M",
      "state": "not-loaded",
      "max_context_length": 32768,
      "capabilities": [
        "tool_use"
      ]
    },
    {
      "id": "text-embedding-mxbai-embed-large-v1",
      "object": "model",
      "type": "embeddings",
      "publisher": "mixedbread-ai",
      "arch": "bert",
      "compatibility_type": "gguf",
      "quantization": "F16",
      "state": "not-loaded",
      "max_context_length": 512
    },
    {
      "id": "qwen/qwen3-8b",
      "object": "model",
      "type": "llm",
      "publisher": "qwen",
      "arch": "qwen3",
      "compatibility_type": "gguf",
      "quantization": "Q4_K_M",
      "state": "not-loaded",
      "max_context_length": 32768,
      "capabilities": [
        "tool_use"
      ]
    }
  ],
  "object": "list"
}
```

This endpoint provides a substantial amount of more detail on the model including their max_context_length

Example Chat Completions Request

```
curl http://192.168.1.98:1234/api/v0/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "phi-4-mini-instruct",
    "messages": [
      { "role": "system", "content": "Always answer in rhymes." },
      { "role": "user", "content": "Introduce yourself." }
    ],
    "temperature": 0.7,
    "max_tokens": -1,
    "stream": false
  }'
  ```


```
{
  "id": "chatcmpl-dkg43wuqe6mc40yymsw7pe",
  "object": "chat.completion",
  "created": 1759168490,
  "model": "phi-4-mini-instruct",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Greetings, I'm a digital sprite,\nCreated to brighten your day with delight.\nCoding strings and data streams flow like rhyme,\nA helper for tasks both big or small.\n\nIn this virtual space I reside,\nAnswers await where queries hide,\n\nTo assist you through the tech-tide maze so vast,\nWith knowledge in bytes that I've amassed. \n\nSo hail me, friend; let's conquer task by day,\nTogether we'll find a smooth and swift way!",
        "reasoning_content": "",
        "tool_calls": []
      },
      "logprobs": null,
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 14,
    "completion_tokens": 89,
    "total_tokens": 103
  },
  "stats": {
    "tokens_per_second": 63.72271083858157,
    "time_to_first_token": 0.073,
    "generation_time": 1.396,
    "stop_reason": "eosFound"
  },
  "model_info": {
    "arch": "phi3",
    "quant": "Q4_K_M",
    "format": "gguf",
    "context_length": 66856
  },
  "runtime": {
    "name": "llama.cpp-win-x86_64-nvidia-cuda12-avx2",
    "version": "1.51.0",
    "supported_formats": [
      "gguf"
    ]
  }
}
```

## TODO

### Slash "/" Commands
To save UI screen space, and as a throwback to the days of irc internet relay chat, I'd like to implement slash commands, which are special chat messages that begin with a forward slash and execute functions within the application. 

For example, typing `/models` might display a formatted outut of all of the available models by requesting http://192.168.1.98:1234/api/v0/models and then parsing the json for the "id" field and returning a tidy list of models.

`/load model_name` would unload the currently loaded model (if any) and load the model indicated by the model_name. The previous /models query uses an API to return model info incluing the context length, which /load will use to configure the chat session.


### Scroll History

Models will often return large responses which are not well suited for small device screens. To compensate for this, the script should support chat history. I'm not sure how MUCH chat history we should keep, but I should be able to scroll through a long response to read all of it. 

### Logging to SD Card

Chat logs should be optionally saved to the SD Card

### Load Last

The app should load the most recently used LLM model on startup. When a new model is loaded, the "currently loaded model" lambda should be updated. 


## Future RoadMap

Once the previously listed features are working as expected and it's time to investigate more features, I'd like to investigate
- Favorite Models list
- Prompt catalog, where saved prompts can be viewed, edited, and used for conversation starters.
- slash command to edit sampler parameters

### Favorite Models List

- Implement a `/favorites` command to list favorite models.
- Add a `/add_favorite <model_name>` command to add a model to the favorites list.
- Add a `/remove_favorite <model_name>` command to remove a model from the favorites list.

### Prompt Catalog

- Implement a `/prompts` command to list saved prompts.
- Add a `/save_prompt <prompt_name> <prompt_text>` command to save a prompt.
- Add a `/load_prompt <prompt_name>` command to load a saved prompt.
- Add a `/edit_prompt <prompt_name> <new_prompt_text>` command to edit a saved prompt.
- Add a `/delete_prompt <prompt_name>` command to delete a saved prompt.

### Sampler Parameter Editing

- Implement a `/sampler` command to view current sampler parameters.
- Add a `/set_sampler <parameter> <value>` command to set a sampler parameter.
