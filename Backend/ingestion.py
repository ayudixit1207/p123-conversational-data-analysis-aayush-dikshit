import os
import csv
import re
import uuid
import pandas as pd
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = "Uploads"


def save_file(file):

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    filename = secure_filename(file.filename or "")

    if not filename:
        raise ValueError("Invalid file name")

    file_path = os.path.join(
        UPLOAD_FOLDER,
        f"{uuid.uuid4().hex}_{filename}"
    )

    file.save(file_path)

    return file_path


def is_forest_dataset(file_path):

    with open(
        file_path,
        "r",
        encoding="utf-8",
        errors="ignore"
    ) as file:

        content = file.read().lower()

    return (
        "bejaia region dataset" in content
        and
        "sidi-bel abbes region dataset" in content
    )


def read_forest_dataset(file_path):

    with open(
        file_path,
        "r",
        encoding="utf-8",
        errors="ignore"
    ) as file:

        lines = file.readlines()


    columns = [
        "day",
        "month",
        "year",
        "Temperature",
        "RH",
        "Ws",
        "Rain",
        "FFMC",
        "DMC",
        "DC",
        "ISI",
        "BUI",
        "FWI",
        "Classes"
    ]


    rows = []

    current_region = None


    for raw_line in lines:

        line = raw_line.strip()

        if not line:
            continue


        lower = line.lower()


        # Region headings
        if "bejaia region dataset" in lower:

            current_region = "Bejaia"
            continue


        if (
            "sidi-bel abbes region dataset"
            in lower
        ):

            current_region = "Sidi-Bel Abbes"
            continue


        # Header rows
        if (
            "day" in lower
            and "month" in lower
            and "year" in lower
            and "temperature" in lower
            and "classes" in lower
        ):

            continue


        if current_region is None:
            continue


        try:

            parts = next(
                csv.reader([line])
            )

        except Exception:

            continue


        parts = [
            value.strip()
            for value in parts
        ]


        # Fix malformed row
        # Example: 14.6 9

        if len(parts) == 13:

            fixed = []

            for value in parts:

                match = re.match(
                    r"^(-?\d+(?:\.\d+)?)\s+(\d+)$",
                    value
                )

                if match:

                    fixed.append(
                        match.group(1)
                    )

                    fixed.append(
                        match.group(2)
                    )

                else:

                    fixed.append(value)


            parts = fixed


        if len(parts) != 14:
            continue


        # Validate first three columns

        try:

            int(float(parts[0]))
            int(float(parts[1]))
            int(float(parts[2]))

        except Exception:

            continue


        rows.append(
            parts + [current_region]
        )


    data = pd.DataFrame(
        rows,
        columns=columns + ["Region"]
    )


    numeric_columns = [
        "day",
        "month",
        "year",
        "Temperature",
        "RH",
        "Ws",
        "Rain",
        "FFMC",
        "DMC",
        "DC",
        "ISI",
        "BUI",
        "FWI"
    ]

    data = data.replace(
        r"^\s*$",
        pd.NA,
        regex=True
    )

    data = data.replace(
        [
            "",
            " ",
            "NULL",
            "null",
            "NA",
            "na",
            "N/A",
            "n/a",
            "NaN",
            "nan",
            "?",
            "-",
            "#N/A"
        ],
        pd.NA
    )

    for column in numeric_columns:

        data[column] = pd.to_numeric(
            data[column],
            errors="coerce"
        )


    data["Classes"] = (
        data["Classes"]
        .astype(str)
        .str.strip()
    )


    data["Region"] = (
        data["Region"]
        .astype(str)
        .str.strip()
    )


    data = data.dropna(
        subset=[
            "day",
            "month",
            "year"
        ]
    )


    data = data.reset_index(
        drop=True
    )


    return data


def read_csv(file_path):

    if is_forest_dataset(file_path):

        return read_forest_dataset(
            file_path
        )


    # Normal CSV

    missing_values = [
        "",
        " ",
        "NULL",
        "null",
        "NA",
        "na",
        "N/A",
        "n/a",
        "NaN",
        "nan",
        "?",
        "-",
        "#N/A"
    ]

    try:

        data = pd.read_csv(
            file_path,
            sep=None,
            engine="python",
            encoding="utf-8",
            on_bad_lines="skip",
            keep_default_na=True,
            na_values=missing_values,
            skipinitialspace=True
        )

    except Exception:

        data = pd.read_csv(
            file_path,
            sep=None,
            engine="python",
            encoding="latin1",
            on_bad_lines="skip",
            keep_default_na=True,
            na_values=missing_values,
            skipinitialspace=True
        )


    data = data.replace(
        r"^\s*$",
        pd.NA,
        regex=True
    )

    data.columns = [
        str(column).strip()
        for column in data.columns
    ]


    data = data.dropna(
        axis=1,
        how="all"
    )


    data = data.dropna(
        axis=0,
        how="all"
    )


    return data


def read_multiple_files(files):

    dataframes = []
    file_names = []


    for file in files:

        if not file.filename:
            continue


        if not file.filename.lower().endswith(
            ".csv"
        ):
            continue


        file_path = save_file(file)

        data = read_csv(
            file_path
        )


        dataframes.append(data)

        file_names.append(
            file.filename
        )


    return dataframes, file_names