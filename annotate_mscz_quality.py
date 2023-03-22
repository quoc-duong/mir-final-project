import os
import subprocess
import pandas as pd
import argparse
import getch
import signal
import json
from tqdm import tqdm


def parse_args():
    # Set up argparse
    parser = argparse.ArgumentParser(description='Annotate Musescore files')
    parser.add_argument('dir_path',
                        type=str,
                        help='Path to directory containing Musescore files')
    parser.add_argument('--metadata',
                        default='score.jsonl',
                        type=str,
                        help='Path to metadata file')
    parser.add_argument('--csv_path',
                        default='score_annotation.csv',
                        type=str,
                        help='Path to output CSV file')
    return parser.parse_args()


def filter_piano(filenames, metadata):
    lookup = {}

    with open(metadata) as f:
        # Parse each line in the file
        for line in tqdm(f):
            # Parse the JSON in the line
            data = json.loads(line)
            # Add the JSON object to the lookup table using the authorUserId as the key
            try:
                lookup[data["id"]] = data
            except KeyError:
                pass

    piano_only = []
    with_piano = []
    # Iterate over the filenames
    for filename in tqdm(filenames):
        # Extract the ID from the filename
        file_id = os.path.splitext(os.path.basename(filename))[0]
        # Look up the corresponding JSON object in the lookup table using the ID as the key
        if file_id in lookup:
            # Check if the instrumentsNames field contains "Piano"
            if ["Piano"] == lookup[file_id]["instrumentsNames"]:
                piano_only.append(filename)
            elif "Piano" in lookup[file_id]["instrumentsNames"]:
                with_piano.append(filename)
    print(
        f'Got {len(piano_only)} piano-only scores and {len(with_piano)} scores that contain piano')
    return piano_only, with_piano


def get_mscz_paths(dir_path):
    # Get list of all subdirectories in directory
    subdir_list = [f.path for f in os.scandir(dir_path) if f.is_dir()]

    # Iterate through subdirectories and get list of .mscz files in each
    file_list = []
    for subdir in subdir_list:
        subdir_files = [os.path.join(subdir, f) for f in os.listdir(
            subdir) if f.endswith('.mscz')]
        file_list += subdir_files
    return file_list


def annotate_scores(file_list):
    # Create empty pandas DataFrame to store annotations
    annotations_df = pd.DataFrame(columns=['filename', 'quality'])
    annotations_df = annotations_df.set_index('filename')
    # Iterate through files and annotate
    for filename in file_list:
        # Open file with Musescore
        mscore_process = subprocess.Popen(
            ['musescore.mscore', filename],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        print(f"Enter annotation for {filename} (g = good, b = bad):")

        # Prompt user to input annotation
        annotation = None
        while annotation not in ['g', 'b', 'q']:
            annotation = getch.getch()
        print(f"Annotation for {filename}: {annotation}")

        # Add annotation to DataFrame
        if annotation == 'g':
            annotations_df.loc[filename] = {'quality': True}
        elif annotation == 'b':
            annotations_df.loc[filename] = {'quality': False}
        elif annotation == 'q':
            print("Stopping program early and saving csv")
            break
    return annotations_df


def main():
    args = parse_args()
    file_list = get_mscz_paths(args.dir_path)
    piano_only_scores, with_piano_scores = filter_piano(
        file_list, args.metadata)
    annotations_df = annotate_scores(piano_only_scores)

    # Save annotations to CSV file
    annotations_df.to_csv(args.csv_path, index=True)

    print("Annotations:")
    print(annotations_df)


if __name__ == "__main__":
    main()
