# ACHIVE

## Step 1: Set Up the Environment

1. Open the VS Code terminal.

2. Create a virtual environment with the command:

    ```sh
    py -m venv .venv
    ```

3. Activate the virtual environment:

    - **On Windows:**

    ```sh
    .venv\Scripts\activate
    ```

    - **On macOS/Linux:**

    ```sh
    source .venv/bin/activate
    ```

4. Install all the required dependencies:

    ```sh
    pip install -r requirements.txt
    ```

## Step 2: Run the API

Run the API with the following command:

```sh
uvicorn app.main:app --reload
```

## Open Browser
http://127.0.0.1:8000/
or
localhost:8000/

Start chatting.