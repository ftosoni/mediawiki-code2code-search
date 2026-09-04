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
function throttle<T extends (...args: unknown[]) => void>(
    fn: T, limitMs: number
): T {
    let lastCall = 0;
    return function (...args) {
        const now = Date.now();
        if (now - lastCall >= limitMs) {
            lastCall = now;
            fn(...args);
        }
    } as T;
}
```

## Candidates

### d001
```
/**
   * Throttle decorator
   * @param {Function} fn
   * @param {Number} freq
   * @return {Function}
   */
  function throttle(fn, freq) {
    var timestamp = 0;
    var threshold = 1000 / freq;
    var lastArgs;
    var timer;
    var invoke = function invoke(args) {
      var now = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : Date.now();
      timestamp = now;
      lastArgs = null;
      if (timer) {
        clearTimeout(timer);
        timer = null;
      }
      fn.apply(void 0, _toConsumableArray(args));
    };
    var throttled = function throttled() {
      var now = Date.now();
      var passed = now - timestamp;
      for (var _len = arguments.length, args = new Array(_len), _key = 0; _key < _len; _key++) {
        args[_key] = arguments[_key];
      }
      if (passed >= threshold) {
        invoke(args, now);
      } else {
        lastArgs = args;
        if (!timer) {
          timer = setTimeout(function () {
            timer = null;
            invoke(lastArgs);
          }, threshold - passed);
        }
      }
    };
    var flush = function flush() {
      return lastArgs && invoke(lastArgs);
    };
    return [throttled, flush];
  }
```

### d002
```
/**
 * Throttle fn, calling at most once
 * in the given interval.
 *
 * @param  {Function} fn
 * @param  {Number} interval
 *
 * @return {Function} throttled function
 */
function throttle(fn, interval) {
  let throttling = false;

  return function(...args) {

    if (throttling) {
      return;
    }

    fn(...args);
    throttling = true;

    setTimeout(() => {
      throttling = false;
    }, interval);
  };
}
```

### d003
```
// @function throttle(fn: Function, time: Number, context: Object): Function
// Returns a function which executes function `fn` with the given scope `context`
// (so that the `this` keyword refers to `context` inside `fn`'s code). The function
// `fn` will be called no more than one time per given amount of `time`. The arguments
// received by the bound function will be any arguments passed when binding the
// function, followed by any arguments passed when invoking the bound function.
// Has an `L.throttle` shortcut.
function throttle(fn, time, context) {
	var lock, args, wrapperFn, later;

	later = function () {
		// reset lock and call if queued
		lock = false;
		if (args) {
			wrapperFn.apply(context, args);
			args = false;
		}
	};

	wrapperFn = function () {
		if (lock) {
			// called too soon, queue to call later
			args = arguments;

		} else {
			// call and lock until later
			fn.apply(context, arguments);
			setTimeout(later, time);
			lock = true;
		}
	};

	return wrapperFn;
}
```

### d004
```
function trackUserExit() {
		var timeout;
		var timeoutDuration = 30 * 60 * 1000; // 30 minutes in milliseconds

		function resetTimer() {
			// Clear the existing timeout
			clearTimeout( timeout );
			timeout = setTimeout( logInactivity, timeoutDuration );
		}

		function logInactivity() {
			logger.logEvent( 'exit', 'inactivity' );
		}

		function throttle( func, delay ) {
			var lastCall = 0;

			return function () {
				var now = Date.now();
				if ( now - lastCall >= delay ) {
					lastCall = now;
					func();
				}
			};
		}

		// Create a throttled version of resetTimer
		var throttledResetTimer = throttle( resetTimer, 3000 ); // 3 seconds between resets
		// Add event listeners with throttled reset
		var events = [
			'mousemove',
			'mousedown',
			'touchstart',
			'touchmove',
			'click',
			'keydown',
			'scroll',
			'wheel'
		];

		events.forEach( function ( eventName ) {
			window.addEventListener( eventName, throttledResetTimer, true );
		} );

		resetTimer(); // Initial timer setup

		window.addEventListener( 'unload', function () {
			logger.logEvent( 'exit', 'browser_tab_close' );
		} );
	}
```

### d005
```
/**
 * Throttles a function and delays its execution, so it's only called at most
 * once within a given time period.
 * @param {Function} fn The function to throttle.
 * @param {number} timeout The amount of time that must pass before the
 *     function can be called again.
 * @return {Function} The throttled function.
 */
function throttle(fn, timeout) {
  var timer = null;
  return function () {
    if (!timer) {
      timer = setTimeout(function() {
        fn();
        timer = null;
      }, timeout);
    }
  };
}
```

### d006
```
function runFunc(endDate){
      lastCall = +new Date();
      func.apply(context, args);
      $interval(function(){queued = null; }, 0, 1, false);
    }
