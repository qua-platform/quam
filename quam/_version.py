from importlib.metadata import version, PackageNotFoundError

try:
    # Reads version from installed package metadata.
    # Replace "quam" with your actual distribution name if different.
    __version__ = version("quam")
except PackageNotFoundError:
    # Fallback when package is not installed (e.g., running from source)
    __version__ = "0.0.0-unknown"
