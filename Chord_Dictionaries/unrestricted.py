import itertools
import json

NUM_STRINGS = 6
MAX_FRET = 19
MIN_CHORD_SIZE = 1
MAX_CHORD_SIZE = 6
BATCH_SIZE = 100000  # Write every 100k chords

def generate_chords():
    # Yield chords one by one, no large memory usage
    for size in range(MIN_CHORD_SIZE, MAX_CHORD_SIZE + 1):
        string_combinations = itertools.combinations(range(1, NUM_STRINGS + 1), size)
        for strings in string_combinations:
            fret_ranges = [range(0, MAX_FRET + 1) for _ in strings]
            for frets in itertools.product(*fret_ranges):
                chord = [f"{s}-{f}" for s, f in zip(strings, frets)]
                yield chord

def write_chords_streaming(filename):
    with open(filename, "w") as f:
        f.write("[\n")  # Start JSON array

        batch = []
        count = 0
        for chord in generate_chords():
            batch.append(chord)
            count += 1

            if len(batch) >= BATCH_SIZE:
                # Write batch to file as JSON lines, comma separated
                f.write(",\n".join(json.dumps(c) for c in batch))
                f.write(",\n")
                batch = []
                print(f"Written {count} chords...")

        # Write remaining batch without trailing comma
        if batch:
            f.write(",\n".join(json.dumps(c) for c in batch))

        f.write("\n]\n")  # End JSON array

    print(f"Done writing {count} chords to {filename}")

if __name__ == "__main__":
    write_chords_streaming("unrestricted.json")
