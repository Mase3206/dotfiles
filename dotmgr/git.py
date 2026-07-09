import shlex
import string
import subprocess
from enum import Enum
from typing import Any, Generic, Optional, TypeVar, Union

from dotmgr import DOTFILES_DIR, DOTFILES_MANAGED_FILE, filelib, outputs


ALL_DOTFILES = filelib.load_dotfiles(DOTFILES_MANAGED_FILE)
T = TypeVar("T")


class GitFileStatus(str, Enum):
    # Note: contains only the statuses we care about
    ADDED = "A "
    MODIFIED = " M"
    DELETED = " D"
    UNTRACKED = "??"


class FileList(Generic[T], list[tuple[GitFileStatus, T]]): ...


def git_cmd(
    args: Union[str, list[str]],
    stdout: bool = False,
    stdin: bool = False,
    check: bool = True,
    **kwargs: Any,
) -> subprocess.CompletedProcess[str]:
    """
    Run a Git command.

    Some key-word arguments are pre-set and should not be changed:
    ```python
    stderr = subprocess.PIPE
    cwd = DOTFILES_DIR
    encoding = "utf-8"
    check = True
    ```


    :param str | list[str] args: Git subcommand and arguments. If str, will be split with :func:`shlex.split`.
    :param bool = False stdout: Pipe stdout
    :param bool = False stdin: Pipe stdin
    :param kwargs: Additional keyword arguments to pass to :func:`subprocess.run`

    :returns subprocess.CompletedProcess[str]:
    """

    if stdout:
        kwargs["stdout"] = subprocess.PIPE
    if stdin:
        kwargs["stdin"] = subprocess.PIPE

    if isinstance(args, str):
        args = shlex.split(args)

    out = subprocess.run(
        ["git", *args],
        cwd=DOTFILES_DIR,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        check=check,
        **kwargs,
    )

    if out.returncode > 0:
        print(out.stderr)
        exit(out.returncode)
    else:
        return out


def get_changed_dotfiles() -> tuple[FileList[filelib.Dotfile], bool]:
    """
    Get a list of dotfiles which have changed in the Git repo.

    :return FileList[Dotfile]: List of changed dotfiles
    :return bool: Whether managed.files has changed
    """

    out = git_cmd(
        "status --porcelain -zu",
        stdout=True,
    )

    lines = out.stdout.split("\0")
    parsed: FileList[filelib.Dotfile] = FileList()
    managed_file_changed = False

    for line in lines:
        if line == "":
            continue
        try:
            status = GitFileStatus(line[:2])
        except ValueError:
            continue

        path = line[3:]
        # Ignore changes to dotmgr itself
        if path.split("/")[0] == "dotmgr":
            continue
        # Ignore unmanaged dotfiles
        if path in ["managed.files"]:
            managed_file_changed = True
        elif path in ALL_DOTFILES.keys():
            parsed.append((status, ALL_DOTFILES[path]))

    return parsed, managed_file_changed


def get_all_changed_files() -> FileList[str]:
    """
    Get all changed files, including dotfiles and non-dotfiles.

    :returns FileList[str]: List of paths (relative to $DOTFILES_DIR) of changed files.
    """

    out = git_cmd(
        "status --porcelain -zu",
        stdout=True,
    )

    lines = out.stdout.split("\0")
    parsed: FileList[str] = FileList()
    for line in lines:
        if line == "":
            continue
        try:
            status = GitFileStatus(line[:2])
        except ValueError:
            continue

        path = line[3:]
        # Ignore changes to dotmgr itself
        parsed.append((status, path))

    return parsed


def generate_commit_message(changed: FileList[filelib.Dotfile], managed_file_changed: bool) -> str:
    """
    Generates a simple commit message for modified dotfiles.

    - **N** - new (added and untracked) files
    - **M** - modified files
    - **D** - deleted files

    **Example message:**
    ```
    N: .bashrc, .vimrc; M: .zshrc, managed.files; D: .config/ruff/ruff.toml
    ```

    **Example usage:**
    ```
    # Get changed files and whether managed.file changed
    changed_files, changed_managed_file = git.get_changed_dotfiles()

    # Pass both to this function - could also be done via argument expansion
    msg = git.generate_commit_message(changed_files, changed_managed_file)
    ```


    :param FileList[Dotfile] changed: List of changed dotfiles
    :param bool managed_file_changed: Whether the managed.files file has changed

    :returns str: Generated commit message
    """

    # Sort the files into the right status "bins"
    new: list[str] = []
    modified: list[str] = []
    if managed_file_changed:
        modified += ["managed.files"]
    deleted: list[str] = []

    for status, df in changed:
        # print(status, df)
        if status == GitFileStatus.ADDED or status == GitFileStatus.UNTRACKED:
            new.append(str(df.relative_path))
        elif status == GitFileStatus.MODIFIED:
            modified.append(str(df.relative_path))
        elif status == GitFileStatus.DELETED:
            deleted.append(str(df.relative_path))
        else:
            print(f"{df} has unknown status {status}")

    message_lines = []
    if new:
        message_lines.append("N: " + ", ".join(new))
    if modified:
        message_lines.append("M: " + ", ".join(modified))
    if deleted:
        message_lines.append("D: " + ", ".join(deleted))

    return "; ".join(message_lines)


