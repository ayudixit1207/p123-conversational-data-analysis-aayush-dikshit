# Conversational Data Analysis Assistant

## HCL Training Project

**Project ID:** P_123  
**Project Title:** Conversational Data Analysis Assistant  
**Training:** HCL Training  
**Domain:** Artificial Intelligence / Data Analytics / LLM / RAG

---

## 1. Project Overview

The **Conversational Data Analysis Assistant** is an AI-powered data analysis application developed as part of **HCL Training**.

The system allows users to upload CSV datasets and interact with their data using natural language. Instead of manually writing Python or pandas code, users can simply ask questions about their dataset.

For example:

- What is the average salary?
- Which department has the highest average salary?
- Which column has the most missing values?
- Show a bar chart of average salary by department.
- Show the distribution of salary.

The system processes the uploaded dataset, understands the user's question, generates pandas-based analysis code, validates the generated code, executes it safely, and presents the result to the user.

The application also includes data profiling, RAG-based retrieval, vector embeddings, Qdrant, PostgreSQL, charts, query history, multiple file support, and a self-repair mechanism for failed generated code.

---

## 2. Problem Statement

Traditional data analysis requires users to have programming knowledge and understand tools such as Python, Pandas, NumPy, and visualization libraries.

The objective of this project is to provide a conversational interface where users can ask questions about their datasets in natural language and receive meaningful analytical results without manually writing code.

---

## 3. Objectives

The main objectives of the project are:

- Allow users to upload CSV datasets.
- Automatically analyze uploaded data.
- Generate dataset profiles.
- Understand natural-language questions.
- Convert natural-language questions into Pandas code.
- Validate generated code before execution.
- Execute generated code in a restricted environment.
- Provide verified answers based on actual dataset results.
- Generate data visualizations.
- Use RAG for relevant dataset context retrieval.
- Maintain query and session history.
- Support multiple CSV files.
- Provide export options for analysis results.
- Handle failed generated code using a limited self-repair mechanism.

---

## 4. Key Features

### CSV Data Upload

Users can upload one or multiple CSV files through the web interface.

### Automatic Data Profiling

The system provides:

- Number of rows
- Number of columns
- Column names
- Data types
- Missing values
- Missing-value percentage
- Unique values
- Duplicate rows
- Numerical statistics
- Categorical summaries
- Data preview

### Natural Language Data Analysis

Users can ask questions in normal language instead of writing Pandas code.

Example:

```text
What is the average salary?