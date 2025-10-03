A sandboxed Python-based command-line terminal with both CLI and Streamlit web UI.
Built for CodeMate Hackathon – Problem Statement 1.

Features

Full REPL terminal with clean prompt and error handling

File/Directory operations: ls, cd, pwd, mkdir, rm, touch, cat, echo, cp, mv, head, tail

System commands: ps, sysmon (CPU/memory snapshot), df (disk usage)

Quality-of-life: help, history (with readline if available), exit / quit

Safety sandbox: all paths are clamped to the project root; no accidental deletions outside allowed scope

Two interfaces:

CLI: interactive terminal (main.py)

Web UI: Streamlit app (app.py) with command history, quick buttons, and interactive output

Getting Started
Installation
git clone https://github.com/Ignite7871/python-terminal.git
cd python-terminal
pip install -r requirements.txt

Run CLI
python main.py

Run Streamlit UI
pip install streamlit
streamlit run app.py

Usage

Examples inside the terminal:

pwd
ls
mkdir demo
cd demo
touch a.txt
cat a.txt
echo "hello" > b.txt
head -n 5 b.txt
sysmon
df


Quick commands like help, history, and exit are also available.

File Structure

main.py → Core terminal implementation and REPL CLI entrypoint

app.py → Streamlit-based web interface (reuses Terminal class)

requirements.txt → Dependencies (minimal: Streamlit only)

