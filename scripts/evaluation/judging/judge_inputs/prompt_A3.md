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
function truncateString(string $str, int $maxLen,
                        string $ellipsis = '...'): string {
    if (mb_strlen($str) <= $maxLen) {
        return $str;
    }
    return mb_substr($str, 0, $maxLen - mb_strlen($ellipsis)) . $ellipsis;
}
```

## Candidates

### d001
```
private function calculateScore( string $a, string $b ): float {
		similar_text( $a, $b, $similarity );
		$distance = levenshtein( $a, $b );
		$maxLen = max( mb_strlen( $a ), mb_strlen( $b ), 1 );
		$distanceScore = max( 0, 100 - ( $distance / $maxLen ) * 100 );
		$score = max( $similarity, $distanceScore );
		return round( $score, 1 );
	}
```

### d002
```
function truncate($str, $len, $ext='...')
{
    $len -= strlen($ext);
    return strlen($str) > $len ? substr($str, 0, $len) . $ext : $str;
}
```

### d003
```
/**
	 * Internal method used for truncation. This method abstracts text truncation into
	 * one common method, allowing users to provide the length measurement function and
	 * function for finding substring.
	 *
	 * For usages, see truncateForDatabase and truncateForVisual.
	 *
	 * @param string $string String to truncate
	 * @param int $length Maximum length of the final text
	 * @param string $ellipsis String to append to the end of truncated text
	 * @param bool $adjustLength Subtract length of ellipsis from $length
	 * @param callable $measureLength Callable function used for determining the length of text
	 * @param callable $getSubstring Callable function used for getting the substrings
	 *
	 * @return string
	 */
	private function truncateInternal(
		$string, $length, $ellipsis, $adjustLength, callable $measureLength, callable $getSubstring
	) {
		# Check if there is no need to truncate
		if ( $measureLength( $string ) <= abs( $length ) ) {
			return $string; // no need to truncate
		}

		# Use the localized ellipsis character
		if ( $ellipsis == '...' ) {
			$ellipsis = $this->msg( 'ellipsis' )->text();
		}
		if ( $length == 0 ) {
			return $ellipsis; // convention
		}

		$stringOriginal = $string;
		# If ellipsis length is >= $length then we can't apply $adjustLength
		if ( $adjustLength && $measureLength( $ellipsis ) >= abs( $length ) ) {
			$string = $ellipsis; // this can be slightly unexpected
		# Otherwise, truncate and add ellipsis...
		} else {
			$ellipsisLength = $adjustLength ? $measureLength( $ellipsis ) : 0;
			if ( $length > 0 ) {
				$length -= $ellipsisLength;
				$string = $getSubstring( $string, 0, $length ); // xyz...
				$string = rtrim( $string ) . $ellipsis;
			} else {
				$length += $ellipsisLength;
				$string = $getSubstring( $string, $length ); // ...xyz
				$string = $ellipsis . ltrim( $string );
			}
		}

		# Do not truncate if the ellipsis makes the string longer/equal (T24181).
		# This check is *not* redundant if $adjustLength, due to the single case where
		# LEN($ellipsis) > ABS($limit arg); $stringOriginal could be shorter than $string.
		if ( $measureLength( $string ) < $measureLength( $stringOriginal ) ) {
			return $string;
		} else {
			return $stringOriginal;
		}
	}
```

### d004
```
private function trimContent( string $content, int $maxLen = self::MAX_LEN ): string {
		$length = mb_strlen( $content ) - 1;
		$startOff = (int)floor( ( $maxLen / 2 ) - 3 );
		$endOff = (int)floor( ( $maxLen / 2 ) - 3 );

		if ( $length >= $maxLen ) {
			$content = mb_substr( $content, 0, $startOff ) . ' ... ' . mb_substr( $content, $length - $endOff );
		}

		return $content;
	}
```

### d005
```
/**
	 * @param string $text The text to truncate.
	 * @param int $length Maximum number of characters.
	 * @param string $ellipsis String to append to the end of truncated text.
	 * @return string
	 */
	public static function truncateLongText( $text, $length = 150, $ellipsis = '...' ) {
		if ( !is_string( $text ) ) {
			return $text;
		}

		return RequestContext::getMain()->getLanguage()->truncateForVisual( $text, $length, $ellipsis );
	}
```

### d006
```
/**
	 * Truncate a string to a specified length in bytes, appending an optional
	 * string (e.g., for ellipsis)
	 * When an ellipsis isn't needed, using mb_strcut() directly is recommended.
	 *
	 * If $length is negative, the string will be truncated from the beginning
	 *
	 * @since 1.31
	 *
	 * @param string $string String to truncate
	 * @param int $length Maximum length in bytes
	 * @param string $ellipsis String to append to the end of truncated text
	 * @param bool $adjustLength Subtract length of ellipsis from $length
	 *
	 * @return string
	 */
	public function truncateForDatabase( $string, $length, $ellipsis = '...', $adjustLength = true ) {
		return $this->truncateInternal(
			$string, $length, $ellipsis, $adjustLength, 'strlen', 'mb_strcut'
		);
	}
