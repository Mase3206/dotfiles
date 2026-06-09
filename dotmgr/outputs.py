#!/usr/bin/python3

"""Console output helpers"""

import string
from enum import Enum


class AnsiColors(str, Enum):
    """ANSI color codes"""

    BLACK = "\033[0;30m"
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    BROWN = "\033[0;33m"
    BLUE = "\033[0;34m"
    PURPLE = "\033[0;35m"
    CYAN = "\033[0;36m"
    LIGHT_GRAY = "\033[0;37m"
    DARK_GRAY = "\033[1;30m"
    LIGHT_RED = "\033[1;31m"
    LIGHT_GREEN = "\033[1;32m"
    YELLOW = "\033[1;33m"
    LIGHT_BLUE = "\033[1;34m"
    LIGHT_PURPLE = "\033[1;35m"
    LIGHT_CYAN = "\033[1;36m"
    LIGHT_WHITE = "\033[1;37m"
    BOLD = "\033[1m"
    FAINT = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    NEGATIVE = "\033[7m"
    CROSSED = "\033[9m"
    END = "\033[0m"


def big_header(content: str):
    print(
        "\n\n"
        + f"{AnsiColors.GREEN}======== {content} ========"
        + f"{AnsiColors.END}\n"
    )


def subheader(content: str):
    print("\n" + f"{AnsiColors.BLUE}---- {content} ----" + f"{AnsiColors.END}")


def step(content: str):
    print(f"{AnsiColors.LIGHT_CYAN}- {content}{AnsiColors.END}")


def status_bad(subject: str, message: str):
    print(f"{subject}: {AnsiColors.RED}{message}{AnsiColors.END}")


def status_good(subject: str, message: str):
    print(f"{subject}: {message}")


def skip(content: str):
    print(f"{AnsiColors.LIGHT_RED}Skipping{AnsiColors.END} {content}")


def confirm(message: str, defaul_yes: bool = True) -> bool:
    while True:
        iput = (
            input(
                f"{message} [{'Y' if defaul_yes else 'y'}/{'n' if defaul_yes else 'N'}]"
            )
            .strip()
            .lower()
        )
        if defaul_yes:
            if iput == "" or iput in string.whitespace or iput in ["y", "yes"]:
                return True
            elif iput in ["n", "no"]:
                return False
            # If neither, continue looping
        else:
            if iput in ["y", "yes"]:
                return True
            elif iput == "" or iput in string.whitespace or iput in ["n", "no"]:
                return False
            # If neither, continue looping
