import os
import subprocess
import pandas as pd
import argparse
import getch
import signal


def main():
    # Set up argparse
    parser = argparse.ArgumentParser(description='Annotate Musescore files')
    parser.add_argument('dir_path',
                        type=str,
                        help='Path to directory containing Musescore files')
    parser.add_argument('--csv_path',
                        default='score_annotation.csv',
                        type=str,
                        help='Path to output CSV file')
    args = parser.parse_args()
    # Get list of all subdirectories in directory
    subdir_list = [f.path for f in os.scandir(args.dir_path) if f.is_dir()]

    # Iterate through subdirectories and get list of .mscz files in each
    file_list = []
    for subdir in subdir_list:
        subdir_files = [os.path.join(subdir, f) for f in os.listdir(
            subdir) if f.endswith('.mscz')]
        file_list += subdir_files

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

    # Save annotations to CSV file
    annotations_df.to_csv(args.csv_path, index=True)

    print("Annotations:")
    print(annotations_df)


if __name__ == "__main__":
    main()
