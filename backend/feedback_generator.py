def generate_feedback(confidence, fillers, pause_ratio, wpm):
    feedback = []

    if confidence < 40:
        feedback.append("Low confidence detected.")
    elif confidence < 70:
        feedback.append("Moderate confidence.")
    else:
        feedback.append("Good confidence.")

    if fillers > 5:
        feedback.append("Too many filler words.")
    else:
        feedback.append("Good fluency.")

    if pause_ratio > 0.3:
        feedback.append("Frequent pauses detected.")

    if wpm < 90:
        feedback.append("Speaking too slowly.")
    elif wpm > 180:
        feedback.append("Speaking too fast.")

    return feedback
