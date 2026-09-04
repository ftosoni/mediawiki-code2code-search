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
def retry(func, max_attempts=3, base_delay=1.0):
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception:
            if attempt == max_attempts - 1:
                raise
            time.sleep(base_delay * (2 ** attempt))
```

## Candidates

### d001
```
def retry(  # pylint: disable=too-many-arguments,useless-suppression
    func: Callable,
    *,
    tries: int = 3,
    delay: timedelta = timedelta(seconds=3),
    backoff_mode: str = "exponential",
    exceptions: Tuple[Type[Exception], ...] = (WmflibError,),
    failure_message: Optional[str] = None,
    dynamic_params_callbacks: Tuple[Callable[[RetryParams, Callable, Tuple, Dict[str, Any]], None], ...] = (),
) -> Callable:
    """Decorator to retry a function or method if it raises certain exceptions with customizable backoff.

    Note:
        The decorated function or method must be idempotent to avoid unwanted side effects.
        It can be called with or without arguments, in the latter case all the default values will be used.

    Examples:
        Define a function that polls for the existence of a file, retrying with the default parameters::

            >>> from pathlib import Path
            >>> from wmflib.decorators import retry
            >>> from wmflib.exceptions import WmflibError
            >>> @retry
            ... def poll_file(path: Path):
            ...     if not path.exists():
            ...         raise WmflibError(f"File {path} not found")
            ...
            >>> poll_file(Path("/tmp"))
            >>> poll_file(Path("/tmp/nonexistent"))
            [1/3, retrying in 3.00s] Attempt to run '__main__.poll_file' raised: File /tmp/nonexistent not found
            [2/3, retrying in 9.00s] Attempt to run '__main__.poll_file' raised: File /tmp/nonexistent not found
            Traceback (most recent call last):
              File "<stdin>", line 1, in <module>
              File "/usr/lib/python3/dist-packages/wmflib/decorators.py", line 160, in wrapper
                return func(*args, **kwargs)
              File "<stdin>", line 4, in poll_file
            wmflib.exceptions.WmflibError: File /tmp/nonexistent not found
            >>>

        Same example, but customizing the decorator parameters::

            >>> from datetime import timedelta
            >>> from pathlib import Path
            >>> from wmflib.decorators import retry
            >>> @retry(tries=5, delay=timedelta(seconds=30), backoff_mode="constant", failure_message="File not found",
            ...        exceptions=(RuntimeError,))
            ... def poll_file(path: Path):
            ...     if not path.exists():
            ...         raise RuntimeError(path)
            ...
            [1/5, retrying in 30.00s] File not found: /tmp/nonexistent
            [2/5, retrying in 30.00s] File not found: /tmp/nonexistent
            [3/5, retrying in 30.00s] File not found: /tmp/nonexistent
            [4/5, retrying in 30.00s] File not found: /tmp/nonexistent
            Traceback (most recent call last):
              File "<stdin>", line 1, in <module>
              File "/usr/lib/python3/dist-packages/wmflib/decorators.py", line 160, in wrapper
                return func(*args, **kwargs)
              File "<stdin>", line 5, in poll_file
            RuntimeError: /tmp/nonexistent

    Arguments:
        func (function, method): the decorated function.
        tries (int, optional): the number of times to try calling the decorated function or method before giving up.
            Must be a positive integer.
        delay (datetime.timedelta, optional): the initial delay in seconds for the first retry, used also as the base
            for the backoff algorithm.
        backoff_mode (str, optional): the backoff mode to use for the delay, available values are shown below. All the
            examples are made with ``tries=5`` and ``delay=3``:

              * **constant**

                .. code-block:: text

                  Nth delay   = delay
                  Total delay = delay * tries
                  Example:      3s, 3s,  3s,  3s,   3s => 15s max possible delay

              * **linear**

                .. code-block:: text

                  Nth delay   = (delay * N) with N in [1, tries]
                  Total delay = 0.5 * tries * (delay + (delay * tries))
                  Example:      3s, 6s,  9s, 12s,  15s => 45s max possible delay

              * **power**

                .. code-block:: text

                  Nth delay   = (delay * 2^N) with N in [0, tries - 1]
                  Total delay = delay * (2**tries - 1)
                  Example:      3s, 6s, 12s, 24s,  48s => 93s max possible delay

              * **exponential**

                .. code-block:: text

                  Nth delay   = (delay^N) with N in [1, tries], delay must be > 1
                  Total delay = (delay * (delay**tries - 1)) / (delay - 1)
                  Example:      3s, 9s, 27s, 81s, 243s => 363s max possible delay

        exceptions (type, tuple, optional): the decorated function call will be retried if it fails until it succeeds
            or `tries` attempts are reached. A retryable failure is defined as raising any of the exceptions listed.
        failure_message (str, optional): the message to log each time there's a retryable failure. Retry information
            and exception message are also included. Default: "Attempt to run '<fully qualified function>' raised"
        dynamic_params_callbacks (tuple): a tuple of callbacks that will be called at runtime to allow to modify the
            decorator's parameters. Each callable must adhere to the following interface::

                def adjust_some_parameter(retry_params: RetryParams, func: Callable, args: Tuple, kwargs: Dict) -> None
                    # Modify the retry_params parameter possibly using the decorated function object or its parameters
                    # that are passed as tuple for the positional arguments and a dictionary for the keyword arguments

            This is a practical example that defines a callback that doubles the delay parameter of the ``@retry``
            decorator if the decorated function/method has a 'slow' keyword argument that is to True::

                def double_delay(retry_params, func, args, kwargs):
                    if kwargs.get("slow", False):
                        retry_params.delay = retry_params.delay * 2

                @retry(delay=timedelta(seconds=10), dynamic_params_callbacks=(double_delay,))
                def do_something(slow=False):
                    # This method will be retried using 10 seconds as delay parameter in the @retry decorator, but
                    # if the 'slow' parameter is set to True it will use a delay of 20 seconds instead.
                    # Do something here.

            **While the callbacks will have access to the parameters passed to the decorated function, they should be
            treated as read-only variables.**

    Returns:
        function: the decorated function.

    """
    if not failure_message:
        failure_message = f"Attempt to run '{func.__module__}.{func.__qualname__}' raised"

    static_params: Dict[str, Any] = {
        "tries": tries,
        "delay": delay,
        "backoff_mode": backoff_mode,
        "exceptions": exceptions,
        "failure_message": failure_message,
    }

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        """Decorated function."""
        params = RetryParams(**static_params)
        for dynamic_params_callback in dynamic_params_callbacks:
            dynamic_params_callback(params, func, args, kwargs)

        params.validate()
        attempt = 0
        while attempt < params.tries - 1:
            attempt += 1
            try:
                # Call the decorated function or method
                return func(*args, **kwargs)
            except exceptions as e:
                sleep = get_backoff_sleep(params.backoff_mode, params.delay.total_seconds(), attempt)
                logger.warning(
                    "[%d/%d, retrying in %.2fs] %s: %s",
                    attempt,
                    params.tries,
                    sleep,
                    params.failure_message,
                    _exception_message(e),
                )
                time.sleep(sleep)

        return func(*args, **kwargs)

    return wrapper
