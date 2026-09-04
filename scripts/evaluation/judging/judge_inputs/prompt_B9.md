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
func processWithPool(jobs []string, workers int,
                     fn func(string) error) []error {
    sem := make(chan struct{}, workers)
    errs := make([]error, len(jobs))
    var wg sync.WaitGroup
    for i, job := range jobs {
        wg.Add(1)
        sem <- struct{}{}
        go func(idx int, j string) {
            defer func() { <-sem; wg.Done() }()
            errs[idx] = fn(j)
        }(i, job)
    }
    wg.Wait()
    return errs
}
```

## Candidates

### d001
```
func newBufferedBackend(sz uint, ev chan Event, errs chan error) (backend, error) {
	w := &fen{
		Events:  ev,
		Errors:  errs,
		dirs:    make(map[string]Op),
		watches: make(map[string]Op),
		done:    make(chan struct{}),
	}

	var err error
	w.port, err = unix.NewEventPort()
	if err != nil {
		return nil, fmt.Errorf("fsnotify.NewWatcher: %w", err)
	}

	go w.readEvents()
	return w, nil
}
```

### d002
```
func startWorkers(beAddr, feAddr string, chBackend chan string, chFrontend chan url.URL, prefixes []string) {
	for i := 0; i < *nBackendWorkers; i++ {
		go backendWorker(beAddr, chBackend, chFrontend, prefixes)
	}

	for i := 0; i < *nFrontendWorkers; i++ {
		go frontendWorker(feAddr, chFrontend)
	}
}
```

### d003
```
// ParallelizeUntil is a framework that allows for parallelizing N
// independent pieces of work until done or the context is canceled.
func ParallelizeUntil(ctx context.Context, workers, pieces int, doWorkPiece DoWorkPieceFunc, opts ...Options) {
	if pieces == 0 {
		return
	}
	o := options{}
	for _, opt := range opts {
		opt(&o)
	}
	chunkSize := o.chunkSize
	if chunkSize < 1 {
		chunkSize = 1
	}

	chunks := ceilDiv(pieces, chunkSize)
	toProcess := make(chan int, chunks)
	for i := 0; i < chunks; i++ {
		toProcess <- i
	}
	close(toProcess)

	var stop <-chan struct{}
	if ctx != nil {
		stop = ctx.Done()
	}
	if chunks < workers {
		workers = chunks
	}
	wg := sync.WaitGroup{}
	wg.Add(workers)
	for i := 0; i < workers; i++ {
		go func() {
			defer utilruntime.HandleCrash()
			defer wg.Done()
			for chunk := range toProcess {
				start := chunk * chunkSize
				end := start + chunkSize
				if end > pieces {
					end = pieces
				}
				for p := start; p < end; p++ {
					select {
					case <-stop:
						return
					default:
						doWorkPiece(p)
					}
				}
			}
		}()
	}
	wg.Wait()
}
```

### d004
```
// NewWatcher creates a new Watcher.
func NewWatcher() (*Watcher, error) {
	ev, errs := make(chan Event), make(chan error)
	b, err := newBackend(ev, errs)
	if err != nil {
		return nil, err
	}
	return &Watcher{b: b, Events: ev, Errors: errs}, nil
}
```

### d005
```
// Errors returns a slice of the `error` instances that have been
// appended to this `MError`.
func (me *MError) Errors() []error {
	me.mux.RLock()
	defer me.mux.RUnlock()

	errs := make([]error, len(me.errors))
	copy(errs, me.errors)

	return errs
}
```

### d006
```
// Gather implements Gatherer.
func (r *Registry) Gather() ([]*dto.MetricFamily, error) {
	var (
		checkedMetricChan   = make(chan Metric, capMetricChan)
		uncheckedMetricChan = make(chan Metric, capMetricChan)
		metricHashes        = map[uint64]struct{}{}
		wg                  sync.WaitGroup
		errs                MultiError          // The collected errors to return in the end.
		registeredDescIDs   map[uint64]struct{} // Only used for pedantic checks
	)

	r.mtx.RLock()
	goroutineBudget := len(r.collectorsByID) + len(r.uncheckedCollectors)
	metricFamiliesByName := make(map[string]*dto.MetricFamily, len(r.dimHashesByName))
	checkedCollectors := make(chan Collector, len(r.collectorsByID))
	uncheckedCollectors := make(chan Collector, len(r.uncheckedCollectors))
	for _, collector := range r.collectorsByID {
		checkedCollectors <- collector
	}
	for _, collector := range r.uncheckedCollectors {
		uncheckedCollectors <- collector
	}
	// In case pedantic checks are enabled, we have to copy the map before
	// giving up the RLock.
	if r.pedanticChecksEnabled {
		registeredDescIDs = make(map[uint64]struct{}, len(r.descIDs))
		for id := range r.descIDs {
			registeredDescIDs[id] = struct{}{}
		}
	}
	r.mtx.RUnlock()

	wg.Add(goroutineBudget)

	collectWorker := func() {
		for {
			select {
			case collector := <-checkedCollectors:
				collector.Collect(checkedMetricChan)
			case collector := <-uncheckedCollectors:
				collector.Collect(uncheckedMetricChan)
			default:
				return
			}
			wg.Done()
		}
	}

	// Start the first worker now to make sure at least one is running.
	go collectWorker()
	goroutineBudget--

	// Close checkedMetricChan and uncheckedMetricChan once all collectors
	// are collected.
	go func() {
		wg.Wait()
		close(checkedMetricChan)
		close(uncheckedMetricChan)
	}()

	// Drain checkedMetricChan and uncheckedMetricChan in case of premature return.
	defer func() {
		if checkedMetricChan != nil {
			for range checkedMetricChan {
			}
		}
		if uncheckedMetricChan != nil {
			for range uncheckedMetricChan {
			}
		}
	}()

	// Copy the channel references so we can nil them out later to remove
	// them from the select statements below.
	cmc := checkedMetricChan
	umc := uncheckedMetricChan

	for {
		select {
		case metric, ok := <-cmc:
			if !ok {
				cmc = nil
				break
			}
			errs.Append(processMetric(
				metric, metricFamiliesByName,
				metricHashes,
				registeredDescIDs,
			))
		case metric, ok := <-umc:
			if !ok {
				umc = nil
				break
			}
			errs.Append(processMetric(
				metric, metricFamiliesByName,
				metricHashes,
				nil,
			))
		default:
			if goroutineBudget <= 0 || len(checkedCollectors)+len(uncheckedCollectors) == 0 {
				// All collectors are already being worked on or
				// we have already as many goroutines started as
				// there are collectors. Do the same as above,
				// just without the default.
				select {
				case metric, ok := <-cmc:
					if !ok {
						cmc = nil
						break
					}
					errs.Append(processMetric(
						metric, metricFamiliesByName,
						metricHashes,
						registeredDescIDs,
					))
				case metric, ok := <-umc:
					if !ok {
						umc = nil
						break
					}
					errs.Append(processMetric(
						metric, metricFamiliesByName,
						metricHashes,
						nil,
					))
				}
				break
			}
			// Start more workers.
			go collectWorker()
			goroutineBudget--
			runtime.Gosched()
		}
		// Once both checkedMetricChan and uncheckdMetricChan are closed
		// and drained, the contraption above will nil out cmc and umc,
		// and then we can leave the collect loop here.
		if cmc == nil && umc == nil {
			break
		}
	}
	return internal.NormalizeMetricFamilies(metricFamiliesByName), errs.MaybeUnwrap()
}
```

### d007
```
func (r *Runner) startWorkers(ctx context.Context) {
	for i := 0; i < r.config.Workers; i++ {
		r.wg.Add(1)
		go worker.Run(
			ctx,
			i,
			r.queryChan,
			&r.wg,
			r.client,
			r.config.Endpoint,
			r.limiter,
			r.statistics,
			r.config.Verbose,
			r.config.Benchmark,
		)
	}
}
```

### d008
```
func newBufferedBackend(sz uint, ev chan Event, errs chan error) (backend, error) {
	kq, closepipe, err := newKqueue()
	if err != nil {
		return nil, err
	}

	w := &kqueue{
		Events:    ev,
		Errors:    errs,
		kq:        kq,
		closepipe: closepipe,
		done:      make(chan struct{}),
		watches:   newWatches(),
	}

	go w.readEvents()
	return w, nil
}
```

### d009
```
func TestWorkers(t *testing.T) {
	input := []string{
		"https://en.wikipedia.org/wiki/Main_Page",
		"https://it.wikipedia.org/wiki/Pagina_principale",
		"http://en.m.wikipedia.org/w/index.php?title=User_talk:127.0.0.1&action=history",
	}

	expected := []string{
		"/w/index.php?title=User_talk:127.0.0.1&action=history",
		"/wiki/Main_Page",
		"/wiki/Pagina_principale",
	}

	testWorkersWrapper(t, nil, input, expected)
}
```

### d010
```
// compress4Xp will compress 4 streams using separate goroutines.
func (s *Scratch) compress4Xp(src []byte) ([]byte, error) {
	if len(src) < 12 {
		return nil, ErrIncompressible
	}
	// Add placeholder for output length
	s.Out = s.Out[:6]

	segmentSize := (len(src) + 3) / 4
	var wg sync.WaitGroup
	var errs [4]error
	wg.Add(4)
	for i := 0; i < 4; i++ {
		toDo := src
		if len(toDo) > segmentSize {
			toDo = toDo[:segmentSize]
		}
		src = src[len(toDo):]

		// Separate goroutine for each block.
		go func(i int) {
			s.tmpOut[i], errs[i] = s.compress1xDo(s.tmpOut[i][:0], toDo)
			wg.Done()
		}(i)
	}
	wg.Wait()
	for i := 0; i < 4; i++ {
		if errs[i] != nil {
			return nil, errs[i]
		}
		o := s.tmpOut[i]
		if len(o) > math.MaxUint16 {
			// We cannot store the size in the jump table
			return nil, ErrIncompressible
		}
		// Write compressed length as little endian before block.
		if i < 3 {
			// Last length is not written.
			s.Out[i*2] = byte(len(o))
			s.Out[i*2+1] = byte(len(o) >> 8)
		}

		// Write output.
		s.Out = append(s.Out, o...)
	}
	return s.Out, nil
}
```

### d011
```
func (c *dynamicClientCert) runWorker() {
	for c.processNextWorkItem() {
	}
}
```

### d012
```
func testWorkersWrapper(t *testing.T, prefixes []string, input []string, expected []string) {
	var feURLs []string
	var beURLs []string
	expectedLen := len(expected)

	backend := httptest.NewServer(http.HandlerFunc(func(rw http.ResponseWriter, req *http.Request) {
		beURLs = append(beURLs, req.URL.String())
		rw.Write([]byte(`OK`))
	}))
	defer backend.Close()
	backendURL, _ := url.Parse(backend.URL)

	frontend := httptest.NewServer(http.HandlerFunc(func(rw http.ResponseWriter, req *http.Request) {
		feURLs = append(feURLs, req.URL.String())
		rw.Write([]byte(`OK`))
	}))
	defer frontend.Close()
	frontendURL, _ := url.Parse(frontend.URL)

	testCh := make(chan string, 10)
	testFrCh := make(chan url.URL, 10)

	for _, url := range input {
		testCh <- url
	}

	startWorkers(backendURL.Host, frontendURL.Host, testCh, testFrCh, prefixes)

	// Wait for all URLs in the channel to be consumed
	for ; len(feURLs) < expectedLen || len(beURLs) < expectedLen; time.Sleep(100 * time.Millisecond) {
	}

	assertEquals(t, len(feURLs), len(beURLs))
	assertEquals(t, len(feURLs), expectedLen)

	assertListEquals(t, feURLs, expected)
	assertListEquals(t, beURLs, expected)
}
```

### d013
```
func TestWorkerPoolWithoutRateLimiter(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{}`))
	}))
	defer server.Close()

	stats := &model.Stats{
		StartTime:         time.Now(),
		MaxLatencySamples: 100,
	}

	client := &http.Client{
		Timeout: 1 * time.Second,
	}

	queryChan := make(chan model.QueryRecord, 10)
	ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
	defer cancel()

	const numWorkers = 5
	var wg sync.WaitGroup

	for i := 0; i < numWorkers; i++ {
		wg.Add(1)
		// nil limiter for unlimited
		go Run(ctx, i, queryChan, &wg, client, server.URL, nil, stats, false, true)
	}

	// Send some queries
	go func() {
		for i := 0; i < 50; i++ {
			select {
			case <-ctx.Done():
				close(queryChan)
				return
			case queryChan <- model.QueryRecord{
				Query: "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 1",
				Line:  i,
			}:
			}
		}
		close(queryChan)
	}()

	wg.Wait()

	total := stats.Success.Load() + stats.Failed.Load()
	if total == 0 {
		t.Error("Expected some processed queries, got 0")
	}
}
```

### d014
```
func newBufferedBackend(sz uint, ev chan Event, errs chan error) (backend, error) {
	// Need to set nonblocking mode for SetDeadline to work, otherwise blocking
	// I/O operations won't terminate on close.
	fd, errno := unix.InotifyInit1(unix.IN_CLOEXEC | unix.IN_NONBLOCK)
	if fd == -1 {
		return nil, errno
	}

	w := &inotify{
		Events:      ev,
		Errors:      errs,
		fd:          fd,
		inotifyFile: os.NewFile(uintptr(fd), ""),
		watches:     newWatches(),
		done:        make(chan struct{}),
		doneResp:    make(chan struct{}),
	}

	go w.readEvents()
	return w, nil
}
```

### d015
```
// PopProcessFunc is passed to Pop() method of Queue interface.
// It is supposed to process the accumulator popped from the queue.
type PopProcessFunc func(obj interface{}, isInInitialList bool) error
```

### d016
```
func newBufferedBackend(sz uint, ev chan Event, errs chan error) (backend, error) {
	port, err := windows.CreateIoCompletionPort(windows.InvalidHandle, 0, 0, 0)
	if err != nil {
		return nil, os.NewSyscallError("CreateIoCompletionPort", err)
	}
	w := &readDirChangesW{
		Events:  ev,
		Errors:  errs,
		port:    port,
		watches: make(watchMap),
		input:   make(chan *input, 1),
		quit:    make(chan chan<- error, 1),
	}
	go w.readEvents()
	return w, nil
}
```

### d017
```
// AggregateGoroutines runs the provided functions in parallel, stuffing all
// non-nil errors into the returned Aggregate.
// Returns nil if all the functions complete successfully.
func AggregateGoroutines(funcs ...func() error) Aggregate {
	errChan := make(chan error, len(funcs))
	for _, f := range funcs {
		go func(f func() error) { errChan <- f() }(f)
	}
	errs := make([]error, 0)
	for i := 0; i < cap(errChan); i++ {
		if err := <-errChan; err != nil {
			errs = append(errs, err)
		}
	}
	return NewAggregate(errs)
}
```

### d018
```
func TestWorkerPoolRaceConditions(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		time.Sleep(1 * time.Millisecond)
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"results": []}`))
	}))
	defer server.Close()

	stats := &model.Stats{
		StartTime:         time.Now(),
		MaxLatencySamples: 1000,
	}

	client := &http.Client{
		Timeout: 5 * time.Second,
	}

	limiter := rate.NewLimiter(rate.Limit(1000), 10)

	queryChan := make(chan model.QueryRecord, 20)

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	const numWorkers = 10
	var wg sync.WaitGroup

	for i := 0; i < numWorkers; i++ {
		wg.Add(1)
		go Run(ctx, i, queryChan, &wg, client, server.URL, limiter, stats, false, true)
	}

	go func() {
		for i := 0; i < 100; i++ {
			select {
			case <-ctx.Done():
				close(queryChan)
				return
			case queryChan <- model.QueryRecord{
				Query: "SELECT * WHERE { ?s ?p ?o } LIMIT 1",
				Line:  i + 1,
			}:
			}
		}
		close(queryChan)
	}()

	wg.Wait()

	if stats.Success.Load() == 0 {
		t.Error("Expected some successful queries, got 0")
	}

	stats.LatencyMu.Lock()
	latencyCount := len(stats.Latencies)
	stats.LatencyMu.Unlock()

	if latencyCount == 0 {
		t.Error("Expected some latency samples, got 0")
	}
}
```

### d019
```
// serverWorker blocks on a *transport.ServerStream channel forever and waits
// for data to be fed by serveStreams. This allows multiple requests to be
// processed by the same goroutine, removing the need for expensive stack
// re-allocations (see the runtime.morestack problem [1]).
//
// [1] https://github.com/golang/go/issues/18138
func (s *Server) serverWorker() {
	for completed := 0; completed < serverWorkerResetThreshold; completed++ {
		f, ok := <-s.serverWorkerChannel
		if !ok {
			return
		}
		f()
	}
	go s.serverWorker()
}
```

## Output

Return raw JSON only. No preamble, no markdown fences, no commentary outside the
object.

```json
{
  "query_id": "B9",
  "labels": {
    "d001": {"score": 1.0, "rationale": "iterative binary search over sorted array"},
    "d002": {"score": 0.0, "rationale": "pytest case asserting search behaviour, not an implementation"}
  }
}
```

Every `doc_id` presented must appear exactly once in `labels`.
