from config import get_output_dir, CURATOR, ANNOTATOR, SOUND_BANK
from .utils.audio_utils import synthesizer
from .utils.jams_utils import load_tone_bank, generate_event
import os

class ComplexGenerator:
    def __init__(self, config):
        self.config = config
        self.tone_bank = load_tone_bank(config["tone_bank_path"])
        base_dir = get_output_dir(self.__class__.__name__)
        self.output_dir = config.get("output_folder", base_dir)

        self.sound_bank = config.get("sound_bank", SOUND_BANK)
        self.sr = config.get("sr", 48000)
        self.noise_level = config.get("noise_level", 0.1)
        self.curator_name, self.curator_email = CURATOR
        self.annotator_name, self.annotator_version = ANNOTATOR

        # grab generate_event params from config, with defaults
        self.event_params = {
            "event_weights": config.get("event_weights", (0.333, 0.333, 0.333)),
            "single_note_duration_range": config.get("single_note_duration_range", (0.1, 1.0)),
            "chord_arpeggio_prob": config.get("chord_arpeggio_prob", 0.7),
            "arpeggio_gap_range": config.get("arpeggio_gap_range", (0.05, 0.2)),
            "arpeggio_overlap_ratio": config.get("arpeggio_overlap_ratio", 0.5),
            "amplitude_range": config.get("amplitude_range", (0.5, 1.0)),
            "chord_duration_range": config.get("chord_duration_range", (0.1, 0.8)),
            "strum_offset_range": config.get("strum_offset_range", (0.05, 1.0)),
        }
        
    def generate_performance(self, num_events=500):
        """
        Generate a list of events for a performance using `generate_event`.
        Each event can be a single note, chord, or silence.
        """
        performance = []
        for _ in range(num_events):
            event = generate_event(
                tone_bank=self.tone_bank,
                sr=self.sr,
                **self.event_params
            )
            if event:  # skip None (silence)
                performance.append(event)  # wrap event as a list
        return performance

    
    def synthesizer(self, performance, output_audio, output_jams):
        synthesizer(
            performance=performance,
            output_audio=output_audio,
            output_jams=output_jams,
            curator_name=self.curator_name,
            curator_email=self.curator_email,
            annotator_name=self.annotator_name,
            annotator_version=self.annotator_version,
        )
        print(f"Synthesized audio: {output_audio} and JAMS: {output_jams}")

    def run(self, num_samples=10, num_events_per_sample=500):
        for i in range(num_samples):
            performance = self.generate_performance(num_events=num_events_per_sample)
            audio_dir = os.path.join(self.output_dir, "audios")
            jams_dir = os.path.join(self.output_dir, "jams")
            os.makedirs(audio_dir, exist_ok=True)
            os.makedirs(jams_dir, exist_ok=True)

            audio_path = os.path.join(audio_dir, f"complex_{i:03d}.wav")
            jams_path = os.path.join(jams_dir, f"complex_{i:03d}.jams")
            self.synthesizer(performance, audio_path, jams_path)


# --------------------------
# Example usage for ComplexGenerator
# --------------------------

# 1️⃣ Create generator instance
# User input parameters for `ComplexGenerator`:
#   - tone_bank_path: str → folder or JSON with available tones
#   - output_dir: str → folder to save generated audio & JAMS
#   - sr: int (optional, default=48000) → sample rate
#   - noise_level: float (optional, default=0.1) → how much background noise to add
#   - annotator: tuple (optional) → (name, version) of annotator
#   - curator: tuple (optional) → (name, email) of curator
#   - sound_bank: str (optional) → folder containing single-note recordings
#   - Event parameters (all optional overrides):
#       * event_weights: tuple → probability of silence, single_note, chord
#       * single_note_duration_range: tuple(float, float)
#       * chord_arpeggio_prob: float
#       * arpeggio_gap_range: tuple(float, float)
#       * arpeggio_overlap_ratio: float
#       * amplitude_range: tuple(float, float)
#       * chord_duration_range: tuple(float, float)
#       * strum_offset_range: tuple(float, float)
# config = {
#     "tone_bank_path": "SingleNotes",
#     "noise_level": 0.2,
#     "event_weights": (0.5, 0.3, 0.2),  # silence, single note, chord
#     "chord_arpeggio_prob": 0.9,        # prefer arpeggios
# }

# generator = ComplexGenerator(config)

# # 2️⃣ Generate performances & synthesize audio
# # User input parameters for `run`:
# #   - num_samples: int → how many audio/JAMS pairs to generate
# #   - num_events_per_sample: int → how many events per performance
# generator.run(
#     num_samples=5,
#     num_events_per_sample=300
# )