```

### d002
```
def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    result = func(*args, **kwargs)
                    if isinstance(result, tuple) and len(result) == 2:
                        data, error = result
                        if error is None or "Retrieved from Wayback Machine" in str(error):
                            return result
                        if attempt < max_attempts - 1:
                            print(f"Attempt {attempt + 1} failed, retrying in {delay}s...")
                            sleep(delay)
                            continue
                    return result
                except Exception as e:
                    if attempt < max_attempts - 1:
                        print(f"Attempt {attempt + 1} failed: {str(e)}, retrying in {delay}s...")
                        sleep(delay)
                    else:
                        if hasattr(func, '__name__') and 'ocr' in func.__name__.lower():
                            return f"OCR Error: {str(e)}"
                        return None, f"Error after {max_attempts} attempts: {str(e)}"
            return result
        return wrapper
```

### d003
```
def wrapper(*args: Any, **kwargs: Any) -> Any:
        """Decorated function."""
        params = RetryParams(**static_params)
        for dynamic_params_callback in dynamic_params_callbacks:
            dynamic_params_callback(params, func, args, kwargs)

        params.validate()
        attempt = 0
        while attempt < params.tries - 1:
            attempt += 1
            try:
                # Call the decorated function or method
                return func(*args, **kwargs)
            except exceptions as e:
                sleep = get_backoff_sleep(params.backoff_mode, params.delay.total_seconds(), attempt)
                logger.warning(
                    "[%d/%d, retrying in %.2fs] %s: %s",
                    attempt,
                    params.tries,
                    sleep,
                    params.failure_message,
                    _exception_message(e),
                )
                time.sleep(sleep)

        return func(*args, **kwargs)
