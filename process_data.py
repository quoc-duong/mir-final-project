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
import music21
import shutil


def parse_args():
    # Set up argparse
    parser = argparse.ArgumentParser(description='Annotate Musescore files')
    parser.add_argument('--dir_path',
                        default='../MuseScore/',
                        type=str,
                        help='Path to directory containing Musescore files')
    parser.add_argument('--metadata',
                        default='./data/score.jsonl',
                        type=str,
                        help='Path to metadata file')
    parser.add_argument('--csv_path',
                        default='./data/score_annotation.csv',
                        type=str,
                        help='Path to output CSV file')
    parser.add_argument('--process',
                        action='store_true',
                        help='Retrieve piano only scores and store in a pickle file (piano_only.pkl)')
    parser.add_argument('--convert',
                        action='store_true',
                        help='Convert mscz files to musicxml')
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

    beethoven = []
    mozart = []
    # Iterate over the filenames
    for filename in tqdm(filenames):
        # Extract the ID from the filename
        file_id = os.path.splitext(os.path.basename(filename))[0]
        # Look up the corresponding JSON object in the lookup table using the ID as the key
        if file_id in lookup:
            # Check if the instrumentsNames field contains "Piano"
            if ["Piano"] == lookup[file_id]["instrumentsNames"]:
                if 'beethoven' in lookup[file_id]["description"].lower():
                    beethoven.append(filename)
                elif 'mozart' in lookup[file_id]["description"].lower():
                    mozart.append(filename)
    print(
        f'Got {len(mozart)} Mozart scores and {len(beethoven)} Beethoven scores')
    return mozart, beethoven


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


def mscz2musicxml(scores, json_name):
    to_discard = []
    pattern = r"\.\./MuseScore/\d+/\d+\.mscz"
    json_batch = create_convert_batch(scores, to_discard)
    with open(json_name, 'w') as f:
        json.dump(json_batch, f)
    while True:
        mscore_process = subprocess.Popen(
            ['musescore.mscore', '-j', json_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print('Waiting to finish')
        mscore_process.wait()
        print('Done')

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
        json_batch = create_convert_batch(scores, to_discard)
        if len(json_batch) == 0:
            break
        with open(json_name, 'w') as f:
            json.dump(json_batch, f)
        print(f"Files to process: {len(json_batch)}")


def create_convert_batch(score_list, to_discard):
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


def get_musicxml_paths(file_list):
    count = 0
    musicxml_paths = []
    for file in file_list:
        musicxml_file = os.path.splitext(file)[0] + '.musicxml'
        if os.path.exists(musicxml_file):
            musicxml_paths.append(musicxml_file)
            count += 1

    print(f'Total number of files with corresponding musicxml: {count}')
    return musicxml_paths


def filter_empty(scores):
    musicxml_paths = get_musicxml_paths(scores)
    filtered_paths = []
    for musicxml in tqdm(musicxml_paths):
        try:
            score = music21.converter.parse(musicxml)
        except music21.Music21Exception:
            continue
        except Exception:
            continue
        if len(score.parts) < 2:
            continue
        rh = score.parts[0].getElementsByClass(music21.stream.Measure)
        lh = score.parts[1].getElementsByClass(music21.stream.Measure)

        if len(rh) == 0 or len(lh) == 0:
            print("The staff is empty")
            print(musicxml)
        else:
            filtered_paths.append(musicxml)
    return filtered_paths


def create_filtered_pickle(filename, obj):
    filtered_musicxml = None
    if not os.path.exists(filename):
        filtered_musicxml = filter_empty(obj)
        with open(filename, 'wb') as f:
            pickle.dump(filtered_musicxml, f)
    else:
        with open(filename, 'rb') as f:
            filtered_musicxml = pickle.load(f)
    return filtered_musicxml


def create_dataset():
    # Create .mscz dataset
    with open('./data/mozart.pkl', 'rb') as f:
        mozart_mscz = pickle.load(f)
    with open('./data/beethoven.pkl', 'rb') as f:
        beethoven_mscz = pickle.load(f)

    os.makedirs('dataset_mscz', exist_ok=True)
    mozart_dir = './dataset_mscz/mozart'
    beethoven_dir = './dataset_mscz/beethoven'
    os.makedirs(mozart_dir, exist_ok=True)
    os.makedirs(beethoven_dir, exist_ok=True)

    for filepath in mozart_mscz:
        shutil.copy(filepath, mozart_dir)
    for filepath in beethoven_mscz:
        shutil.copy(filepath, beethoven_dir)

    # Create MusicXML dataset
    with open('./data/filtered_mozart.pkl', 'rb') as f:
        mozart_musicxml = pickle.load(f)
    with open('./data/filtered_beethoven.pkl', 'rb') as f:
        beethoven_musicxml = pickle.load(f)

    os.makedirs('dataset_musicxml', exist_ok=True)
    mozart_dir = './dataset_musicxml/mozart'
    beethoven_dir = './dataset_musicxml/beethoven'
    os.makedirs(mozart_dir, exist_ok=True)
    os.makedirs(beethoven_dir, exist_ok=True)

    for filepath in mozart_musicxml:
        shutil.copy(filepath, mozart_dir)
    for filepath in beethoven_musicxml:
        shutil.copy(filepath, beethoven_dir)


def main():
    args = parse_args()
    if args.process:
        file_list = get_mscz_paths(args.dir_path)
        mozart, beethoven = filter_piano(
            file_list, args.metadata)

        # Store Mozart and Beethoven MuseScore files list in pickle files
        with open('./data/mozart.pkl', 'wb') as f:
            pickle.dump(mozart, f)

        with open('./data/beethoven.pkl', 'wb') as f:
            pickle.dump(beethoven, f)

    with open('./data/mozart.pkl', 'rb') as f:
        mozart = pickle.load(f)
    with open('./data/beethoven.pkl', 'rb') as f:
        beethoven = pickle.load(f)

    if args.convert:
        mscz2musicxml(mozart, './data/mozart.json')
        mscz2musicxml(beethoven, './data/beethoven.json')

    filtered_musicxml_mozart = create_filtered_pickle(
        './data/filtered_mozart.pkl', mozart)
    filtered_musicxml_beethoven = create_filtered_pickle(
        './data/filtered_beethoven.pkl', beethoven)

    print(f"There is {len(filtered_musicxml_mozart)} Mozart files")
    print(f"There is {len(filtered_musicxml_beethoven)} Beethoven files")

    create_dataset()


if __name__ == "__main__":
    main()
