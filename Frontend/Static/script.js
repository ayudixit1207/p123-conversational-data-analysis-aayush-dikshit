async function uploadFiles() {

    const fileInput =
        document.getElementById("fileInput");

    const message =
        document.getElementById("uploadMessage");


    if (fileInput.files.length === 0) {

        message.innerText =
            "Please select at least one CSV file.";

        return;
    }


    const formData =
        new FormData();


    // Add all selected files
    for (
        let i = 0;
        i < fileInput.files.length;
        i++
    ) {

        formData.append(
            "files",
            fileInput.files[i]
        );
    }


    message.innerText =
        "Uploading files...";


    try {

        const response =
            await fetch("/upload", {

                method: "POST",

                body: formData

            });


        const data =
            await response.json();


        if (!response.ok) {

            message.innerText =
                data.error || "Upload failed.";

            return;
        }


        message.innerText =
            data.total_files +
            " file(s) uploaded successfully.";


        if (document.getElementById("rowCount")) {
            showProfile(data.profile);
        }

        if (document.getElementById("uploadedFiles")) {
            renderUploadedFiles(data.files || []);
        }


    } catch (error) {

        message.innerText =
            "Upload error: " +
            error.message;

    }
}


function showProfile(profile) {

    document.getElementById("rowCount").innerText =
        profile.rows;


    document.getElementById("columnCount").innerText =
        profile.columns;


    document.getElementById("fileCount").innerText =
        profile.total_files;


    document.getElementById("missingCount").innerText =
        profile.total_missing;


    document.getElementById("duplicateCount").innerText =
        profile.duplicate_rows;


    // --------------------------------------------
    // COLUMN INFORMATION
    // --------------------------------------------

    const columnTable =
        document.getElementById("columnTable");


    columnTable.innerHTML = "";


    profile.column_details.forEach(
        function(column) {

            const row =
                document.createElement("tr");


            row.innerHTML = `
                <td>${column.name}</td>
                <td>${column.type}</td>
                <td>${column.missing}</td>
                <td>${column.missing_percent}%</td>
                <td>${column.unique}</td>
            `;


            columnTable.appendChild(row);
        }
    );


    // --------------------------------------------
    // NUMERIC SUMMARY
    // --------------------------------------------

    const numericTable =
        document.getElementById("numericTable");


    numericTable.innerHTML = "";


    profile.numeric_summary.forEach(
        function(column) {

            const row =
                document.createElement("tr");


            row.innerHTML = `
                <td>${column.column}</td>
                <td>${column.mean}</td>
                <td>${column.median}</td>
                <td>${column.std}</td>
                <td>${column.min}</td>
                <td>${column.max}</td>
            `;


            numericTable.appendChild(row);
        }
    );


    // --------------------------------------------
    // DATA PREVIEW
    // --------------------------------------------

    const previewTables =
        document.getElementById("previewTables");

    previewTables.replaceChildren();

    (profile.preview_groups || []).forEach(
        function(group) {
            const section = document.createElement("section");
            section.className = "preview-group";

            const title = document.createElement("h3");
            title.innerText = group.name;
            section.appendChild(title);

            const tableContainer = document.createElement("div");
            tableContainer.className = "table-container";

            const table = document.createElement("table");
            const head = document.createElement("thead");
            const headerRow = document.createElement("tr");

            group.columns.forEach(function(column) {
                const header = document.createElement("th");
                header.innerText = column;
                headerRow.appendChild(header);
            });

            head.appendChild(headerRow);
            table.appendChild(head);

            const body = document.createElement("tbody");
            group.rows.forEach(function(item) {
                const row = document.createElement("tr");
                group.columns.forEach(function(column) {
                    const cell = document.createElement("td");
                    cell.innerText = item[column] ?? "";
                    row.appendChild(cell);
                });
                body.appendChild(row);
            });

            table.appendChild(body);
            tableContainer.appendChild(table);
            section.appendChild(tableContainer);
            previewTables.appendChild(section);
        }
    );
}


// --------------------------------------------
// ASK QUESTION
// --------------------------------------------

async function askQuestion() {

    const input =
        document.getElementById(
            "questionInput"
        );


    const answerBox =
        document.getElementById(
            "answerBox"
        );


    const codeBox =
        document.getElementById(
            "codeBox"
        );


    const question =
        input.value.trim();


    if (!question) {

        answerBox.innerText =
            "Please enter a question.";

        return;
    }


    answerBox.innerText =
        "Thinking...";


    codeBox.innerText =
        "";


    try {

        const response =
            await fetch("/ask", {

                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    question: question
                })

            });


        const data =
            await response.json();


        if (!response.ok) {

            answerBox.innerText =
                data.error ||
                "Something went wrong.";

            return;
        }


        answerBox.innerText =
            data.answer || "";


        codeBox.innerText =
            data.code || "";


    } catch (error) {

        answerBox.innerText =
            "Error: " +
            error.message;
    }
}


async function loadUploadedFiles() {
    const message = document.getElementById("filesMessage");

    try {
        const response = await fetch("/api/files");
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Could not load uploaded files.");
        }

        renderUploadedFiles(data.files || []);
    } catch (error) {
        message.innerText = error.message;
    }
}


async function loadCurrentProfile() {
    try {
        const response = await fetch("/api/profile");
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Could not load dataset profile.");
        }

        if (data.profile) {
            showProfile(data.profile);
        }
    } catch (error) {
        console.error(error);
    }
}


function renderUploadedFiles(files) {
    const list = document.getElementById("uploadedFiles");
    const count = document.getElementById("uploadedFileCount");

    if (!list || !count) return;

    list.replaceChildren();
    count.innerText = files.length;

    if (files.length === 0) {
        const emptyMessage = document.createElement("p");
        emptyMessage.className = "empty-files-message";
        emptyMessage.innerText = "No files uploaded yet.";
        list.appendChild(emptyMessage);
        return;
    }

    files.forEach((file) => {
        const row = document.createElement("div");
        row.className = "uploaded-file-row";

        const details = document.createElement("div");
        details.className = "uploaded-file-details";

        const name = document.createElement("strong");
        name.innerText = file.name;

        const metadata = document.createElement("span");
        metadata.innerText = `${file.rows} rows · ${file.columns} columns`;

        const removeButton = document.createElement("button");
        removeButton.type = "button";
        removeButton.className = "remove-file-button";
        removeButton.innerText = "Remove";
        removeButton.setAttribute("aria-label", `Remove ${file.name}`);
        removeButton.addEventListener("click", () => removeUploadedFile(file));

        details.append(name, metadata);
        row.append(details, removeButton);
        list.appendChild(row);
    });
}


async function removeUploadedFile(file) {
    if (!window.confirm(`Remove ${file.name} from the active dataset?`)) return;

    const message = document.getElementById("filesMessage");
    message.innerText = `Removing ${file.name}...`;

    try {
        const response = await fetch(`/api/files/${encodeURIComponent(file.id)}`, {
            method: "DELETE"
        });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Could not remove the file.");
        }

        renderUploadedFiles(data.files || []);
        message.innerText = `${file.name} removed from the active dataset.`;
    } catch (error) {
        message.innerText = error.message;
    }
}


document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById("rowCount")) {
        loadCurrentProfile();
    }

    if (document.getElementById("uploadedFiles")) {
        loadUploadedFiles();
    }
});