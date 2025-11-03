"""Input handling and file processing."""

import base64
import sys
from pathlib import Path


class InputHandler:
    """Handles various input types (stdin, file, text)."""

    SUPPORTED_EXTENSIONS = {
        ".txt",
        ".md",
        ".json",
        ".csv",
        ".log",
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".html",
        ".css",
        ".xml",
        ".yaml",
        ".yml",
        ".toml",
        ".sh",
    }

    SUPPORTED_MEDIA_EXTENSIONS = {
        ".pdf",
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
        ".mp3",
        ".wav",
        ".m4a",
    }

    @staticmethod
    def has_stdin() -> bool:
        """Check if there's data in stdin."""
        return not sys.stdin.isatty()

    @staticmethod
    def read_stdin() -> str:
        """Read all data from stdin."""
        return sys.stdin.read()

    @staticmethod
    def load_input(source: str | None = None) -> tuple[str, str]:
        """
        Load input from various sources.

        Returns:
            Tuple of (content, source_description)
        """
        # Priority: stdin > file path > inline text
        if InputHandler.has_stdin():
            content = InputHandler.read_stdin()
            return content, "stdin"

        if source:
            # Try to treat as file path
            file_path = Path(source)
            if file_path.exists():
                return InputHandler.load_file(file_path)
            else:
                # Treat as inline text
                return source, "inline_text"

        # No input provided
        return "", "none"

    @staticmethod
    def load_file(file_path: Path) -> tuple[str, str]:
        """
        Load content from a file.

        Returns:
            Tuple of (content, source_description)
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = file_path.suffix.lower()

        # Handle text files
        if ext in InputHandler.SUPPORTED_EXTENSIONS:
            with open(file_path) as f:
                content = f.read()
            return content, f"file:{file_path.name}"

        # Handle media files (base64 encode)
        if ext in InputHandler.SUPPORTED_MEDIA_EXTENSIONS:
            if ext == ".pdf":
                return InputHandler._handle_pdf(file_path)
            elif ext in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
                return InputHandler._handle_image(file_path)
            elif ext in {".mp3", ".wav", ".m4a"}:
                return InputHandler._handle_audio(file_path)

        # Default: try to read as text
        try:
            with open(file_path) as f:
                content = f.read()
            return content, f"file:{file_path.name}"
        except UnicodeDecodeError:
            raise ValueError(
                f"Cannot read file: {file_path}. Unsupported format or binary file."
            )

    @staticmethod
    def _handle_image(file_path: Path) -> tuple[str, str]:
        """Handle image files by base64 encoding."""
        with open(file_path, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        ext = file_path.suffix.lower().lstrip(".")
        mime_type = f"image/{ext}"
        content = f"[Image: {file_path.name}]\nMIME: {mime_type}\nBase64:\n{b64}"
        return content, f"image:{file_path.name}"

    @staticmethod
    def _handle_pdf(file_path: Path) -> tuple[str, str]:
        """Handle PDF files."""
        try:
            import PyPDF2
        except ImportError:
            raise ImportError(
                "PDF support requires PyPDF2. Install with: pip install PyPDF2"
            )

        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"

        return text, f"pdf:{file_path.name}"

    @staticmethod
    def _handle_audio(file_path: Path) -> tuple[str, str]:
        """Handle audio files by base64 encoding."""
        with open(file_path, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        ext = file_path.suffix.lower().lstrip(".")
        mime_type = f"audio/{ext}"
        content = f"[Audio: {file_path.name}]\nMIME: {mime_type}\nBase64:\n{b64}"
        return content, f"audio:{file_path.name}"

    @staticmethod
    def get_file_info(file_path: Path) -> dict:
        """Get metadata about a file."""
        if not file_path.exists():
            return {"exists": False}

        stat = file_path.stat()
        return {
            "exists": True,
            "path": str(file_path),
            "name": file_path.name,
            "size": stat.st_size,
            "extension": file_path.suffix.lower(),
            "is_text": file_path.suffix.lower() in InputHandler.SUPPORTED_EXTENSIONS,
            "is_media": file_path.suffix.lower() in InputHandler.SUPPORTED_MEDIA_EXTENSIONS,
        }
