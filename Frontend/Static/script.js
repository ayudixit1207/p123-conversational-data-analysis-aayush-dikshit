let currentChart = null;


// =========================
// PAGE LOAD
// =========================

document.addEventListener("DOMContentLoaded", function () {

    setupUpload();

    setupAsk();

    loadProfile();

    loadFiles();

});


// =========================
// UPLOAD SETUP
// =========================

function setupUpload() {

    const uploadForm =
        document.getElementById("uploadForm");

    if (!uploadForm) {
        console.log("Upload form not found");
        return;
    }

    uploadForm.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();

            const fileInput =
                document.getElementById("fileInput");

            const message =
                document.getElementById("uploadMessage");

            if (!fileInput) {
                console.log("File input not found");
                return;
            }

            if (fileInput.files.length === 0) {

                if (message) {
                    message.innerText =
                        "Please select CSV file(s).";
                }

                return;
            }

            const formData =
                new FormData();

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

            try {

                if (message) {
                    message.innerText =
                        "Uploading...";
                }

                const response =
                    await fetch(
                        "/upload",
                        {
                            method: "POST",
                            body: formData
                        }
                    );

                const data =
                    await response.json();

                if (!response.ok) {

                    throw new Error(
                        data.error ||
                        "Upload failed"
                    );
                }

                if (message) {

                    message.innerText =
                        data.message ||
                        "File uploaded successfully.";
                }

                if (data.profile) {
                    showProfile(
                        data.profile
                    );
                }

                loadFiles();

                fileInput.value = "";

            } catch (error) {

                console.log(
                    "Upload error:",
                    error
                );

                if (message) {

                    message.innerText =
                        "Error: " +
                        error.message;
                }
            }
        }
    );
}


// =========================
// LOAD PROFILE
// =========================

async function loadProfile() {

    try {

        const response =
            await fetch("/profile");

        const data =
            await response.json();

        if (data.profile) {

            showProfile(
                data.profile
            );
        }

    } catch (error) {

        console.log(
            "Profile error:",
            error
        );
    }
}


// =========================
// SHOW PROFILE
// =========================

