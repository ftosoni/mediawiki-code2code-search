You are an expert software engineer annotating a code retrieval benchmark.

You will be given one QUERY code snippet and a set of CANDIDATE code snippets
retrieved from a corpus. The candidates are in arbitrary order; their order carries
no information and must not influence your judgement.

Label each candidate independently for how well it satisfies the intent of the query
snippet.

## Relevance scale

- **1.0 — Relevant.** Implements the same computational task, or a correct specific
  solution for the query's intent. Differences in variable naming, code style, or
  programming language do not reduce relevance when the task is the same.
- **0.5 — Partially relevant.** Topically related: a partial realization of the intent,
  a non-idiomatic or incomplete implementation, or code where the target logic appears
  only as a helper step inside a larger function.
- **0.0 — Irrelevant.** Does not address the task, or overlaps only superficially
  (shared identifiers such as `mid` or `min` while performing an unrelated task).
- **null — Cannot determine.** The snippet is too truncated or context-dependent to
  judge. Use sparingly.

## Procedure

Judge each candidate on its own terms, against the query only. Do not compare
candidates to each other, do not rank them, and do not assume any particular number
of candidates is relevant — all of them may be relevant, or none.

For each candidate, write one short technical `rationale` (max 20 words) naming the
concrete task the snippet performs and, when the score is 0.5 or 0.0, the specific
reason for the deduction (e.g. "unit test for the target function, not an
implementation"; "shared identifier `mid`, performs base64 padding").

## Query snippet

```
def compute_swhid(content: bytes) -> str:
    sha1 = hashlib.new('sha1')
    header = f"blob {len(content)}\0".encode()
    sha1.update(header + content)
    return f"swh:1:cnt:{sha1.hexdigest()}"
```

## Candidates

### d001
```
def sha256_of(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
```

### d002
```
def sha1(filename):
    fd = io.open(filename, 'rb')
    h = hashlib.sha1()
    data = True
    while data:
        data = fd.read(4096)
        if data:
            h.update(data)
    fd.close()

    return h.hexdigest()
```

### d003
```
def sha_utf8(x):
                if isinstance(x, str):
                    x = x.encode("utf-8")
                return hashlib.sha1(x).hexdigest()
```

### d004
```
def test_sha1_complete_calculation(self) -> None:
        """Test sha1 of complete file."""
        res = tools.compute_file_hash(self.filename, sha='sha1')
        self.assertIn(res, (
            '1c12696e1119493a625aa818a35c41916ce32d0c',
            '146121e6d0461916c9a0fab00dc718acdb6a6b14',
        ))
```

### d005
```
def rehash(path: str, blocksize: int = 1 << 20) -> Tuple[str, str]:
    """Return (encoded_digest, length) for path using hashlib.sha256()"""
    h, length = hash_file(path, blocksize)
    digest = "sha256=" + urlsafe_b64encode(h.digest()).decode("latin1").rstrip("=")
    return (digest, str(length))
```

### d006
```
def __hash__(self):
        """
        Return a consistend hash of a file using its sha1 hash.
        The sha1 hash should always be present and unmutable.
        """
        return hash(self.sha1)
```

### d007
```
def sha1sum(path):
    """Calculates the sha1 sum of a given file without loading it at once in memory"""
    sha1sum = hashlib.sha1()
    with open(path, 'rb') as fd:
        block = fd.read(2**16)
        while len(block) != 0:
            sha1sum.update(block)
            block = fd.read(2**16)
    return sha1sum.hexdigest().zfill(40)
```

### d008
```
def _calculate_sha512(self, file_path: str) -> str:
        """Calculate SHA512 checksum of a file."""
        sha512_hash = hashlib.sha512()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha512_hash.update(chunk)
        return sha512_hash.hexdigest()
```

### d009
```
def hash_pin(pin: str) -> str:
    return hashlib.sha1(f"{pin} added salt".encode("utf-8", "replace")).hexdigest()[:12]
```

### d010
```
def calculate_sha256(file_path: str) -> str:
    '''
    Calcuate the sha256 of a file
    '''

    sha256_hash = hashlib.sha256()
    with open(file_path,'rb') as f:
        for byte_block in iter(lambda: f.read(4096),b''):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()
```

### d011
```
def test_sha1_complete_calculation(self):
        """Test sha1 of complete file."""
        res = tools.compute_file_hash(self.filename, sha='sha1')
        self.assertIn(res, (
            '1c12696e1119493a625aa818a35c41916ce32d0c',
            '146121e6d0461916c9a0fab00dc718acdb6a6b14',
        ))
```

## Output

Return raw JSON only. No preamble, no markdown fences, no commentary outside the
object.

```json
{
  "query_id": "D2",
  "labels": {
    "d001": {"score": 1.0, "rationale": "iterative binary search over sorted array"},
    "d002": {"score": 0.0, "rationale": "pytest case asserting search behaviour, not an implementation"}
  }
}
```

Every `doc_id` presented must appear exactly once in `labels`.