```

### d007
```
/**
	 * Cut a filename if it is too long but keep the extension
	 * @param string $string
	 * @param int $max
	 * @return string
	 */
	public static function cutFilename( string $string, int $max = 100 ): string {
		$length = strlen( $string );
		if ( $length > $max ) {
			$string = substr( $string, $length - $max, $length - 1 );
		}

		return $string;
	}
```

### d008
```
function truncate( str: string, maxLen = 20 ) {
	str = str.replace( /\n/gu, '' );
	if ( str.length > maxLen ) {
		str = str.slice( 0, maxLen - 3 ) + '...';
	}
	return str;
}
```

### d009
```
/**
	 * Truncate a string to a specified number of characters, appending an optional
	 * string (e.g., for ellipsis).
	 *
	 * This provides the multibyte version of truncateForDatabase() method of this class,
	 * suitable for truncation based on number of characters, instead of number of bytes.
	 *
	 * The input should be a raw UTF-8 string, and *NOT* be HTML
	 * escaped. It is not safe to truncate HTML-escaped strings,
	 * because the entity can be truncated! Use ::truncateHtml() if you
	 * need a specific number of HTML-encoded bytes, or
	 * ::truncateForDatabase() if you need a specific number of PHP
	 * bytes.
	 *
	 * If $length is negative, the string will be truncated from the beginning.
	 *
	 * @since 1.31
	 *
	 * @param string $string String to truncate
	 * @param int $length Maximum number of characters
	 * @param string $ellipsis String to append to the end of truncated text
	 * @param bool $adjustLength Subtract length of ellipsis from $length
	 *
	 * @return string
	 */
	public function truncateForVisual( $string, $length, $ellipsis = '...', $adjustLength = true ) {
		// Passing encoding to mb_strlen and mb_substr is optional.
		// Encoding defaults to mb_internal_encoding(), which is set to UTF-8 in Setup.php, so
		// explicit specification of encoding is skipped.
		// Note: Both multibyte methods are callables invoked in truncateInternal.
		return $this->truncateInternal(
			$string, $length, $ellipsis, $adjustLength, 'mb_strlen', 'mb_substr'
		);
	}
```

### d010
```
func shortenString(s string, maxLen int) string {
	// for cleaner, one-line ouput, replace some white-space chars
	// with their escaped version
	s = strings.Replace(s, "\n", `\n`, -1)
	s = strings.Replace(s, "\r", `\r`, -1)
	s = strings.Replace(s, "\t", `\t`, -1)
	if maxLen < 0 {
		return s
	}
	if utf8.RuneCountInString(s) < maxLen {
		return s
	}
	// add "…" to indicate truncation
	return string(append([]rune(s)[:maxLen-3], '…'))
}
```

### d011
```
/**
	 * Truncate a string to a specified length in bytes, appending an optional
	 * string (e.g. for ellipses)
	 *
	 * The database offers limited byte lengths for some columns in the database;
	 * multi-byte character sets mean we need to ensure that only whole characters
	 * are included, otherwise broken characters can be passed to the user
	 *
	 * If $length is negative, the string will be truncated from the beginning
	 *
	 * @param $string String to truncate
	 * @param $length Int: maximum length (including ellipses)
	 * @param $ellipsis String to append to the truncated text
	 * @param $adjustLength Boolean: Subtract length of ellipsis from $length.
	 *	$adjustLength was introduced in 1.18, before that behaved as if false.
	 * @return string
	 */
	function truncate( $string, $length, $ellipsis = '...', $adjustLength = true ) {
		# Use the localized ellipsis character
		if ( $ellipsis == '...' ) {
			$ellipsis = wfMsgExt( 'ellipsis', array( 'escapenoentities', 'language' => $this ) );
		}
		# Check if there is no need to truncate
		if ( $length == 0 ) {
			return $ellipsis; // convention
		} elseif ( strlen( $string ) <= abs( $length ) ) {
			return $string; // no need to truncate
		}
		$stringOriginal = $string;
		# If ellipsis length is >= $length then we can't apply $adjustLength
		if ( $adjustLength && strlen( $ellipsis ) >= abs( $length ) ) {
			$string = $ellipsis; // this can be slightly unexpected
		# Otherwise, truncate and add ellipsis...
		} else {
			$eLength = $adjustLength ? strlen( $ellipsis ) : 0;
			if ( $length > 0 ) {
				$length -= $eLength;
				$string = substr( $string, 0, $length ); // xyz...
				$string = $this->removeBadCharLast( $string );
				$string = $string . $ellipsis;
			} else {
				$length += $eLength;
				$string = substr( $string, $length ); // ...xyz
				$string = $this->removeBadCharFirst( $string );
				$string = $ellipsis . $string;
			}
		}
		# Do not truncate if the ellipsis makes the string longer/equal (bug 22181).
		# This check is *not* redundant if $adjustLength, due to the single case where
		# LEN($ellipsis) > ABS($limit arg); $stringOriginal could be shorter than $string.
		if ( strlen( $string ) < strlen( $stringOriginal ) ) {
			return $string;
		} else {
			return $stringOriginal;
		}
	}