```

### d004
```
def retry_call(func, cleanup=lambda: None, retries=0, trap=()):
    """
    Given a callable func, trap the indicated exceptions
    for up to 'retries' times, invoking cleanup on the
    exception. On the final attempt, allow any exceptions
    to propagate.
    """
    attempts = itertools.count() if retries == float('inf') else range(retries)
    for attempt in attempts:
        try:
            return func()
        except trap:
            cleanup()

    return func()
```

### d005
```
def retry(
    wait: float, stop_after_delay: float
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator to automatically retry a function on error.

    If the function raises, the function is recalled with the same arguments
    until it returns or the time limit is reached. When the time limit is
    surpassed, the last exception raised is reraised.

    :param wait: The time to wait after an error before retrying, in seconds.
    :param stop_after_delay: The time limit after which retries will cease,
        in seconds.
    """

    def wrapper(func: Callable[P, T]) -> Callable[P, T]:

        @functools.wraps(func)
        def retry_wrapped(*args: P.args, **kwargs: P.kwargs) -> T:
            # The performance counter is monotonic on all platforms we care
            # about and has much better resolution than time.monotonic().
            start_time = perf_counter()
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception:
                    if perf_counter() - start_time > stop_after_delay:
                        raise
                    sleep(wait)

        return retry_wrapped

    return wrapper
```

### d006
```
def retry_function(func):
    for attempt in range(1, POST_ATTEMPTS + 1):
        try:
            return func()
        except Exception:
            if attempt >= POST_ATTEMPTS:
                raise
            else:
                logging.exception("Error on attempt %d" % attempt)
                time.sleep(attempt * 10)
```

### d007
```
def add_polish_description_to_item(item, description_text, summary="Dodano polski opis"):
    """
    Adds a Polish description to a Wikidata item with conflict resolution.
    Retries with exponential backoff on conflict errors.
    """
    max_attempts = 5
    attempt = 0
    while attempt < max_attempts:
        try:
            item.get()  # Fetch current data
            if 'pl' in item.descriptions:
                log_message("info", f"Opis już istnieje dla elementu: {item.descriptions['pl']}" , verbose=verbose)
                return
            item.editDescriptions({'pl': description_text}, summary=summary)
            log_message("info", f"Description '{description_text}' added successfully." , verbose=verbose)
            return  # Exit if successful
        except pywikibot.exceptions.APIError as e:
            if "wikibase-conflict-patched" in str(e):
                log_message("warning", "Conflict detected; retrying with backoff." , verbose=verbose)
                adaptive_sleep(attempt)  # Wait before retrying
                attempt += 1
            else:
                log_message("error", f"Unexpected error: {e}" , verbose=verbose)
                raise  # Reraise other exceptions not related to conflict
    log_message("error", "Max attempts reached without success in resolving conflict." , verbose=verbose)
```

### d008
```
def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    result = func(*args, **kwargs)
                    if isinstance(result, tuple) and len(result) == 2:
                        data, error = result
                        if error is None or "Retrieved from Wayback Machine" in str(error):
                            return result
                        if attempt < max_attempts - 1:
                            print(f"Attempt {attempt + 1} failed, retrying in {delay}s...")
                            sleep(delay)
                            continue
                    return result
                except Exception as e:
                    if attempt < max_attempts - 1:
                        print(f"Attempt {attempt + 1} failed: {str(e)}, retrying in {delay}s...")
                        sleep(delay)
                    else:
                        if hasattr(func, '__name__') and 'ocr' in func.__name__.lower():
                            return f"OCR Error: {str(e)}"
                        return None, f"Error after {max_attempts} attempts: {str(e)}"
            return result
```

### d009
```
def retry_on_failure(max_attempts=10, delay=2):
    """Decorator to retry function on failure"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    result = func(*args, **kwargs)
                    if isinstance(result, tuple) and len(result) == 2:
                        data, error = result
                        if error is None or "Retrieved from Wayback Machine" in str(error):
                            return result
                        if attempt < max_attempts - 1:
                            print(f"Attempt {attempt + 1} failed, retrying in {delay}s...")
                            sleep(delay)
                            continue
                    return result
                except Exception as e:
                    if attempt < max_attempts - 1:
                        print(f"Attempt {attempt + 1} failed: {str(e)}, retrying in {delay}s...")
                        sleep(delay)
                    else:
                        if hasattr(func, '__name__') and 'ocr' in func.__name__.lower():
                            return f"OCR Error: {str(e)}"
                        return None, f"Error after {max_attempts} attempts: {str(e)}"
            return result
        return wrapper
    return decorator
```

### d010
```
def _fetch_tree_with_retry(repo_url: str):
    last_exc = None
    for attempt in range(1, _RETRY_ATTEMPTS + 1):
        try:
            return fetch_repo_tree(repo_url)
        except SyncError as exc:
            last_exc = exc
            if attempt < _RETRY_ATTEMPTS:
                wait = _RETRY_BACKOFF_BASE ** attempt
                logger.warning(
                    "[check] Tree fetch attempt %d/%d failed — retry in %ds: %s",
                    attempt, _RETRY_ATTEMPTS, wait, exc,
                )
                time.sleep(wait)
    raise last_exc or SyncError("Unknown tree fetch error")
```

### d011
```
def upload_to_commons(site, FilePage, image, target_filename, img_format, exif_data, description, max_attempts=10):
    """Upload image to Wikimedia Commons"""

    # Filename should already have correct extension from title generation
    # No extension checking or modification here - use filename as-is

    # Save image temporarily with correct format
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{img_format}')
    try:
        # Convert OpenCV image back to PIL to preserve EXIF
        img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)

        # Save with EXIF data if available
        save_kwargs = {}
        if exif_data:
            save_kwargs['exif'] = exif_data

        if img_format == 'png':
            img_pil.save(temp_file.name, 'PNG', optimize=True, **save_kwargs)
        elif img_format == 'jpg':
            img_pil.save(temp_file.name, 'JPEG', quality=95, **save_kwargs)
        else:
            img_pil.save(temp_file.name, **save_kwargs)

        # Try uploading with retries
        for attempt in range(max_attempts):
            try:
                file_page = FilePage(site, f'File:{target_filename}')

                if file_page.exists():
                    logger.info(f"File already exists: {target_filename}")
                    return False, 'File already exists'

                logger.info(f"Uploading {target_filename} (attempt {attempt + 1}/{max_attempts})")

                success = file_page.upload(
                    source=temp_file.name,
                    comment=f"Pypan 0.1.1a0",
                    text=description,
                    ignore_warnings=True,
                )

                if success:
                    logger.info(f"Successfully uploaded {target_filename}")
                    return True, ''
                else:
                    logger.warning(f"Upload failed - server response for {target_filename}")

            except UploadError as e:
                logger.warning(f"Upload warning for {target_filename}: {str(e)}")

            except Exception as e:
                logger.error(f"Error uploading {target_filename}: {str(e)}")

            if attempt < max_attempts - 1:
                logger.info(f"Waiting 10 seconds before retry...")
                sleep(10)

        return False, 'Max attempts reached'

    finally:
        # Clean up temp file
        try:
            os.unlink(temp_file.name)
        except:
            pass
```

### d012
```
def adaptive_sleep(attempt, base_delay=5):
    """
    Adaptive sleep based on attempt count to manage request rate.
    Applies exponential backoff.
    """
    delay = base_delay * (2 ** attempt)
    log_message("info", f"Adaptive sleep for {delay} seconds due to API rate limiting..." , verbose=verbose)
    sleep(delay)
```

## Output

Return raw JSON only. No preamble, no markdown fences, no commentary outside the
object.

```json
{
  "query_id": "A5",
  "labels": {
    "d001": {"score": 1.0, "rationale": "iterative binary search over sorted array"},
    "d002": {"score": 0.0, "rationale": "pytest case asserting search behaviour, not an implementation"}
  }
}
```

Every `doc_id` presented must appear exactly once in `labels`.
