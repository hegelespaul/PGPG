import itertools
import json
import itertools
import json

NUM_STRINGS = 6
MAX_FRET = 19
MAX_SPAN = 4
MAX_FINGERS = 3

STANDARD_TUNING = {
    '1': 64,  # E4
    '2': 59,  # B3
    '3': 55,  # G3
    '4': 50,  # D3
    '5': 45,  # A2
    '6': 40   # E2
}

def generate_fretboard(fret_limit=MAX_FRET):
    return {
        str(s): list(range(0, fret_limit + 1))
        for s in range(1, NUM_STRINGS + 1)
    }

def has_duplicate_midi_notes(strings, frets):
    midi_notes = set()
    for s, f in zip(strings, frets):
        if f is None:
            continue
        midi = STANDARD_TUNING[s] + f
        if midi in midi_notes:
            return True
        midi_notes.add(midi)
    return False

def is_valid_fingering(strings, frets):
    fretted = [f for f in frets if f not in (None, 0)]
    if not fretted:
        return False

    # Rule: if any fret > 5, then disallow open strings (0)
    if any(f > 5 for f in frets if f is not None) and any(f == 0 for f in frets):
        return False

    if max(fretted) - min(fretted) > MAX_SPAN:
        return False

    lowest_fret = min(fretted)  # candidate for barre
    barre_indices = [i for i, f in enumerate(frets) if f == lowest_fret]
    if not barre_indices:
        return False

    first_barre_idx = min(barre_indices)

    for i, f in enumerate(frets):
        if f not in (None, 0) and i < first_barre_idx:
            return False

    other_frets = set(f for f in fretted if f != lowest_fret)
    total_fingers = 1 + len(other_frets)

    if total_fingers > MAX_FINGERS:
        return False

    if has_duplicate_midi_notes(strings, frets):
        return False

    return True

def generate_valid_chords():
    fretboard = generate_fretboard()
    all_chords = []

    for chord_size in range(2, 7):
        for strings in itertools.combinations(fretboard.keys(), chord_size):
            frets_options = [fretboard[s] for s in strings]

            for frets in itertools.product(*frets_options):
                if is_valid_fingering(strings, frets):
                    chord = [f"{s}-{f}" for s, f in zip(strings, frets)]
                    all_chords.append(chord)

    return all_chords

if __name__ == "__main__":
    valid_chords = generate_valid_chords()

    with open("valid_chords.json", "w") as f:
        json.dump(valid_chords, f, indent=4)

    print(f"Saved {len(valid_chords)} chords to pisitional_feasible_chords.json")