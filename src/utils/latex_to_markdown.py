import re
from typing import List, Match
import regex
from itertools import chain


def remove_text_before_first_heading(markdown_text: str) -> str:
    """
    Removes all text before the first heading in the given markdown text.

    Args:
        markdown_text (str): The markdown text to process.

    Returns:
        str: The processed markdown text with text before the first heading removed.
    """
    # Search for the first markdown heading in the text
    match = re.search(r"^#{1,6} .*", markdown_text, re.MULTILINE)
    if not match:
        return markdown_text

    # Get the start position of the first heading
    first_heading_position = match.start()

    # Return the text starting from the first heading
    return markdown_text[first_heading_position:]


def replace_ampersand_inside_math_env(latex_table: str) -> str:
    result = []
    in_math_env = False
    start_idx = 0

    for idx, char in enumerate(latex_table):
        if char == '$':
            in_math_env = not in_math_env

        if in_math_env and char == '&':
            result.append(latex_table[start_idx:idx] + '__TEMP__AND__')
            start_idx = idx + 1

    result.append(latex_table[start_idx:])
    return ''.join(result)


def replace_double_backslash_inside_math_env(latex: str) -> str:
    result = []
    in_math_env = False
    start_idx = 0

    # Adjusting the loop so it does not go out of range, considering length of "\\\\" is 2
    for idx in range(len(latex) - 1):
        if latex[idx] == '$':
            in_math_env = not in_math_env

        # If within math environment and encounter "\\\\", replace it
        if in_math_env and latex[idx:idx+2] == '\\\\':
            result.append(latex[start_idx:idx] +
                          '__TEMP__NEWLINE__')
            start_idx = idx + 2  # advance the index by the length of "\\\\", which is 2

    # Append the remaining text
    result.append(latex[start_idx:])
    return ''.join(result)


def delete_line_breaks_inside_math_env(latex: str) -> str:
    result = []
    in_math_env = False
    start_idx = 0

    for idx, char in enumerate(latex):
        if char == '$':
            in_math_env = not in_math_env

        # If within math environment and encounter "\n", replace it
        if in_math_env and char == '\n':
            # Append text up to the line break
            result.append(latex[start_idx:idx])
            start_idx = idx + 1  # Skip the line break

    # Append the remaining text
    result.append(latex[start_idx:])
    return ''.join(result)


def extract_braces(input_str):
    stack = []
    i = -1
    for i, c in enumerate(input_str):
        if c == '{':
            stack.append(i)
        elif c == '}':
            if stack:
                stack.pop()
        else:
            continue
    if stack:
        raise ValueError('Unmatched opening brace')
    else:
        return input_str[:i]


def handle_multicolumn(cell: str) -> List[str]:
    cell = cell.strip(' ')
    match = re.search(r'\\multicolumn\{(\d+)\}\{.*?\}\{', cell)
    if match:
        col_span = int(match.group(1))
        start_pos = match.end()
        content = extract_braces(cell[start_pos:]).strip(' ')
        return [content] * col_span
    else:
        return [cell.strip(' ')]


def handle_multirow(table: List[List[str]]) -> List[List[str]]:
    for i, row in enumerate(table):
        for j, cell in enumerate(row):
            match = re.search(r'\\multirow(\[.*?\])?\{(\d+)\}\{.*?\}\{', cell)
            if match:
                repetitions = int(match.group(2))
                start_pos = match.end()
                content = extract_braces(cell[start_pos:]).strip(' ')
                # Modify the current cell
                table[i][j] = content
                # Check the following rows for repetitions
                for rep in range(1, repetitions):
                    if i+rep < len(table):
                        table[i+rep][j] = content
    return table


def latex_table_to_nested_list(latex_table: str) -> List[List[str]]:
    # 1. Remove '\\hline'
    latex_table = re.sub(r'\\hline', '', latex_table)

    # 2. Remove '\\begin{tabular}{...}' and '\\end{tabular}'
    latex_table = re.sub(r'\\end\{tabular\}', '', latex_table)
    latex_table = re.sub(r'\\begin\{tabular\}\{[^\}]*\}', '', latex_table)

    # Replace newline and "&" temporarily inside math environment
    latex_table = replace_double_backslash_inside_math_env(latex_table)
    latex_table = replace_ampersand_inside_math_env(latex_table)
    latex_table = delete_line_breaks_inside_math_env(latex_table)

    # Split LaTeX table into rows, removing rows containing '\cline'
    rows = filter(lambda row: len(row) != 0 and '\\cline' not in row, map(
        lambda row: row.strip(' ').strip('\n'), latex_table.split('\\\\')))

    # Split each row into cells
    table = [row.split('&') for row in rows]

    # Handle \multicolumn command for each cell, and then \multirow command
    table = [list(chain(*[handle_multicolumn(cell) for cell in row]))
             for row in table]

    table = handle_multirow(table)

    # Restore replaced newline and "&"
    table = [[cell.replace('__TEMP__NEWLINE__', '\\\\').replace('__TEMP__AND__', '&').strip(' ')
              for cell in row] for row in table]

    # Find the maximum number of columns
    max_cols = max(len(row) for row in table)

    # Pad rows to have equal number of columns
    table = [row + [''] * (max_cols - len(row)) for row in table]

    return table


def generate_markdown_table(data: List[List[str]]) -> str:
    if not data:
        return ""

    # Header row
    header_row = '| ' + ' | '.join(data[0]) + ' |'

    # Separator row
    separator_row = '| --- ' * len(data[0]) + '|'

    # Data rows
    data_rows = []
    for row in data[1:]:
        data_rows.append('| ' + ' | '.join(row) + ' |')

    # Combine all rows
    markdown_table = header_row + '\n' + \
        separator_row + '\n' + '\n'.join(data_rows)

    return markdown_table