```

### d012
```
function ellipsis($str, $len = 50) {
    return strlen($str) > $len ? substr($str, 0, $len) . '...' : $str;
}
```

### d013
```
/**
	 * @since 3.2
	 *
	 * @param string $firstCol
	 * @param int $indentLen
	 * @param int $expectedSecondColLen
	 *
	 * @return string
	 */
	public function firstCol( string $firstCol, int $indentLen = 0, int $expectedSecondColLen = 0 ): string {
		if ( $indentLen > 0 ) {
			$firstCol = sprintf( "%-{$indentLen}s%s", '', $firstCol );
		}

		$maxLen = self::MAX_LEN;

		if ( $expectedSecondColLen > 0 ) {
			$maxLen -= $expectedSecondColLen;
		}

		$firstCol = $this->trimContent( $firstCol, $maxLen );
		$this->firstColLen = mb_strlen( $firstCol );

		return $firstCol;
	}
```

### d014
```
/**
	 * Returns no more than a requested number of characters, preserving words
	 *
	 * @param string $text Source text to extract from
	 * @param int $requestedLength Maximum number of characters to return
	 * @return string
	 */
	public function getFirstChars( $text, $requestedLength ) {
		if ( $requestedLength <= 0 ) {
			return $text === '' ? '' : $this->ellipsis;
		}

		$length = mb_strlen( $text );
		if ( $length <= $requestedLength ) {
			return $text;
		}

		// This ungreedy pattern always matches, just might return an empty string
		$pattern = '/^[\w\/]*>?/su';
		preg_match( $pattern, mb_substr( $text, $requestedLength ), $m );
		$truncatedText = mb_substr( $text, 0, $requestedLength ) . $m[0];
		if ( $truncatedText === $text ) {
			return $text;
		}

		$truncatedText = $this->tidy( $truncatedText ) . $this->ellipsis;
		return mb_strlen( $truncatedText ) < $length ? $truncatedText : $text;
	}
```

### d015
```
function truncate(string $str, int $length) : string {
	assert($length >= 0);
	
	return strlen($str) > $length ? substr($str, 0, $length) . '...' : $str;
}
```

### d016
```
/**
	 * Get the filter pattern with <b> elements surrounding the searched pattern
	 *
	 * @param stdClass $row
	 * @return string
	 */
	private function getHighlightedPattern( stdClass $row ) {
		if ( $this->searchMode === null ) {
			throw new LogicException( 'Cannot search without a mode.' );
		}
		$maxLen = 50;
		$searchPattern = $this->searchPattern ?? '';
		if ( $this->searchMode === 'LIKE' ) {
			$position = mb_stripos( $row->af_pattern, $searchPattern );
			$length = mb_strlen( $searchPattern );
		} else {
			$regex = '/' . $searchPattern . '/u';
			if ( $this->searchMode === 'IRLIKE' ) {
				$regex .= 'i';
			}

			$matches = [];
			// phpcs:ignore Generic.PHP.NoSilencedErrors.Discouraged
			$check = @preg_match(
				$regex,
				$row->af_pattern,
				$matches
			);
			// This may happen in case of catastrophic backtracking, or regexps matching
			// the empty string.
			if ( $check === false || strlen( $matches[0] ) === 0 ) {
				return htmlspecialchars( mb_substr( $row->af_pattern, 0, 50 ) );
			}

			$length = mb_strlen( $matches[0] );
			$position = mb_strpos( $row->af_pattern, $matches[0] );
		}

		$remaining = $maxLen - $length;
		if ( $remaining <= 0 ) {
			$pattern = '<b>' .
				htmlspecialchars( mb_substr( $row->af_pattern, $position, $maxLen ) ) .
				'</b>';
		} else {
			// Center the snippet on the matched string
			$minoffset = max( $position - round( $remaining / 2 ), 0 );
			$pattern = mb_substr( $row->af_pattern, $minoffset, $maxLen );
			$pattern =
				htmlspecialchars( mb_substr( $pattern, 0, $position - $minoffset ) ) .
				'<b>' .
				htmlspecialchars( mb_substr( $pattern, $position - $minoffset, $length ) ) .
				'</b>' .
				htmlspecialchars( mb_substr(
						$pattern,
						$position - $minoffset + $length,
						$remaining - ( $position - $minoffset + $length )
					)
				);
		}
		return $pattern;
	}
```

## Output

Return raw JSON only. No preamble, no markdown fences, no commentary outside the
object.

```json
{
  "query_id": "A3",
  "labels": {
    "d001": {"score": 1.0, "rationale": "iterative binary search over sorted array"},
    "d002": {"score": 0.0, "rationale": "pytest case asserting search behaviour, not an implementation"}
  }
}
```

Every `doc_id` presented must appear exactly once in `labels`.
