import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import librosa
import librosa.display
import numpy as np
import os
import jams

def tablaturize_jams(jam, audio_path, save_path=None):
    # MIDI numbers for open strings from 6th (low E) to 1st (high e)
    str_midi_dict = {0: 40, 1: 45, 2: 50, 3: 55, 4: 59, 5: 64}
    string_dict = {0: 'E', 1: 'A', 2: 'D', 3: 'G', 4: 'B', 5: 'e'}
    style_dict = {0: 'r', 1: 'y', 2: 'b', 3: '#FF7F50', 4: 'g', 5: '#800080'}

    # Create figure with two vertical subplots: tab on top, spectrogram below
    fig, (ax_tab, ax_spec) = plt.subplots(2, 1, figsize=(20, 8), gridspec_kw={'height_ratios': [1, 1.5]}, sharex=True)

    handle_list = []
    s = 0  # string index (0 = lowest string, 5 = highest)

    # Try to find either note_midi or pitch_midi annotations
    annos = jam.search(namespace='note_midi')
    if len(annos) == 0:
        annos = jam.search(namespace='pitch_midi')

    for string_track in annos:
        color = style_dict[s]
        handle_list.append(
            mlines.Line2D([], [], color=color, label=string_dict[s])
        )
        # Draw horizontal bars for durations on ax_tab
        for note in string_track:
            start_time = note[0]
            duration = note[1]
            ax_tab.barh(y=s+1, width=duration, left=start_time, height=0.6, color=color, alpha=0.2, edgecolor=None)
        # Draw fret markers on top
        for note in string_track:
            start_time = note[0]
            midi_note = note[2]
            fret = int(round(midi_note - str_midi_dict[s]))
            ax_tab.scatter(start_time, s+1,
                           marker="${}$".format(fret),
                           color=color, zorder=10)
        s += 1

    # Vertical grid lines for time on ax_tab
    for t in range(0, 100):
        if t % 4 == 0:
            ax_tab.axvline(x=t, color='black', linestyle='-', linewidth=0.8)  # solid every 4 sec
        else:
            ax_tab.axvline(x=t, color='gray', linestyle='--', linewidth=0.5)  # dotted every 1 sec

    # Horizontal lines per string on ax_tab
    for string in range(1, 7):
        ax_tab.axhline(y=string, color='gray', linestyle='-', linewidth=0.1, alpha=1)

    # Labels and legend on ax_tab
    ax_tab.set_ylabel('String Number')
    ax_tab.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), handles=handle_list, ncol=6)
    ax_tab.set_ylim(0.5, 6.5)
    ax_tab.set_yticks([1, 2, 3, 4, 5, 6])
    ax_tab.set_yticklabels(['E', 'A', 'D', 'G', 'B', 'e'])  # Strings from low to high
    # ax_tab.invert_yaxis()
    ax_tab.set_xlim(0, 100)

    # Audio spectrogram plot if audio path is provided
    if audio_path:
        y, sr = librosa.load(audio_path, sr=None)
        # Compute constant-Q spectrogram
        C = librosa.cqt(y, sr=sr, hop_length=512)
        C_db = librosa.amplitude_to_db(np.abs(C), ref=np.max)
        librosa.display.specshow(C_db, sr=sr, x_axis='time', y_axis='cqt_note', hop_length=512, ax=ax_spec)
        ax_spec.set_title('Constant-Q Spectrogram')
        ax_spec.set_xlim(0, 100)
        ax_spec.label_outer()  # hide x-label on top plot

    ax_tab.set_title('Guitar Tab Notation with Note Durations')
    ax_tab.set_xlabel('Time (seconds)')

    plt.tight_layout()

    # Save or show
    if save_path:
        plt.savefig(save_path)
    else:
        plt.show()

# ✅ Load .jams file correctly
# jam_path = os.path.join('data', 'SingleNotesGenerator_outputs', 'jams', 'run_cycle00_001.jams')
# audio_path = os.path.join('data', 'SingleNotesGenerator_outputs', 'audios', 'run_cycle00_001.wav')

# jam_path = os.path.join('data', 'ChordEventsGenerator_outputs','common_chords', 'jams', 'run_cycle01_001.jams')
# audio_path = os.path.join('data', 'ChordEventsGenerator_outputs','common_chords', 'audios', 'run_cycle01_001.wav')

# jam_path = os.path.join('Combined',  'jams', 'complex_001.jams')
# audio_path = os.path.join('Combined', 'audios', 'complex_001.wav')

jam_path = 'synthetic_060.jams'
audio_path = 'synthetic_060.wav'

jam = jams.load(jam_path)

tablaturize_jams(jam, audio_path, save_path='Fig2.png')
