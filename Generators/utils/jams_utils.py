import json
import random
import librosa
import numpy as np
import glob
from pathlib import Path


def make_annotation_container(string_index, namespace, curator, annotator, inverted_strings):
    """Create a JAMS annotation container for pitch_contour or note_midi."""
    return {
        "annotation_metadata": {
            "curator": {"name": curator[0], "email": curator[1]},
            "annotator": {"name": annotator[0], "version": annotator[1]},
            "version": "1.0",
            "data_source": inverted_strings[string_index],
        },
        "namespace": namespace,
        "data": [] if namespace == "note_midi" else {"time": [], "duration": [], "value": [], "confidence": []},
        "sandbox": {},
        "time": None,
        "duration": None,
    }

def generate_random_notes(
    num_notes,
    standard_tuning,
    duration_range,
    silence_prob,
    silence_duration_range,
    curator_name,
    curator_email,
    annotator_name,
    annotator_version,
    inverted_strings,
    string_range=(1, 6),
    fret_range=(0, 12),
):
    """Generate random single notes for 6 strings."""

    pitch_annotations = [
        make_annotation_container(
            i, "pitch_contour",
            (curator_name, curator_email),
            (annotator_name, annotator_version),
            inverted_strings
        ) for i in range(6)
    ]

    midi_annotations = [
        make_annotation_container(
            i, "note_midi",
            (curator_name, curator_email),
            (annotator_name, annotator_version),
            inverted_strings
        ) for i in range(6)
    ]

    current_time = 0.0
    for i in range(num_notes):
        string = random.randint(*string_range)
        fret = random.randint(*fret_range)
        duration = round(random.uniform(*duration_range), 3)
        string_index = 6 - string
        base_midi = standard_tuning[string - 1]
        midi_note = base_midi + fret
        freq = librosa.midi_to_hz(midi_note)

        # Pitch annotation
        pitch_annotations[string_index]["data"]["time"].append(current_time)
        pitch_annotations[string_index]["data"]["duration"].append(duration)
        pitch_annotations[string_index]["data"]["value"].append(
            {"voiced": True, "index": i, "frequency": freq}
        )
        pitch_annotations[string_index]["data"]["confidence"].append(1.0)

        # MIDI annotation
        midi_annotations[string_index]["data"].append(
            {"time": current_time, "duration": duration, "value": midi_note, "confidence": 1.0}
        )

        # Silence
        if random.random() < silence_prob:
            current_time += round(random.uniform(*silence_duration_range), 3)
        current_time += duration

    # Finalize times
    for i in range(6):
        pitch_annotations[i]["time"] = round(current_time, 3)
        pitch_annotations[i]["duration"] = round(current_time, 3)
        midi_annotations[i]["time"] = round(current_time, 3)
        midi_annotations[i]["duration"] = round(current_time, 3)

    return pitch_annotations, midi_annotations, current_time

def make_chord_annotations(
    sampled_events,
    curator_name,
    curator_email,
    annotator_name,
    annotator_version,
    standard_tuning,
    inverted_strings,
    duration_range=(0.23, 1.2),
    silence_prob=1.0,
    silence_duration_range=(0.1, 0.5)
):
    """Create pitch_contour and note_midi annotations from sampled events."""

    pitch_contours, note_midis = [], []
    for i in range(6):
        pitch_contours.append({
            "annotation_metadata": {
                "curator": {"name": curator_name, "email": curator_email},
                "annotator": {"name": annotator_name, "version": annotator_version},
                "version": "1.0",
                "data_source": inverted_strings[i]
            },
            "namespace": "pitch_contour",
            "data": {"time": [], "duration": [], "value": [], "confidence": []},
            "sandbox": {},
            "time": None,
            "duration": None
        })
        note_midis.append({
            "annotation_metadata": {
                "curator": {"name": curator_name, "email": curator_email},
                "annotator": {"name": annotator_name, "version": annotator_version},
                "version": "1.0",
                "data_source": inverted_strings[i]
            },
            "namespace": "note_midi",
            "data": [],
            "sandbox": {},
            "time": None,
            "duration": None
        })

    current_time = 0.0
    for event_index, event in enumerate(sampled_events):
        duration = round(random.uniform(*duration_range), 3)
        for note in event:
            string, fret = map(int, note.split("-"))
            string_index = 6 - string
            midi_note = standard_tuning[string - 1] + fret
            freq = librosa.midi_to_hz(midi_note)

            pitch_contours[string_index]["data"]["time"].append(current_time)
            pitch_contours[string_index]["data"]["duration"].append(0.0)
            pitch_contours[string_index]["data"]["value"].append({
                "voiced": True,
                "index": event_index,
                "frequency": freq
            })
            pitch_contours[string_index]["data"]["confidence"].append(1.0)

            note_midis[string_index]["data"].append({
                "time": current_time,
                "duration": duration,
                "value": midi_note,
                "confidence": 1.0
            })

        if random.random() < silence_prob:
            silence = round(random.uniform(*silence_duration_range), 3)
        else:
            silence = 0.0
        current_time += duration + silence

    for i in range(6):
        pitch_contours[i]["time"] = pitch_contours[i]["duration"] = round(current_time, 3)
        note_midis[i]["time"] = note_midis[i]["duration"] = round(current_time, 3)

    return pitch_contours, note_midis, current_time

