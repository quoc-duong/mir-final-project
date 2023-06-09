import os
import pandas as pd
import numpy as np
from tqdm import tqdm
import music21
from music21 import *
from music21.stream import Score, Part
import glob


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
    df = pd.DataFrame()
    for score in tqdm(material):
        loadedScore = converter.parse(score)
        measures_rh = loadedScore.parts[0]
        measures_lh = loadedScore.parts[1]
        lr = [Part(measures_lh), Part(measures_rh)]

        for voice in lr:
            for e in voice.flat.notes.stream():
                if not df.empty and score not in df.index:
                    df.loc[score] = [0] * len(df.columns)
                if e.isChord:
                    for n in e.notes:
                        noteName = n.nameWithOctave
                        noteDur = n.quarterLength
                        if noteDur == 0:
                            if not countGraceNotes:
                                continue
                        if noteName not in df:
                            df[noteName] = 0
                        if score not in df.index:
                            df.loc[score] = 0
                        df.at[score, noteName] += noteDur
                else:
                    noteName = e.nameWithOctave
                    noteDur = e.quarterLength
                    if noteDur == 0:
                        if not countGraceNotes:
                            continue
                    if noteName not in df:
                        df[noteName] = 0
                    if score not in df.index:
                        df.loc[score] = 0
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
    dataset_path = './dataset_musicxml/'
    mozart_files = glob.glob(dataset_path + 'mozart/*')
    beethoven_files = glob.glob(dataset_path + 'beethoven/*')

    print(f"There is {len(mozart_files)} Mozart files")
    print(f"There is {len(beethoven_files)} Beethoven files")

    df_mozart_complexity = create_complexity_df(mozart_files)
    df_beethoven_complexity = create_complexity_df(beethoven_files)
    df_mozart_complexity.to_csv('complexity_mozart.csv', index=True)
    df_beethoven_complexity.to_csv(
        'complexity_beethoven.csv', index=True)

    df_mozart_pitch = get_pitch_hist_single(mozart_files)
    df_beethoven_pitch = get_pitch_hist_single(beethoven_files)

    # Get all columns from both pitch histograms
    columns = list(set(df_mozart_pitch.columns).union(
        set(df_beethoven_pitch.columns)))

    # Reindex dataframes with union of columns, filling missing values with 0
    df_mozart_pitch = df_mozart_pitch.reindex(columns=columns, fill_value=0)
    df_beethoven_pitch = df_beethoven_pitch.reindex(
        columns=columns, fill_value=0)

    df_mozart_pitch.to_csv('pitch_mozart.csv', index=True)
    df_beethoven_pitch.to_csv('pitch_beethoven.csv', index=True)


if __name__ == '__main__':
    main()
