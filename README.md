# latex-translator

With this tool, you can translate and convert `.tex` files into Japanese-translated `.md` files.
Notably, it allows for the specification of a correspondence table between sentences in the original language and the translated Japanese sentences.
This feature ensures that even specialized documents can be accurately translated and transformed into a readable Markdown format.

## Setup

### 1. Launch Dev Container

Launch Dev Container with [VSCode Dev Container Extension](https://code.visualstudio.com/docs/devcontainers/containers) or [GitHub Codespaces](https://github.com/features/codespaces).

### 2. Create .env file

Copy `.env.example` as `.env`

```
cp .env.example .env
```

Set `OPENAI_API_KEY` .
   You can find it in https://platform.openai.com/account/api-keys

## Usage

### 1. Put the `.tex` file to be translated

Put the `.tex` file to be translated anywhere in the workspace.

`.tex` files exported from [Mathpix](https://mathpix.com/) are assumed as input.

### 2. Configure file paths

`TEX_PATH` (original `.tex` file put in 1.), `MD_PATH` (`.md` file with original content) and `TRANSLATION_MD_PATH` (translated `.md` file) are defined in top of [src/translate.ipynb](./src/translate.ipynb).
To change the file paths, edit the values of these variables.

To notice ChatGPT list of pair of original and translated sentences, `corr_list` should be set.

### 3. Run Jupyter Notebook Cells

Run all cells in [src/translate.ipynb](./src/translate.ipynb) sequentially.

## Example

See [/example](./example) directory.
