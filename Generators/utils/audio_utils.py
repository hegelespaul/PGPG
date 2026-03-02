import os
import json
import random
import numpy as np
import librosa
import glob
import jams
import soundfile as sf
import time

# --------------------------
# 1. Preload audio durations
# --------------------------
def preload_audio_durations(base_folder, sample_rate=48000):
    """
    Scan all folders in `base_folder` and cache the duration of each audio file.

    Returns:
        dict: {folder_name: [(filename, duration), ...]}
    """
    duration_cache = {}
    start_total = time.time()

    for folder in os.listdir(base_folder):
        folder_start = time.time()
        folder_path = os.path.join(base_folder, folder)
        if not os.path.isdir(folder_path):
            continue
        valid_files = []
        for file in os.listdir(folder_path):
            if file.lower().endswith(('.wav', '.flac', '.aiff', '.mp3')):
                filepath = os.path.join(folder_path, file)
                try:
                    dur = librosa.get_duration(path=filepath, sr=sample_rate)
                    valid_files.append((file, dur))
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")
        if valid_files:
            duration_cache[folder] = valid_files
        folder_end = time.time()
        print(f"Processed folder '{folder}' in {folder_end - folder_start:.2f} seconds")

    end_total = time.time()
    print(f"Total preloading time: {end_total - start_total:.2f} seconds")
    return duration_cache

# --------------------------
# 2. Pad audio for stretch
# --------------------------
def pad_audio_for_stretch(y, n_fft=2048):
    """
    Pad audio with zeros if shorter than `n_fft` for time-stretching.
    """
    if len(y) < n_fft:
        y = np.pad(y, (0, n_fft - len(y)), mode='constant')
    return y

# --------------------------
# 3. Apply fade-in / fade-out
# --------------------------
def apply_fade(y, fadein_samples=20, fadeout_samples=20):
    """
    Apply fade-in and fade-out to an audio signal.
    """
    fade_in_window = np.hanning(fadein_samples * 2)[:fadein_samples]
    fade_out_window = np.hanning(fadeout_samples * 2)[fadeout_samples:]
    
    if len(y) >= fadein_samples:
        y[:fadein_samples] *= fade_in_window
    if len(y) >= fadeout_samples:
        y[-fadeout_samples:] *= fade_out_window
    return y

# --------------------------
# 4. Scale audio amplitude randomly
# --------------------------
def scale_amplitude(y, amplitude_range=(0.6, 0.9)):
    """
    Scale the amplitude of an audio array by a random factor in `amplitude_range`.
    """
    rand_amp = random.uniform(*amplitude_range)
    return y * rand_amp

# --------------------------
# 5. Add light white noise
# --------------------------
def add_white_noise(y, noise_level_range=(0.001, 0.005)):
    """
    Add small white noise to an audio signal.
    """
    noise_level = random.uniform(*noise_level_range)
    noise = np.random.normal(0, noise_level, size=y.shape)
    return y + noise

# --------------------------
# 5. Synthesize Jams
# --------------------------
def synthesize_jams_to_audio(
    jams_file_path,
    output_dir,
    singlenotes_base_folder,
    file_duration_cache,
    sample_rate=48000,
    fadein_samples=20,
    fadeout_samples=20,
    amplitude_range=(0.6, 0.9),
    noise_level_range=(0.001, 0.005)):
    
    """Standalone function to convert a JAMS file into polyphonic audio."""
    jam_data = jams.load(jams_file_path)
    num_samples = int(jam_data.file_metadata.duration * sample_rate)
    string_audio = np.zeros((6, num_samples))

    for ann in jam_data['annotations']:

        if ann['namespace'] != 'note_midi':
            continue
        
        string_idx = int(ann['annotation_metadata']['data_source'])
        
        for note_event in ann['data']:
            time = note_event[0]
            dur = note_event[1]
            midi_note = note_event[2]
            
            STANDARD_TUNING = [40, 45, 50, 55, 59, 64]
            fret = midi_note - STANDARD_TUNING[string_idx]
            folder_name = f"{6 - string_idx}-{fret}"
            note_folder = os.path.join(singlenotes_base_folder, folder_name)

            if folder_name not in file_duration_cache:
                continue

            valid_files = [
                fname for fname, file_dur in file_duration_cache[folder_name]
                if file_dur >= dur
            ]
            if not valid_files:
                print(f"Warning: No valid file found in {folder_name} for duration {dur}")
                continue

            audio_file = random.choice(valid_files)
            y, _ = librosa.load(os.path.join(note_folder, audio_file), sr=sample_rate, mono=False)
            
            if y.ndim == 2:  # stereo
                L, R = y[0], y[1]
                y = 0.5 * (L + R)   # mid channel (phase-safe average)
            else:
                y = y  # already mono
                
            y = y[:int(dur * sample_rate)] 
            y = librosa.util.normalize(y)
            y = apply_fade(y, fadein_samples, fadeout_samples)
            y = scale_amplitude(y, amplitude_range)

            start = int(time * sample_rate)
            end = min(start + len(y), num_samples)
            string_audio[string_idx, start:end] += y[:end-start]
            

    poly_audio = np.sum(string_audio, axis=0)
    poly_audio = add_white_noise(poly_audio, noise_level_range)
    poly_audio = librosa.util.normalize(poly_audio)

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, os.path.splitext(os.path.basename(jams_file_path))[0] + ".wav")
    sf.write(output_path, poly_audio, sample_rate, subtype='PCM_24')
    print(f"Saved audio: {output_path}")
    return output_path