function showProfile(profile) {

    if (!profile) {
        return;
    }


    // Rows

    const rowsElement =
        document.getElementById(
            "rowCount"
        );

    if (rowsElement) {

        rowsElement.innerText =
            profile.rows ?? 0;
    }


    // Columns

    const columnsElement =
        document.getElementById(
            "columnCount"
        );

    if (columnsElement) {

        columnsElement.innerText =
            profile.columns ?? 0;
    }


    // Missing values

    const missingElement =
        document.getElementById(
            "missingCount"
        );

    if (missingElement) {

        missingElement.innerText =
            profile.total_missing ?? 0;
    }


    // Duplicate rows

    const duplicateElement =
        document.getElementById(
            "duplicateCount"
        );

    if (duplicateElement) {

        duplicateElement.innerText =
            profile.duplicate_rows ?? 0;
    }


    // Files

    const fileCountElement =
        document.getElementById(
            "fileCount"
        );

    if (fileCountElement) {

        fileCountElement.innerText =
            profile.total_files ?? 0;
    }


    // =========================
    // COLUMN DETAILS
    // =========================

    const columnBody =
        document.getElementById(
            "columnTable"
        );

    if (columnBody) {

        columnBody.innerHTML = "";

        if (profile.column_details) {

            profile.column_details.forEach(
                function (column) {

                    const row =
                        document.createElement(
                            "tr"
                        );

                    row.innerHTML = `
                        <td>${column.name}</td>
                        <td>${column.type}</td>
                        <td>${column.missing}</td>
                        <td>${column.missing_percent}%</td>
                        <td>${column.unique}</td>
                    `;

                    columnBody.appendChild(
                        row
                    );
                }
            );
        }
    }


    // =========================
    // NUMERIC SUMMARY
    // =========================

    const numericBody =
        document.getElementById(
            "numericTable"
        );

    if (numericBody) {

        numericBody.innerHTML = "";

        if (profile.numeric_summary) {

            profile.numeric_summary.forEach(
                function (item) {

                    const row =
                        document.createElement(
                            "tr"
                        );

                    row.innerHTML = `
                        <td>${item.column}</td>
                        <td>${item.mean}</td>
                        <td>${item.median}</td>
                        <td>${item.std}</td>
                        <td>${item.min}</td>
                        <td>${item.max}</td>
                    `;

                    numericBody.appendChild(
                        row
                    );
                }
            );
        }
    }


    // =========================
    // PREVIEW
    // =========================

    const previewContainer =
        document.getElementById(
            "previewTables"
        );

    if (previewContainer) {

        previewContainer.innerHTML = "";

        const previewGroups =
            profile.preview_groups || [

                {
                    name: "Dataset",

                    columns:
                        Object.keys(
                            profile.preview?.[0] || {}
                        ),

                    rows:
                        profile.preview || []
                }

            ];


        previewGroups.forEach(
            function (group) {

                const section =
                    document.createElement(
                        "section"
                    );

                section.className =
                    "preview-group";


                const heading =
                    document.createElement(
                        "h3"
                    );

                heading.innerText =
                    group.name ||
                    "Dataset";


                section.appendChild(
                    heading
                );


                const table =
                    document.createElement(
                        "table"
                    );


                const header =
                    table.createTHead()
                        .insertRow();


                const body =
                    table.createTBody();


                (group.columns || [])
                    .forEach(
                        function (column) {

                            const cell =
                                document.createElement(
                                    "th"
                                );

                            cell.innerText =
                                column;

                            header.appendChild(
                                cell
                            );
                        }
                    );


                (group.rows || [])
                    .forEach(
                        function (item) {

                            const row =
                                body.insertRow();


                            (group.columns || [])
                                .forEach(
                                    function (column) {

                                        const cell =
                                            row.insertCell();

                                        cell.innerText =
                                            item[column] ?? "";
                                    }
                                );
                        }
                    );


                section.appendChild(
                    table
                );


                previewContainer.appendChild(
                    section
                );
            }
        );


        if (previewGroups.length === 0) {

            previewContainer.innerText =
                "No preview data available.";
        }
    }
}


// =========================
// ASK SETUP
// =========================

function setupAsk() {

    [
        "questionInput",
        "question"
    ].forEach(
        function (inputId) {

            const input =
                document.getElementById(
                    inputId
                );

            if (input) {

                input.addEventListener(
                    "keydown",
                    function (event) {

                        if (
                            event.key === "Enter"
                        ) {

                            event.preventDefault();

                            askQuestion();
                        }
                    }
                );
            }
        }
    );
}


// =========================
// ASK QUESTION
// =========================

async function askQuestion() {

    const questionInput =
        document.getElementById(
            "questionInput"
        ) ||
        document.getElementById(
            "question"
        );


    const answerBox =
        document.getElementById(
            "answerBox"
        );


    const codeBox =
        document.getElementById(
            "codeBox"
        ) ||
        document.getElementById(
            "generatedCode"
        );


    const question =
        questionInput?.value.trim();


    if (!question) {

        if (answerBox) {

            answerBox.innerText =
                "Please enter a question.";
        }

        return;
    }


    try {

        if (answerBox) {

            answerBox.innerText =
                "Processing...";
        }


        const response =
            await fetch(
                "/ask",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            question
                        })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.error ||
                "Question failed"
            );
        }


        if (answerBox) {

            renderMarkdownAnswer(
                answerBox,
                data.answer ||
                "No answer received."
            );
        }


        if (codeBox) {

            codeBox.textContent =
                data.code || "";
        }


        if (data.chart) {

            showChart(
                data.chart
            );
        }


        // IMPORTANT:
        // Creates CSV/PDF/PNG buttons

        setupExportButtons(
            data
        );


    } catch (error) {

        console.log(
            "Ask error:",
            error
        );


        if (answerBox) {

            answerBox.innerText =
                "Error: " +
                error.message;
        }
    }
}


