from itertools import product
import json


forte_classes = {
    "2-note": {"2-1": [0, 1], "2-2": [0, 2], "2-3": [0, 3], "2-4": [0, 4], "2-5": [0, 5], "2-6": [0, 6]},
    "3-note": {"3-1": [0, 1, 2], "3-2": [0, 1, 3], "3-3": [0, 1, 4], "3-4": [0, 1, 5], "3-5": [0, 1, 6],
               "3-6": [0, 2, 4], "3-7": [0, 2, 5], "3-8": [0, 2, 6], "3-9": [0, 2, 7], "3-10": [0, 3, 6],
               "3-11": [0, 3, 7], "3-12": [0, 4, 7]},
    "4-note": {"4-1": [0, 1, 2, 3], "4-2": [0, 1, 2, 4], "4-3": [0, 1, 2, 5], "4-4": [0, 1, 2, 6],
               "4-5": [0, 1, 3, 4], "4-6": [0, 1, 3, 5], "4-7": [0, 1, 3, 6], "4-8": [0, 1, 3, 7],
               "4-9": [0, 1, 4, 5], "4-10": [0, 1, 4, 6], "4-11": [0, 1, 4, 7], "4-12": [0, 1, 5, 6],
               "4-13": [0, 1, 5, 7], "4-14": [0, 1, 5, 8], "4-15": [0, 1, 6, 7], "4-16": [0, 2, 3, 5],
               "4-17": [0, 2, 3, 6], "4-18": [0, 2, 4, 6], "4-19": [0, 2, 4, 7], "4-20": [0, 2, 5, 7],
               "4-21": [0, 2, 5, 8], "4-22": [0, 2, 6, 8], "4-23": [0, 2, 6, 9], "4-24": [0, 3, 4, 7],
               "4-25": [0, 3, 5, 7], "4-26": [0, 3, 5, 8], "4-27": [0, 3, 6, 8], "4-28": [0, 3, 6, 9],
               "4-29": [0, 4, 6, 8], "4-30": [0, 4, 6, 9], "4-31": [0, 4, 7, 10]}
}

string_tunings = [40, 45, 50, 55, 59, 64]  # MIDI numbers E2..E4
max_fret = 15
pisadas = []

for string_idx, open_midi in enumerate(string_tunings, 1):
    for fret in range(1, max_fret + 1):  # exclude open strings
        pc = (open_midi + fret) % 12
        pisadas.append([string_idx, fret, pc])

def normalize_chord_5frets(chord):
    """Shift lowest fret to 1 (all frets >0)"""
    frets = [f for (_, f, _) in chord]
    min_fret = min(frets)
    return [(s, f - min_fret + 1, pc) for (s, f, pc) in chord]

def is_valid_chord(chord):
    """No repeated strings, no repeated pitch classes, fits within 5 frets"""
    strings = [s for (s, _, _) in chord]
    pcs = [pc for (_, _, pc) in chord]
    if len(strings) != len(set(strings)):
        return False
    if len(pcs) != len(set(pcs)):
        return False
    frets = [f for (_, f, _) in chord]
    return (max(frets) - min(frets) + 1) <= 5

def positions_for_set(forte_set, pisadas):
    """Return all combinations of fret positions matching a Forte set"""
    groups = []
    for pc in forte_set:
        group = [p for p in pisadas if p[2] == pc]
        if not group:
            return []
        groups.append(group)

    combos = []
    for prod in product(*groups):
        if is_valid_chord(prod):
            combos.append(list(prod))
    return combos


all_diagrams = []
seen = set()
window = 5  # 5-fret shapes

for category in forte_classes:
    for fc_name, pc_set in forte_classes[category].items():
        chord_positions = positions_for_set(pc_set, pisadas)
        for chord in chord_positions:
            norm_chord = normalize_chord_5frets(chord)
            min_fret = min(f for (_, f, _) in norm_chord)
            # generate all transpositions that fit within 1..15 frets
            for offset in range(-1, max_fret - window + 1):
                transposed = [(s, f + offset, pc) for (s, f, pc) in norm_chord]
                if is_valid_chord(transposed):
                    key = tuple(sorted((s, f, pc) for (s, f, pc) in transposed))
                    if key not in seen:
                        seen.add(key)
                        diagram = [f"{s}-{f}" for (s, f, pc) in transposed]
                        all_diagrams.append(diagram)

# remove duplicates after generation
unique_diagrams = []
seen_diagrams = set()
for diagram in all_diagrams:
    key = tuple(diagram)  
    if key not in seen_diagrams:
        seen_diagrams.add(key)
        unique_diagrams.append(diagram)

all_diagrams = unique_diagrams

print(json.dumps(all_diagrams[:10], indent=2))  # first 10 diagrams

with open("no_bar_chords.json", "w") as f:
    json.dump(all_diagrams, f, indent=2)