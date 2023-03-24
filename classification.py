import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib
import time

import matplotlib.pyplot as plt

CSVs = {
    'mozart': [
        './data/complexity_mozart.csv',
        './data/pitch_mozart.csv'
    ],
    'beethoven': [
        './data/complexity_beethoven.csv',
        './data/pitch_beethoven.csv'
    ]
}


def convert_func(x):
    return round(eval(x), 3) if isinstance(x, str) else x


def load_data(CSVs):
    # Add missing columns for each pitch csv
    df_mo = pd.read_csv('data/pitch_mozart.csv', index_col=0)
    df_be = pd.read_csv('data/pitch_beethoven.csv', index_col=0)
    columns = list(set(df_mo.columns).union(set(df_be.columns)))

    # Reindex dataframes with union of columns, filling missing values with 0
    df_mo = df_mo.reindex(columns=columns, fill_value=0)
    df_be = df_be.reindex(columns=columns, fill_value=0)

    df_mo.to_csv('data/pitch_mozart.csv', index=True)
    df_be.to_csv('data/pitch_beethoven.csv', index=True)

    X = []
    y = []

    if not isinstance(CSVs, object):
        raise Exception('CSVs must be an object')

    column_names = None
    print(f'Train mozart/beethoven scores')
    for subtype in CSVs.keys():
        print(f'Composer: {subtype}')
        for csv in CSVs[subtype]:
            print(f'csv {csv}')

        df_complexity = pd.read_csv(CSVs[subtype][0], index_col=0)
        df_pitch = pd.read_csv(CSVs[subtype][1], index_col=0)

        merged_df = pd.merge(df_complexity, df_pitch, how='inner',
                             left_index=True, right_index=True)

        # Drop NaN rows
        merged_df.dropna(inplace=True)
        # Convert fractional values to float
        merged_df = merged_df.applymap(convert_func)
        # Use numerical index
        merged_df = merged_df.reset_index(drop=True)
        column_names = merged_df.columns.to_numpy()

        for index, row in merged_df.iterrows():
            X.append(row)
            y.append(subtype)

    X = np.array(X)
    y = np.array(y)
    print(
        f'Done loading data! \nShape of X: {X.shape} \nShape of y: {y.shape}')
    return X, y, column_names


def train(X_train, y_train, model_name):
    # Initialize
    forest = RandomForestClassifier(random_state=0)
    forest.fit(X_train, y_train)

    # Save model weights to file
    joblib.dump(forest, model_name)


def compute_importances_on_impurity(column_names, model_name):
    forest = joblib.load(model_name)
    # Bad hardcoded labels
    # feature_names = pd.read_csv('../data/ihd_dan.csv').columns[1:]

    # feature_names = [f"feature {i}" for i in range(X.shape[1])]
    start_time = time.time()
    importances = forest.feature_importances_
    std = np.std(
        [tree.feature_importances_ for tree in forest.estimators_], axis=0)
    elapsed_time = time.time() - start_time

    print(
        f"Elapsed time to compute the importances: {elapsed_time:.3f} seconds")

    forest_importances = pd.Series(importances, index=column_names)

    fig, ax = plt.subplots()
    forest_importances.plot.bar(yerr=std, ax=ax)
    ax.set_title(f"Feature importances using MDI, model: {model_name}")
    ax.set_ylabel("Mean decrease in impurity")
    fig.tight_layout()
    plt.show()


def test(X_test, y_test, model_name):
    # Load from saved model weights file
    forest = joblib.load(model_name)
    y_pred = forest.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    return accuracy


def main():
    # Data loading and preparing
    X, y, column_names = load_data(CSVs)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, stratify=y, random_state=42)

    # Training the model
    train(X_train, y_train, 'composer_model.joblib')
    print('Done training role type.')

    # Testing the model
    acc = test(X_test, y_test, 'composer_model.joblib')
    print(f'Role Type Accuracy: {acc}')

    # Feature importance
    compute_importances_on_impurity(column_names, 'composer_model.joblib')


if __name__ == '__main__':
    main()