// =========================
// MARKDOWN ANSWER
// =========================

function renderMarkdownAnswer(
    element,
    markdown
) {

    if (
        window.marked?.parse &&
        window.DOMPurify?.sanitize
    ) {

        element.innerHTML =
            window.DOMPurify.sanitize(
                window.marked.parse(
                    String(markdown)
                )
            );

        return;
    }


    element.textContent =
        String(markdown);
}


// =========================
// SHOW CHART
// =========================

function showChart(chart) {

    const oldCanvas =
        document.getElementById(
            "dataChart"
        );


    if (!oldCanvas) {

        console.log(
            "Chart canvas not found"
        );

        return;
    }


    const chartContainer =
        oldCanvas.parentElement;


    if (chartContainer) {

        chartContainer.style.position =
            "relative";

        chartContainer.style.marginInline =
            "auto";

        chartContainer.style.maxWidth =
            chart.type === "heatmap"
                ? "640px"
                : "100%";

        chartContainer.style.height =
            chart.type === "heatmap"
                ? "clamp(320px, 70vw, 640px)"
                : "420px";
    }


    // Destroy old chart

    const existingChart =
        Chart.getChart(
            oldCanvas
        );


    if (existingChart) {

        existingChart.destroy();
    }


    if (currentChart) {

        try {

            currentChart.destroy();

        } catch (error) {

            console.log(
                "Chart destroy error:",
                error
            );
        }

        currentChart = null;
    }


    // Create fresh canvas

    const newCanvas =
        document.createElement(
            "canvas"
        );


    newCanvas.id =
        "dataChart";


    oldCanvas.replaceWith(
        newCanvas
    );


    // =========================
    // HEATMAP
    // =========================

    if (
        chart.type === "heatmap"
    ) {

        const labels =
            chart.labels || [];


        const values =
            chart.matrix ||
            chart.values ||
            [];


        const matrixData = [];


        for (
            let i = 0;
            i < labels.length;
            i++
        ) {

            for (
                let j = 0;
                j < labels.length;
                j++
            ) {

                let value = 0;


                if (
                    values[i] &&
                    values[i][j] !== undefined &&
                    values[i][j] !== null
                ) {

                    value =
                        Number(
                            values[i][j]
                        );
                }


                matrixData.push({

                    x:
                        labels[j],

                    y:
                        labels[i],

                    v:
                        value
                });
            }
        }


        currentChart =
            new Chart(
                newCanvas,
                {

                    type: "matrix",

                    data: {

                        datasets: [

                            {

                                label:
                                    "Correlation",

                                data:
                                    matrixData,


                                backgroundColor:
                                    function (
                                        context
                                    ) {

                                        const value =
                                            context
                                                .dataset
                                                .data[
                                                    context
                                                        .dataIndex
                                                ]
                                                .v;


                                        if (
                                            value >= 0.7
                                        ) {

                                            return "rgba(0, 120, 255, 0.9)";
                                        }


                                        if (
                                            value >= 0.3
                                        ) {

                                            return "rgba(0, 180, 150, 0.8)";
                                        }


                                        if (
                                            value <= -0.7
                                        ) {

                                            return "rgba(255, 70, 70, 0.9)";
                                        }


                                        if (
                                            value <= -0.3
                                        ) {

                                            return "rgba(255, 160, 60, 0.8)";
                                        }


                                        return "rgba(200, 200, 200, 0.7)";
                                    },


                                width:
                                    function (
                                        context
                                    ) {

                                        const chartArea =
                                            context.chart.chartArea;


                                        if (
                                            !chartArea
                                        ) {

                                            return 20;
                                        }


                                        if (
                                            labels.length === 0
                                        ) {

                                            return 20;
                                        }


                                        return (
                                            chartArea.width /
                                            labels.length *
                                            0.9
                                        );
                                    },


                                height:
                                    function (
                                        context
                                    ) {

                                        const chartArea =
                                            context.chart.chartArea;


                                        if (
                                            !chartArea
                                        ) {

                                            return 20;
                                        }


                                        if (
                                            labels.length === 0
                                        ) {

                                            return 20;
                                        }


                                        return (
                                            chartArea.height /
                                            labels.length *
                                            0.9
                                        );
                                    }
                            }

                        ]
                    },


                    options: {

                        responsive: true,

                        maintainAspectRatio:
                            false,


                        scales: {

                            x: {

                                type:
                                    "category",

                                labels:
                                    labels,

                                offset:
                                    true,

                                grid: {
                                    display:
                                        false
                                }
                            },


                            y: {

                                type:
                                    "category",

                                labels:
                                    labels,

                                offset:
                                    true,

                                reverse:
                                    true,

                                grid: {
                                    display:
                                        false
                                }
                            }
                        },


                        plugins: {

                            legend: {
                                display:
                                    false
                            },


                            tooltip: {

                                callbacks: {

                                    title:
                                        function (
                                            context
                                        ) {

                                            const item =
                                                context[0]
                                                    .raw;


                                            return (
                                                item.y +
                                                " vs " +
                                                item.x
                                            );
                                        },


                                    label:
                                        function (
                                            context
                                        ) {

                                            return (
                                                "Correlation: " +
                                                Number(
                                                    context.raw.v
                                                ).toFixed(2)
                                            );
                                        }
                                }
                            }
                        }
                    }
                }
            );


        return;
    }


    // =========================
    // PIE CHART
    // =========================

    if (
        chart.type === "pie"
    ) {

        currentChart =
            new Chart(
                newCanvas,
                {

                    type: "pie",

                    data: {

                        labels:
                            chart.labels || [],

                        datasets: [

                            {

                                label:
                                    chart.title ||
                                    "Data",

                                data:
                                    chart.values || []
                            }

                        ]
                    },


                    options: {

                        responsive: true,

                        maintainAspectRatio:
                            false,

                        plugins: {

                            legend: {

                                position:
                                    "right"
                            }
                        }
                    }
                }
            );


        return;
    }


    // =========================
    // BAR CHART
    // =========================

    if (
        chart.type === "bar"
    ) {

        currentChart =
            new Chart(
                newCanvas,
                {

                    type: "bar",

                    data: {

                        labels:
                            chart.labels || [],

                        datasets: [

                            {

                                label:
                                    chart.title ||
                                    "Data",

                                data:
                                    chart.values || []
                            }

                        ]
                    },


                    options: {

                        responsive: true,

                        maintainAspectRatio:
                            false,

                        scales: {

                            y: {

                                beginAtZero:
                                    true
                            }
                        }
                    }
                }
            );


        return;
    }


    // =========================
    // LINE CHART
    // =========================

    if (
        chart.type === "line"
    ) {

        currentChart =
            new Chart(
                newCanvas,
                {

                    type: "line",

                    data: {

                        labels:
                            chart.labels || [],

                        datasets: [

                            {

                                label:
                                    chart.title ||
                                    "Data",

                                data:
                                    chart.values || [],

                                tension:
                                    0.3,

                                fill:
                                    false
                            }

                        ]
                    },


                    options: {

                        responsive: true,

                        maintainAspectRatio:
                            false,

                        scales: {

                            y: {

                                beginAtZero:
                                    false
                            }
                        }
                    }
                }
            );


        return;
    }


    // =========================
    // SCATTER CHART
    // =========================

    if (
        chart.type === "scatter"
    ) {

        let scatterData = [];


        if (chart.points) {

            scatterData =
                chart.points.map(
                    function (point) {

                        return {

                            x:
                                Number(
                                    point.x
                                ),

                            y:
                                Number(
                                    point.y
                                )
                        };
                    }
                );

        }


        else if (
            chart.x_values &&
            chart.y_values
        ) {

            for (
                let i = 0;
                i < chart.x_values.length;
                i++
            ) {

                scatterData.push({

                    x:
                        Number(
                            chart.x_values[i]
                        ),

                    y:
                        Number(
                            chart.y_values[i]
                        )
                });
            }
        }


        currentChart =
            new Chart(
                newCanvas,
                {

                    type: "scatter",

                    data: {

                        datasets: [

                            {

                                label:
                                    chart.title ||
                                    "Data",

                                data:
                                    scatterData
                            }

                        ]
                    },


                    options: {

                        responsive: true,

                        maintainAspectRatio:
                            false,

                        scales: {

                            x: {

                                type:
                                    "linear",

                                position:
                                    "bottom"
                            }
                        }
                    }
                }
            );


        return;
    }


    // =========================
    // HISTOGRAM
    // =========================

    if (
        chart.type === "histogram"
    ) {

        currentChart =
            new Chart(
                newCanvas,
                {

                    type: "bar",

                    data: {

                        labels:
                            chart.labels || [],

                        datasets: [

                            {

                                label:
                                    chart.title ||
                                    "Distribution",

                                data:
                                    chart.values || []
                            }

                        ]
                    },


                    options: {

                        responsive: true,

                        maintainAspectRatio:
                            false,

                        scales: {

                            y: {

                                beginAtZero:
                                    true
                            }
                        }
                    }
                }
            );


        return;
    }
}


