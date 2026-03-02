from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import numpy as np

def per_string_metrics(pred, gt):
    """
    Compute accuracy, precision, recall, and F1 per string, plus mean across strings.

    Args:
        pred: np.array, shape (N, 6, num_classes), one-hot predictions
        gt:   np.array, shape (N, 6, num_classes), one-hot ground truth

    Returns:
        metrics: dict with per-string metrics and overall mean for precision, recall, F1
    """
    pred_idx = np.argmax(pred, axis=-1)  # convert one-hot to class indices (N,6)
    gt_idx   = np.argmax(gt, axis=-1)

    metrics = {}
    accs, precisions, recalls, f1s = [], [], [], []

    for s in range(6):
        y_true = gt_idx[:, s]
        y_pred = pred_idx[:, s]

        acc = accuracy_score(y_true, y_pred)
        prec = precision_score(y_true, y_pred, average="weighted", zero_division=0)
        rec = recall_score(y_true, y_pred, average="weighted", zero_division=0)
        f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0)

        metrics[f"string_{6-s}"] = {
            "accuracy": acc,
            "precision": prec,
            "recall": rec,
            "f1": f1
        }

        accs.append(acc)
        precisions.append(prec)
        recalls.append(rec)
        f1s.append(f1)

    # Mean across all strings
    metrics["mean"] = {
        "accuracy": np.mean(accs),
        "precision": np.mean(precisions),
        "recall": np.mean(recalls),
        "f1": np.mean(f1s)
    }

    return metrics


def global_unused_open_fretted_strings(pred, gt):
    pred_classes = np.argmax(pred, axis=-1)  # (N,6)
    gt_classes   = np.argmax(gt, axis=-1)    # (N,6)

    # Map to 3 states
    map_to_state = lambda x: np.where(x==0, 0, np.where(x==1, 1, 2))
    pred_states = map_to_state(pred_classes)
    gt_states   = map_to_state(gt_classes)

    precisions, recalls, f1s = [], [], []
    for s in range(6):  # per string
        y_true = gt_states[:, s]
        y_pred = pred_states[:, s]
        precisions.append(precision_score(y_true, y_pred, average="weighted", zero_division=0))
        recalls.append(recall_score(y_true, y_pred, average="weighted", zero_division=0))
        f1s.append(f1_score(y_true, y_pred, average="weighted", zero_division=0))

    return {
        "accuracy": accuracy_score(gt_states.flatten(), pred_states.flatten()),
        "precision": np.mean(precisions),
        "recall": np.mean(recalls),
        "f1": np.mean(f1s),
    }

def cardinality_accuracy(pred, gt):
    """
    Compute chord cardinality accuracy (overall + per group).

    - A chord's cardinality = number of active strings per chord.
    - inactive (unused) = index 0 in one-hot vector
    - active (open/fretted) = index 1 or higher

    Args:
        pred: np.array of shape (N,6,num_classes), one-hot encoded predictions
        gt:   np.array of shape (N,6,num_classes), one-hot encoded labels

    Returns:
        dict with:
            "overall": float
            "by_cardinality": {k: acc for chords with cardinality=k}
    """
    # Convert one-hot to class indices
    pred_classes = np.argmax(pred, axis=-1)  # shape (N,6)
    gt_classes   = np.argmax(gt, axis=-1)    # shape (N,6)

    # Count active strings per chord (ignore unused = index 0)
    card_pred = np.sum(pred_classes != 0, axis=1)
    card_true = np.sum(gt_classes != 0, axis=1)

    # Overall accuracy
    overall_acc = np.mean(card_pred == card_true)

    # Per-cardinality group accuracy
    by_card = {}
    for k in range(2, 7):  # groups 2..6 active strings
        mask = (card_true == k)
        if np.any(mask):  # only if such chords exist
            acc_k = np.mean(card_pred[mask] == card_true[mask])
            by_card[k] = acc_k
        else:
            by_card[k] = None  # or 0.0 if you prefer

    return {
        "overall": overall_acc,
        "by_group": by_card
    }

def fretboard_hamming_distance(pred, gt):
    """
    Compute unweighted Chord Shape Distance (CSD) per chord size (2–6 notes)
    and global mean for a batch of chords (6x21 one-hot labels),
    penalizing any mismatch, including extra notes on unused strings.
    
    Args:
        pred: np.array of shape (N,6,21), one-hot predictions
        gt:   np.array of shape (N,6,21), one-hot labels
    
    Returns:
        csd_per_size: dict {num_notes: mean unweighted CSD for chords with num_notes}
        global_mean: float, mean unweighted CSD over all chords
    """
    N = len(pred)
    pred_classes = np.argmax(pred, axis=-1)  # (N,6)
    gt_classes   = np.argmax(gt, axis=-1)    # (N,6)
    
    csd_list = []
    csd_by_size = {n: [] for n in range(2, 7)}
    
    for i in range(N):
        # Count active strings in GT
        active_true = np.where(gt_classes[i] != 0)[0]
        num_notes = len(active_true)
        if num_notes < 2 or num_notes > 6:
            continue  # skip non-chords
        
        # Unweighted CSD per chord, penalize any mismatch
        csd = 0.0
        for s in range(6):
            y_true = gt_classes[i, s]
            y_pred = pred_classes[i, s]
            if y_true != y_pred:
                csd += 1.0
        csd /= 6.0  # normalize by total strings

        csd_list.append(csd)
        csd_by_size[num_notes].append(csd)
    
    # Mean CSD per chord size
    csd_per_size = {n: (np.mean(csd_by_size[n]) if csd_by_size[n] else 0.0) for n in range(2, 7)}
    global_mean = np.mean(csd_list) if csd_list else 0.0
    
    return csd_per_size, global_mean

