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
func doWithRetry(client *http.Client, req *http.Request,
                 maxRetries int) (*http.Response, error) {
    var lastErr error
    for i := 0; i < maxRetries; i++ {
        resp, err := client.Do(req)
        if err == nil && resp.StatusCode < 500 {
            return resp, nil
        }
        lastErr = err
        time.Sleep(time.Duration(i+1) * time.Second)
    }
    return nil, lastErr
}
```

## Candidates

### d001
```
// Stream formats and executes the request, and offers streaming of the response.
// Returns io.ReadCloser which could be used for streaming of the response, or an error
// Any non-2xx http status code causes an error.  If we get a non-2xx code, we try to convert the body into an APIStatus object.
// If we can, we return that as an error.  Otherwise, we create an error that lists the http status and the content of the response.
func (r *Request) Stream(ctx context.Context) (io.ReadCloser, error) {
	if r.err != nil {
		return nil, r.err
	}

	if err := r.tryThrottle(ctx); err != nil {
		return nil, err
	}

	client := r.c.Client
	if client == nil {
		client = http.DefaultClient
	}

	retry := r.retryFn(r.maxRetries)
	url := r.URL().String()
	for {
		if err := retry.Before(ctx, r); err != nil {
			return nil, err
		}

		req, err := r.newHTTPRequest(ctx)
		if err != nil {
			return nil, err
		}
		resp, err := client.Do(req)
		retry.After(ctx, r, resp, err)
		if err != nil {
			// we only retry on an HTTP response with 'Retry-After' header
			return nil, err
		}

		switch {
		case (resp.StatusCode >= 200) && (resp.StatusCode < 300):
			handleWarnings(resp.Header, r.warningHandler)
			return resp.Body, nil

		default:
			done, transformErr := func() (bool, error) {
				defer resp.Body.Close()

				if retry.IsNextRetry(ctx, r, req, resp, err, neverRetryError) {
					return false, nil
				}
				result := r.transformResponse(resp, req)
				if err := result.Error(); err != nil {
					return true, err
				}
				return true, fmt.Errorf("%d while accessing %v: %s", result.statusCode, url, string(result.body))
			}()
			if done {
				return nil, transformErr
			}
		}
	}
}
```

### d002
```
func (cs *clientStream) withRetry(op func(a *csAttempt) error, onSuccess func()) error {
	cs.mu.Lock()
	for {
		if cs.committed {
			cs.mu.Unlock()
			// toRPCErr is used in case the error from the attempt comes from
			// NewClientStream, which intentionally doesn't return a status
			// error to allow for further inspection; all other errors should
			// already be status errors.
			return toRPCErr(op(cs.attempt))
		}
		if len(cs.replayBuffer) == 0 {
			// For the first op, which controls creation of the stream and
			// assigns cs.attempt, we need to create a new attempt inline
			// before executing the first op.  On subsequent ops, the attempt
			// is created immediately before replaying the ops.
			var err error
			if cs.attempt, err = cs.newAttemptLocked(false /* isTransparent */); err != nil {
				cs.mu.Unlock()
				cs.finish(err)
				return err
			}
		}
		a := cs.attempt
		cs.mu.Unlock()
		err := op(a)
		cs.mu.Lock()
		if a != cs.attempt {
			// We started another attempt already.
			continue
		}
		if err == io.EOF {
			<-a.s.Done()
		}
		if err == nil || (err == io.EOF && a.s.Status().Code() == codes.OK) {
			onSuccess()
			cs.mu.Unlock()
			return err
		}
		if err := cs.retryLocked(a, err); err != nil {
			cs.mu.Unlock()
			return err
		}
	}
}
```

### d003
```
// doNoRetry issues a request req, replacing its context (if any) with ctx.
func (c *Client) doNoRetry(ctx context.Context, req *http.Request) (*http.Response, error) {
	req.Header.Set("User-Agent", c.userAgent())
	res, err := c.httpClient().Do(req.WithContext(ctx))
	if err != nil {
		select {
		case <-ctx.Done():
			// Prefer the unadorned context error.
			// (The acme package had tests assuming this, previously from ctxhttp's
			// behavior, predating net/http supporting contexts natively)
			// TODO(bradfitz): reconsider this in the future. But for now this
			// requires no test updates.
			return nil, ctx.Err()
		default:
			return nil, err
		}
	}
	return res, nil
}
```

### d004
```
// MaxRetries makes the request use the given integer as a ceiling of retrying upon receiving
// "Retry-After" headers and 429 status-code in the response. The default is 10 unless this
// function is specifically called with a different value.
// A zero maxRetries prevent it from doing retires and return an error immediately.
func (r *Request) MaxRetries(maxRetries int) *Request {
	if maxRetries < 0 {
		maxRetries = 0
	}
	r.maxRetries = maxRetries
	return r
}
```

### d005
```
func loadHTTPBytes(timeout time.Duration) func(path string) ([]byte, error) {
	return func(path string) ([]byte, error) {
		client := &http.Client{Timeout: timeout}
		req, err := http.NewRequest(http.MethodGet, path, nil) //nolint:noctx
		if err != nil {
			return nil, err
		}

		if LoadHTTPBasicAuthUsername != "" && LoadHTTPBasicAuthPassword != "" {
			req.SetBasicAuth(LoadHTTPBasicAuthUsername, LoadHTTPBasicAuthPassword)
		}

		for key, val := range LoadHTTPCustomHeaders {
			req.Header.Set(key, val)
		}

		resp, err := client.Do(req)
		defer func() {
			if resp != nil {
				if e := resp.Body.Close(); e != nil {
					log.Println(e)
				}
			}
		}()
		if err != nil {
			return nil, err
		}

		if resp.StatusCode != http.StatusOK {
			return nil, fmt.Errorf("could not access document at %q [%s] ", path, resp.Status)
		}

		return io.ReadAll(resp.Body)
	}
}
```

### d006
```
func checkStatusCode(resp *http.Response, d Debug) error {
	if resp.StatusCode == http.StatusTooManyRequests {
		retry, err := strconv.ParseInt(resp.Header.Get("Retry-After"), 10, 64)
		if err != nil {
			return err
		}
		return &RateLimitedError{time.Duration(retry) * time.Second}
	}

	// Slack seems to send an HTML body along with 5xx error codes. Don't parse it.
	if resp.StatusCode != http.StatusOK {
		logResponse(resp, d)
		return StatusCodeError{Code: resp.StatusCode, Status: resp.Status}
	}

	return nil
}
```

### d007
```
// Execute sends a SPARQL query to the endpoint and returns the latency and any error
func Execute(ctx context.Context, client *http.Client, endpoint string, query model.QueryRecord) (time.Duration, error) {
	decodedQuery, err := url.QueryUnescape(query.Query)
	if err != nil {
		decodedQuery = query.Query
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, endpoint, strings.NewReader(decodedQuery))
	if err != nil {
		return 0, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", contentTypeSparqlQuery)
	req.Header.Set("Accept", acceptJSON)
	req.Header.Set("User-Agent", userAgent)

	start := time.Now()
	resp, err := client.Do(req)
	latency := time.Since(start)

	if err != nil {
		return latency, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		io.Copy(io.Discard, resp.Body)
		return latency, fmt.Errorf("HTTP %d: %s", resp.StatusCode, resp.Status)
	}

	return latency, nil
}
```

### d008
```
func retryAfterResponse() *http.Response {
	return retryAfterResponseWithDelay("1")
}
```

### d009
```
func (m *Client) HandleRatelimit(name string, resp *model.Response) error {
	if resp == nil {
		return fmt.Errorf("Got a nil model response from %s", name)
	}

	if resp.StatusCode != 429 {
		return fmt.Errorf("StatusCode error: %d", resp.StatusCode)
	}

	waitTime, err := strconv.Atoi(resp.Header.Get("X-RateLimit-Reset"))
	if err != nil {
		return err
	}

	m.logger.Warnf("Ratelimited on %s for %d", name, waitTime)

	time.Sleep(time.Duration(waitTime) * time.Second)

	return nil
}
```

### d010
```
// DownloadFileAuth downloads the given URL using the specified authentication token.
func DownloadFileAuth(url string, auth string) (*[]byte, error) {
	var buf bytes.Buffer
	client := &http.Client{
		Timeout: time.Second * 5,
	}
	req, err := http.NewRequest("GET", url, nil)
	if auth != "" {
		req.Header.Add("Authorization", auth)
	}
	if err != nil {
		return nil, err
	}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	io.Copy(&buf, resp.Body)
	data := buf.Bytes()
	return &data, nil
}
```

### d011
```
type requestRetryFunc func(maxRetries int) WithRetry
```

### d012
```
func retryAfterResponseWithDelay(delay string) *http.Response {
	return retryAfterResponseWithCodeAndDelay(http.StatusInternalServerError, delay)
}
```

### d013
```
func (t *tracingTransport) RoundTrip(req *http.Request) (*http.Response, error) {
	reqID := req.Header.Get("X-Request-ID")
	if reqID == "" {
		reqID = uuid.New().String()
		req.Header.Set("X-Request-ID", reqID)
	}

	slog.Debug(
		"Outgoing request",
		"reqID", reqID,
		"method", req.Method,
		"URL", req.URL,
	)

	start := time.Now()
	resp, err := t.next.RoundTrip(req)
	elapsed := time.Since(start)

	if err != nil {
		slog.Error(
			"Response error",
			"reqID", reqID,
			"elapsed", elapsed,
			"error", err,
		)
		return resp, err
	}

	resp.Header.Set("X-Request-ID", reqID)
	slog.Debug(
		"Incoming response",
		"reqID", reqID,
		"status", resp.StatusCode,
		"elapsed", elapsed,
	)

	return resp, err
}
```

### d014
```
// do - execute http request.
func (c *Client) do(req *http.Request) (resp *http.Response, err error) {
	defer func() {
		if IsNetworkOrHostDown(err, false) {
			c.markOffline()
		}
	}()

	resp, err = c.httpClient.Do(req)
	if err != nil {
		// Handle this specifically for now until future Golang versions fix this issue properly.
		if urlErr, ok := err.(*url.Error); ok {
			if strings.Contains(urlErr.Err.Error(), "EOF") {
				return nil, &url.Error{
					Op:  urlErr.Op,
					URL: urlErr.URL,
					Err: errors.New("Connection closed by foreign host " + urlErr.URL + ". Retry again."),
				}
			}
		}
		return nil, err
	}

	// Response cannot be non-nil, report error if thats the case.
	if resp == nil {
		msg := "Response is empty. " + reportIssue
		return nil, errInvalidArgument(msg)
	}

	// If trace is enabled, dump http request and response,
	// except when the traceErrorsOnly enabled and the response's status code is ok
	if c.isTraceEnabled && !(c.traceErrorsOnly && resp.StatusCode == http.StatusOK) {
		err = c.dumpHTTP(req, resp)
		if err != nil {
			return nil, err
		}
	}

	return resp, nil
}
```

### d015
```
// Watch attempts to begin watching the requested location.
// Returns a watch.Interface, or an error.
func (r *Request) Watch(ctx context.Context) (watch.Interface, error) {
	// We specifically don't want to rate limit watches, so we
	// don't use r.rateLimiter here.
	if r.err != nil {
		return nil, r.err
	}

	client := r.c.Client
	if client == nil {
		client = http.DefaultClient
	}

	isErrRetryableFunc := func(request *http.Request, err error) bool {
		// The watch stream mechanism handles many common partial data errors, so closed
		// connections can be retried in many cases.
		if net.IsProbableEOF(err) || net.IsTimeout(err) {
			return true
		}
		return false
	}
	retry := r.retryFn(r.maxRetries)
	url := r.URL().String()
	for {
		if err := retry.Before(ctx, r); err != nil {
			return nil, retry.WrapPreviousError(err)
		}

		req, err := r.newHTTPRequest(ctx)
		if err != nil {
			return nil, err
		}

		resp, err := client.Do(req)
		retry.After(ctx, r, resp, err)
		if err == nil && resp.StatusCode == http.StatusOK {
			return r.newStreamWatcher(resp)
		}

		done, transformErr := func() (bool, error) {
			defer readAndCloseResponseBody(resp)

			if retry.IsNextRetry(ctx, r, req, resp, err, isErrRetryableFunc) {
				return false, nil
			}

			if resp == nil {
				// the server must have sent us an error in 'err'
				return true, nil
			}
			if result := r.transformResponse(resp, req); result.err != nil {
				return true, result.err
			}
			return true, fmt.Errorf("for request %s, got status: %v", url, resp.StatusCode)
		}()
		if done {
			if isErrRetryableFunc(req, err) {
				return watch.NewEmptyWatch(), nil
			}
			if err == nil {
				// if the server sent us an HTTP Response object,
				// we need to return the error object from that.
				err = transformErr
			}
			return nil, retry.WrapPreviousError(err)
		}
	}
}
```

### d016
```
// WithRetry allows the client to retry a request up to a certain number of times
// Note that WithRetry is not safe for concurrent use by multiple
// goroutines without additional locking or coordination.
type WithRetry interface {
	// IsNextRetry advances the retry counter appropriately
	// and returns true if the request should be retried,
	// otherwise it returns false, if:
	//  - we have already reached the maximum retry threshold.
	//  - the error does not fall into the retryable category.
	//  - the server has not sent us a 429, or 5xx status code and the
	//    'Retry-After' response header is not set with a value.
	//  - we need to seek to the beginning of the request body before we
	//    initiate the next retry, the function should log an error and
	//    return false if it fails to do so.
	//
	// restReq: the associated rest.Request
	// httpReq: the HTTP Request sent to the server
	// resp: the response sent from the server, it is set if err is nil
	// err: the server sent this error to us, if err is set then resp is nil.
	// f: a IsRetryableErrorFunc function provided by the client that determines
	//    if the err sent by the server is retryable.
	IsNextRetry(ctx context.Context, restReq *Request, httpReq *http.Request, resp *http.Response, err error, f IsRetryableErrorFunc) bool

	// Before should be invoked prior to each attempt, including
	// the first one. If an error is returned, the request should
	// be aborted immediately.
	//
	// Before may also be additionally responsible for preparing
	// the request for the next retry, namely in terms of resetting
	// the request body in case it has been read.
	Before(ctx context.Context, r *Request) error

	// After should be invoked immediately after an attempt is made.
	After(ctx context.Context, r *Request, resp *http.Response, err error)

	// WrapPreviousError wraps the error from any previous attempt into
	// the final error specified in 'finalErr', so the user has more
	// context why the request failed.
	// For example, if a request times out after multiple retries then
	// we see a generic context.Canceled or context.DeadlineExceeded
	// error which is not very useful in debugging. This function can
	// wrap any error from previous attempt(s) to provide more context to
	// the user. The error returned in 'err' must satisfy the
	// following conditions:
	//  a: errors.Unwrap(err) = errors.Unwrap(finalErr) if finalErr
	//     implements Unwrap
	//  b: errors.Unwrap(err) = finalErr if finalErr does not
	//     implements Unwrap
	//  c: errors.Is(err, otherErr) = errors.Is(finalErr, otherErr)
	WrapPreviousError(finalErr error) (err error)
}
```

### d017
```
func defaultRequestRetryFn(maxRetries int) WithRetry {
	return &withRetry{maxRetries: maxRetries}
}
```

### d018
```
func fetchIMDSToken(client *http.Client, endpoint string) (string, error) {
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()

	req, err := http.NewRequestWithContext(ctx, http.MethodPut, endpoint+tokenPath, nil)
	if err != nil {
		return "", err
	}
	req.Header.Add(tokenRequestTTLHeader, tokenTTL)
	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	data, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}
	if resp.StatusCode != http.StatusOK {
		return "", errors.New(resp.Status)
	}
	return string(data), nil
}
```

### d019
```
// retry function will check if we're ratelimited and retries again when backoff time expired
// returns original error if not 429 ratelimit
func (b *Bmatrix) retry(f func() error) error {
	b.rateMutex.Lock()
	defer b.rateMutex.Unlock()

	for {
		if err := f(); err != nil {
			if backoff, ok := b.handleRatelimit(err); ok {
				time.Sleep(backoff)
			} else {
				return err
			}
		} else {
			return nil
		}
	}
}
```

### d020
```
func getEcsTaskCredentials(client *http.Client, endpoint string, token string) (ec2RoleCredRespBody, error) {
	req, err := http.NewRequest(http.MethodGet, endpoint, nil)
	if err != nil {
		return ec2RoleCredRespBody{}, err
	}

	if token != "" {
		req.Header.Set("Authorization", token)
	}

	resp, err := client.Do(req)
	if err != nil {
		return ec2RoleCredRespBody{}, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return ec2RoleCredRespBody{}, errors.New(resp.Status)
	}

	respCreds := ec2RoleCredRespBody{}
	if err := jsoniter.NewDecoder(resp.Body).Decode(&respCreds); err != nil {
		return ec2RoleCredRespBody{}, err
	}

	return respCreds, nil
}
```

## Output

Return raw JSON only. No preamble, no markdown fences, no commentary outside the
object.

```json
{
  "query_id": "B12",
  "labels": {
    "d001": {"score": 1.0, "rationale": "iterative binary search over sorted array"},
    "d002": {"score": 0.0, "rationale": "pytest case asserting search behaviour, not an implementation"}
  }
}
```

Every `doc_id` presented must appear exactly once in `labels`.