```

### d007
```
function throttle<T extends (...args: any[]) => any>(
  func: T,
  delay: number = 500
): (...args: Parameters<T>) => void {
  let lastRun = 0;
  let timeoutId: NodeJS.Timeout | null = null;

  return function (...args: Parameters<T>) {
    const now = Date.now();

    if (now - lastRun >= delay) {
      lastRun = now;
      func(...args);
    } else {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }

      timeoutId = setTimeout(() => {
        lastRun = Date.now();
        func(...args);
      }, delay - (now - lastRun));
    }
  };
}
```

### d008
```
function useThrottle<T extends (...args: any[]) => any>(
  callback: T,
  delay: number = 500
): T {
  const lastRunRef = useRef<number>(0);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  return useCallback(
    ((...args: any[]) => {
      const now = Date.now();
      const timeSinceLastRun = now - lastRunRef.current;

      if (timeSinceLastRun >= delay) {
        // Execute immediately if enough time has passed
        lastRunRef.current = now;
        callback(...args);
      } else {
        // Schedule execution for later
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }

        timeoutRef.current = setTimeout(() => {
          lastRunRef.current = Date.now();
          callback(...args);
        }, delay - timeSinceLastRun);
      }
    }) as T,
    [callback, delay]
  );
}
```

### d009
```
/**
 * Throttle decorator
 * @param {Function} fn
 * @param {Number} freq
 * @return {Function}
 */
function throttle(fn, freq) {
  let timestamp = 0;
  let threshold = 1000 / freq;
  let lastArgs;
  let timer;

  const invoke = (args, now = Date.now()) => {
    timestamp = now;
    lastArgs = null;
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
    fn(...args);
  };

  const throttled = (...args) => {
    const now = Date.now();
    const passed = now - timestamp;
    if (passed >= threshold) {
      invoke(args, now);
    } else {
      lastArgs = args;
      if (!timer) {
        timer = setTimeout(() => {
          timer = null;
          invoke(lastArgs);
        }, threshold - passed);
      }
    }
  };

  const flush = () => lastArgs && invoke(lastArgs);

  return [throttled, flush];
}
```

### d010
```
// ---------- helpers ----------
  function throttle(fn, waitMs) {
    let last = 0, timer = 0, pendingArgs = null;
    return (...args) => {
      const now = Date.now();
      const remaining = waitMs - (now - last);
      if (remaining <= 0) {
        last = now;
        fn(...args);
      } else {
        pendingArgs = args;
        clearTimeout(timer);
        timer = setTimeout(() => { last = Date.now(); fn(...pendingArgs); }, remaining);
      }
    };
  }
```

### d011
```
function _throttle(callback, ms) {
		return function () {
			if (!_throttleTimeout) {
				var args = arguments,
					_this = this
				;

				_throttleTimeout = setTimeout(function () {
					if (args.length === 1) {
						callback.call(_this, args[0]);
					} else {
						callback.apply(_this, args);
					}

					_throttleTimeout = void 0;
				}, ms);
			}
		};
	}
```

### d012
```
function throttle(fn, wait) {
      if (wait === void 0) { wait = 250; }
      var previous = 0;
      var timeout = null;
      var result;
      var storedContext;
      var storedArgs;
      var later = function () {
          previous = Date.now();
          timeout = null;
          result = fn.apply(storedContext, storedArgs);
          if (!timeout) {
              storedContext = null;
              storedArgs = [];
          }
      };
      return function () {
          var args = [];
          for (var _i = 0; _i < arguments.length; _i++) {
              args[_i] = arguments[_i];
          }
          var now = Date.now();
          var remaining = wait - (now - previous);
          storedContext = this;
          storedArgs = args;
          if (remaining <= 0 || remaining > wait) {
              if (timeout) {
                  clearTimeout(timeout);
                  timeout = null;
              }
              previous = now;
              result = fn.apply(storedContext, storedArgs);
              if (!timeout) {
                  storedContext = null;
                  storedArgs = [];
              }
          }
          else if (!timeout) {
              timeout = setTimeout(later, remaining);
          }
          return result;
      };
  }
```

### d013
```
function throttle(callback, ms) {
    return function () {
      if (!_throttleTimeout) {
        var args = arguments,
          _this = this;
        if (args.length === 1) {
          callback.call(_this, args[0]);
        } else {
          callback.apply(_this, args);
        }
        _throttleTimeout = setTimeout(function () {
          _throttleTimeout = void 0;
        }, ms);
      }
    };
  }
```

### d014
```
function throttle( func, delay ) {
			var lastCall = 0;

			return function () {
				var now = Date.now();
				if ( now - lastCall >= delay ) {
					lastCall = now;
					func();
				}
			};
		}
```

## Output

Return raw JSON only. No preamble, no markdown fences, no commentary outside the
object.

```json
{
  "query_id": "C4",
  "labels": {
    "d001": {"score": 1.0, "rationale": "iterative binary search over sorted array"},
    "d002": {"score": 0.0, "rationale": "pytest case asserting search behaviour, not an implementation"}
  }
}
```

Every `doc_id` presented must appear exactly once in `labels`.
