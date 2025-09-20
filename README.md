# Vocabulary Go

[![Forks](https://img.shields.io/github/forks/lucasw0908/Vocabulary-Go.svg?style=social&label=Fork&maxAge=2592000)](https://github.com/lucasw0908/Vocabulary-Go/blob/main/LICENSE)
[![Stars](https://img.shields.io/github/stars/lucasw0908/Vocabulary-Go.svg)](https://github.com/lucasw0908/Vocabulary-Go/blob/main/LICENSE)
[![License](https://img.shields.io/github/license/lucasw0908/Vocabulary-Go.svg)](https://github.com/lucasw0908/Vocabulary-Go/blob/main/LICENSE)
[![Issues](https://img.shields.io/github/issues/lucasw0908/Vocabulary-Go.svg)](https://github.com/lucasw0908/Vocabulary-Go/issues)
[![Pull Requests](https://img.shields.io/github/issues-pr/lucasw0908/Vocabulary-Go.svg)](https://github.com/lucasw0908/Vocabulary-Go/pulls)


## Description

Vocabulary Go is a web application designed to help users enhance their vocabulary skills through interactive quizzes and exercises. The application leverages advanced language models to generate questions and provide instant feedback, making learning engaging and effective. 

## Features

### Flashcards

An intuitive way to memorize vocabulary with definitions, pronunciation, and examples, helping you retain words through repetition.

### Word Test

Quick tests designed in exam style to check your word knowledge and strengthen mastery with multiple formats.

### Sentence Fill-in

Practice words in real-life sentences by filling in the blanks, improving both memory and natural usage.

### Custom Question Library Upload

Upload your own word sets, and AI will turn them into interactive quizzes for personalized learning.

## Configuration

### Environment Variables

Please create a `.env` file in the root directory and add the following variables:

> [*example .env file*](https://github.com/lucasw0908/Vocabulary-Go/blob/main/flask/app/.env.example)

### Settings JSON File

You can customize the application settings by modifying the `settings.json` file located in the root directory. Below is an example of the settings structure:

> [*settings.json file*](https://github.com/lucasw0908/Vocabulary-Go/blob/main/flask/app/settings.json)

Or create `local_settings.py` to override specific settings without modifying the main `settings.json` file.

*Example of local_settings.py*

```python
LOG_LEVEL = "DEBUG"
API_MODEL_NAME = "gemini-2.5-pro"
```


## Quick Start

### Docker Setup

```shell
docker compose up -d --build
```

### Manual Setup

1. Change directory into the `flask` directory:

    ```shell
    cd flask
    ```

2. Install the required dependencies:

    ```shell
    pip install -r requirements.txt
    ```

    or using uv package manager:

    ```shell
    uv sync
    ```

3. Run the Flask application:

    ```shell
    python main.py
    ```

    or using uv package manager:

    ```shell
    uv run main.py
    ```

4. Access the application at `http://localhost:8080`.


## Q&A

### How to add more API keys?

You can add more API keys by editing the `.env` file and adding additional keys in the `API_KEYS` variable, separated by commas.

## Support

> [!TIP]
> If you have any questions or need assistance, feel free to join our Discord server.

[![Discord](https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/SjWzwyDYc2)