// =========================
// LOAD FILES
// =========================

async function loadFiles() {

    try {

        const response =
            await fetch(
                "/files-data"
            );


        const data =
            await response.json();


        const tableBody =
            document.getElementById(
                "filesBody"
            );


        if (!tableBody) {
            return;
        }


        tableBody.innerHTML = "";


        if (!data.files) {
            return;
        }


        data.files.forEach(
            function (file) {

                const row =
                    document.createElement(
                        "tr"
                    );


                row.innerHTML = `

                    <td>
                        ${file.file_name}
                    </td>

                    <td>
                        ${file.rows}
                    </td>

                    <td>
                        ${file.columns}
                    </td>

                    <td>

                        <button
                            onclick="deleteFile('${file.file_name}')"
                        >
                            Delete
                        </button>

                    </td>

                `;


                tableBody.appendChild(
                    row
                );
            }
        );


    } catch (error) {

        console.log(
            "Files loading error:",
            error
        );
    }
}


// =========================
// DELETE FILE
// =========================

async function deleteFile(
    fileName
) {

    const confirmDelete =
        confirm(
            "Are you sure you want to delete " +
            fileName +
            "?"
        );


    if (!confirmDelete) {
        return;
    }


    try {

        const response =
            await fetch(
                "/delete-file",
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        file_name:
                            fileName
                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.error ||
                "Delete failed"
            );
        }


        alert(
            data.message ||
            "File deleted successfully."
        );


        loadFiles();


        if (data.profile) {

            showProfile(
                data.profile
            );
        }


    } catch (error) {

        alert(
            "Error: " +
            error.message
        );
    }
}


