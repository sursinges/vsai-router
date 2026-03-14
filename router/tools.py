import subprocess


def run_python(code):

    try:

        result = subprocess.run(
            ["python", "-c", code],
            capture_output=True,
            text=True,
            timeout=10
        )

        return result.stdout

    except Exception as e:

        return str(e)