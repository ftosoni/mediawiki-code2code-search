# Contributing to MediaWiki Code2Code Search

Thank you for your interest in contributing! We welcome contributions from the community to help improve the MediaWiki developer ecosystem.

## 🛠️ Development Setup

To set up a development environment, follow these steps:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ftosoni/mediawiki-code2code-search.git
   cd mediawiki-code2code-search
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-asyncio flake8
   ```

## 🧪 Testing and Quality

Before submitting a Pull Request, please ensure your changes pass the automated checks.

### Running Tests
We use `pytest` for testing. To run the lightweight API and connectivity tests:
```bash
pytest tests/test_api.py tests/test_hf_availability.py
```
*Note: Large model tests in `tests/test_jina_components.py` are generally excluded from CI and standard local runs to save resources.*

### Linting
We follow PEP 8 standards. You can check your code with `flake8`:
```bash
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
```

## 📜 Technical Guidelines
Please review our [GUIDELINES.md](./GUIDELINES.md) for details on:
- Staying within the **6 GiB RAM limit** for Toolforge.
- Optimising for **CPU-only** inference.
- Using SQLite for metadata persistence.

## 🤝 Contribution Process
1. **Open an Issue**: For any major changes, please open an issue first to discuss what you would like to change.
2. **Create a Branch**: Use a descriptive branch name (e.g., `fix/search-latency` or `feature/new-language`).
3. **Submit a Pull Request**: Provide a clear description of the changes and link to the relevant issue.