// =========================
// EXPORT BUTTONS
// =========================

function setupExportButtons(data) {

    const answerBox =
        document.getElementById(
            "answerBox"
        );


    if (!answerBox) {
        return;
    }


    let exportBox =
        document.getElementById(
            "exportBox"
        );


    if (!exportBox) {

        exportBox =
            document.createElement(
                "div"
            );

        exportBox.id =
            "exportBox";

        exportBox.style.marginTop =
            "15px";

        exportBox.style.display =
            "flex";

        exportBox.style.gap =
            "10px";

        exportBox.style.flexWrap =
            "wrap";


        answerBox.insertAdjacentElement(
            "afterend",
            exportBox
        );
    }


    exportBox.innerHTML = "";


    // =========================
    // CSV BUTTON
    // =========================

    if (
        data &&
        data.result !== null &&
        data.result !== undefined
    ) {

        const csvButton =
            document.createElement(
                "button"
            );


        csvButton.innerText =
            "Download Result CSV";


        csvButton.type =
            "button";


        csvButton.addEventListener(
            "click",
            function () {

                downloadResultCSV(
                    data
                );

            }
        );


        exportBox.appendChild(
            csvButton
        );
    }


    // =========================
    // PDF BUTTON
    // =========================

    if (data) {

        const pdfButton =
            document.createElement(
                "button"
            );


        pdfButton.innerText =
            "Download Result PDF";


        pdfButton.type =
            "button";


        pdfButton.addEventListener(
            "click",
            function () {

                downloadResultPDF(
                    data
                );

            }
        );


        exportBox.appendChild(
            pdfButton
        );
    }


    // =========================
    // PNG BUTTON
    // =========================

    if (
        data &&
        data.chart
    ) {

        const pngButton =
            document.createElement(
                "button"
            );


        pngButton.innerText =
            "Download Chart PNG";


        pngButton.type =
            "button";


        pngButton.addEventListener(
            "click",
            function () {

                downloadChartPNG(
                    data.chart.title ||
                    "data-chart"
                );

            }
        );


        exportBox.appendChild(
            pngButton
        );
    }
}


