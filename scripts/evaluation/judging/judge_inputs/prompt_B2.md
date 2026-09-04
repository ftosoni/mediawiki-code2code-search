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
function delayExecution(fn, waitMs) {
    let timer;
    return function (...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), waitMs);
    };
}
```

## Candidates

### d001
```
createDelay(e=10){let n,s;const i=()=>{n&&(clearTimeout(n),n=void 0),s&&(s(),s=void 0)};return this.timeouts.push(i),()=>new Promise(((r,o)=>{i(),s=o,n=setTimeout((()=>{n=void 0,s=void 0,r()}),e)}))}
```

### d002
```
/**
   * @returns {void}
   */
  function debounced() {
    const context = this;
    const args = arguments;

    clearTimeout(timer);
    timer = setTimeout(function () {
      return fn.apply(context, args);
    }, wait);
  }
```

### d003
```
function taskDebounce(fn) {
    var scheduled = false;
    return function() {
      if (!scheduled) {
        scheduled = true;
        setTimeout(function() {
          scheduled = false;
          fn();
        }, timeoutDuration);
      }
    };
  }
```

### d004
```
/**
 * Executes an action at or after the specified number of seconds.
 * (copied from SearchSatisfaction)
 *
 * @param {number[]} checkinTimes Times (in seconds from start) when the
 *  action should be executed.
 * @param {Function} fn The action to execute.
 * @private
 */
function interval( checkinTimes, fn ) {
	// found this example, wanted to do it, no idea how require works in mw
	// const visibleTimeout = require( 'mediawiki.visibleTimeout' );
	//     ...
	//     visibleTimeout.set( action, 1000 * timeout );
	// have no idea how require works in mw world, will figure out later
	let checkin = checkinTimes.shift();
	let timeout = checkin;
	function action() {
		const current = checkin;
		fn( current );
		checkin = checkinTimes.shift();
		if ( checkin ) {
			timeout = checkin - current;
			setTimeout( action, 1000 * timeout );
		}
	}
	setTimeout( action, 1000 * timeout );
}
```

### d005
```
/* global setTimeout clearTimeout */

  /**
   * @typedef { {
   *   (...args: any[]): any;
   *   flush: () => void;
   *   cancel: () => void;
   * } } DebouncedFunction
   */

  /**
   * Debounce fn, calling it only once if the given time
   * elapsed between calls.
   *
   * Lodash-style the function exposes methods to `#clear`
   * and `#flush` to control internal behavior.
   *
   * @param  {Function} fn
   * @param  {Number} timeout
   *
   * @return {DebouncedFunction} debounced function
   */
  function debounce(fn, timeout) {

    let timer;

    let lastArgs;
    let lastThis;

    let lastNow;

    function fire(force) {

      let now = Date.now();

      let scheduledDiff = force ? 0 : (lastNow + timeout) - now;

      if (scheduledDiff > 0) {
        return schedule(scheduledDiff);
      }

      fn.apply(lastThis, lastArgs);

      clear();
    }

    function schedule(timeout) {
      timer = setTimeout(fire, timeout);
    }

    function clear() {
      if (timer) {
        clearTimeout(timer);
      }

      timer = lastNow = lastArgs = lastThis = undefined;
    }

    function flush() {
      if (timer) {
        fire(true);
      }

      clear();
    }

    /**
     * @type { DebouncedFunction }
     */
    function callback(...args) {
      lastNow = Date.now();

      lastArgs = args;
      lastThis = this;

      // ensure an execution is scheduled
      if (!timer) {
        schedule(timeout);
      }
    }

    callback.flush = flush;
    callback.cancel = clear;

    return callback;
  }
```

### d006
```
/**
 * Debounce a function to delay invoking until wait (ms) have elapsed since the last invocation.
 * @param {function(...*): *} fn The function to be debounced.
 * @param {number} wait Milliseconds to wait before invoking again.
 * @return {function(...*): void} The debounced function.
 */
function debounce(fn, wait) {
  /**
   * A cached setTimeout handler.
   * @type {number | undefined}
   */
  let timer;

  /**
   * @returns {void}
   */
  function debounced() {
    const context = this;
    const args = arguments;

    clearTimeout(timer);
    timer = setTimeout(function () {
      return fn.apply(context, args);
    }, wait);
  }

  return debounced;
}
```

### d007
```
// Throttle helper
  function trumbowygThrottle(callback, delay) {
    var last;
    var timer;

    return function () {
      var context = this;
      var now = +new Date();
      var args = arguments;

      if (last && now < last + delay) {
        clearTimeout(timer);
        timer = setTimeout(function () {
          last = now;
          callback.apply(context, args);
        }, delay);
      } else {
        last = now;
        callback.apply(context, args);
      }
    };
  }
```

### d008
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

### d009
```
function defer(fn) {
  setTimeout(fn, 0);
}
```

### d010
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

### d011
```
/**
	 * Throttle the calls to a function. Arguments and context are maintained for
	 * the throttled function
	 *  @param {function} fn Function to be called
	 *  @param {int} [freq=200] call frequency in mS
	 *  @returns {function} wrapped function
	 *  @memberof DataTable#oApi
	 */
	function _fnThrottle( fn, freq ) {
		var
			frequency = freq || 200,
			last,
			timer;
	
		return function () {
			var
				that = this,
				now  = +new Date(),
				args = arguments;
	
			if ( last && now < last + frequency ) {
				clearTimeout( timer );
	
				timer = setTimeout( function () {
					last = undefined;
					fn.apply( that, args );
				}, frequency );
			}
			else if ( last ) {
				last = now;
				fn.apply( that, args );
			}
			else {
				last = now;
			}
		};
	}
```

### d012
```
function delayer() {
		return ( function () {
			var timer = 0;

			return function ( callback, milliseconds ) {
				clearTimeout( timer );

				if ( callback === false ) {
					// sometimes we need to just cancel the timer without
					// setting up another one
					return;
				}

				timer = setTimeout( callback, milliseconds );
			};
		}() );
	}
```

### d013
```
// Helper function to delay execution
	delay( ms ) {
		return new Promise( ( resolve ) => {
			setTimeout( resolve, ms );
		} );
	}
```

### d014
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

### d015
```
// Helper function to delay execution and raise an exception
	delay_rej( ms ) {
		return new Promise( ( resolve, reject ) => {
			setTimeout( reject, ms );
		} );
	}
```

### d016
```
waitForMs( ms ) {
		// eslint-disable-next-line no-promise-executor-return
		return new Promise( ( resolve ) => setTimeout( resolve, ms ) );
	}
```

## Output

Return raw JSON only. No preamble, no markdown fences, no commentary outside the
object.

```json
{
  "query_id": "B2",
  "labels": {
    "d001": {"score": 1.0, "rationale": "iterative binary search over sorted array"},
    "d002": {"score": 0.0, "rationale": "pytest case asserting search behaviour, not an implementation"}
  }
}
```

Every `doc_id` presented must appear exactly once in `labels`.
