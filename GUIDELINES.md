# Development Guidelines

This document outlines the architectural constraints and development best practices for the MediaWiki Code2Code Search project.

## 🚀 Performance & Resource Constraints

### 1. RAM Usage (6 GiB Limit)
The application is deployed on Wikimedia Toolforge, which has a strict **6 GiB RAM limit** for webservices.
- **SQLite for Metadata**: Avoid loading large JSON/list structures into memory. Use the indexed SQLite database (`backend/functions.db`) for all metadata lookups.
- **FAISS Indexing**: Use `IndexIVFPQ` or other compressed FAISS indexes to keep the memory footprint low.
- **Lazy Loading**: Ensure models and indexes are loaded once during the server lifespan, not on every request.

### 2. CPU-Only Environment
The production environment (Toolforge) is **CPU-only**.
- **Recall vs. Rerank**: Highly accurate but heavy models (like Rerankers) should be used sparingly or optimized. The current architecture prioritizes the **recall model** (`jina-code-embeddings-0.5b`) which is fast on CPUs.
- **Quantization**: If memory or speed becomes an issue, consider dynamic quantization for models.

### 3. Asymmetric Pipeline
The project follows a "Build Heavy, Serve Light" philosophy:
- **Indexing (GPU)**: Extraction and neural vectorization should be performed on a GPU-equipped machine to generate the `mediawiki.index`.
- **Serving (CPU)**: The `app.py` server is optimized for high-speed retrieval on standard CPU hardware.

## 🛠️ Code & Architecture

### 1. Asynchronous I/O
- Use `httpx.AsyncClient` for external API calls (e.g., Software Heritage) to avoid blocking the event loop.
- Endpoints should be `async def` when performing I/O.

### 2. Toolforge Compatibility
- Paths should be relative to the application root where possible, or use the `BASE_DIR` pattern defined in `app.py`.
- The application includes specific patches (e.g., environment variables for `torch`, user identification) to run smoothly in Toolforge's Kubernetes environment.

### 3. Localization (i18n)
- The frontend supports multiple languages. When adding features, ensure strings are externalized into the i18n JSON files.
- The `update_i18n.py` script can be used to synchronize translation keys.

## 🧪 Testing

- **Mocking**: When writing tests for the API, always mock the `SentenceTransformer` and other heavy models to ensure CI runs quickly without downloading weights.
- **Safe Testing**: Never run tests that write to production folders (`backend/swh_cache`, etc.). Use temporary directories for test artifacts.