def format_changed_human(changed: FileList[filelib.Dotfile], managed_file_changed: bool) -> str:
    """
    Format the list of changed files in a more human-friendly way.

    **Example message:**
    ```
    New (untracked and just added):
    - .bashrc
    - .vimrc

    Modified files:
    - .zshrc
    - managed.files

    Deleted files:
    - .config/ruff/ruff.toml
    ```


    :param FileList[Dotfile] changed: List of changed dotfiles
    :param bool managed_file_changed: Whether the managed.files file has changed

    :returns str: Generated message
    """

    new: list[str] = []
    modified: list[str] = []
    if managed_file_changed:
        modified += ["managed.files"]
    deleted: list[str] = []

    for status, df in changed:
        if status == GitFileStatus.ADDED or status == GitFileStatus.UNTRACKED:
            new.append(str(df.relative_path))
        elif status == GitFileStatus.MODIFIED:
            modified.append(str(df.relative_path))
        elif status == GitFileStatus.DELETED:
            deleted.append(str(df.relative_path))
        else:
            print(f"{df} has unknown status {status}")

    message_lines = []
    if new:
        message_lines.append("New (untracked and just added):")
        for n in new:
            message_lines.append(
                f"{outputs.AnsiColors.GREEN}{outputs.AnsiColors.BOLD}-{outputs.AnsiColors.END} {n}"
            )
        message_lines.append("")

    if modified:
        message_lines.append("Modified files:")
        for m in modified:
            message_lines.append(
                f"{outputs.AnsiColors.BLUE}{outputs.AnsiColors.BOLD}-{outputs.AnsiColors.END} {m}"
            )
        message_lines.append("")

    if deleted:
        message_lines.append("Deleted files:")
        for d in deleted:
            message_lines.append(
                f"{outputs.AnsiColors.RED}{outputs.AnsiColors.BOLD}-{outputs.AnsiColors.END} {d}"
            )
        message_lines.append("")

    # Remove hanging newline (if present (which it should be (I think)))
    if len(message_lines) > 0:
        if message_lines[-1].strip() in string.whitespace or message_lines[-1].strip() == "":
            message_lines = message_lines[:-1]

        return "\n".join(message_lines)
    else:
        return "No changes to managed dotfiles detected."


def commit_dotfiles(
    changed: FileList[filelib.Dotfile],
    managed_file_changed: bool,
    message: Optional[str] = None,
):
    """
    Commit the given changed dotfiles to the Git repo in $DOTFILES_DIR.

    :param FileList[Dotfile] changed: List of changed dotfiles
    :param bool managed_file_changed: Whether the managed.files file has changed
    :param Optional[str] message: Optional manual commit message. If not given, a message will automatically
        be generated by :func:`~dotmgr.git.generate_commit_message`
    """

    if not message:
        message = generate_commit_message(changed, managed_file_changed)

    file_paths = [str(change[1].relative_path) for change in changed]
    if managed_file_changed:
        file_paths += ["managed.files"]

    # Add files
    git_cmd(["add", *file_paths])

    # Commit
    git_cmd(["commit", "-m", message])


def push_dotfiles():
    """Runs `git push`."""
    git_cmd("push")


def stash_push():
    """Runs `git stash` to stash the current uncommited changes."""
    git_cmd("stash")


def stash_pop():
    """Runs `git stash pop` to unstash the previously-stashed changes."""
    out = git_cmd("stash pop", check=False)
    if out.returncode == 1 and out.stderr == 'No stash entries found':
        print(out.stderr)
        return
    else:
        out.check_returncode()


def pull():
    """Runs `git pull`."""
    git_cmd("pull")
