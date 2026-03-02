from Generators import SingleNotesGenerator, ChordEventsGenerator, ComplexGenerator
import glob
import os
import shutil

# ===========================
# USER SETTINGS
# ===========================
NUM_FILES = 15   # total files in the combined dataset

PROPORTIONS = {   # fractions for each generator
    "single": 1/3,
    "chord": 1/3,
    "complex": 1/3
}

OUTPUT_DIR = "Combined"  # final dataset folder
CHORD_JSON = "Chords_Distribution/common_chords.json"
TONE_BANK = "SingleNotes"

# ===========================
# CALCULATE DISTRIBUTION
# ===========================
num_single = int(NUM_FILES * PROPORTIONS["single"])
num_chord = int(NUM_FILES * PROPORTIONS["chord"])
num_complex = NUM_FILES - num_single - num_chord  # ensure sum = NUM_FILES

print(f"🎯 Target distribution: {num_single} single, {num_chord} chord, {num_complex} complex")

# ===========================
# 1. SINGLE NOTES
# ===========================
print("\n🎵 Generating Single Notes...")
single_gen = SingleNotesGenerator(
    num_notes=360, 
    num_files=num_single, 
    output_folder="SingleNotesPerformances"
)
single_gen.generate()
single_gen.synthesize_all()

# ===========================
# 2. CHORD EVENTS
# ===========================
print("\n🎹 Generating Chord Events...")
chord_gen = ChordEventsGenerator(
    event_json_path=CHORD_JSON,
    used_indices_path="used_indices.json",
    num_to_sample=360,
    cycles=1,
    num_files=num_chord,
    output_folder="ChordEventsPerformances"
)
chord_gen.generate()
chord_gen.synthesize_all()

# ===========================
# 3. COMPLEX EVENTS
# ===========================
print("\n🎼 Generating Complex Events...")
complex_config = {
    "tone_bank_path": TONE_BANK,
    "noise_level": 0.2,
    "event_weights": (0.5, 0.3, 0.2),  # silence, single note, chord
    "chord_arpeggio_prob": 0.9,
    "output_folder": "ComplexEventsPerformances"
}
complex_gen = ComplexGenerator(complex_config)
complex_gen.run(num_samples=num_complex, num_events_per_sample=300)

# ===========================
# 4. COLLECT FILES
# ===========================
print("\n📂 Collecting files...")

single_audio = glob.glob("SingleNotesPerformances/audios/*.wav")
chord_audio = glob.glob("ChordEventsPerformances/audios/*.wav")
complex_audio = glob.glob("ComplexEventsPerformances/audios/*.wav")

single_jams = glob.glob(f"SingleNotesPerformances/{CHORD_JSON}/jams/*.jams")
chord_jams = glob.glob("ChordEventsPerformances/jams/*.jams")  # unified!
complex_jams = glob.glob("ComplexEventsPerformances/jams/*.jams")

combined_audio = single_audio[:num_single] + chord_audio[:num_chord] + complex_audio[:num_complex]
combined_jams  = single_jams[:num_single] + chord_jams[:num_chord] + complex_jams[:num_complex]

# ===========================
# 5. SAVE COMBINED DATASET
# ===========================
audio_dir = os.path.join(OUTPUT_DIR, "audios")
jams_dir = os.path.join(OUTPUT_DIR, "jams")
os.makedirs(audio_dir, exist_ok=True)
os.makedirs(jams_dir, exist_ok=True)

for f in combined_audio:
    shutil.copy(f, os.path.join(audio_dir, os.path.basename(f)))

for f in combined_jams:
    shutil.copy(f, os.path.join(jams_dir, os.path.basename(f)))

print("\n✅ Combined dataset ready!")
print("   Audios →", audio_dir)
print("   JAMS   →", jams_dir)
