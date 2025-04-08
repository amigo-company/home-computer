import subprocess

def run(process: str | list[str], cwd: str = None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        process,
        capture_output=True,
        cwd=cwd
    )


def launch(process: str | list[str]) -> subprocess.Popen:
    return subprocess.Popen(
        process,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )