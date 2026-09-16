
import argparse

from qyro.cmdline.commands.clean import CleanCommand


def test_configure_does_not_add_arguments():
    parser = argparse.ArgumentParser()

    CleanCommand.configure(parser)

    args = parser.parse_args([])

    assert vars(args) == {}


def test_execute_prints_message(capsys):
    result = CleanCommand.execute(argparse.Namespace())

    captured = capsys.readouterr()

    assert result == 0
    assert captured.out == "Clean command selected.\n"
