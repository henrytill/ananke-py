import subprocess


def test():
    """
    Run all unittests.
    """
    subprocess.run(['python', '-u', '-m', 'unittest', 'discover'])


def test_coverage():
    """
    Run all unittests with coverage.
    """
    subprocess.run(['coverage', 'run', '-m', 'unittest', 'discover'])
    subprocess.run(['coverage', 'xml'])
