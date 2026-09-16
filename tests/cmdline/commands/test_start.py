
import argparse

from qyro.cmdline.commands.start import StartCommand


def test_configure_does_not_add_arguments():
    parser = argparse.ArgumentParser()

    StartCommand.configure(parser)

    args = parser.parse_args([])

    assert vars(args) == {}


def test_execute_prints_message(capsys):
    result = StartCommand.execute(argparse.Namespace())

    captured = capsys.readouterr()

    assert result == 0
    assert captured.out == "Start command selected.\n"