def synthesizer(
    performance,
    curator_name,
    curator_email,
    annotator_name,
    annotator_version,
    output_audio="synthetic.wav",
    output_jams="synthetic.jams",
    sr=48000,
    standard_tuning=[64, 59, 55, 50, 45, 40],
 
):
    """Render synthetic performance as audio and JAMS annotations."""
    audio_buffer = np.zeros(1, dtype=np.float32)
    current_sample = 0
    annotations = [[] for _ in range(6)]

    fade_duration = 0.05
    fade_samples = int(fade_duration * sr)
    hann = np.hanning(fade_samples * 2)
    fade_in, fade_out = hann[:fade_samples], hann[fade_samples:]

    for tone_list in performance:
        if tone_list is None:
            silence_samples = int(random.uniform(0.1, 5) * sr)
            current_sample += silence_samples
            continue

        max_end_sample = current_sample
        for tone in tone_list:
            s, f = tone["string"], tone["fret"]
            y, _ = librosa.load(tone["file"], sr=sr)

            if y.ndim == 2:
                y = 0.5 * (y[0] + y[1])
            y = y / np.max(np.abs(y)) if np.max(np.abs(y)) > 0 else y
            y *= tone["amplitude"]

            desired_samples = tone["duration_samples"]
            if len(y) < desired_samples:
                y = np.pad(y, (0, desired_samples - len(y)), mode='constant')
            else:
                y = y[:desired_samples]

            if len(y) > fade_samples * 2:
                y[:fade_samples] *= fade_in
                y[-fade_samples:] *= fade_out

            start = current_sample + tone["time_offset_samples"]
            end = start + len(y)
            if end > len(audio_buffer):
                audio_buffer = np.pad(audio_buffer, (0, end - len(audio_buffer)), mode='constant')

            audio_buffer[start:end] += y

            midi_note = standard_tuning[s - 1] + f
            annotations[s - 1].append({
                "time": start / sr,
                "duration": desired_samples / sr,
                "value": midi_note,
                "confidence": 1.0
            })
            max_end_sample = max(max_end_sample, end)

        current_sample = max_end_sample + int(random.uniform(0.1, 0.3) * sr)

    audio_buffer = audio_buffer[:current_sample]
    duration_seconds = current_sample / sr
    audio_buffer = add_background_noise(
        audio_buffer, sr, duration_seconds,
        noise_folder="FloorDataset",
        noise_level=random.uniform(0.5, 1.0)
    )

    sf.write(output_audio, audio_buffer, sr)

    jam_annotations = []
    for i, ann in enumerate(reversed(annotations)):
        jam_annotations.append({
            "annotation_metadata": {
                "curator": {"name": curator_name, "email": curator_email},
                "annotator": {"name": annotator_name, "version": annotator_version},
                "version": "1.0",
                "data_source": str(i)
            },
            "namespace": "note_midi",
            "data": ann,
            "sandbox": {},
            "time": duration_seconds,
            "duration": duration_seconds
        })

    jams_data = {
        "annotations": jam_annotations,
        "file_metadata": {
            "title": "Synthetic Performance",
            "artist": "Hegel Pedroza",
            "duration": duration_seconds,
            "jams_version": "0.3.1"
        },
        "sandbox": {}
    }
    with open(output_jams, "w") as f:
        json.dump(jams_data, f, indent=4)

    print(f"✅ Synthesized audio: {output_audio}")
    print(f"✅ JAMS annotation: {output_jams}")

def add_background_noise(audio_buffer, sr, total_duration, noise_folder="FloorDataset", noise_level=0.1):
    """Mix background noise into an audio buffer with normalization."""
    noise_files = glob.glob(f"{noise_folder}/**/*.wav", recursive=True)
    if not noise_files:
        print("No background noise files found.")
        return audio_buffer

    noise_file = random.choice(noise_files)
    noise_audio, _ = librosa.load(noise_file, sr=sr)

    total_length = int(sr * total_duration)
    repeats = (total_length // len(noise_audio)) + 1
    noise_full = np.tile(noise_audio, repeats)[:total_length]

    if len(audio_buffer) < total_length:
        pad_amount = total_length - len(audio_buffer)
        audio_buffer = np.pad(audio_buffer, (0, pad_amount), mode='constant')
    else:
        audio_buffer = audio_buffer[:total_length]

    mixed_audio = audio_buffer + noise_full * noise_level

    max_amp = np.max(np.abs(mixed_audio))
    if max_amp > 1.0:
        mixed_audio = mixed_audio / max_amp

    return mixed_audio[:len(audio_buffer)]