// =========================
// DOWNLOAD RESULT CSV
// =========================

function downloadResultCSV(data) {

    const question =
        data.question || "";


    const result =
        data.result ?? "";


    const answer =
        data.answer || "";


    const code =
        data.code || "";


    const rows = [

        [
            "Question",
            "Result",
            "Answer",
            "Generated Code"
        ],

        [
            question,
            result,
            answer,
            code
        ]

    ];


    const csvContent =
        rows
            .map(
                function (row) {

                    return row
                        .map(csvEscape)
                        .join(",");

                }
            )
            .join("\n");


    const blob =
        new Blob(
            [csvContent],
            {
                type:
                    "text/csv;charset=utf-8;"
            }
        );


    const url =
        URL.createObjectURL(
            blob
        );


    const link =
        document.createElement(
            "a"
        );


    link.href =
        url;


    link.download =
        "analysis_result.csv";


    document.body.appendChild(
        link
    );


    link.click();


    document.body.removeChild(
        link
    );


    URL.revokeObjectURL(
        url
    );
}


// =========================
// CSV ESCAPE
// =========================

function csvEscape(value) {

    const text =
        String(
            value ?? ""
        );


    return '"' +
        text
            .replace(
                /"/g,
                '""'
            )
            .replace(
                /\r?\n/g,
                " "
            ) +
        '"';
}


// =========================
// DOWNLOAD RESULT PDF
// =========================

