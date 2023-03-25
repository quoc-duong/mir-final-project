# mir-final-project

Classification of Mozart and Beethoven scores with extracted features such as pitch histogram and note density using music21.

Dataset retrieved from https://github.com/musescore/MuseScore/tree/30557dec4e573f0aa5e78043da1b7564da222452

Metadata file `score.jsonl` retrieved from https://musescore-dataset.xmader.com/score.jsonl

## Usage

### `process_data.py`

Using the metadata file, we can retrieve information about instruments and the composers in the description.

To retrieve the piano only scores, use the `--process`, which will save the list of piano-only MuseScore files from Mozart and Beethoven in the `data` folder.

To convert the `.mscz` files into MusicXML (`.musicxml`), you can run the script with `--convert` which will require the pickle files generated with `--process` option. It will create the `.musicxml` files in the same directories as the `.mscz` files. Runs the MuseScore program as a subprocess (mscore) to convert all the files.

>WARNING: the `--convert` option might get stuck for unknown reasons, you can run
`musescore.mscore -j data.json` manually to convert your data. With data.json being the json containing the input in `.mscz` and output in `.musicxml`. You can use the function `create_convert_batch` to create your json file. For more information: https://musescore.org/en/handbook/3/command-line-options#Run_a_batch_job_converting_multiple_documents

The script will generated pickle files that contain the list of Mozart and Beethoven in MusicXML format.

```
python process_data.py <musescore_directory> --process --convert
```

After getting the list of Mozart and Beethoven files in MusicXML format, you will find the separated `.mscz` and `.musicxml` datasets in `dataset_mscz` and `dataset_musicxml`.

### `extract_features.py`

Extract features from Mozart and Beethoven MusicXML files such as pitch histogram and note density (or complexity) in csv files.
Requires `dataset_musicxml` with subfolders `mozart` and `beethoven` containing MusicXML files.

### `classification.py`

Uses Random Forests to classify between Mozart and Beethoven scores and computes feature importance.
