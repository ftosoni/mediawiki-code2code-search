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
def gcd(a, b):
    while b:
        a, b = b, a % b
    return a
```

## Candidates

### d001
```
/**
	 * Format a rational number, reducing fractions
	 *
	 * @param mixed $num The value to format
	 * @return mixed A floating point number or whatever we were fed
	 */
	private function formatFraction( $num ) {
		$m = [];
		$num ??= '';
		if ( preg_match( '/^(-?\d+)\/(\d+)$/', $num, $m ) ) {
			$numerator = (int)$m[1];
			$denominator = (int)$m[2];
			$gcd = $this->gcd( abs( $numerator ), $denominator );
			if ( $gcd !== 0 ) {
				// 0 shouldn't happen! ;)
				return $this->formatNum( $numerator / $gcd ) . '/' . $this->formatNum( $denominator / $gcd );
			}
		}

		return $this->formatNum( $num );
	}
```

### d002
```
/**
	 * Calculate the greatest common divisor of two integers.
	 *
	 * @param int $a Numerator
	 * @param int $b Denominator
	 * @return int
	 */
	private function gcd( $a, $b ) {
		/*
			// https://en.wikipedia.org/wiki/Euclidean_algorithm
			// Recursive form would be:
			if ( $b == 0 )
				return $a;
			else
				return gcd( $b, $a % $b );
		*/
		while ( $b != 0 ) {
			$remainder = $a % $b;

			// tail recursion...
			$a = $b;
			$b = $remainder;
		}

		return $a;
	}
```

### d003
```
/**
     * Returns the greatest common divisor of the two numbers.
     *
     * This method can be overridden by the concrete implementation if the underlying library
     * has built-in support for GCD calculations.
     *
     * @return string The GCD, always positive, or zero if both arguments are zero.
     *
     * @pure
     */
    public function gcd(string $a, string $b): string
    {
        if ($a === '0') {
            return $this->abs($b);
        }

        if ($b === '0') {
            return $this->abs($a);
        }

        return $this->gcd($b, $this->divR($a, $b));
    }
```

### d004
```
/* utility function for checking ratio */
	function respectsAspectRatio(a, b, w, h) {

		function greatestCommonDivisor(a,b) {
			if (b == 0) {
				return a
			}
		    return greatestCommonDivisor(b, a % b)
		}

		var gcd = greatestCommonDivisor(a,b);

		return a / gcd === w && b / gcd === h;
	}
```

### d005
```
function gcd(a, b) {
      return b ? gcd(b, a % b) : a;
    }
```

### d006
```
func __stime64_scale64_ceil(tls *libc.TLS, x Int64_t, factor Int64_t, divisor Int64_t) Int64_t {
	var gcd Int64_t = ^factor&(factor-int64(1)) & ^divisor & (divisor-int64(1)) + int64(1)

	return __stime64_scale32_ceil(tls, x, int32(factor/gcd), int32(divisor/gcd))
}
```

### d007
```
func __utime64_scale64_floor(tls *libc.TLS, x Uint64_t, factor Uint64_t, divisor Uint64_t) Uint64_t {
	var gcd Uint64_t = ^factor&(factor-uint64(1)) & ^divisor & (divisor-uint64(1)) + uint64(1)

	return __utime64_scale32_floor(tls, x, uint32(factor/gcd), uint32(divisor/gcd))
}
```

### d008
```
public function testNamedOperator() {
		$node = new Literal( '\\gcd' );
		$result = $node->toMMLTree();
		$this->assertStringContainsString( '>gcd</mo>', (string)$result );
	}
```

### d009
```
func __stime64_scale64_floor(tls *libc.TLS, x Int64_t, factor Int64_t, divisor Int64_t) Int64_t {
	var gcd Int64_t = ^factor&(factor-int64(1)) & ^divisor & (divisor-int64(1)) + int64(1)

	return __stime64_scale32_floor(tls, x, int32(factor/gcd), int32(divisor/gcd))
}
```

### d010
```
#[Override]
    public function gcd(string $a, string $b): string
    {
        return gmp_strval(gmp_gcd($a, $b));
    }
```

### d011
```
/**
     * Returns the simplified value of this BigRational.
     *
     * @pure
     */
    public function simplified(): BigRational
    {
        $gcd = $this->numerator->gcd($this->denominator);

        $numerator = $this->numerator->quotient($gcd);
        $denominator = $this->denominator->quotient($gcd);

        return new BigRational($numerator, $denominator, false);
    }
```

### d012
```
// Gcd action undocumented
func (b *WorkbookFunctionsRequestBuilder) Gcd(reqObj *WorkbookFunctionsGcdRequestParameter) *WorkbookFunctionsGcdRequestBuilder {
	bb := &WorkbookFunctionsGcdRequestBuilder{BaseRequestBuilder: b.BaseRequestBuilder}
	bb.BaseRequestBuilder.baseURL += "/gcd"
	bb.BaseRequestBuilder.requestObject = reqObj
	return bb
}
```

### d013
```
// (public) gcd(this,a) (HAC 14.54)
function bnGCD(a) {
  var x = (this.s<0)?this.negate():this.clone();
  var y = (a.s<0)?a.negate():a.clone();
  if(x.compareTo(y) < 0) { var t = x; x = y; y = t; }
  var i = x.getLowestSetBit(), g = y.getLowestSetBit();
  if(g < 0) return x;
  if(i < g) g = i;
  if(g > 0) {
    x.rShiftTo(g,x);
    y.rShiftTo(g,y);
  }
  while(x.signum() > 0) {
    if((i = x.getLowestSetBit()) > 0) x.rShiftTo(i,x);
    if((i = y.getLowestSetBit()) > 0) y.rShiftTo(i,y);
    if(x.compareTo(y) >= 0) {
      x.subTo(y,x);
      x.rShiftTo(1,x);
    }
    else {
      y.subTo(x,y);
      y.rShiftTo(1,y);
    }
  }
  if(g > 0) y.lShiftTo(g,y);
  return y;
}
```

## Output

Return raw JSON only. No preamble, no markdown fences, no commentary outside the
object.

```json
{
  "query_id": "A1",
  "labels": {
    "d001": {"score": 1.0, "rationale": "iterative binary search over sorted array"},
    "d002": {"score": 0.0, "rationale": "pytest case asserting search behaviour, not an implementation"}
  }
}
```

Every `doc_id` presented must appear exactly once in `labels`.
