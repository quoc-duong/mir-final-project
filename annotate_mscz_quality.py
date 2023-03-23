import os
import subprocess
import pandas as pd
import argparse
import getch
import signal
import json
from tqdm import tqdm
import pickle
import re


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


def mscz2musicxml(score_list, to_discard):
    json_out = []

    for filename in tqdm(score_list):
        c = 0
        for f in to_discard:
            if filename == f:
                c = 1
                break
        if c:
            continue
        musicxml_name = filename.replace('.mscz', '.musicxml')
        if os.path.exists(musicxml_name):
            continue
        output = {}
        output['in'] = filename
        output['out'] = musicxml_name
        json_out.append(output)
    print(f"Job will process {len(json_out)} files")
    return json_out


def count_musicxml(file_list):
    count = 0

    for file in file_list:
        musicxml_file = os.path.splitext(file)[0] + '.musicxml'
        if os.path.exists(musicxml_file):
            count += 1
            print(f'{file} has a corresponding musicxml file.')

    print(f'Total number of files with corresponding musicxml: {count}')


def main():
    args = parse_args()
    # file_list = get_mscz_paths(args.dir_path)
    # piano_only_scores, with_piano_scores = filter_piano(
    #    file_list, args.metadata)
    # with open('piano_only.pkl', 'wb') as f:
    #    pickle.dump(piano_only_scores, f)

    # with open('with_piano.pkl', 'wb') as f:
    #    pickle.dump(with_piano_scores, f)

    # Load the list from the file
    with open('piano_only.pkl', 'rb') as f:
        piano_only_scores = pickle.load(f)

    to_discard = []
    pattern = r"\.\./MuseScore/\d+/\d+\.mscz"
    json_batch = mscz2musicxml(piano_only_scores, to_discard)
    while True:
        mscore_process = subprocess.Popen(
            ['musescore.mscore', '-j', 'data.json'], stderr=subprocess.PIPE)
        mscore_process.wait()

        # Get last error line
        err_out = mscore_process.stderr.read().decode()
        matches = re.findall(pattern, err_out)
        if len(matches) != 0:
            problematic_file = matches[-1]
            print(problematic_file)
            if problematic_file not in to_discard:
                print(f"Discarding {problematic_file}")
                to_discard.append(problematic_file)
        # Add file that's problematic to the discard list
        print(to_discard)
        json_batch = mscz2musicxml(piano_only_scores, to_discard)
        if len(json_batch) == 0:
            break
        with open('data.json', 'w') as f:
            json.dump(json_batch, f)
        count_musicxml(piano_only_scores)
    count_musicxml(piano_only_scores)
    exit(0)
    annotations_df = annotate_scores(piano_only_scores)

    # Save annotations to CSV file
    annotations_df.to_csv(args.csv_path, index=True)

    print("Annotations:")
    print(annotations_df)


if __name__ == "__main__":
    main()
