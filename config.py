import os

# Base directory for generated outputs
BASE_OUTPUT_DIR = "data"

# Metadata
CURATOR = ("Hegel Pedroza", "h.pedroza@correo.ler.uam.mx")
ANNOTATOR = ("Synthetic Generator", "1.0")

# Single notes audio folder
SOUND_BANK="SingleNotes"

# Build default folders dynamically using class names
def get_output_dir(class_name: str) -> str:
    """
    Returns a default directory for a given class name.
    """
    return os.path.join(BASE_OUTPUT_DIR, f"{class_name}_outputs")