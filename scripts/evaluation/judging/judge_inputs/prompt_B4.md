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
def evict_oldest(cache: dict, max_size: int) -> None:
    while len(cache) > max_size:
        oldest_key = next(iter(cache))
        del cache[oldest_key]
```

## Candidates

### d001
```
// RemoveOldest removes the oldest item from the cache.
func (c *Cache) RemoveOldest() {
	if c.cache == nil {
		return
	}
	ele := c.ll.Back()
	if ele != nil {
		c.removeElement(ele)
	}
}
```

### d002
```
/**
	 * Evict the least recently used entry.
	 */
	evictLRU() {
		let oldestKey
		let oldestTime = Infinity

		for (const [key, entry] of this.cache) {
			if (entry.lastAccessed < oldestTime) {
				oldestTime = entry.lastAccessed
				oldestKey = key
			}
		}

		if (oldestKey) {
			this.cache.delete(oldestKey)
			if (this.enableStats) {
				this.stats.evictions++
				this.stats.size--
			}
		}
	}
```

### d003
```
/**
	 * Evict entries to reduce memory pressure.
	 */
	evictByMemoryPressure() {
		// Sort entries by access frequency and recency
		const entries = Array.from(this.cache.entries()).sort((a, b) => {
			const [, entryA] = a
			const [, entryB] = b

			// Prefer keeping frequently accessed and recently accessed entries
			const scoreA = entryA.accessCount * 0.7 + (Date.now() - entryA.lastAccessed) * -0.3
			const scoreB = entryB.accessCount * 0.7 + (Date.now() - entryB.lastAccessed) * -0.3

			return scoreA - scoreB
		})

		// Remove the least valuable entries (first 25%)
		const toRemove = Math.ceil(entries.length * 0.25)
		for (let i = 0; i < toRemove; i++) {
			const [key] = entries[i]
			this.cache.delete(key)
			if (this.enableStats) {
				this.stats.evictions++
				this.stats.size--
			}
		}
	}
```

### d004
```
_emitEvictions(cache) {
		if (typeof this.onEviction !== 'function') {
			return;
		}

		for (const [key, item] of cache) {
			this.onEviction(key, item.value);
		}
	}
```

### d005
```
def test_cache_repeated_event() -> None:
    """Verify the cache detects (and rejects) repeated events."""
    cache = JobEvents()

    event = FakeK8sPodGenerator.new(
        account="tool1", phase="Running", job_emails=JobEmailsConfig.ALL
    )
    cache.add_event(event)
    assert len(cache.cache) == 1

    for userjobs in cache.cache:
        assert len(userjobs.jobs) == 1
        for job in userjobs.jobs:
            assert len(job.events) == 1
```

### d006
```
def test_cache_delete_one() -> None:
    """Verify the event cache is kept in expected state after adding/removing an object."""
    cache = JobEvents()

    cache.add_event(
        FakeK8sPodGenerator.new(phase="Running", job_emails=JobEmailsConfig.ALL)
    )
    assert len(cache.cache) == 1

    cache.flush()
    assert len(cache.cache) == 0
```

### d007
```
private function pruneExcessStashedEntries( BagOStuff $cache, UserIdentity $user, string $newKey ): void {
		$key = $cache->makeKey( 'visualeditor-serialization-recent', $user->getName() );

		$keyList = $cache->get( $key ) ?: [];
		if ( count( $keyList ) >= self::MAX_CACHE_RECENT ) {
			$oldestKey = array_shift( $keyList );
			$cache->delete( $oldestKey );
		}

		$keyList[] = $newKey;
		$cache->set( $key, $keyList, 2 * self::MAX_CACHE_TTL );
	}
```

### d008
```
def cache_delete(self) -> None:
        """
        Deletes the artifact from all of its cache locations.
        """
        for cache in self.caches:
            if cache.exists(self):
                cache.delete(self)
```

### d009
```
function del (cache, key, opts = {}) {
  if (!opts.removeFully)
    return insert(cache, key, null, opts)

  const bucket = bucketPath(cache, key)
  return rimraf(bucket)
}
```

### d010
```
def test_cache_delete_multiple() -> None:
    """Verify the event cache is kept in an expected state after removing multiple objects."""
    cache = JobEvents()

    event1 = FakeK8sPodGenerator.new(
        account="tool1", phase="Running", job_emails=JobEmailsConfig.ALL
    )
    cache.add_event(event1)
    assert len(cache.cache) == 1

    event2 = FakeK8sPodGenerator.new(
        account="tool2", phase="Running", job_emails=JobEmailsConfig.ALL
    )
    cache.add_event(event2)
    assert len(cache.cache) == 2

    event3 = FakeK8sPodGenerator.new(
        account="tool3", phase="Running", job_emails=JobEmailsConfig.ALL
    )
    cache.add_event(event3)
    assert len(cache.cache) == 3

    cache.flush()
    assert len(cache.cache) == 0
```

### d011
```
def copy_cache(
    cache: t.Optional[t.MutableMapping[t.Any, t.Any]],
) -> t.Optional[t.MutableMapping[t.Tuple["weakref.ref[t.Any]", str], "Template"]]:
    """Create an empty copy of the given cache."""
    if cache is None:
        return None

    if type(cache) is dict:  # noqa E721
        return {}

    return LRUCache(cache.capacity)  # type: ignore
```

### d012
```
// removeOldest removes the oldest item from the cache.
func (c *LRU) removeOldest() {
	ent := c.evictList.Back()
	if ent != nil {
		c.removeElement(ent)
	}
}
```

### d013
```
# start, length, rows 
 

def peek(c,pos):
    
    if idxs[pos] >= cache[pos][0] + cache[pos][1]:
        c.execute("SELECT page,hitcount FROM %s ORDER BY 'page' LIMIT %d OFFSET %d  " % (pos,50000,idxs[pos]))
        rows = c.fetchall()
        cache[pos][0] += cache[pos][1]
        cache[pos][1] = len(rows)
        cache[pos][2] = rows
        
        if len(rows) == 0:
            idxs[pos] = -1

    try:
        return cache[pos][2][idxs[pos]-cache[pos][0]]
    except IndexError:
        return ('',0)
```

### d014
```
def remove_key(self, key) -> None:
        """Remove all values for a given key."""
        with suppress(KeyError):
            self.size -= len(self.data[key])
            del self.data[key]
```

### d015
```
def get_cache_stats() -> dict[str, Any]:
    """
    Get cache statistics

    Returns:
        Dictionary with cache stats including size, maxsize, and ttl
    """
    cache = get_cache()
    return {
        "current_size": len(cache),
        "max_size": cache.maxsize,
        "ttl_seconds": cache.ttl,
    }
```

### d016
```
def get_cache() -> TTLCache:
    """
    Get or create the global TTLCache instance

    Returns:
        TTLCache instance configured with environment settings
    """
    global _cache
    if _cache is None:
        ttl = Config.cache.get_ttl_seconds()
        max_size = Config.cache.get_max_size()
        _cache = TTLCache(maxsize=max_size, ttl=ttl)
        logger.info(f"Created TTLCache with max_size={max_size}, ttl={ttl}s")
    return _cache
```

## Output

Return raw JSON only. No preamble, no markdown fences, no commentary outside the
object.

```json
{
  "query_id": "B4",
  "labels": {
    "d001": {"score": 1.0, "rationale": "iterative binary search over sorted array"},
    "d002": {"score": 0.0, "rationale": "pytest case asserting search behaviour, not an implementation"}
  }
}
```

Every `doc_id` presented must appear exactly once in `labels`.
