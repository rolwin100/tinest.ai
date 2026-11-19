uv run --project services/tts python3 -c "
from qwen_tts import Qwen3TTSModel
model = Qwen3TTSModel.from_pretrained(
    'Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice', device_map='cpu', dtype='float32',
)
print('languages:', model.get_supported_languages())
print('speakers: ', model.get_supported_speakers())
"