def latex_table_to_markdown_table(latex: str) -> str:
    """
    Converts all LaTeX tables in the given LaTeX text to markdown tables.

    Args:
        latex (str): The LaTeX text containing tables to convert.

    Returns:
        str: The LaTeX text with all tables converted to markdown tables.
    """
    # Find and replace tabular environments with their markdown counterparts
    latex = re.sub(r"\\begin\{tabular\}\{.*?}.*?\\end\{tabular\}",
                   lambda latex: generate_markdown_table(latex_table_to_nested_list(latex.group(0))), latex, flags=re.DOTALL)

    return latex


def remove_comments(latex: str) -> str:
    latex = latex.replace(r'\%', '__TEMP__PERCENT__')
    latex = re.sub(' %.*', '', latex)
    latex = re.sub('%.*', '', latex)
    latex = latex.replace('__TEMP__PERCENT__', r'\%')

    return latex


def latex_to_markdown(latex: str) -> str:
    """
    Converts a LaTeX document into a markdown document.

    Args:
        latex (str): The LaTeX document to convert.

    Returns:
        str: The markdown document converted from the LaTeX document.
    """
    latex = re.sub(r"(\\emph{)(.*?)\}", r"*\2*", latex)
    latex = re.sub(r"(\\textbf{)(.*?)\}", r"**\2**", latex)
    latex = re.sub(r'\\setcounter\{.*?\}\{.*?\}', r"", latex)
    latex = regex.compile(
        r"(\\author{)((?:[^{}]+|{(?:[^{}]+|{[^{}]*})*})*)\}").sub(lambda match: f"## Auther\n{match.group(2)}", latex)
    latex = re.sub(r"(\\date{)(.*?)\}", r"\2", latex)
    latex = re.sub(r"(\\title{)(.*?)\}", r"# \2", latex)
    latex = re.sub(r"\\maketitle", "", latex)
    latex = re.sub(r"\\begin{center}", "", latex)
    latex = re.sub(r"\\end{center}", "", latex)
    latex = re.sub(r'\\href\{(.*?)\}\{(.*?)\}', r'[\2](\1)', latex)
    latex = re.sub(r"(\\documentclass{)(.*?)\}", "", latex)
    latex = re.sub(r"(\\documentclass\[)(.*?)\}", "", latex)
    latex = re.sub(r"(\\usepackage{)(.*?)\}", "", latex)
    latex = re.sub(r"(\\usepackage\[)(.*?)\}", "", latex)
    latex = regex.compile(
        r"(\\section{)((?:[^{}]+|{(?:[^{}]+|{[^{}]*})*})*)\}").sub(lambda match: f"## {match.group(2)}", latex)
    latex = regex.compile(
        r"(\\subsection{)((?:[^{}]+|{(?:[^{}]+|{[^{}]*})*})*)\}").sub(lambda match: f"### {match.group(2)}", latex)
    latex = regex.compile(
        r"(\\subsubsection{)((?:[^{}]+|{(?:[^{}]+|{[^{}]*})*})*)\}").sub(lambda match: f"#### {match.group(2)}", latex)
    latex = re.sub(r"\$\$\$\$(.*?)\$\$\$\$", r"$$\1$$", latex)
    latex = re.sub(r"(.*)\\begin{equation}", r"\n\n$$", latex)
    latex = re.sub(r"(.*)\\end{equation}", r"$$\n\n", latex)
    latex = re.sub(r"(.*)\\begin{itemize}\n", r"", latex)
    latex = re.sub(r"(.*)(\\end{itemize})\n", r"", latex)
    latex = re.sub(r"(.*)\\begin{enumerate}\n", r"", latex)
    latex = re.sub(r"(.*)(\\end{enumerate})\n", r"", latex)
    latex = re.sub(r"(.*)\\begin{abstract}\n", r"", latex)
    latex = re.sub(r"(.*)(\\end{abstract})\n", r"", latex)
    latex = re.sub(r"(.*)\\begin{enumerate}\n", r"", latex)
    latex = re.sub(r"(.*)(\\end{enumerate})\n", r"", latex)
    latex = re.sub(r"(.*)(\\centering)\n", r"", latex)
    latex = re.sub(r"\\label{.*?}", r"", latex)
    latex = re.sub(r"(.*)\\item", r"*", latex)
    latex = remove_comments(latex)
    latex = re.sub(r'\\begin{blockquote}',
                   r'\'{{\'% panel theme="note" %\'\'}}', latex)
    latex = re.sub(r"\\end{blockquote}", r"'{{'% /panel %'}}'", latex)
    latex = re.sub(r"\\begin{figure}\[(.*?)\]\n",
                   r"<center> \n '{{'< figure", latex)
    latex = re.sub(
        r"\s\\caption{(.*?)}\n", r' caption="\1" caption-position="bottom" caption-effect="fade"', latex)
    latex = re.sub(r"\n\\end{figure}", r">}}\n</center>", latex)
    latex = re.sub(
        r'\\includegraphics\[.*?\]{(.*?)}', lambda match: f'![./images/{match.group(1)}.jpg](./images/{match.group(1)}.jpg)', latex)
    latex = re.sub(r"\\begin{document}", "", latex)
    latex = re.sub(r"\\end{document}", "", latex)
    latex = latex_table_to_markdown_table(latex)
    latex = remove_text_before_first_heading(latex)
    latex = re.sub(r"\n\n\n", "\n\n", latex)
    return latex
