"""Put a process and its children under a memory ceiling.

A runaway agent, tool or test should fail alone rather than exhaust the machine. On
Windows this uses a job object, which child processes join automatically. Elsewhere
it sets the address-space limit, which children inherit.

    python -m chaser_agent.process_limits --process-mb 2048 --total-mb 4096 -- command args
"""

from __future__ import annotations

import argparse
import ctypes
import os
import subprocess
import sys
from ctypes import wintypes

LIMIT_PROCESS_MEMORY = 0x100
LIMIT_JOB_MEMORY = 0x200
EXTENDED_LIMIT_INFORMATION = 9
_held_jobs: list[object] = []


class _BasicLimits(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_longlong),
        ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class _IoCounters(ctypes.Structure):
    _fields_ = [(name, ctypes.c_ulonglong) for name in ("Read", "Write", "Other", "ReadBytes", "WriteBytes", "OtherBytes")]


class _ExtendedLimits(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _BasicLimits),
        ("IoInfo", _IoCounters),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


def _limit_windows(process_mb: int, total_mb: int) -> None:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    job = kernel32.CreateJobObjectW(None, None)
    if not job:
        raise OSError(ctypes.get_last_error(), "A memory-limit job could not be created")
    limits = _ExtendedLimits()
    limits.BasicLimitInformation.LimitFlags = LIMIT_PROCESS_MEMORY | LIMIT_JOB_MEMORY
    limits.ProcessMemoryLimit = process_mb * 1024 * 1024
    limits.JobMemoryLimit = total_mb * 1024 * 1024
    if not kernel32.SetInformationJobObject(job, EXTENDED_LIMIT_INFORMATION, ctypes.byref(limits), ctypes.sizeof(limits)):
        raise OSError(ctypes.get_last_error(), "The memory limit could not be set")
    if not kernel32.AssignProcessToJobObject(job, kernel32.GetCurrentProcess()):
        raise OSError(ctypes.get_last_error(), "This process could not join the memory-limit job")
    # Closing the last handle would end the job's limits, so it is held for the process's life.
    _held_jobs.append(job)


def limit_memory(*, process_mb: int, total_mb: int | None = None) -> None:
    """Cap this process and every child it starts. Allocations beyond the cap fail."""
    if process_mb <= 0:
        raise ValueError("A memory limit must be positive")
    total = total_mb or process_mb
    if os.name == "nt":
        _limit_windows(process_mb, total)
        return
    import resource

    resource.setrlimit(resource.RLIMIT_AS, (process_mb * 1024 * 1024, process_mb * 1024 * 1024))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--process-mb", type=int, required=True)
    parser.add_argument("--total-mb", type=int)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("Name a command after --")
    limit_memory(process_mb=args.process_mb, total_mb=args.total_mb)
    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    sys.exit(main())
