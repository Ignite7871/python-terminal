#!/usr/bin/env python3
"""
CodeMate Hackathon – Problem Statement 1: Python-Based Command Terminal
Entry point: main.py (keep this file at repo root)

Features implemented (meets mandatory requirements):
  • Python backend command processor with REPL
  • File/dir ops: ls, cd, pwd, mkdir, rm, touch, cat, echo, cp, mv
  • Error handling for invalid/malformed commands
  • Clean CLI interface (prompt shows cwd relative to project root)
  • System monitoring commands: ps, sysmon (CPU/memory), df (disk)
  • Safe sandbox: prevents navigating or deleting outside the project root

Nice-to-have included:
  • help command with usage hints
  • history command (uses readline if available; falls back gracefully)

No external dependencies; standard library only.

Author: You (Srisu) – built for CodeMate AI Hackathon
"""
from __future__ import annotations

import os
import sys
import shlex
import shutil
import platform
import subprocess
from pathlib import Path
from datetime import datetime

# ----------------------------
# Utility: Optional readline
# ----------------------------
try:
    import readline  # type: ignore
except Exception:  # pragma: no cover
    readline = None  # Not available on some platforms

# ----------------------------
# Terminal Core
# ----------------------------
class Terminal:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.cwd = self.root
        self.commands = {
            'help': self.cmd_help,
            'pwd': self.cmd_pwd,
            'ls': self.cmd_ls,
            'cd': self.cmd_cd,
            'mkdir': self.cmd_mkdir,
            'rm': self.cmd_rm,
            'touch': self.cmd_touch,
            'cat': self.cmd_cat,
            'echo': self.cmd_echo,
            'cp': self.cmd_cp,
            'mv': self.cmd_mv,
            'head': self.cmd_head,
            'tail': self.cmd_tail,
            'ps': self.cmd_ps,
            'sysmon': self.cmd_sysmon,
            'df': self.cmd_df,
            'history': self.cmd_history,
            'exit': self.cmd_exit,
            'quit': self.cmd_exit,
        }
        self._ensure_root_exists()
        self._init_history()

    # ------------- helpers -------------
    def _ensure_root_exists(self):
        self.root.mkdir(parents=True, exist_ok=True)

    def _init_history(self):
        if readline:
            histfile = str(self.root / '.terminal_history')
            try:
                readline.read_history_file(histfile)
            except Exception:
                pass
            import atexit
            atexit.register(lambda: self._save_history(histfile))

    def _save_history(self, histfile: str):
        if readline:
            try:
                readline.write_history_file(histfile)
            except Exception:
                pass

    def _resolve_path(self, path_str: str | None) -> Path:
        """Resolve user path within sandbox root (prevent escaping root)."""
        if not path_str:
            return self.cwd
        p = Path(path_str)
        if not p.is_absolute():
            p = (self.cwd / p).resolve()
        else:
            p = p.resolve()
        # sandbox: clamp to root
        try:
            p.relative_to(self.root)
        except ValueError:
            # If outside, map back under root
            p = (self.root / p.name).resolve()
        return p

    def _print_err(self, msg: str):
        print(f"error: {msg}")

    def _confirm(self, prompt: str) -> bool:
        try:
            return input(f"{prompt} [y/N]: ").strip().lower() == 'y'
        except EOFError:
            return False

    # ------------- REPL -------------
    def run(self):
        self._banner()
        while True:
            try:
                rel = str(self.cwd.relative_to(self.root)) if self.cwd != self.root else ''
                prompt = f"codemate:{rel if rel else '/'}$ "
                line = input(prompt)
            except (EOFError, KeyboardInterrupt):
                print("\nexit")
                break
            if not line.strip():
                continue
            self.execute(line)

    def execute(self, line: str):
        try:
            parts = shlex.split(line)
        except ValueError as e:
            self._print_err(f"parse error: {e}")
            return
        cmd, *args = parts
        handler = self.commands.get(cmd)
        if not handler:
            self._print_err(f"unknown command: {cmd}. Try 'help'.")
            return
        try:
            handler(args)
        except SystemExit:
            raise
        except Exception as e:
            self._print_err(str(e))

    # ------------- Commands -------------
    def cmd_help(self, args):
        print("""
Built-in commands:
  help                 Show this help
  pwd                  Print working directory
  ls [path]            List files (add -a to include hidden)
  cd [path]            Change directory (sandboxed to project root)
  mkdir <dir>...       Create directories (supports multiple)
  rm [-r] <path>...    Remove files; -r for directories
  touch <file>...      Create empty file(s) or update mtime
  cat <file>...        Print file(s)
  echo [text]          Print text
  cp <src> <dst>       Copy file/dir (dst may be dir)
  mv <src> <dst>       Move/rename
  head [-n N] <file>   First N lines (default 10)
  tail [-n N] <file>   Last N lines (default 10)
  ps                   Show running processes (system)
  sysmon               CPU & memory snapshot
  df                   Disk usage for project root
  history              Show recent command history (if available)
  exit | quit          Leave terminal
""".strip())

    def cmd_pwd(self, args):
        print(str(self.cwd))

    def cmd_ls(self, args):
        show_all = False
        target = None
        for a in args:
            if a == '-a':
                show_all = True
            else:
                target = a
        path = self._resolve_path(target)
        if not path.exists():
            self._print_err("path not found")
            return
        if path.is_file():
            print(path.name)
            return
        items = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        for p in items:
            if not show_all and p.name.startswith('.'):
                continue
            suffix = '/' if p.is_dir() else ''
            print(p.name + suffix)

    def cmd_cd(self, args):
        path = self._resolve_path(args[0]) if args else self.root
        if not path.exists() or not path.is_dir():
            self._print_err("no such directory")
            return
        # sandbox: prevent escape by re-check
        try:
            path.relative_to(self.root)
        except ValueError:
            self._print_err("access outside project root is blocked")
            return
        self.cwd = path

    def cmd_mkdir(self, args):
        if not args:
            self._print_err("usage: mkdir <dir>...")
            return
        for d in args:
            Path(self._resolve_path(d)).mkdir(parents=True, exist_ok=True)

    def cmd_rm(self, args):
        if not args:
            self._print_err("usage: rm [-r] <path>...")
            return
        recursive = False
        paths = []
        for a in args:
            if a == '-r':
                recursive = True
            else:
                paths.append(a)
        for pstr in paths:
            p = self._resolve_path(pstr)
            if not p.exists():
                self._print_err(f"not found: {pstr}")
                continue
            if p.is_dir():
                if not recursive:
                    self._print_err(f"is a directory (use -r): {pstr}")
                    continue
                if not self._confirm(f"rm -r {p}"):
                    print("aborted")
                    continue
                shutil.rmtree(p)
            else:
                p.unlink()

    def cmd_touch(self, args):
        if not args:
            self._print_err("usage: touch <file>...")
            return
        for f in args:
            p = self._resolve_path(f)
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, 'a', encoding='utf-8'):
                os.utime(p, None)

    def cmd_cat(self, args):
        if not args:
            self._print_err("usage: cat <file>...")
            return
        for f in args:
            p = self._resolve_path(f)
            if not p.exists() or not p.is_file():
                self._print_err(f"no such file: {f}")
                continue
            with open(p, 'r', encoding='utf-8', errors='replace') as fh:
                print(fh.read(), end='')

    def cmd_echo(self, args):
        print(' '.join(args))

    def cmd_cp(self, args):
        if len(args) < 2:
            self._print_err("usage: cp <src> <dst>")
            return
        src = self._resolve_path(args[0])
        dst = self._resolve_path(args[1])
        if not src.exists():
            self._print_err("source not found")
            return
        if src.is_dir():
            if dst.exists() and dst.is_dir():
                dst = dst / src.name
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            if dst.is_dir():
                dst = dst / src.name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    def cmd_mv(self, args):
        if len(args) < 2:
            self._print_err("usage: mv <src> <dst>")
            return
        src = self._resolve_path(args[0])
        dst = self._resolve_path(args[1])
        if not src.exists():
            self._print_err("source not found")
            return
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))

    def _read_n_lines(self, path: Path, n: int, tail: bool = False):
        if n <= 0:
            return
        if tail:
            # simple memory-friendly tail
            from collections import deque
            dq = deque(maxlen=n)
            with open(path, 'r', encoding='utf-8', errors='replace') as fh:
                for line in fh:
                    dq.append(line)
            for line in dq:
                print(line, end='')
        else:
            with open(path, 'r', encoding='utf-8', errors='replace') as fh:
                for i, line in enumerate(fh):
                    if i >= n:
                        break
                    print(line, end='')

    def cmd_head(self, args):
        if not args:
            self._print_err("usage: head [-n N] <file>")
            return
        n = 10
        files = []
        it = iter(args)
        for a in it:
            if a == '-n':
                try:
                    n = int(next(it))
                except Exception:
                    self._print_err("invalid N")
                    return
            else:
                files.append(a)
        for f in files:
            p = self._resolve_path(f)
            if not p.exists() or not p.is_file():
                self._print_err(f"no such file: {f}")
                continue
            self._read_n_lines(p, n, tail=False)

    def cmd_tail(self, args):
        if not args:
            self._print_err("usage: tail [-n N] <file>")
            return
        n = 10
        files = []
        it = iter(args)
        for a in it:
            if a == '-n':
                try:
                    n = int(next(it))
                except Exception:
                    self._print_err("invalid N")
                    return
            else:
                files.append(a)
        for f in files:
            p = self._resolve_path(f)
            if not p.exists() or not p.is_file():
                self._print_err(f"no such file: {f}")
                continue
            self._read_n_lines(p, n, tail=True)

    def cmd_ps(self, args):
        """List running processes using system tools (cross-platform best-effort)."""
        try:
            if platform.system() == 'Windows':
                subprocess.run(["tasklist"], check=False)
            else:
                subprocess.run(["ps", "-e", "-o", "pid,comm,pcpu,pmem"], check=False)
        except Exception as e:
            self._print_err(f"ps failed: {e}")

    def cmd_sysmon(self, args):
        """Print simple CPU/memory snapshot without external deps."""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"Snapshot @ {now}")
        # CPU load avg (Unix only)
        if hasattr(os, 'getloadavg'):
            try:
                la1, la5, la15 = os.getloadavg()
                print(f"loadavg: 1m={la1:.2f} 5m={la5:.2f} 15m={la15:.2f}")
            except Exception:
                pass
        # Memory info (best effort)
        try:
            if platform.system() == 'Linux':
                with open('/proc/meminfo', 'r', encoding='utf-8', errors='ignore') as fh:
                    lines = [next(fh) for _ in range(5)]
                for ln in lines:
                    print(ln.strip())
            elif platform.system() == 'Darwin':
                subprocess.run(["vm_stat"], check=False)
            elif platform.system() == 'Windows':
                subprocess.run(["wmic", "OS", "get", "FreePhysicalMemory,TotalVisibleMemorySize", "/Value"], check=False)
        except Exception as e:
            self._print_err(f"mem info failed: {e}")

    def cmd_df(self, args):
        total, used, free = shutil.disk_usage(self.root)
        def gb(x):
            return x / (1024**3)
        print(f"Filesystem (project root): total={gb(total):.2f}G used={gb(used):.2f}G free={gb(free):.2f}G")

    def cmd_history(self, args):
        if not readline:
            print("history unavailable on this platform")
            return
        hist_len = readline.get_current_history_length()
        start = max(1, hist_len - 50 + 1)
        for i in range(start, hist_len + 1):
            print(f"{i}: {readline.get_history_item(i)}")

    def cmd_exit(self, args):
        raise SystemExit(0)

    # ------------- UI -------------
    def _banner(self):
        print(
            """
CodeMate Python Terminal (sandboxed)\nType 'help' to see commands, 'exit' to leave.
            """.strip()
        )


# ----------------------------
# Main entry
# ----------------------------

def main():
    # Use the directory containing main.py as the sandbox root
    root = Path(__file__).parent
    term = Terminal(root)
    term.run()


if __name__ == '__main__':
    try:
        main()
    except SystemExit as e:
        sys.exit(e.code)
    except Exception as e:
        print(f"fatal: {e}")
        sys.exit(1)
