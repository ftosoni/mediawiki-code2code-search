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
func fanOut(inputs []string,
            process func(string) (string, error)) ([]string, error) {
    results := make([]string, len(inputs))
    var wg sync.WaitGroup
    errCh := make(chan error, len(inputs))
    for i, inp := range inputs {
        wg.Add(1)
        go func(idx int, s string) {
            defer wg.Done()
            r, err := process(s)
            if err != nil { errCh <- err; return }
            results[idx] = r
        }(i, inp)
    }
    wg.Wait()
    close(errCh)
    if err := <-errCh; err != nil { return nil, err }
    return results, nil
}
```

## Candidates

### d001
```
// updateClientConnState is invoked by grpc to push a ClientConnState update to
// the underlying balancer.  This is always executed from the serializer, so
// it is safe to call into the balancer here.
func (ccb *ccBalancerWrapper) updateClientConnState(ccs *balancer.ClientConnState) error {
	errCh := make(chan error)
	uccs := func(ctx context.Context) {
		defer close(errCh)
		if ctx.Err() != nil || ccb.balancer == nil {
			return
		}
		name := gracefulswitch.ChildName(ccs.BalancerConfig)
		if ccb.curBalancerName != name {
			ccb.curBalancerName = name
			channelz.Infof(logger, ccb.cc.channelz, "Channel switches to new LB policy %q", name)
		}
		err := ccb.balancer.UpdateClientConnState(*ccs)
		if logger.V(2) && err != nil {
			logger.Infof("error from balancer.UpdateClientConnState: %v", err)
		}
		errCh <- err
	}
	onFailure := func() { close(errCh) }

	// UpdateClientConnState can race with Close, and when the latter wins, the
	// serializer is closed, and the attempt to schedule the callback will fail.
	// It is acceptable to ignore this failure. But since we want to handle the
	// state update in a blocking fashion (when we successfully schedule the
	// callback), we have to use the ScheduleOr method and not the MaybeSchedule
	// method on the serializer.
	ccb.serializer.ScheduleOr(uccs, onFailure)
	return <-errCh
}
```

### d002
```
// Process - Sole handler for reading from the input channel
func (a512srv *Avx512Server) Process() {
	for {
		select {
		case block := <-a512srv.blocksCh:
			if block.reset {
				a512srv.reset(block.uid)
				continue
			}
			index := block.uid & 0xf
			// fmt.Println("Adding message:", block.uid, index)

			if a512srv.lanes[index].block != nil { // If slot is already filled, process all inputs
				//fmt.Println("Invoking Blocks()")
				a512srv.blocks()
			}
			a512srv.totalIn++
			a512srv.lanes[index] = Avx512LaneInfo{uid: block.uid, block: block.msg}
			if block.final {
				a512srv.lanes[index].outputCh = block.sumCh
			}
			if a512srv.totalIn == len(a512srv.lanes) {
				// fmt.Println("Invoking Blocks() while FULL: ")
				a512srv.blocks()
			}

			// TODO: test with larger timeout
		case <-time.After(1 * time.Microsecond):
			for _, lane := range a512srv.lanes {
				if lane.block != nil { // check if there is any input to process
					// fmt.Println("Invoking Blocks() on TIMEOUT: ")
					a512srv.blocks()
					break // we are done
				}
			}
		}
	}
}
```

### d003
```
func (r *binaryDecoder) readAttributes(n int) (map[string]string, error) {
	if n == 0 {
		return nil, nil
	}

	ret := make(map[string]string)
	for i := 0; i < n; i++ {
		idx, err := r.readInt8(false)
		if err != nil {
			return nil, err
		}

		index, err := r.readString(idx)
		if err != nil {
			return nil, err
		}

		idx, err = r.readInt8(false)
		if err != nil {
			return nil, err
		}

		ret[index], err = r.readString(idx)
		if err != nil {
			return nil, err
		}
	}

	return ret, nil
}
```

### d004
```
func main() {
	s := spin.New()

	var wg sync.WaitGroup
	doneChan := make(chan struct{})
	for _, cfgPath := range getConfigPaths() {
		if *fancy {
			wg.Add(1)
			go func() {
				for {
					select {
					case <-doneChan:
						doneChan = make(chan struct{})
						fmt.Printf("\r  \033[36mprocessing %s\033[m done.\n", cfgPath)
						wg.Done()
						return
					default:
						fmt.Printf("\r  \033[36mprocessing %s\033[m %s", cfgPath, s.Next())
						time.Sleep(100 * time.Millisecond)
					}
				}
			}()
		}

		var t0 time.Time
		if *debug {
			t0 = time.Now()
		}
		process, err := NewProcess(cfgPath, *outputPath)
		if err != nil {
			log.Fatalln("[ERR]", err)
		}
		process.Generate(*noCGO)
		if err := process.Flush(*noCGO); err != nil {
			log.Fatalln("[ERR]", err)
		}
		if *debug {
			fmt.Printf("done in %v\n", time.Now().Sub(t0))
		}
		if *fancy {
			close(doneChan)
			wg.Wait()
		}
	}
}
```

### d005
```
// process - Sole handler for reading from the input channel.
func (s *md5Server) process(newClients chan newClient) {
	// To fill up as many lanes as possible:
	//
	// 1. Wait for a cycle id.
	// 2. If not already in a lane, add, otherwise leave on channel
	// 3. Start timer
	// 4. Check if lanes is full, if so, goto 10 (process).
	// 5. If timeout, goto 10.
	// 6. Wait for new id (goto 2)  or timeout (goto 10).
	// 10. Process.
	// 11. Check all input if there is already input, if so add to lanes.
	// 12. Goto 1

	// lanes contains the lanes.
	var lanes lanesInfo
	// lanesFilled contains the number of filled lanes for current cycle.
	var lanesFilled int
	// clients contains active clients
	var clients = make(map[uint64]chan blockInput, Lanes)

	addToLane := func(uid uint64) {
		cl, ok := clients[uid]
		if !ok {
			// Unknown client. Maybe it was already removed.
			return
		}
		// Check if we already have it.
		for _, lane := range lanes[:lanesFilled] {
			if lane.uid == uid {
				return
			}
		}
		// Continue until we get a block or there is nothing on channel
		for {
			select {
			case block, ok := <-cl:
				if !ok {
					// Client disconnected
					delete(clients, block.uid)
					return
				}
				if block.uid != uid {
					panic(fmt.Errorf("uid mismatch, %d (block) != %d (client)", block.uid, uid))
				}
				// If reset message, reset and we're done
				if block.reset {
					delete(s.digests, uid)
					continue
				}

				// If requesting sum, we will need to maintain state.
				if block.sumCh != nil {
					var dig digest
					d, ok := s.digests[uid]
					if ok {
						dig.s[0] = binary.LittleEndian.Uint32(d[0:4])
						dig.s[1] = binary.LittleEndian.Uint32(d[4:8])
						dig.s[2] = binary.LittleEndian.Uint32(d[8:12])
						dig.s[3] = binary.LittleEndian.Uint32(d[12:16])
					} else {
						dig.s[0], dig.s[1], dig.s[2], dig.s[3] = init0, init1, init2, init3
					}

					sum := sumResult{}
					// Add end block to current digest.
					blockScalar(&dig.s, block.msg)

					binary.LittleEndian.PutUint32(sum.digest[0:], dig.s[0])
					binary.LittleEndian.PutUint32(sum.digest[4:], dig.s[1])
					binary.LittleEndian.PutUint32(sum.digest[8:], dig.s[2])
					binary.LittleEndian.PutUint32(sum.digest[12:], dig.s[3])
					block.sumCh <- sum
					if block.msg != nil {
						s.buffers <- block.msg
					}
					continue
				}
				if len(block.msg) == 0 {
					continue
				}
				lanes[lanesFilled] = block
				lanesFilled++
				return
			default:
				return
			}
		}
	}
	addNewClient := func(cl newClient) {
		if _, ok := clients[cl.uid]; ok {
			panic("internal error: duplicate client registration")
		}
		clients[cl.uid] = cl.input
	}

	allLanesFilled := func() bool {
		return lanesFilled == Lanes || lanesFilled >= len(clients)
	}

	for {
		// Step 1.
		for lanesFilled == 0 {
			select {
			case cl, ok := <-newClients:
				if !ok {
					return
				}
				addNewClient(cl)
				// Check if it already sent a payload.
				addToLane(cl.uid)
				continue
			case uid := <-s.cycle:
				addToLane(uid)
			}
		}

	fillLanes:
		for !allLanesFilled() {
			select {
			case cl, ok := <-newClients:
				if !ok {
					return
				}
				addNewClient(cl)

			case uid := <-s.cycle:
				addToLane(uid)
			default:
				// Nothing more queued...
				break fillLanes
			}
		}

		// If we did not fill all lanes, check if there is more waiting
		if !allLanesFilled() {
			runtime.Gosched()
			for uid := range clients {
				addToLane(uid)
				if allLanesFilled() {
					break
				}
			}
		}
		if false {
			if !allLanesFilled() {
				fmt.Println("Not all lanes filled", lanesFilled, "of", len(clients))
				//pprof.Lookup("goroutine").WriteTo(os.Stdout, 1)
			} else if true {
				fmt.Println("all lanes filled")
			}
		}
		// Process the lanes we could collect
		s.blocks(lanes[:lanesFilled])

		// Clear lanes...
		lanesFilled = 0
		// Add all current queued
		for uid := range clients {
			addToLane(uid)
			if allLanesFilled() {
				break
			}
		}
	}
}
```

### d006
```
// Map applies f to each element of input, returning the mapped result.
//
// Map always uses at most runtime.GOMAXPROCS goroutines. For a configurable
// goroutine limit, use a custom Mapper.
func Map[T, R any](input []T, f func(*T) R) []R {
	return Mapper[T, R]{}.Map(input, f)
}
```

### d007
```
func RunServer(ctx context.Context, logger *slog.Logger, srv *grpc.Server, network, addr string) (chan struct{}, error) {
	ch := make(chan struct{})
	if err := ctx.Err(); err != nil {
		return ch, err
	}

	wg := sync.WaitGroup{}
	listener, err := net.Listen(network, addr)
	if err != nil {
		return ch, fmt.Errorf("net.Listen() failed: %w", err)
	}

	go func() {
		logger.Info("starting gRPC server")
		wg.Add(1)
		defer wg.Done()
		defer listener.Close()

		if err := srv.Serve(listener); err != nil {
			logger.Error("grpc.Serve() failed",
				slog.String("bind_address", addr),
				slog.Any("error", err),
			)
		}
	}()

	// wait till ctx is done
	go func() {
		<-ctx.Done()
		logger.Info("Gracefully stoppping gRPC server (30 seconds timeout)")
		stopped := make(chan struct{})
		// https://github.com/grpc/grpc-go/issues/2448
		go func() {
			srv.GracefulStop()
			close(stopped)
		}()
		select {
		case <-time.After(30 * time.Second):
			srv.Stop()
		case <-stopped:
			srv.Stop()
		}
		wg.Wait()
		close(ch)
	}()

	return ch, nil
}
```

### d008
```
// waitForProcessing waits for the worker goroutines to finish processing items
// and call Done on them.
func (q *Type) waitForProcessing() {
	q.cond.L.Lock()
	defer q.cond.L.Unlock()
	// Ensure that we do not wait on a queue which is already empty, as that
	// could result in waiting for Done to be called on items in an empty queue
	// which has already been shut down, which will result in waiting
	// indefinitely.
	if q.processing.len() == 0 {
		return
	}
	q.cond.Wait()
}
```

### d009
```
// distribute sends event to all watchers. Blocking.
func (m *Broadcaster) distribute(event Event) {
	if m.fullChannelBehavior == DropIfChannelFull {
		for _, w := range m.watchers {
			select {
			case w.result <- event:
			case <-w.stopped:
			default: // Don't block if the event can't be queued.
			}
		}
	} else {
		for _, w := range m.watchers {
			select {
			case w.result <- event:
			case <-w.stopped:
			}
		}
	}
}
```

### d010
```
// reader verifies the server preface and reads all subsequent data from
// network connection.  If the server preface is not read successfully, an
// error is pushed to errCh; otherwise errCh is closed with no error.
func (t *http2Client) reader(errCh chan<- error) {
	var errClose error
	defer func() {
		close(t.readerDone)
		if errClose != nil {
			t.Close(errClose)
		}
	}()

	if err := t.readServerPreface(); err != nil {
		errCh <- err
		return
	}
	close(errCh)
	if t.keepaliveEnabled {
		atomic.StoreInt64(&t.lastRead, time.Now().UnixNano())
	}

	// loop to keep reading incoming messages on this transport.
	for {
		t.controlBuf.throttle()
		frame, err := t.framer.fr.ReadFrame()
		if t.keepaliveEnabled {
			atomic.StoreInt64(&t.lastRead, time.Now().UnixNano())
		}
		if err != nil {
			// Abort an active stream if the http2.Framer returns a
			// http2.StreamError. This can happen only if the server's response
			// is malformed http2.
			if se, ok := err.(http2.StreamError); ok {
				t.mu.Lock()
				s := t.activeStreams[se.StreamID]
				t.mu.Unlock()
				if s != nil {
					// use error detail to provide better err message
					code := http2ErrConvTab[se.Code]
					errorDetail := t.framer.fr.ErrorDetail()
					var msg string
					if errorDetail != nil {
						msg = errorDetail.Error()
					} else {
						msg = "received invalid frame"
					}
					t.closeStream(s, status.Error(code, msg), true, http2.ErrCodeProtocol, status.New(code, msg), nil, false)
				}
				continue
			}
			// Transport error.
			errClose = connectionErrorf(true, err, "error reading from server: %v", err)
			return
		}
		switch frame := frame.(type) {
		case *http2.MetaHeadersFrame:
			t.operateHeaders(frame)
		case *http2.DataFrame:
			t.handleData(frame)
		case *http2.RSTStreamFrame:
			t.handleRSTStream(frame)
		case *http2.SettingsFrame:
			t.handleSettings(frame, false)
		case *http2.PingFrame:
			t.handlePing(frame)
		case *http2.GoAwayFrame:
			errClose = t.handleGoAway(frame)
		case *http2.WindowUpdateFrame:
			t.handleWindowUpdate(frame)
		default:
			if logger.V(logLevel) {
				logger.Errorf("transport: http2Client.reader got unhandled frame type %v.", frame)
			}
		}
	}
}
```

### d011
```
func proxyRaw(t *ProxyTarget, c echo.Context) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		in, _, err := c.Response().Hijack()
		if err != nil {
			c.Set("_error", fmt.Errorf("proxy raw, hijack error=%w, url=%s", err, t.URL))
			return
		}
		defer in.Close()

		out, err := net.Dial("tcp", t.URL.Host)
		if err != nil {
			c.Set("_error", echo.NewHTTPError(http.StatusBadGateway, fmt.Sprintf("proxy raw, dial error=%v, url=%s", err, t.URL)))
			return
		}
		defer out.Close()

		// Write header
		err = r.Write(out)
		if err != nil {
			c.Set("_error", echo.NewHTTPError(http.StatusBadGateway, fmt.Sprintf("proxy raw, request header copy error=%v, url=%s", err, t.URL)))
			return
		}

		errCh := make(chan error, 2)
		cp := func(dst io.Writer, src io.Reader) {
			_, err = io.Copy(dst, src)
			errCh <- err
		}

		go cp(out, in)
		go cp(in, out)
		err = <-errCh
		if err != nil && err != io.EOF {
			c.Set("_error", fmt.Errorf("proxy raw, copy body error=%w, url=%s", err, t.URL))
		}
	})
}
```

### d012
```
func (s *Server) readLogs(ctx context.Context) {
	processed := prometheus.Labels{"status": "processed"}
	discarded := prometheus.Labels{"status": "discarded"}
	for {
		// By keeping this in an infinite loop fifo-log-demux is able to re-open
		// the logFifoPath after an EOF that's usually received cause the other side of
		// the pipe has been closed
		f, err := os.Open(s.logFifoPath)
		if err != nil {
			log.Println(err)
			return
		}
		defer f.Close()

		scanner := bufio.NewScanner(f)

		for scanner.Scan() {
			// Read data as fast as possible, discarding messages if needed
			data := scanner.Bytes()
			// We need a clone of the slice to be injected on the publish channel
			// or we would have concurrency issues between the goroutines sending
			// data to the clients and this one
			// slices is only available on go >=1.21
			//publishData := slices.Clone(data)
			publishData := append(data[:0:0], data...)
			select {
			case <-ctx.Done():
				return
			default:
			}

			if ok := s.broker.Publish(publishData); ok {
				inputMessages.With(processed).Inc()
			} else {
				inputMessages.With(discarded).Inc()
			}
		}
	}
}
```

### d013
```
// goListDriver uses the go list command to interpret the patterns and produce
// the build system package structure.
// See driver for more details.
//
// overlay is the JSON file that encodes the cfg.Overlay
// mapping, used by 'go list -overlay=...'
func goListDriver(cfg *Config, runner *gocommand.Runner, overlay string, patterns []string) (_ *DriverResponse, err error) {
	// Make sure that any asynchronous go commands are killed when we return.
	parentCtx := cfg.Context
	if parentCtx == nil {
		parentCtx = context.Background()
	}
	ctx, cancel := context.WithCancel(parentCtx)
	defer cancel()

	response := newDeduper()

	state := &golistState{
		cfg:        cfg,
		ctx:        ctx,
		vendorDirs: map[string]bool{},
		overlay:    overlay,
		runner:     runner,
	}

	// Fill in response.Sizes asynchronously if necessary.
	if cfg.Mode&NeedTypesSizes != 0 || cfg.Mode&(NeedTypes|NeedTypesInfo) != 0 {
		errCh := make(chan error)
		go func() {
			compiler, arch, err := getSizesForArgs(ctx, state.cfgInvocation(), runner)
			response.dr.Compiler = compiler
			response.dr.Arch = arch
			errCh <- err
		}()
		defer func() {
			if sizesErr := <-errCh; sizesErr != nil {
				err = sizesErr
			}
		}()
	}

	// Determine files requested in contains patterns
	var containFiles []string
	restPatterns := make([]string, 0, len(patterns))
	// Extract file= and other [querytype]= patterns. Report an error if querytype
	// doesn't exist.
extractQueries:
	for _, pattern := range patterns {
		eqidx := strings.Index(pattern, "=")
		if eqidx < 0 {
			restPatterns = append(restPatterns, pattern)
		} else {
			query, value := pattern[:eqidx], pattern[eqidx+len("="):]
			switch query {
			case "file":
				containFiles = append(containFiles, value)
			case "pattern":
				restPatterns = append(restPatterns, value)
			case "": // not a reserved query
				restPatterns = append(restPatterns, pattern)
			default:
				for _, rune := range query {
					if rune < 'a' || rune > 'z' { // not a reserved query
						restPatterns = append(restPatterns, pattern)
						continue extractQueries
					}
				}
				// Reject all other patterns containing "="
				return nil, fmt.Errorf("invalid query type %q in query pattern %q", query, pattern)
			}
		}
	}

	// See if we have any patterns to pass through to go list. Zero initial
	// patterns also requires a go list call, since it's the equivalent of
	// ".".
	if len(restPatterns) > 0 || len(patterns) == 0 {
		dr, err := state.createDriverResponse(restPatterns...)
		if err != nil {
			return nil, err
		}
		response.addAll(dr)
	}

	if len(containFiles) != 0 {
		if err := state.runContainsQueries(response, containFiles); err != nil {
			return nil, err
		}
	}

	// (We may yet return an error due to defer.)
	return response.dr, nil
}
```

### d014
```
func (c *processCollector) processCollect(ch chan<- Metric) {
	// noop on this platform
	return
}
```

### d015
```
// ForEachIdx is the same as ForEach except it also provides the
// index of the element to the callback.
func (iter Iterator[T]) ForEachIdx(input []T, f func(int, *T)) {
	if iter.MaxGoroutines == 0 {
		// iter is a value receiver and is hence safe to mutate
		iter.MaxGoroutines = defaultMaxGoroutines()
	}

	numInput := len(input)
	if iter.MaxGoroutines > numInput {
		// No more concurrent tasks than the number of input items.
		iter.MaxGoroutines = numInput
	}

	var idx atomic.Int64
	// Create the task outside the loop to avoid extra closure allocations.
	task := func() {
		i := int(idx.Add(1) - 1)
		for ; i < numInput; i = int(idx.Add(1) - 1) {
			f(i, &input[i])
		}
	}

	var wg conc.WaitGroup
	for i := 0; i < iter.MaxGoroutines; i++ {
		wg.Go(task)
	}
	wg.Wait()
}
```

### d016
```
func RunPrometheusServer(ctx context.Context, logger *slog.Logger, addrs []string, cs ...prometheus.Collector) (chan struct{}, error) {
	ch := make(chan struct{})
	if err := ctx.Err(); err != nil {
		close(ch)
		return ch, err
	}

	reg := prometheus.NewPedanticRegistry()

	for _, collector := range cs {
		if err := reg.Register(collector); err != nil {
			close(ch)
			return ch, fmt.Errorf("prometheus.Register() failed: %w", err)
		}
	}

	if err := reg.Register(prometheus.NewProcessCollector(prometheus.ProcessCollectorOpts{})); err != nil {
		close(ch)
		return ch, fmt.Errorf("prometheus.Register() failed to register ProcessCollector: %w", err)
	}
	if err := reg.Register(prometheus.NewGoCollector()); err != nil {
		close(ch)
		return ch, fmt.Errorf("prometheus.Register() failed to register GoCollector: %w", err)
	}

	mux := http.NewServeMux()
	mux.Handle("/metrics", promhttp.HandlerFor(reg, promhttp.HandlerOpts{}))

	var wg sync.WaitGroup
	wg.Add(len(addrs))

	servers := make([]*http.Server, len(addrs), len(addrs))

	for index, addr := range addrs {
		servers[index] = &http.Server{
			Addr:    addr,
			Handler: mux,
		}

		go func() {
			defer wg.Done()
			if err := servers[index].ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
				logger.Error("ListenAndServe() failed",
					slog.String("bind_address", addr),
					slog.Any("error", err))
			}
		}()
	}

	go func() {
		defer close(ch)
		// wait till context is done
		<-ctx.Done()
		logger.Info("Gracefully stopping prometheus server (30 seconds timeout)")
		shutdownCtx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
		defer cancel()
		for _, server := range servers {
			server.Shutdown(shutdownCtx)
		}
		// we need a goroutine here to provide a timeout on wg.Wait()
		stopped := make(chan struct{})
		go func() {
			// wait till http servers are done
			wg.Wait()
			close(stopped)
		}()
		select {
		case <-shutdownCtx.Done():
		case <-stopped:
		}
	}()

	return ch, nil
}
```

### d017
```
func (e *Encoder) EncodeMapSorted(m map[string]interface{}) error {
	if m == nil {
		return e.EncodeNil()
	}
	if err := e.EncodeMapLen(len(m)); err != nil {
		return err
	}

	keys := make([]string, 0, len(m))

	for k := range m {
		keys = append(keys, k)
	}

	sort.Strings(keys)

	for _, k := range keys {
		if err := e.EncodeString(k); err != nil {
			return err
		}
		if err := e.Encode(m[k]); err != nil {
			return err
		}
	}

	return nil
}
```

### d018
```
func (c *processCollector) processCollect(ch chan<- Metric) {
	c.errorCollectFn(ch)
}
```

### d019
```
// start builds the name resolver using the resolver.Builder in cc and returns
// any error encountered.  It must always be the first operation performed on
// any newly created ccResolverWrapper, except that close may be called instead.
func (ccr *ccResolverWrapper) start() error {
	errCh := make(chan error)
	ccr.serializer.TrySchedule(func(ctx context.Context) {
		if ctx.Err() != nil {
			return
		}
		opts := resolver.BuildOptions{
			DisableServiceConfig: ccr.cc.dopts.disableServiceConfig,
			DialCreds:            ccr.cc.dopts.copts.TransportCredentials,
			CredsBundle:          ccr.cc.dopts.copts.CredsBundle,
			Dialer:               ccr.cc.dopts.copts.Dialer,
			Authority:            ccr.cc.authority,
		}
		var err error
		ccr.resolver, err = ccr.cc.resolverBuilder.Build(ccr.cc.parsedTarget, ccr, opts)
		errCh <- err
	})
	return <-errCh
}
```

## Output

Return raw JSON only. No preamble, no markdown fences, no commentary outside the
object.

```json
{
  "query_id": "C3",
  "labels": {
    "d001": {"score": 1.0, "rationale": "iterative binary search over sorted array"},
    "d002": {"score": 0.0, "rationale": "pytest case asserting search behaviour, not an implementation"}
  }
}
```

Every `doc_id` presented must appear exactly once in `labels`.
