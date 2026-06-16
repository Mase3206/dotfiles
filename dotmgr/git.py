import shlex
import string
import subprocess
from enum import Enum
from typing import Union

from dotmgr import DOTFILES_DIR, DOTFILES_MANAGED_FILE, filelib, outputs

ALL_DOTFILES = filelib.load_dotfiles(DOTFILES_MANAGED_FILE)


class GitFileStatus(str, Enum):
    # Note: contains only the statuses we care about
    ADDED = "A "
    MODIFIED = " M"
    DELETED = " D"
    UNTRACKED = "??"


FileList = list[tuple[GitFileStatus, filelib.Dotfile]]


def git_cmd(
    args: Union[str, list[str]], stdout: bool = False, stdin: bool = False, **kwargs
):
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
        **kwargs,
    )

    if out.returncode > 0:
        print(out.stderr)
        exit(out.returncode)
    else:
        return out


def get_changed_dotfiles() -> tuple[FileList, bool]:
    '''
    Get a list of dotfiles which have changed in the Git repo.

    Returns
    -------
    :return FileList: List of changed files
    :return bool: Whether managed.files has changed
    '''
    # out = subprocess.run(
    #     ['git', 'status', '--porcelain', '-z'],
    #     stdout=subprocess.PIPE,
    #     encoding='utf-8',
    #     cwd=DOTFILES_DIR
    # )
    out = git_cmd(
        "status --porcelain -z",
        stdout=True,
    )

    lines = out.stdout.split("\0")
    parsed: FileList = []
    managed_file_changed = False
    # files_to_notice = [*ALL_DOTFILES.keys(), 'managed.files']
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
        if path in ['managed.files']:
            managed_file_changed = True
        elif path in ALL_DOTFILES.keys():
            parsed.append((status, ALL_DOTFILES[path]))

    return parsed, managed_file_changed


def get_all_changed_files() -> list[tuple[GitFileStatus, str]]:
    out = git_cmd(
        "status --porcelain -z",
        stdout=True,
    )

    lines = out.stdout.split("\0")
    parsed: list[tuple[GitFileStatus, str]] = []
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


def generate_commit_message(changed: FileList, managed_file_changed: bool = False) -> str:
    # Sort the files into the right status "bins"
    new: list[str] = []
    modified: list[str] = []
    if managed_file_changed:
        modified += ['managed.files']
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

    # new += ['.asdf']

    message_lines = []
    if new:
        message_lines.append("N: " + ", ".join(new))
    if modified:
        message_lines.append("M: " + ", ".join(modified))
    if deleted:
        message_lines.append("D: " + ", ".join(deleted))

    return "; ".join(message_lines)


def format_changed_human(changed: FileList, managed_file_changed: bool = True) -> str:
    new: list[str] = []
    modified: list[str] = []
    if managed_file_changed:
        modified += ['managed.files']
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
        if (
            message_lines[-1].strip() in string.whitespace
            or message_lines[-1].strip() == ""
        ):
            message_lines = message_lines[:-1]

        return "\n".join(message_lines)
    else:
        return "No changes to managed dotfiles detected."


def commit_dotfiles(changed: FileList, managed_file_changed: bool = False):
    message = generate_commit_message(changed, managed_file_changed)

    file_paths = [str(change[1].relative_path) for change in changed]
    if managed_file_changed:
        file_paths += ['managed.files']

    # Add files
    git_cmd(["add", *file_paths]).check_returncode()

    # Commit
    git_cmd(["commit", "-m", message]).check_returncode()

    # Push
    # push_dotfiles()


def push_dotfiles():
    # changed_dotfiles = get_changed_dotfiles()
    # all_changed = get_all_changed_files()
    # changed_non_dotfiles = [f for f in all_changed if f not in changed_dotfiles]

    # if len(changed_non_dotfiles) > 0:

    git_cmd("push").check_returncode()


def stash_push():
    git_cmd("stash").check_returncode()


def stash_pop():
    git_cmd("stash pop").check_returncode()


def pull():
    git_cmd("pull").check_returncode()


# print(generate_commit_message(status_dotfiles()))

# print(ALL_DOTFILES['.zshrc'])
# for s in status_dotfiles():
#     print(s[0], s[1])

# print(lines)
