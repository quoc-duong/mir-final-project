import os
import pickle
import pandas as pd
import numpy as np
from tqdm import tqdm
import music21
from music21 import *
from music21.stream import Score, Part
from process_data import create_filtered_pickle


def compute_complexity(score):
    complexity_values = []
    measures_rh = score.parts[0].getElementsByClass(stream.Measure)
    measures_lh = score.parts[1].getElementsByClass(stream.Measure)
    lr = [Part(measures_lh), Part(measures_rh)]
    for voice in lr:
        # Convert the voice to a pitch array
        if len(voice.flat.notes.stream()) == 0:
            complexity_values.append(0)
            continue
        note_array = np.array([e.duration.quarterLength / len(e.pitches) if e.isChord and len(
            e.pitches) > 0 else e.duration.quarterLength for e in voice.flat.notes.stream()])

        if not len(note_array):
            complexity_values.append(0)
            continue

        complexity_values.append(len(note_array) / sum(note_array))

    # Return the average note complexity across all voices
    return np.mean(complexity_values)


def get_pitch_hist_single(material, countGraceNotes=True):

    df = pd.DataFrame(columns=['F#3', 'G#3', 'A3', 'A#3', 'B3', 'C#4',
                      'C##4', 'D#4', 'E4', 'F#4', 'G#4', 'A4', 'A#4', 'B4', 'C#5', 'D#5', 'E5', 'F#5', 'G#5', 'A5', 'A#5', 'B5', 'C#6'])

    for score in tqdm(material):
        loadedScore = converter.parse(score)

        rh = loadedScore.parts[0]
        lh = loadedScore.parts[1]
        parts = [lh, rh]
        # Work with each part
        for part in parts:
            # Get the notes from the current part
            notes = part.flat.notes.stream()
            print(notes)

            # Set the duration of grace notes if needed
            if countGraceNotes:
                minDur = 0.25
                for n in notes:
                    noteDur = n.quarterLength
                    if noteDur != 0 and noteDur < minDur:
                        minDur = noteDur

            df.loc[score] = [0] * len(df.columns)
            # Count pitches in the current segment
            for n in notes:
                noteName = n.nameWithOctave
                noteDur = n.quarterLength
                if noteDur == 0:
                    if not countGraceNotes:
                        continue
                if noteName not in df.columns:
                    df = df.assign(noteName=0)
                df.at[score, noteName] += noteDur

    return df


def create_complexity_df(score_list):
    df = pd.DataFrame(columns=['complexity'])

    for filename in tqdm(score_list):
        score = converter.parse(filename)
        complexity = compute_complexity(score)
        df.loc[filename] = complexity

    return df


def main():
    with open('filtered_mozart.pkl', 'rb') as f:
        filtered_musicxml_mozart = pickle.load(f)
    with open('filtered_beethoven.pkl', 'rb') as f:
        filtered_musicxml_beethoven = pickle.load(f)

    print(f"There is {len(filtered_musicxml_mozart)} Mozart files")
    print(f"There is {len(filtered_musicxml_beethoven)} Beethoven files")

    #df_mozart_complexity = create_complexity_df(filtered_musicxml_mozart)
    #df_beethoven_complexity = create_complexity_df(filtered_musicxml_beethoven)

    df_mozart_pitch = get_pitch_hist_single(filtered_musicxml_mozart)
    df_beethoven_pitch = get_pitch_hist_single(filtered_musicxml_beethoven)
    print(df_mozart_pitch)

    #df_mozart.to_csv('mozart.csv', index=True)
    #df_beethoven.to_csv('beethoven.csv', index=True)


if __name__ == '__main__':
    main()
