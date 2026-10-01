import pandas as pd


def get_raw_missing(file_path):

    total_missing = 0
    column_missing = {}


    try:

        with open(
            file_path,
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as file:

            lines = file.readlines()


        content = "".join(lines).lower()


        is_forest = (
            "bejaia region dataset" in content
            and
            "sidi-bel abbes region dataset" in content
        )

        if is_forest:
            from Backend.ingestion import read_forest_dataset

            raw = read_forest_dataset(file_path)
            total_missing = int(raw.isna().sum().sum())

            for column in raw.columns:
                column_missing[str(column).strip()] = int(
                    raw[column].isna().sum()
                )

            return total_missing, column_missing


        # =================================
        # NORMAL CSV
        # =================================

        if not is_forest:

            try:

                raw = pd.read_csv(
                    file_path,
                    sep=None,
                    engine="python",
                    encoding="utf-8"
                )

            except Exception:

                raw = pd.read_csv(
                    file_path,
                    sep=None,
                    engine="python",
                    encoding="latin1"
                )


            total_missing = int(
                raw.isna().sum().sum()
            )


            for column in raw.columns:

                column_missing[
                    str(column).strip()
                ] = int(
                    raw[column].isna().sum()
                )


            return total_missing, column_missing


        # =================================
        # FOREST FIRE DATASET
        # =================================

        header_found = False


        for line in lines:

            line = line.strip()

            if not line:
                continue


            lower = line.lower()


            # ---------------------------------
            # Region heading
            # ---------------------------------

            if (
                "sidi-bel abbes region dataset"
                in lower
            ):

                # If this file is interpreted as
                # a normal CSV row, 13 fields
                # are missing.

                total_missing += 13

                continue


            if (
                "bejaia region dataset"
                in lower
            ):

                continue


            # ---------------------------------
            # Header
            # ---------------------------------

            if (
                "day" in lower
                and "month" in lower
                and "year" in lower
                and "temperature" in lower
                and "classes" in lower
            ):

                header_found = True
                continue


            if not header_found:
                continue


            # ---------------------------------
            # Read data row
            # ---------------------------------

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


            # ---------------------------------
            # Malformed row
            # ---------------------------------

            if len(parts) == 13:

                for value in parts:

                    match = re.match(
                        r"^(-?\d+(?:\.\d+)?)\s+(\d+)$",
                        value
                    )

                    if match:

                        total_missing += 1

                        column_missing["FWI"] = 1

                        break


        return total_missing, column_missing


    except Exception as error:

        print(
            "Missing calculation error:",
            error
        )

        return 0, {}


def get_profile(
    data,
    raw_missing=0,
    raw_column_missing=None,
    source_files=None
):

    profile = {}

    missing_mask = data.isna()

    for column in data.select_dtypes(
        include=["object", "string"]
    ).columns:
        missing_mask[column] |= (
            data[column]
            .astype("string")
            .str.strip()
            .eq("")
            .fillna(False)
        )

    actual_missing = int(missing_mask.sum().sum())

    if raw_column_missing is None:
        raw_column_missing = {}

    if actual_missing > int(raw_missing):
        raw_missing = actual_missing

    actual_column_missing = missing_mask.sum().astype(int).to_dict()

    for column, missing in actual_column_missing.items():
        raw_value = raw_column_missing.get(column)
        if raw_value is not None:
            raw_column_missing[column] = max(
                int(raw_value),
                int(missing)
            )
        else:
            raw_column_missing[column] = int(missing)

    profile["rows"] = int(len(data))
    profile["columns"] = int(len(data.columns))
    profile["duplicate_rows"] = int(data.duplicated().sum())

    column_details = []
    source_files = source_files or []
    missing_total = 0
    for column in data.columns:
        missing = max(
            int(raw_column_missing.get(column, 0)),
            int(actual_column_missing[column]),
        )

        if source_files:
            present_rows = sum(
                int(source["rows"])
                for source in source_files
                if column in source["schema"]
            )
            absent_rows = max(0, len(data) - present_rows)
            missing = max(0, missing - absent_rows)
            percentage_denominator = present_rows
        else:
            percentage_denominator = len(data)

        missing_total += missing
        missing_percent = (
            round((missing / percentage_denominator) * 100, 2)
            if percentage_denominator
            else 0
        )
        column_details.append({
            "name": str(column),
            "type": str(data[column].dtype),
            "missing": missing,
            "missing_percent": missing_percent,
            "unique": int(data[column].nunique(dropna=True)),
        })
    profile["column_details"] = column_details
    profile["total_missing"] = (
        missing_total
        if source_files
        else int(max(raw_missing, actual_missing))
    )

    numeric_summary = []
    numeric_columns = data.select_dtypes(include="number").columns
    for column in numeric_columns:
        values = data[column].dropna()
        if values.empty:
            continue
        numeric_summary.append({
            "column": str(column),
            "count": int(values.count()),
            "mean": round(float(values.mean()), 2),
            "median": round(float(values.median()), 2),
            "std": round(float(values.std()), 2),
            "min": round(float(values.min()), 2),
            "max": round(float(values.max()), 2),
        })
    profile["numeric_summary"] = numeric_summary

    categorical_summary = []
    categorical_columns = data.select_dtypes(include="object").columns
    for column in categorical_columns:
        values = data[column].value_counts(dropna=False).head(10)
        categorical_summary.append({
            "column": str(column),
            "values": [
                {"value": str(value), "count": int(count)}
                for value, count in values.items()
            ],
        })
    profile["categorical_summary"] = categorical_summary

    if source_files:
        preview_frames = []
        row_offset = 0

        for source in source_files:
            source_rows = int(source["rows"])
            source_preview = data.iloc[
                row_offset:row_offset + source_rows
            ].head(5).copy()
            source_preview.insert(
                0,
                "Source File",
                source.get("name", "Uploaded file")
            )
            preview_frames.append(source_preview)
            row_offset += source_rows

        preview = (
            pd.concat(preview_frames, ignore_index=True)
            if preview_frames
            else data.head(10)
        )
    else:
        preview = data.head(10)

    preview = preview.astype(object)
    preview = preview.where(pd.notna(preview), None)
    profile["preview"] = preview.to_dict(orient="records")

    preview_groups = []
    if source_files:
        row_offset = 0
        for source in source_files:
            source_rows = int(source["rows"])
            source_columns = [
                column
                for column in source["schema"]
                if column in data.columns
            ]
            source_preview = data.iloc[
                row_offset:row_offset + source_rows
            ][source_columns].head(5).astype(object)
            source_preview = source_preview.where(
                pd.notna(source_preview),
                None
            )
            preview_groups.append({
                "name": source.get("name", "Uploaded file"),
                "columns": [str(column) for column in source_columns],
                "rows": source_preview.to_dict(orient="records"),
            })
            row_offset += source_rows
    else:
        preview_groups.append({
            "name": "Dataset",
            "columns": [str(column) for column in data.columns],
            "rows": profile["preview"],
        })

    profile["preview_groups"] = preview_groups

    return profile


    for column in numeric_columns:

        values = data[column].dropna()


        if len(values) == 0:
            continue


        numeric_summary.append({

            "column":
                str(column),

            "count":
                int(values.count()),

            "mean":
                round(
                    float(values.mean()),
                    2
                ),

            "median":
                round(
                    float(values.median()),
                    2
                ),

            "std":
                round(
                    float(values.std()),
                    2
                ),

            "min":
                round(
                    float(values.min()),
                    2
                ),

            "max":
                round(
                    float(values.max()),
                    2
                )

        })


    profile["numeric_summary"] = (
        numeric_summary
    )


    # =================================
    # CATEGORICAL SUMMARY
    # =================================

    categorical_summary = []


    categorical_columns = (
        data
        .select_dtypes(
            include="object"
        )
        .columns
        .tolist()
    )


    for column in categorical_columns:

        counts = (
            data[column]
            .value_counts(
                dropna=False
            )
            .head(10)
        )


        values = []


        for value, count in counts.items():

            values.append({

                "value":
                    str(value),

                "count":
                    int(count)

            })


        categorical_summary.append({

            "column":
                str(column),

            "values":
                values

        })


    profile["categorical_summary"] = (
        categorical_summary
    )