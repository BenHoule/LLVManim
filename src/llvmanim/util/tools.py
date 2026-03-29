"""
Finds the commandline tools needed to run the project on the user's machine,
while also allowing the user to override paths
"""

import os
import platform
import shutil
from functools import cache, lru_cache
from glob import glob
from pathlib import Path


def sort_by_llvm_version(candidate: str):
    try:
        return int(candidate.split("-")[-1])
    except Exception:
        return -1


@cache
def try_to_find_latest_llvm_bin_dir_on_linux():
    if os.environ.get("NO_LLVM_DEFAULT_SEARCH"):
        return None
    default_path = Path("/", "usr", "lib", "llvm")
    # I don't know of any linux distros that would make this exist
    # but if it exists, it's probably what the user intends.
    if default_path.is_dir():
        bin_dir = default_path.joinpath("bin")
        if bin_dir.is_dir():
            return bin_dir
        return None

    candidates = glob(str(Path("/", "usr", "lib", "llvm*")))
    latest = max(candidates, key=sort_by_llvm_version)
    return Path(latest).joinpath("bin")


@cache
def llvm_bin_dir() -> Path | None:
    """
    The path to the directory containing the LLVM binary tools (eg., /usr/lib/llvm-18/bin if using llvm 18 on ubuntu).

    If the LLVM_BIN_DIR environment variable is not set, all LLVM tools (except those that are explicitly overridden)
    will be found in PATH with their standard names. If the user is on linux

    The default lookup might fail on many systems (like Debian-based distros)

    """
    from_env = os.environ.get("LLVM_BIN_DIR")
    if from_env is not None:
        return Path(from_env)
    # we have explicit linux support for searching for being smarter on linux
    if "linux" in platform.system().lower():
        return try_to_find_latest_llvm_bin_dir_on_linux()
    return None


@lru_cache(16)
def llvm_tool(name: str) -> Path | None:
    """
    Gets the path to an LLVM binary tool by name based on explicit overrides.
    """
    env_value = os.environ.get(name.capitalize().replace(" ", "_"))
    if env_value is not None:
        return Path(env_value)
    bin_dir = llvm_bin_dir()
    if bin_dir is None:
        fallback = shutil.which(name)
        if fallback is None:
            return None
        return Path(fallback)
    return bin_dir.joinpath(name)


@lru_cache(maxsize=16)
def find_tool(name: str) -> Path | None:
    """
    Finds a commandline tool by first checking if a user-provided explicit override exists,
    falling back to searching on PATH.
    """
    from_env = os.environ.get(name.capitalize().replace(" ", "_"))
    if from_env is None:
        on_path = shutil.which(name)
        if on_path is None:
            return None
        return Path(on_path)
    from_env = Path(from_env)
    if not from_env.exists():
        return None
    return from_env


@cache
def ffmpeg() -> Path | None:
    """
    The path to the ffmpeg binary to be used. If the FFMPEG env variable is unset, will be found on PATH
    """
    return find_tool("ffmpeg")