function downloadResultPDF(data) {

    if (
        !window.jspdf ||
        !window.jspdf.jsPDF
    ) {

        alert(
            "PDF library is not loaded."
        );

        return;
    }


    const jsPDF =
        window.jspdf.jsPDF;


    const pdf =
        new jsPDF();


    const question =
        String(
            data.question || ""
        );


    const answer =
        String(
            data.answer || ""
        );


    const result =
        String(
            data.result ?? ""
        );


    const code =
        String(
            data.code || ""
        );


    let y = 20;


    // =========================
    // TITLE
    // =========================

    pdf.setFontSize(
        18
    );


    pdf.setFont(
        "helvetica",
        "bold"
    );


    pdf.text(
        "Conversational Data Analysis Assistant",
        20,
        y
    );


    y += 15;


    // =========================
    // QUESTION
    // =========================

    pdf.setFontSize(
        12
    );


    pdf.setFont(
        "helvetica",
        "bold"
    );


    pdf.text(
        "Question:",
        20,
        y
    );


    y += 7;


    pdf.setFont(
        "helvetica",
        "normal"
    );


    const questionLines =
        pdf.splitTextToSize(
            question,
            170
        );


    pdf.text(
        questionLines,
        20,
        y
    );


    y +=
        questionLines.length * 6 +
        8;


    // =========================
    // ANSWER
    // =========================

    if (y > 270) {

        pdf.addPage();

        y = 20;
    }


    pdf.setFont(
        "helvetica",
        "bold"
    );


    pdf.text(
        "Answer:",
        20,
        y
    );


    y += 7;


    pdf.setFont(
        "helvetica",
        "normal"
    );


    const answerLines =
        pdf.splitTextToSize(
            answer,
            170
        );


    for (
        let i = 0;
        i < answerLines.length;
        i++
    ) {

        if (y > 275) {

            pdf.addPage();

            y = 20;
        }


        pdf.text(
            answerLines[i],
            20,
            y
        );


        y += 6;
    }


    y += 8;


    // =========================
    // VERIFIED RESULT
    // =========================

    if (result) {

        if (y > 260) {

            pdf.addPage();

            y = 20;
        }


        pdf.setFont(
            "helvetica",
            "bold"
        );


        pdf.text(
            "Verified Result:",
            20,
            y
        );


        y += 7;


        pdf.setFont(
            "helvetica",
            "normal"
        );


        const resultLines =
            pdf.splitTextToSize(
                result,
                170
            );


        for (
            let i = 0;
            i < resultLines.length;
            i++
        ) {

            if (y > 275) {

                pdf.addPage();

                y = 20;
            }


            pdf.text(
                resultLines[i],
                20,
                y
            );


            y += 6;
        }


        y += 8;
    }


    // =========================
    // GENERATED CODE
    // =========================

    if (code) {

        if (y > 250) {

            pdf.addPage();

            y = 20;
        }


        pdf.setFont(
            "helvetica",
            "bold"
        );


        pdf.text(
            "Generated Code:",
            20,
            y
        );


        y += 7;


        pdf.setFont(
            "courier",
            "normal"
        );


        pdf.setFontSize(
            9
        );


        const codeLines =
            pdf.splitTextToSize(
                code,
                170
            );


        for (
            let i = 0;
            i < codeLines.length;
            i++
        ) {

            if (y > 275) {

                pdf.addPage();

                y = 20;
            }


            pdf.text(
                codeLines[i],
                20,
                y
            );


            y += 5;
        }
    }


    // =========================
    // FOOTER
    // =========================

    const pageCount =
        pdf.internal.getNumberOfPages();


    for (
        let i = 1;
        i <= pageCount;
        i++
    ) {

        pdf.setPage(i);


        pdf.setFont(
            "helvetica",
            "normal"
        );


        pdf.setFontSize(
            8
        );


        pdf.text(
            "Generated by Conversational Data Analysis Assistant",
            20,
            290
        );
    }


    // =========================
    // SAVE PDF
    // =========================

    pdf.save(
        "analysis_result.pdf"
    );
}


// =========================
// DOWNLOAD CHART PNG
// =========================

function downloadChartPNG(
    title
) {

    if (!currentChart) {

        alert(
            "No chart is available to download."
        );

        return;
    }


    try {

        const image =
            currentChart.toBase64Image(
                "image/png",
                1
            );


        const link =
            document.createElement(
                "a"
            );


        link.href =
            image;


        link.download =
            sanitizeFileName(
                title
            ) +
            ".png";


        document.body.appendChild(
            link
        );


        link.click();


        document.body.removeChild(
            link
        );


    } catch (error) {

        console.log(
            "Chart export error:",
            error
        );


        alert(
            "Could not download the chart."
        );
    }
}


// =========================
// SAFE FILE NAME
// =========================

function sanitizeFileName(
    name
) {

    return String(
        name ||
        "data-chart"
    )

        .replace(
            /[<>:"/\\|?*]+/g,
            "_"
        )

        .replace(
            /\s+/g,
            "_"
        )

        .substring(
            0,
            80
        );
}