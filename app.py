#!/usr/bin/env python3
"""
Streamlit UI for Problem 1 (reuses Terminal from main.py)
Run:
  pip install streamlit
  streamlit run streamlit_app.py
"""
from __future__ import annotations
import io
import os
from pathlib import Path
from contextlib import redirect_stdout
import streamlit as st

# Import your Terminal class from the CLI implementation
from main import Terminal

# ----------------------- Setup -----------------------
st.set_page_config(page_title="CodeMate Terminal – Streamlit", page_icon="💻", layout="wide")

ROOT = Path(__file__).parent.resolve()

# Create single Terminal instance per session
if "terminal" not in st.session_state:
    st.session_state.terminal = Terminal(ROOT)
    # Capture banner once
    buf = io.StringIO()
    with redirect_stdout(buf):
        st.session_state.terminal._banner()
    st.session_state.history = [(None, buf.getvalue())]  # list of (cmd, output)
    st.session_state.cwd = "/"

term: Terminal = st.session_state.terminal

# ----------------------- Helpers -----------------------
def run_command(cmd: str) -> str:
    out_buf = io.StringIO()
    with redirect_stdout(out_buf):
        try:
            term.execute(cmd)
        except SystemExit:
            print("exit")
        except Exception as e:
            print(f"error: {e}")
    return out_buf.getvalue()

# Update cwd for status
try:
    rel = str(term.cwd.relative_to(term.root)) if term.cwd != term.root else "/"
except Exception:
    rel = "/"
st.session_state.cwd = rel

# ----------------------- UI -----------------------
left, right = st.columns([2, 1])

with left:
    st.markdown("## CodeMate Terminal – Streamlit UI")
    st.caption("Showcase for Problem 1 (Python terminal; same behavior as CLI)")

    # Output window
    out_container = st.container(border=True)
    with out_container:
        for cmd, output in st.session_state.history:
            if cmd:
                st.markdown(f"`$ {cmd}`")
            if output:
                st.code(output.rstrip("\n"), language="bash")

    # Input row
    st.write("")
    with st.form("cmd_form", clear_on_submit=True):
        cmd = st.text_input("Command", placeholder="e.g., ls, pwd, mkdir demo, cd demo, touch a.txt")
        submitted = st.form_submit_button("Run", type="primary", use_container_width=True)
        if submitted and cmd.strip():
            output = run_command(cmd.strip())
            st.session_state.history.append((cmd.strip(), output))
            st.rerun()

with right:
    st.markdown("### Quick Actions")
    c1, c2 = st.columns(2)
    if c1.button("pwd", use_container_width=True):
        st.session_state.history.append(("pwd", run_command("pwd")))
        st.rerun()
    if c2.button("ls", use_container_width=True):
        st.session_state.history.append(("ls", run_command("ls")))
        st.rerun()
    c3, c4 = st.columns(2)
    if c3.button("sysmon", use_container_width=True):
        st.session_state.history.append(("sysmon", run_command("sysmon")))
        st.rerun()
    if c4.button("df", use_container_width=True):
        st.session_state.history.append(("df", run_command("df")))
        st.rerun()

    st.divider()
    st.markdown("### Project Browser (read-only)")
    # Simple tree list (read-only): show first level + files
    try:
        root_items = sorted(os.listdir(ROOT))
        for name in root_items:
            p = ROOT / name
            if name.startswith('.'):
                continue
            if p.is_dir():
                st.markdown(f"**{name}/**")
                try:
                    inner = sorted(os.listdir(p))[:8]
                    for child in inner:
                        st.markdown(f"- {child}{'/' if (p/child).is_dir() else ''}")
                except Exception:
                    pass
            else:
                st.markdown(f"- {name}")
    except Exception as e:
        st.info(f"(browser error: {e})")

    st.divider()
    if st.button("Clear Output", use_container_width=True):
        banner_buf = io.StringIO()
        with redirect_stdout(banner_buf):
            term._banner()
        st.session_state.history = [(None, banner_buf.getvalue())]
        st.rerun()

    st.caption(f"cwd: {st.session_state.cwd}")