def save_jams(output_folder, cycle, run_index, annotations, duration, curator_name, title_prefix="Random Events"):
    """Save a JAMS file with the given annotations and return the output path."""

    jams_data = {
        "annotations": annotations,
        "file_metadata": {
            "title": f"{title_prefix} - Cycle {cycle}",
            "artist": curator_name,
            "duration": round(duration, 3),
            "jams_version": "0.3.1",
        },
        "sandbox": {},
    }

    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    out_path = output_folder / f"run_cycle{cycle:02d}_{run_index:03d}.jams"
    with open(out_path, "w") as f:
        json.dump(jams_data, f, indent=4)

    return out_path

def load_tone_bank(base_path):
    """Load available single note samples organized by string-fret folders."""
    base_path = Path(base_path)  # Convert to Path if it's a string
    tone_bank = {}
    for folder in base_path.iterdir():
        if folder.is_dir():
            key = folder.name  # e.g., '1-0'
            try:
                string_num, fret_num = map(int, key.split('-'))
            except ValueError:
                continue
            if fret_num <= 19:
                tone_bank[key] = list(folder.glob("*.wav"))
    return tone_bank

def parse_string_fret(s_f: str):
    """Split 's-f' string into int(string), int(fret)."""
    s, f = s_f.split("-")
    return int(s), int(f)

def generate_one_chord():
    """Generate a random chord as string-fret pairs."""
    chord_size = random.randint(2, 6)
    strings = random.sample(range(1, 7), chord_size)
    return [f"{s}-{random.randint(0, 19)}" for s in strings]

def generate_event(
    tone_bank,
    sr=48000,
    event_weights=(0.333, 0.333, 0.333),
    single_note_duration_range=(0.1, 1.0),
    chord_arpeggio_prob=0.7,
    arpeggio_gap_range=(0.05, 0.2),
    arpeggio_overlap_ratio=0.5,
    amplitude_range=(0.5, 1.0),
    chord_duration_range=(0.1, 0.8),
    strum_offset_range=(0.05, 1.0),
):
    """Randomly generate silence, single note, or chord event with configurable ranges."""

    event_type = random.choices(
        ["silence", "single_note", "chord"],
        weights=event_weights,
        k=1
    )[0]

    if event_type == "silence":
        return None

    elif event_type == "single_note":
        valid_keys = [k for k in tone_bank if tone_bank[k] and parse_string_fret(k)[1] != 0]
        if not valid_keys:
            return None
        key = random.choice(valid_keys)
        s, f = parse_string_fret(key)
        file = random.choice(tone_bank[key])
        y, _ = librosa.load(file, sr=sr)
        total_samples = len(y)
        duration_samples = int(total_samples * random.uniform(*single_note_duration_range))

        return [{
            "string": s,
            "fret": f,
            "file": str(file),
            "duration_samples": duration_samples,
            "time_offset_samples": 0,
            "amplitude": round(random.uniform(*amplitude_range), 3)
        }]

    elif event_type == "chord":
        chord = generate_one_chord()
        used_strings = set()
        tone_list = []

        is_arpeggio = random.random() < chord_arpeggio_prob
        if is_arpeggio:
            random.shuffle(chord)
            current_offset_samples = 0
            note_gap_samples = int(random.uniform(*arpeggio_gap_range) * sr)

            for key in chord:
                if key not in tone_bank or not tone_bank[key]:
                    continue
                s, f = parse_string_fret(key)
                if s in used_strings:
                    continue
                used_strings.add(s)
                file = random.choice(tone_bank[key])
                y, _ = librosa.load(file, sr=sr)
                total_samples = len(y)
                duration_samples = int(total_samples * random.uniform(*single_note_duration_range))

                tone_list.append({
                    "string": s,
                    "fret": f,
                    "file": str(file),
                    "duration_samples": duration_samples,
                    "time_offset_samples": current_offset_samples,
                    "amplitude": round(random.uniform(*amplitude_range), 3)
                })
                step = int(duration_samples * (1 - arpeggio_overlap_ratio)) + note_gap_samples
                current_offset_samples += step
        else:
            max_strum_offset_samples = int(random.uniform(*strum_offset_range) * sr)
            for key in chord:
                if key not in tone_bank or not tone_bank[key]:
                    continue
                s, f = parse_string_fret(key)
                if s in used_strings:
                    continue
                used_strings.add(s)
                file = random.choice(tone_bank[key])
                y, _ = librosa.load(file, sr=sr)
                total_samples = len(y)
                duration_samples = int(total_samples * random.uniform(*chord_duration_range))
                time_offset_samples = random.randint(0, max_strum_offset_samples)

                tone_list.append({
                    "string": s,
                    "fret": f,
                    "file": str(file),
                    "duration_samples": duration_samples,
                    "time_offset_samples": time_offset_samples,
                    "amplitude": round(random.uniform(*amplitude_range), 3)
                })

        return tone_list if tone_list else None