def fret_error_distance_per_string(pred, gt):
    """
    Compute Fret Error Distance (FED) per string and overall average
    for one-hot encoded chords (6x21 vectors).

    Handles:
    - Unused strings (index 0) in GT are ignored
    - Open strings (index 1) mapped to fret 0
    - Fretted strings (index 2-20) mapped to fret index-1
    - Missing predicted strings (pred index 0) are penalized with the fret number

    Args:
        pred: np.array of shape (N,6,21), one-hot predictions
        gt:   np.array of shape (N,6,21), one-hot labels

    Returns:
        {
            "per_string": {1: mean_fed_str1, ..., 6: mean_fed_str6},
            "overall": float
        }
    """
    N = len(pred)
    pred_classes = np.argmax(pred, axis=-1)  # shape (N,6)
    gt_classes   = np.argmax(gt, axis=-1)    # shape (N,6)

    per_string_errors = {s: [] for s in range(6)}  # string indices 0-5

    for i in range(N):
        for s in range(6):
            gt_val = gt_classes[i, s]
            pred_val = pred_classes[i, s]

            if gt_val == 0:
                continue  # skip unused strings in GT

            # Ground truth fret: 0=open, else fret index -1
            fret_true = 0 if gt_val == 1 else gt_val - 1

            # Handle missing predicted string
            if pred_val == 0:
                error = fret_true  # penalize proportionally to fret
            else:
                fret_pred = 0 if pred_val == 1 else pred_val - 1
                error = abs(fret_pred - fret_true)

            per_string_errors[s].append(error)

    # Compute mean per string
    per_string_mean = {6-s: (np.mean(v) if v else 0.0)
                       for s, v in per_string_errors.items()}

    # Overall mean across strings
    overall_mean = np.mean(list(per_string_mean.values()))

    return {
        "per_string": per_string_mean,
        "overall": overall_mean
    }

def chord_spacing_consistency(pred, gt):
    """
    Compute Chord Spacing Consistency (CSC) per chord size and global mean,
    including both vertical (Y, strings) and horizontal (X, frets) distances.

    Args:
        pred: np.array of shape (N,6,21), one-hot predictions
        gt:   np.array of shape (N,6,21), one-hot labels

    Returns:
        csc_per_size: dict {num_notes: {"X": mean CSC-X, "Y": mean CSC-Y}}
        global_csc: dict with mean CSC-X and CSC-Y averaged across chord sizes
    """
    N = len(pred)
    pred_classes = np.argmax(pred, axis=-1)  # (N,6)
    gt_classes   = np.argmax(gt, axis=-1)    # (N,6)

    # Store per-chord-size CSC
    csc_by_size = {n: {"X": [], "Y": []} for n in range(2,7)}

    for i in range(N):
        active_true = np.where(gt_classes[i] != 0)[0]
        active_pred = np.where(pred_classes[i] != 0)[0]

        num_notes = len(active_true)
        if num_notes < 2 or num_notes > 6 or len(active_pred) < 2:
            continue

        # --- Y-span (strings)
        span_true_y = active_true.max() - active_true.min()
        span_pred_y = active_pred.max() - active_pred.min()
        csc_y = 1.0 - abs(span_true_y - span_pred_y) / 5.0
        csc_y = np.clip(csc_y, 0.0, 1.0)

        # --- X-span (frets)
        frets_true = gt_classes[i][active_true]
        frets_pred = pred_classes[i][active_pred]
        span_true_x = frets_true.max() - frets_true.min()
        span_pred_x = frets_pred.max() - frets_pred.min()
        csc_x = 1.0 - abs(span_true_x - span_pred_x) / 20.0
        csc_x = np.clip(csc_x, 0.0, 1.0)

        csc_by_size[num_notes]["X"].append(csc_x)
        csc_by_size[num_notes]["Y"].append(csc_y)

    # Mean CSC per chord size
    csc_per_size = {
        n: {
            "X": float(np.mean(csc_by_size[n]["X"])) if csc_by_size[n]["X"] else 0.0,
            "Y": float(np.mean(csc_by_size[n]["Y"])) if csc_by_size[n]["Y"] else 0.0
        }
        for n in range(2,7)
    }

    # Global mean across all chord sizes that have at least one chord
    all_x = [v for n in csc_by_size for v in csc_by_size[n]["X"]]
    all_y = [v for n in csc_by_size for v in csc_by_size[n]["Y"]]
    global_csc = {
        "X": float(np.mean(all_x)) if all_x else 0.0,
        "Y": float(np.mean(all_y)) if all_y else 0.0
    }

    return csc_per_size, global_csc