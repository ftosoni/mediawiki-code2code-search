web: mkdir -p /workspace && ln -sf /data/project/code2codesearch/workspace/models /workspace/models && gunicorn app:app -k uvicorn.workers.UvicornWorker --workers=2 --timeout 120 --bind 0.0.0.0
