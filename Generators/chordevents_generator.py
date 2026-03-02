import os
import json
import random
from config import get_output_dir, CURATOR, ANNOTATOR, SOUND_BANK
from .utils.jams_utils import save_jams, make_chord_annotations
from .utils.audio_utils import preload_audio_durations, synthesize_jams_to_audio


class ChordEventsGenerator:
    def __init__(self, 
                 event_json_path,
                 output_folder=None,
                 used_indices_path="used_indices.json",
                 num_to_sample=360,
                 cycles=1,
                 curator=CURATOR,
                 annotator=ANNOTATOR,
                 num_files=None,
                 duration_range=(0.23, 1.2),
                 silence_prob=1.0,
                 silence_duration_range=(0.1, 0.5)):
        self.event_json_path = event_json_path
        self.used_indices_path = used_indices_path
        self.num_to_sample = num_to_sample
        self.cycles = cycles
        self.curator_name, self.curator_email = curator
        self.annotator_name, self.annotator_version = annotator
        self.standard_tuning = [64, 59, 55, 50, 45, 40]
        self.inverted_strings = ["0", "1", "2", "3", "4", "5"]

        # User parameters
        self.num_files = num_files
        self.duration_range = duration_range
        self.silence_prob = silence_prob
        self.silence_duration_range = silence_duration_range

        dataset_name = os.path.splitext(os.path.basename(self.event_json_path))[0]
        self.output_folder = output_folder or os.path.join(get_output_dir(self.__class__.__name__), dataset_name)
        os.makedirs(self.output_folder, exist_ok=True)

        with open(self.event_json_path, "r") as f:
            self.all_events = json.load(f)
        self.total_events = len(self.all_events)

    def generate(self):
        """
        Generate JAMS files using the instance parameters.
        """
        run_index = len([f for f in os.listdir(self.output_folder) if f.startswith("run_")]) + 1
        files_created = 0

        for cycle in range(1, self.cycles + 1):
            print(f"\n🔁 Starting cycle {cycle}")

            if os.path.exists(self.used_indices_path):
                os.remove(self.used_indices_path)
                print("🗑 Deleted used indices file.")
            used_indices = set()

            while True:
                available_indices = [i for i in range(self.total_events) if i not in used_indices]
                if not available_indices:
                    print(f"✅ All events processed for cycle {cycle}.")
                    break

                sample_size = min(self.num_to_sample, len(available_indices))
                sampled_indices = random.sample(available_indices, sample_size)
                sampled_events = [self.all_events[i] for i in sampled_indices]
                used_indices.update(sampled_indices)

                with open(self.used_indices_path, "w") as f:
                    json.dump(sorted(list(used_indices)), f, indent=4)

                # Pass extra parameters to make_chord_annotations
                pitch_contours, note_midis, current_time = make_chord_annotations(
                    sampled_events,
                    curator_name=self.curator_name,
                    curator_email=self.curator_email,
                    annotator_name=self.annotator_name,
                    annotator_version=self.annotator_version,
                    standard_tuning=self.standard_tuning,
                    inverted_strings=self.inverted_strings,
                    duration_range=self.duration_range,
                    silence_prob=self.silence_prob,
                    silence_duration_range=self.silence_duration_range
                )

                annotations = []
                for i in range(6):
                    annotations.append(pitch_contours[i])
                    annotations.append(note_midis[i])

                dataset_name = os.path.splitext(os.path.basename(self.event_json_path))[0]
                jams_folder = os.path.join(self.output_folder, dataset_name, "jams")
                os.makedirs(jams_folder, exist_ok=True)
                out_path = save_jams(jams_folder, cycle, run_index, annotations, current_time, self.curator_name)
                print(f"✅ Saved {sample_size} events to {out_path} ({self.total_events - len(used_indices)} remaining)")
                run_index += 1
                files_created += 1

                # Stop if we reached the requested number of files
                if self.num_files is not None and files_created >= self.num_files:
                    print(f"🎯 Generated requested {self.num_files} files, stopping.")
                    if os.path.exists(self.used_indices_path):
                        os.remove(self.used_indices_path)
                        print("🗑 Deleted used indices file after reaching requested files.")
                    return
    
    duration_cache = preload_audio_durations(base_folder=SOUND_BANK, sample_rate=48000)

    def synthesize_all(self, singlenotes_base_folder=SOUND_BANK, file_duration_cache=duration_cache, **kwargs):
        dataset_name = os.path.splitext(os.path.basename(self.event_json_path))[0]
        output_dir = os.path.join(self.output_folder, dataset_name, "audios")
        os.makedirs(output_dir, exist_ok=True)

        jams_files = [f for f in os.listdir(os.path.join(self.output_folder, dataset_name, 'jams')) if f.lower().endswith(".jams")]
        for jams_file in jams_files:
            jams_path = os.path.join(self.output_folder, dataset_name, 'jams', jams_file)
            synthesize_jams_to_audio(
                jams_file_path=jams_path,
                output_dir=output_dir,
                singlenotes_base_folder=singlenotes_base_folder,
                file_duration_cache=file_duration_cache,
                **kwargs
            )


# # --------------------------
# # Example usage for ChordEventsGenerator
# # --------------------------

# # 1️⃣ Create generator instance
# # User input parameters for `ChordEventsGenerator`:
# #   - event_json_path: str → JSON file containing chord events
# #   - used_indices_path: str → file to store used indices
# #   - num_to_sample: int → number of events per JAMS file
# #   - cycles: int → number of passes over all events
# #   - output_dir: str → folder to save generated JAMS files
# generator = ChordEventsGenerator(
#     event_json_path="Chords_Distribution/common_chords.json",
#     used_indices_path="used_indices.json",
#     num_to_sample=360,
#     cycles=1,
#     num_files=5
#     # curator=("User Name", "user@email.com"),
#     # annotator=("AnnotatorName", "1.0"),
#     # duration_range=(0.23, 1.2),
#     # silence_prob=1.0,
#     # silence_duration_range=(0.1, 0.5)
# )

# # 2️⃣ Generate JAMS files
# # No user parameters here; generate() uses the settings from the generator instance
# generator.generate()  # creates JAMS files

# # 3️⃣ Preload audio durations (needed for synthesis)
# # User input parameters for `preload_audio_durations`:
# #   - base_folder: str → folder containing single note audio samples
# #   - sample_rate: int → sample rate for duration calculation
# file_duration_cache = preload_audio_durations(
#     SOUND_BANK,   # folder containing single-note recordings
#     sample_rate=48000
# )

# # 4️⃣ Synthesize all generated JAMS to audio
# # User input parameters for `synthesize_all`:
# #   - singlenotes_base_folder: str → folder with single note audio samples
# #   - file_duration_cache: dict → preloaded durations
# #   - output_dir: str (optional) → folder where audio will be saved
# #   - **kwargs → additional parameters passed to synthesize_jams_to_audio
# generator.synthesize_all(
#     singlenotes_base_folder="SingleNotes",
#     file_duration_cache=file_duration_cache,
#     # Optional overrides:
#     # output_dir="ChordAudios",
#     # sample_rate=48000,
#     # fadein_samples=20,
#     # fadeout_samples=20,
#     # amplitude_range=(0.6, 0.9),
#     # noise_level_range=(0.001, 0.005)
# )