import os
from config import get_output_dir, CURATOR, ANNOTATOR, SOUND_BANK
from .utils.jams_utils import generate_random_notes, save_jams
from .utils.audio_utils import preload_audio_durations, synthesize_jams_to_audio 


class SingleNotesGenerator:
    def __init__(self, output_folder=None, num_notes=360, num_files=100, curator=CURATOR, annotator=ANNOTATOR,
                 duration_range=(0.1, 2.0), silence_prob=0.2, silence_duration_range=(0.1, 5.0)):
        self.num_notes = num_notes
        self.num_files = num_files
        self.output_folder = output_folder or get_output_dir(self.__class__.__name__)
        self.curator_name, self.curator_email = curator
        self.annotator_name, self.annotator_version = annotator
        self.duration_range = duration_range
        self.silence_prob = silence_prob
        self.silence_duration_range = silence_duration_range
        self.standard_tuning = [64, 59, 55, 50, 45, 40]  # EADGBE
        self.inverted_strings = ["0", "1", "2", "3", "4", "5"]
        os.makedirs(self.output_folder, exist_ok=True)

    def _generate_notes(self):
        return generate_random_notes(
            num_notes=self.num_notes,
            standard_tuning=self.standard_tuning,
            duration_range=self.duration_range,
            silence_prob=self.silence_prob,
            silence_duration_range=self.silence_duration_range,
            curator_name=self.curator_name,
            curator_email=self.curator_email,
            annotator_name=self.annotator_name,
            annotator_version=self.annotator_version,
            inverted_strings=self.inverted_strings
        )

    def generate(self):
        for file_idx in range(1, self.num_files + 1):
            pitch_annotations, midi_annotations, current_time = self._generate_notes()

            annotations = []
            for i in range(6):
                annotations.append(pitch_annotations[i])
                annotations.append(midi_annotations[i])

            out_path = save_jams(
                os.path.join(self.output_folder, 'jams'),
                cycle=0,
                run_index=file_idx,
                annotations=annotations,
                duration=current_time,
                curator_name=self.curator_name,
                title_prefix="Random Single Notes"
            )
            print(f"✅ Generated file {file_idx} with {self.num_notes} notes: {out_path}")
            
    duration_cache = preload_audio_durations(base_folder=SOUND_BANK, sample_rate=48000)

    def synthesize_all(self, singlenotes_base_folder= SOUND_BANK, file_duration_cache=duration_cache, **kwargs):
        output_dir = os.path.join(self.output_folder, "audios")
        jams_files = [f for f in os.listdir(os.path.join(self.output_folder, 'jams')) if f.lower().endswith(".jams")]
        for jams_file in jams_files:
            jams_path = os.path.join(self.output_folder, 'jams', jams_file)
            synthesize_jams_to_audio(
                jams_file_path=jams_path,
                output_dir=output_dir,
                singlenotes_base_folder=singlenotes_base_folder,
                file_duration_cache=file_duration_cache,
                **kwargs
            )



# # --------------------------
# # Example usage
# # --------------------------

# # 1️⃣ Create generator instance
# # User input parameters for `SingleNotesGenerator`:
# #   - num_notes: int → number of notes per file
# #   - num_files: int → number of JAMS files to generate
# #   - curator: tuple → (name, email) of curator
# #   - annotator: tuple → (name, version) of annotator
# #   - duration_range: tuple → min/max duration of notes in seconds
# #   - silence_prob: float → probability of inserting a silence
# #   - silence_duration_range: tuple → min/max duration of silences
# generator = SingleNotesGenerator(
#     num_notes=360,
#     num_files=5,
#     # curator=("User Name", "user@email.com"),
#     # annotator=("AnnotatorName", "1.0"),
#     # duration_range=(0.1, 2.0),
#     # silence_prob=0.2,
#     # silence_duration_range=(0.1, 5.0)
# )

# # 2️⃣ Generate JAMS files
# # No user parameters here; `generate()` uses the settings from the generator instance
# generator.generate()  # creates JAMS files

# # 3️⃣ Preload audio durations (needed for synthesis)
# # User input parameters for `preload_audio_durations`:
# #   - base_folder: str → folder containing audio files (SOUND_BANK)
# #   - sample_rate: int → sample rate for duration calculation
# file_duration_cache = preload_audio_durations(
#     SOUND_BANK,
#     sample_rate=48000
# )

# # 4️⃣ Synthesize all generated JAMS to audio
# # User input parameters for `synthesize_all`:
# #   - singlenotes_base_folder: str → folder with single note audio samples
# #   - file_duration_cache: dict → preloaded durations
# #   - output_dir: str (optional) → folder where audio will be saved
# #   - **kwargs → additional user parameters passed to synthesize_jams_to_audio:
# #       • sample_rate: int → output audio sample rate
# #       • fadein_samples: int → number of samples to fade in
# #       • fadeout_samples: int → number of samples to fade out
# #       • amplitude_range: tuple → min/max amplitude scaling
# #       • noise_level_range: tuple → min/max noise to add
# generator.synthesize_all(
#     singlenotes_base_folder="SingleNotes",
#     file_duration_cache=file_duration_cache,
#     # Optional overrides:
#     # output_dir="CustomAudioFolder",
#     # sample_rate=48000,
#     # fadein_samples=20,
#     # fadeout_samples=20,
#     # amplitude_range=(0.6, 0.9),
#     # noise_level_range=(0.001, 0.005)
# )
