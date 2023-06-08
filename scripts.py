import subprocess


def test():
    """
    Run all unittests. Equivalent to:
    `poetry run python -u -m unittest discover`
    """
    subprocess.run(['python', '-u', '-m', 'unittest', 'discover'])


def coverage():
    """
    Run all unittests with coverage. Equivalent to:
    `poetry run python -u -m coverage run -m unittest discover`
    """
    subprocess.run(['coverage', 'run', '-m', 'unittest', 'discover'])
