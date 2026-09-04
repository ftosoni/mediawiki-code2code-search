# Human gold labelling sheet (40 pooled docs)

Score each snippet 1.0 / 0.5 / 0.0 / null, then transcribe the scores into gold_template.json.

## A4:d007  — score: ____

Query:
```
func encodeJSON(v interface{}) ([]byte, error) {
    data, err := json.Marshal(v)
    if err != nil {
        return nil, fmt.Errorf("json encode: %w", err)
    }
    return data, nil
}
```

Candidate:
```
// MarshalJSON is a custom marshal function that knows how to encode Parameter as JSON
func (p *Parameter) MarshalJSON() ([]byte, error) {
	b1, err := json.Marshal(p.Refable)
	if err != nil {
		return nil, err
	}
	b2, err := json.Marshal(p.ParameterProps)
	if err != nil {
		return nil, err
	}
	b3, err := json.Marshal(p.VendorExtensible)
	if err != nil {
		return nil, err
	}
	return swag.ConcatJSON(b1, b2, b3), nil
}
```

---

## B8:d005  — score: ____

Query:
```
public function verifyCaptcha(string $token,
                              string $userAnswer): bool {
    $expected = $this->store->get($token);
    if ($expected === null) return false;
    $this->store->delete($token);
    return hash_equals($expected, strtolower(trim($userAnswer)));
}
```

Candidate:
```
protected function accept( $expected ) {
		if ( !is_array( $expected ) ) {
			$expected = array( $expected );
		}

		$this->nextToken();
		$got = is_array( $this->token ) ? $this->token[0] : $this->token;
		if ( in_array( $got, $expected, true ) ) {
			return true;
		}

		$this->i -= 2;
		$this->nextToken();
		return false;
	}
```

---

## B3:d013  — score: ____

Query:
```
public function invalidateUserSession(User $user): void {
    $user->setToken();
    $user->saveSettings();
    SessionManager::singleton()->invalidateSessionsForUser($user);
}
```

Candidate:
```
/**
 * @covers \InvalidateUserSessions
 * @group Database
 * @author Dreamy Jazz
 */
class InvalidateUserSessionsTest extends MaintenanceBaseTestCase {
	public function getMaintenanceClass() {
		return InvalidateUserSessions::class;
	}

	/** @dataProvider provideExecuteForFatalError */
	public function testExecuteForFatalError( $options, $expectedOutputRegex ) {
		$this->expectCallToFatalError();
		foreach ( $options as $name => $value ) {
			$this->maintenance->setOption( $name, $value );
		}
		$this->maintenance->execute();
		$this->expectOutputRegex( $expectedOutputRegex );
	}

	public static function provideExecuteForFatalError() {
		return [
			'No options provided' => [ [], '/Either --user or --file is required/' ],
			'Both user and file provided' => [
				[ 'user' => 'test', 'file' => 'test' ], '/Cannot use both --user and --file/',
			],
			'Filename is not valid' => [
				[ 'file' => '/test/invalidpath/testing' ],
				'/Could not open ' . preg_quote( '/test/invalidpath/testing', '/' ) . '/',
			],
		];
	}

	/** @dataProvider provideExecute */
	public function testExecute( $options, $expectedUsernames, $expectedOutputString ) {
		// Mock the SessionManager service to expect calls to ::invalidateSessionsForUser
		$mockSessionManager = $this->createMock( SessionManager::class );
		$mockSessionManager->expects( $this->exactly( count( $expectedUsernames ) ) )
			->method( 'invalidateSessionsForUser' )
			->willReturnCallback( function ( $actualUser ) use ( $expectedUsernames ) {
				$this->assertContains( $actualUser->getName(), $expectedUsernames );
			} );
		$this->setService( 'SessionManager', $mockSessionManager );
		// Run the maintenance script
		foreach ( $options as $name => $value ) {
			$this->maintenance->setOption( $name, $value );
		}
		$this->maintenance->execute();
		$this->expectOutputString( $expectedOutputString );
	}

	public static function provideExecute() {
		return [
			'User argument for non-existing user' => [
				[ 'user' => 'Non-existing test user' ],
				[ 'Non-existing test user' ],
				"Could not find user Non-existing test user, tried to invalidate anyway\n",
			],
		];
	}

	public function testExecuteForFileOfUsernames() {
		$testUser1 = $this->getTestUser()->getUserIdentity();
		$testUser2 = $this->getTestSysop()->getUserIdentity();
		$testFilename = $this->getNewTempFile();
		file_put_contents( $testFilename, "Non-existing test user\n$testUser1\n$testUser2" );
		$this->testExecute(
			[ 'file' => $testFilename, 'batch-size' => 1 ],
			[ 'Non-existing test user', $testUser1->getName(), $testUser2->getName() ],
			"Could not find user Non-existing test user, tried to invalidate anyway\n" .
			"Invalidated sessions for user $testUser1\nInvalidated sessions for user $testUser2\n",
		);
	}

	public function testExecuteForThrownException() {
		// Mock the SessionManager service to throw an error when ::invalidateSessionsForUser is called.
		$mockSessionManager = $this->createMock( SessionManager::class );
		$mockSessionManager->method( 'invalidateSessionsForUser' )
			->willThrowException( new RuntimeException( "Testing\nTest" ) );
		$this->setService( 'SessionManager', $mockSessionManager );
		// Run the maintenance script
		$this->maintenance->setOption( 'user', 'Testing' );
		$this->maintenance->execute();
		$this->expectOutputString( "Failed to invalidate sessions for user Testing | Testing Test\n" );
	}
}
```

---

## C3:d008  — score: ____

Query:
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

Candidate:
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

---

## D1:d004  — score: ____

Query:
```
public function extractWikiLinks(string $wikitext): array {
    $links = [];
    if (preg_match_all(
            '/\[\[([^|\]]+)(?:\|[^\]]+)?\]\]/', $wikitext, $m)) {
        foreach ($m[1] as $target) {
            $links[] = Title::newFromText(trim($target));
        }
    }
    return array_filter($links);
}
```

Candidate:
```
/**
	 * Examines a wikitext string and finds users that were mentioned
	 * @param string $wikitext
	 * @return User[]
	 */
	protected function getMentionedUsersFromWikitext( $wikitext ) {
		$title = Title::newMainPage(); // Bogus title used for parser

		$options = ParserOptions::newFromAnon();

		$output = MediaWikiServices::getInstance()->getParser()
			->parse( $wikitext, $title, $options );

		$users = [];
		foreach ( $output->getLinkList( ParserOutputLinkTypes::LOCAL, NS_USER )
				  as [ 'link' => $link ] ) {
			$user = User::newFromName( $link->getDBkey() );
			if ( !$user || !$user->isRegistered() ) {
				continue;
			}

			$users[$user->getId()] = $user;
		}

		return $users;
	}
```

---

## B8:d003  — score: ____

Query:
```
public function verifyCaptcha(string $token,
                              string $userAnswer): bool {
    $expected = $this->store->get($token);
    if ($expected === null) return false;
    $this->store->delete($token);
    return hash_equals($expected, strtolower(trim($userAnswer)));
}
```

Candidate:
```
public function verify( OATHUser $user, array $data ): bool {
		global $wgOATHAuthWindowRadius;

		$token = $data['token'] ?? '';

		if ( $this->secret['mode'] !== 'hotp' ) {
			// @codeCoverageIgnoreStart
			throw new DomainException( 'OATHAuth extension does not support non-HOTP tokens' );
			// @codeCoverageIgnoreEnd
		}

		// Prevent replay attacks
		$services = MediaWikiServices::getInstance();
		$store = $services->getMainObjectStash();

		if ( $store instanceof EmptyBagOStuff ) {
			// @codeCoverageIgnoreStart
			// Try and find some usable cache if the MainObjectStash isn't useful
			$store = $services->getObjectCacheFactory()->getLocalServerInstance( CACHE_ANYTHING );
			// @codeCoverageIgnoreEnd
		}

		$key = $store->makeKey( 'oathauth-totp', 'usedtokens', $user->getCentralId() );
		$lastWindow = (int)$store->get( $key );

		$results = HOTP::generateByTimeWindow(
			Base32::decode( $this->secret['secret'] ),
			$this->secret['period'],
			-$wgOATHAuthWindowRadius,
			$wgOATHAuthWindowRadius,
			(int)ConvertibleTimestamp::now( TimestampFormat::UNIX )
		);

		// Remove any whitespace from the received token, which can be an intended group separator
		$token = preg_replace( '/\s+/', '', $token );

		$clientIP = RequestContext::getMain()->getRequest()->getIP();

		$logger = $this->getLogger();

		// Check to see if the user's given token is in the list of tokens generated
		// for the time window.
		foreach ( $results as $window => $result ) {
			if ( $window <= $lastWindow || !hash_equals( $result->toHOTP( 6 ), $token ) ) {
				continue;
			}

			$lastWindow = $window;

			$logger->info( 'OATHAuth user {user} entered a valid OTP from {clientip}', [
				'user' => $user->getAccount(),
				'clientip' => $clientIP,
			] );

			$store->set(
				$key,
				$lastWindow,
				$this->secret['period'] * ( 1 + 2 * $wgOATHAuthWindowRadius )
			);

			return true;
		}

		return false;
	}
```

---

## B10:d015  — score: ____

Query:
```
private function getDescendants(int $catId, int $depth = 0): array {
    if ($depth > $this->maxDepth) return [];
    $children = $this->db->selectFieldValues(
        'categorylinks', 'cl_from',
        ['cl_to' => $catId, 'cl_type' => 'subcat']
    );
    $result = $children;
    foreach ($children as $child) {
        $result = array_merge(
            $result, $this->getDescendants($child, $depth + 1)
        );
    }
    return $result;
}
```

Candidate:
```
/**
	 * This function handles adding the children of the nodes in the Top Category tree.
	 * Also, it determines whether or not the node is selected depending on $cur_values
	 * @param array $children
	 * @param int $level
	 * @param int $depth
	 * @param array $cur_values
	 * @return array
	 */
	public static function addSubCategories( $children, $level, $depth, $cur_values ) {
		$newChildren = [];
		foreach ( $children as $child ) {
			$is_selected = false;
			if ( $cur_values !== null ) {
				if ( in_array( $child->title, $cur_values ) ) {
					$is_selected = true;
					unset( $cur_values[ array_search( $child->title, $cur_values ) ] );
				}
			}

			$newChild = [
				'text' => $child->title,
				'level' => $level,
				'children' => self::addSubCategories( $child->children, $level + 1, $depth, $cur_values )
			];
			$newChild['state']['opened'] = $level <= $depth;
			if ( $is_selected ) {
				$newChild['state']['selected'] = true;
			}
			$newChildren[] = $newChild;
		}
		return $newChildren;
	}
```

---

## B5:d008  — score: ____

Query:
```
public function isRateLimited(string $action, UserIdentity $user): bool {
    $key = $this->makeKey($action, $user->getId());
    $count = $this->cache->get($key) ?? 0;
    return $count >= ($this->limits[$action] ?? PHP_INT_MAX);
}
```

Candidate:
```
/**
	 * Checks, if the user reached the number of false CAPTCHAs and give him some vacation
	 * or run self::passCaptcha() and clear counter if correct.
	 *
	 * @param string|null $index Captcha identifier
	 * @param string|null $word Captcha solution
	 * @param User $user User for throttling captcha solving attempts
	 * @return bool
	 * @see self::passCaptcha()
	 */
	public function passCaptchaLimited( $index, $word, User $user ) {
		// don't increase pingLimiter here, just check, if CAPTCHA limit exceeded
		if ( $user->pingLimiter( 'badcaptcha', 0 ) ) {
			// for debugging add a proper error message, the user will just see a false captcha error message
			$this->log( 'User reached RateLimit, preventing action' );
			return false;
		}

		if ( $this->passCaptcha( $index, $word, $user ) ) {
			return true;
		}

		// captcha was not solved: increase the limit and return false
		$user->pingLimiter( 'badcaptcha' );
		return false;
	}
```

---

## C5:d002  — score: ____

Query:
```
-- Lua
local function serialize(val, indent)
    indent = indent or 0
    if type(val) == "table" then
        local parts = {}
        for k, v in pairs(val) do
            parts[#parts+1] = string.rep("  ", indent+1)
                .. tostring(k) .. " = " .. serialize(v, indent+1)
        end
        return "{\n" .. table.concat(parts, ",\n")
            .. "\n" .. string.rep("  ", indent) .. "}"
    end
    return tostring(val)
end
```

Candidate:
```
/**
 * Converts PHP data into a Lua (Scribunto) module
 */
class LuaSerializer implements LoggerAwareInterface {

	use LoggerAwareTrait;

	private const RESERVED = [
		'and', 'break', 'do', 'else', 'elseif',
		'end', 'false', 'for', 'function', 'if',
		'in', 'local', 'nil', 'not', 'or',
		'repeat', 'return', 'then', 'true', 'until', 'while'
	];

	public function __construct() {
		$this->logger = new NullLogger();
	}

	/**
	 * Convert JSON data into a Lua module. The return from the call is suitable
	 * for writing to a Module: namespace page and loading with mw.loadData.
	 * @param array $stuff
	 * @return string
	 */
	public function serialize( array $stuff ) {
		return 'return ' . $this->convertToLua( $stuff );
	}

	/**
	 * Convert to an unquoted name if possible, otherwise do normal string.
	 *
	 * @param string $stuff
	 * @return bool
	 */
	private function convertToLuaIdentifier( $stuff ) {
		if (
			is_string( $stuff ) &&
			preg_match( "/^[a-zA-Z][a-zA-Z0-9_]*$/", $stuff ) &&
			!in_array( $stuff, self::RESERVED )
		) {
			return $stuff;
		} else {
			return '[' . $this->convertToLua( $stuff ) . ']';
		}
	}

	/**
	 * Convert JSON data into a Lua table.
	 * @param array|string|int|float|bool|null $stuff
	 * @param int $level Indentation level
	 * @return string
	 */
	protected function convertToLua( $stuff, $level = 1 ) {
		if ( is_string( $stuff ) ) {
			return '"' . addcslashes( $stuff, "\0..\37\"\\" ) . '"';
		}

		if ( is_int( $stuff ) || is_float( $stuff ) ) {
			return (string)$stuff;
		}
		if ( is_bool( $stuff ) ) {
			return $stuff ? 'true' : 'false';
		}
		if ( $stuff === null ) {
			return 'nil';
		}

		if ( is_array( $stuff ) ) {
			$out = "{\n";
			// Bit hacky, try and figure out if it is numeric array.
			if ( isset( $stuff[0] ) && isset( $stuff[count( $stuff ) - 1] ) ) {
				foreach ( $stuff as $value ) {
					$out .= $this->convertToLua( $value ) . ',';
				}
			} else {
				foreach ( $stuff as $key => $value ) {
					// $out .= str_repeat( "\t", $level );
					if ( is_int( $key ) ) {
						// lua is 1-based.
						$key++;
					}
					$out .= $this->convertToLuaIdentifier( $key ) . '='
						. $this->convertToLua( $value, $level + 1 ) . ",\n";
				}
			}
			// We are running out of space, don't pretty print.
			// $out .= str_repeat( "\t", $level - 1 );
			$out .= "}";
			return $out;
		}
		$this->logger->error( "$stuff is invalid type" );
		die();
	}

}
```

---

## A3:d011  — score: ____

Query:
```
function truncateString(string $str, int $maxLen,
                        string $ellipsis = '...'): string {
    if (mb_strlen($str) <= $maxLen) {
        return $str;
    }
    return mb_substr($str, 0, $maxLen - mb_strlen($ellipsis)) . $ellipsis;
}
```

Candidate:
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

---

## C2:d004  — score: ____

Query:
```
def parse_iso_date(date_str: str) -> datetime:
    return datetime.fromisoformat(
        date_str.replace('Z', '+00:00')
    )
```

Candidate:
```
def _from_iso8601(cls, timestr: str) -> Timestamp:
        """Convert a string in ISO8601 format to a Timestamp object.

        ISO8601 format:
        ``YYYY-MM-DD[T ]HH:MM:SS[[.,]ffffff][Z|±HH[MM[SS[.ffffff]]]]``

        .. version-added:: 7.5
        """
        RE_ISO8601 = (r'(?:\d{4}-\d{2}-\d{2})(?P<sep>[T ])'  # noqa: N806
                      r'(?:\d{2}:\d{2}:\d{2})(?P<u>[.,]\d{1,6})?'
                      r'(?P<tz>Z|[+\-]\d{2}:?\d{,2})?'
                      )
        m = re.fullmatch(RE_ISO8601, timestr)

        if not m:
            raise ValueError(
                f'time data {timestr!r} does not match ISO8601 format.')

        strpfmt = f'%Y-%m-%d{m["sep"]}%H:%M:%S'
        strpstr = timestr[:19]

        if m['u']:
            strpfmt += '.%f'
            strpstr += m['u'].replace(',', '.')  # .ljust(7, '0')

        if m['tz']:
            if m['tz'] == 'Z':
                strpfmt += 'Z'
                strpstr += 'Z'
            else:
                strpfmt += '%z'
                # strptime wants HHMM, without ':'
                strpstr += (m['tz'].replace(':', '')).ljust(5, '0')

        ts = cls.strptime(strpstr, strpfmt)
        if ts.tzinfo is not None:
            ts = ts.astimezone(datetime.timezone.utc).replace(tzinfo=None)

        return ts
```

---

## C5:d017  — score: ____

Query:
```
-- Lua
local function serialize(val, indent)
    indent = indent or 0
    if type(val) == "table" then
        local parts = {}
        for k, v in pairs(val) do
            parts[#parts+1] = string.rep("  ", indent+1)
                .. tostring(k) .. " = " .. serialize(v, indent+1)
        end
        return "{\n" .. table.concat(parts, ",\n")
            .. "\n" .. string.rep("  ", indent) .. "}"
    end
    return tostring(val)
end
```

Candidate:
```
function linkedwiki.print_r ( t )
    local print_r_cache={}
    local function sub_print_r(t,indent)
            if (type(t)=="table") then
                for pos,val in pairs(t) do
                    if (type(val)=="table") then
                        mw.log(indent.."["..pos.."] => "..tostring(t).." {")
                        sub_print_r(val,indent..string.rep(" ",string.len(pos)+8))
                        mw.log(indent..string.rep(" ",string.len(pos)+6).."}")
                    else
                        mw.log(indent.."["..pos.."] => "..tostring(val))
                    end
                end
            else
                mw.log(indent..tostring(t))
            end
    end
    sub_print_r(t,"  ")
end
```

---

## B11:d009  — score: ____

Query:
```
def fetch_all_pages(endpoint, params, page_size=50):
    results, offset = [], 0
    while True:
        params.update({'limit': page_size, 'offset': offset})
        batch = requests.get(endpoint, params=params).json()
        if not batch:
            break
        results.extend(batch)
        offset += page_size
    return results
```

Candidate:
```
/**
 * @param {"draft"|"published"} status
 * @param {string|null} offset
 * @return {Promise<Translation[]>}
 */
async function fetchTranslations(status, offset = null) {
  if (mw.user.isAnon()) {
    return Promise.resolve([]);
  }
  const params = {
    action: "query",
    format: "json",
    assert: "user",
    formatversion: 2,
    list: "contenttranslation",
    usecase: "unified-dashboard",
    type: status,
  };

  if (offset) {
    params["offset"] = offset;
  }

  const api = new mw.Api();

  return api.get(params).then(async (response) => {
    const apiResponse = response.query.contenttranslation.translations;
    let results;

    if (status === "draft") {
      results = apiResponse.map(
        (item) => new DraftTranslation({ ...item, status })
      );
    } else {
      results = apiResponse.map(
        (item) => new PublishedTranslation({ ...item, status })
      );
    }

    if (response.continue?.offset) {
      const restOfResults = await fetchTranslations(
        status,
        response.continue.offset
      );
      results = results.concat(restOfResults);
    }

    return results;
  });
}
```

---

## C4:d014  — score: ____

Query:
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

Candidate:
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

---

## D3:d019  — score: ____

Query:
```
def parse_irc_message(raw: str) -> dict:
    prefix, command, params = None, None, []
    if raw.startswith(':'):
        prefix, raw = raw[1:].split(' ', 1)
    parts = raw.split(' ', 1)
    command = parts[0]
    if len(parts) > 1:
        ti = parts[1].find(' :')
        if ti >= 0:
            params = parts[1][:ti].split()
            params.append(parts[1][ti+2:])
        else:
            params = parts[1].split()
    return {'prefix': prefix, 'command': command, 'params': params}
```

Candidate:
```
def parse_headers(message):
    """
    Turn a Message object into a list of WSGI-style headers.
    """
    headers_out = []        
    for full_header in message.headers:
        if not full_header:            
            # Shouldn't happen, but we'll just ignore
            continue                     
        if full_header[0].isspace():
            # Continuation line, add to the last header
            if not headers_out:                        
                raise ValueError(
                    "First header starts with a space (%r)" % full_header)
            last_header, last_value = headers_out.pop()                   
            value = last_value + ' ' + full_header.strip()
            headers_out.append((last_header, value))      
            continue                                
        try:        
            header, value = full_header.split(':', 1)
        except:                                      
            raise ValueError("Invalid header: %r" % full_header)
        value = value.strip()                                   
        if header.lower() not in filtered_headers:
            headers_out.append((header, value))   
    return headers_out
```

---

## B4:d005  — score: ____

Query:
```
def evict_oldest(cache: dict, max_size: int) -> None:
    while len(cache) > max_size:
        oldest_key = next(iter(cache))
        del cache[oldest_key]
```

Candidate:
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

---

## D3:d009  — score: ____

Query:
```
def parse_irc_message(raw: str) -> dict:
    prefix, command, params = None, None, []
    if raw.startswith(':'):
        prefix, raw = raw[1:].split(' ', 1)
    parts = raw.split(' ', 1)
    command = parts[0]
    if len(parts) > 1:
        ti = parts[1].find(' :')
        if ti >= 0:
            params = parts[1][:ti].split()
            params.append(parts[1][ti+2:])
        else:
            params = parts[1].split()
    return {'prefix': prefix, 'command': command, 'params': params}
```

Candidate:
```
def _format_jenkins_message(body: str) -> Tuple[str, List[str], Optional[str]]:
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    if not lines:
        return "(no details)", [], None
    status_emoji: Optional[str] = None
    first = lines[0]
    if "verified" in first.lower():
        status_emoji = _jenkins_status_emoji(first)
        lines = lines[1:]
    lines = _drop_patch_prefix(lines)
    if not lines:
        return first, [], status_emoji
    action = lines[0]
    remainder = lines[1:]
    return action, remainder, status_emoji
```

---

## B4:d009  — score: ____

Query:
```
def evict_oldest(cache: dict, max_size: int) -> None:
    while len(cache) > max_size:
        oldest_key = next(iter(cache))
        del cache[oldest_key]
```

Candidate:
```
function del (cache, key, opts = {}) {
  if (!opts.removeFully)
    return insert(cache, key, null, opts)

  const bucket = bucketPath(cache, key)
  return rimraf(bucket)
}
```

---

## C4:d001  — score: ____

Query:
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

Candidate:
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

---

## D1:d002  — score: ____

Query:
```
public function extractWikiLinks(string $wikitext): array {
    $links = [];
    if (preg_match_all(
            '/\[\[([^|\]]+)(?:\|[^\]]+)?\]\]/', $wikitext, $m)) {
        foreach ($m[1] as $target) {
            $links[] = Title::newFromText(trim($target));
        }
    }
    return array_filter($links);
}
```

Candidate:
```
/**
	 * Returns an array of title objects that are used as templates in the given Wikitext.
	 * @param string $wikitext Wiki markup
	 * @return array Title objects
	 */
	public function getTemplateTitles( $wikitext ) {
		# not very sophisticated but only used for lockout prevention
		$regex = '|{{:(.*?)}}|';
		$matches = [];
		preg_match_all( $regex, $wikitext, $matches );
		$templateTitles = [];
		foreach ( $matches[1] as $templateTitleText ) {
			$tmpTitle = Title::newFromText( $templateTitleText );
			if ( $tmpTitle !== null ) {
				$templateTitles[] = $tmpTitle;
			}
		}
		return $templateTitles;
	}
```

---

## B10:d003  — score: ____

Query:
```
private function getDescendants(int $catId, int $depth = 0): array {
    if ($depth > $this->maxDepth) return [];
    $children = $this->db->selectFieldValues(
        'categorylinks', 'cl_from',
        ['cl_to' => $catId, 'cl_type' => 'subcat']
    );
    $result = $children;
    foreach ($children as $child) {
        $result = array_merge(
            $result, $this->getDescendants($child, $depth + 1)
        );
    }
    return $result;
}
```

Candidate:
```
/**
	 * @param array $nodes
	 */
	private function getSubCategoriesFromPath( array $nodes ) {
		if ( $this->detectRecursion( $nodes ) ) {
			$dupes = $nodes;
			$dupes = array_unique( $dupes );
			sort( $dupes );
			$this->dupes[implode( '|', $dupes )] = $nodes;
			return;
		}
		$last = end( $nodes );
		$subcategories = $this->getSubCategoriesFromDB( $last );
		foreach ( $subcategories as $subcat ) {
			$this->getSubCategoriesFromPath( array_merge( $nodes, [ $subcat ] ) );
		}
	}
```

---

## C2:d006  — score: ____

Query:
```
def parse_iso_date(date_str: str) -> datetime:
    return datetime.fromisoformat(
        date_str.replace('Z', '+00:00')
    )
```

Candidate:
```
def extract_since(response):
    json_response = response.json()
    date_str = json_response['_source']['timestamp']
    date = datetime.utcfromtimestamp(date_str, )
    lag = datetime.utcnow() - date
    return lag
```

---

## D4:d001  — score: ____

Query:
```
public function run(string $hook, array $args = []): bool {
    foreach ($this->getHandlers($hook) as $handler) {
        $ret = $handler(...$args);
        if ($ret === false) {
            return false;
        }
    }
    return true;
}
```

Candidate:
```
class PlainLabelRenderer implements LabelRenderer {
	/**
	 * @inheritDoc
	 */
	public function render_label( string $input, string $for, array $args ) : string {
		//if ( isset( $args['style'] ) ) {
		if ( !empty( $for ) ) {
			$args['for'] = $for;
		}
		$ret         = '<label ';
		foreach ( $args as $k => $v ) {
			$ret .= $k . '="' . $v . '" ';
		}
		$ret .= '>' . $input . '</label>';
		return $ret;
			/*} else {
				return trim( Xml::label(
					$input,
					$for,
					$args
				) );
			}*/
	}
}
```

---

## A3:d005  — score: ____

Query:
```
function truncateString(string $str, int $maxLen,
                        string $ellipsis = '...'): string {
    if (mb_strlen($str) <= $maxLen) {
        return $str;
    }
    return mb_substr($str, 0, $maxLen - mb_strlen($ellipsis)) . $ellipsis;
}
```

Candidate:
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

---

## D4:d003  — score: ____

Query:
```
public function run(string $hook, array $args = []): bool {
    foreach ($this->getHandlers($hook) as $handler) {
        $ret = $handler(...$args);
        if ($ret === false) {
            return false;
        }
    }
    return true;
}
```

Candidate:
```
/**
	 * getDurationIntervals handler
	 * @param Language $lang
	 * @param array $args
	 * @return array
	 */
	private function getDurationIntervals( $lang, $args ) {
		$this->checkType( 'getDurationIntervals', 1, $args[0], 'number' );
		$this->checkTypeOptional( 'getDurationIntervals', 2, $args[1], 'table', [] );

		[ $seconds, $chosenIntervals ] = $args;
		$chosenIntervals = array_values( $chosenIntervals );

		$ret = $lang->getDurationIntervals( $seconds, $chosenIntervals );
		return [ $ret ];
	}
```

---

## B2:d010  — score: ____

Query:
```
function delayExecution(fn, waitMs) {
    let timer;
    return function (...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), waitMs);
    };
}
```

Candidate:
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

---

## A3:d015  — score: ____

Query:
```
function truncateString(string $str, int $maxLen,
                        string $ellipsis = '...'): string {
    if (mb_strlen($str) <= $maxLen) {
        return $str;
    }
    return mb_substr($str, 0, $maxLen - mb_strlen($ellipsis)) . $ellipsis;
}
```

Candidate:
```
function truncate(string $str, int $length) : string {
	assert($length >= 0);
	
	return strlen($str) > $length ? substr($str, 0, $length) . '...' : $str;
}
```

---

## A3:d012  — score: ____

Query:
```
function truncateString(string $str, int $maxLen,
                        string $ellipsis = '...'): string {
    if (mb_strlen($str) <= $maxLen) {
        return $str;
    }
    return mb_substr($str, 0, $maxLen - mb_strlen($ellipsis)) . $ellipsis;
}
```

Candidate:
```
function ellipsis($str, $len = 50) {
    return strlen($str) > $len ? substr($str, 0, $len) . '...' : $str;
}
```

---

## A2:d003  — score: ____

Query:
```
function binarySearch(arr, target) {
    let lo = 0, hi = arr.length - 1;
    while (lo <= hi) {
        const mid = (lo + hi) >> 1;
        if (arr[mid] === target) return mid;
        if (arr[mid] < target) lo = mid + 1;
        else hi = mid - 1;
    }
    return -1;
}
```

Candidate:
```
/**
 * Searches the specified Array for the provided key using the binary
 * search algorithm.  The Array must be sorted.
 * @param {Array} arr
 * @param key
 * @param {function} compareFunc
 * @returns {number} The position of the key in the Array, if it is found.
 * If it is not found, it returns a negative number which is the bitwise complement of the index of the first element that is larger than key.
 */
function binarySearch(arr, key, compareFunc) {
  var low = 0;
  var high = arr.length-1;

  while (low <= high) {
    var mid = (low + high) >>> 1;
    var midVal = arr[mid];
    var cmp = compareFunc(midVal, key);
    if (cmp < 0) {
      low = mid + 1;
    }
    else if (cmp > 0) {
      high = mid - 1;
    }
    else
    {
      //The key was found in the Array
      return mid;
    }
  }
  return ~low;  // key not found
}
```

---

## B11:d008  — score: ____

Query:
```
def fetch_all_pages(endpoint, params, page_size=50):
    results, offset = [], 0
    while True:
        params.update({'limit': page_size, 'offset': offset})
        batch = requests.get(endpoint, params=params).json()
        if not batch:
            break
        results.extend(batch)
        offset += page_size
    return results
```

Candidate:
```
def works_list(author_id):
    try:
        page = request.args.get("page", 1, type=int)

        # Ensure page is at least 1
        if page < 1:
            page = 1

        # Calculate offset for pagination (50 items per page)
        page_size = 50
        offset = (page - 1) * page_size

        # To show the query link at the top of the results 
        query = squeries.query_for_works_by_an_author.format(qname=author_id, lang=languages.get_locale(), 
                                                             limit_clause="", offset_clause="")
        wqs_link = "https://query.wikidata.org/#" + requests.utils.quote(query)

        author = pdclasses.Author(author_id)

        search_result, complete, continue_offset, results_quantity = author.getWorks(limit=page_size, offset=offset)

        if results_quantity > 10000:
            results_quantity = 10000
            
        page_range = {"start": offset + 1, 
                      "end": offset + page_size if (offset + page_size) <= results_quantity else results_quantity}

        has_next = continue_offset is not None
        has_prev = page > 1

        return render_template("works-list.html",
            title=_('List of works') + " - " + print_field(author.name),
            author_name=print_field(author.name),
            wqs_link=wqs_link,
            author_works=search_result,
            complete=complete,
            results_quantity=results_quantity,
            page_range=page_range,
            page=page,
            has_next=has_next,
            has_prev=has_prev
        )

    except:  # If the Q number doesn't match any item or the item is not about a human
        abort(404)
```

---

## A4:d009  — score: ____

Query:
```
func encodeJSON(v interface{}) ([]byte, error) {
    data, err := json.Marshal(v)
    if err != nil {
        return nil, fmt.Errorf("json encode: %w", err)
    }
    return data, nil
}
```

Candidate:
```
// Encode writes the JSON encoding of v to the stream,
// followed by a newline character.
//
// See the documentation for Marshal for details about the
// conversion of Go values to JSON.
func (enc *Encoder) Encode(v interface{}) error {
	if enc.err != nil {
		return enc.err
	}
	e := newEncodeState()
	err := e.marshal(v, encOpts{escapeHTML: enc.escapeHTML})
	if err != nil {
		return err
	}

	// Terminate each value with a newline.
	// This makes the output look a little nicer
	// when debugging, and some kind of space
	// is required if the encoded value was a number,
	// so that the reader knows there aren't more
	// digits coming.
	e.WriteByte('\n')

	b := e.Bytes()
	if enc.indentPrefix != "" || enc.indentValue != "" {
		if enc.indentBuf == nil {
			enc.indentBuf = new(bytes.Buffer)
		}
		enc.indentBuf.Reset()
		err = Indent(enc.indentBuf, b, enc.indentPrefix, enc.indentValue)
		if err != nil {
			return err
		}
		b = enc.indentBuf.Bytes()
	}
	if _, err = enc.w.Write(b); err != nil {
		enc.err = err
	}
	encodeStatePool.Put(e)
	return err
}
```

---

## B4:d001  — score: ____

Query:
```
def evict_oldest(cache: dict, max_size: int) -> None:
    while len(cache) > max_size:
        oldest_key = next(iter(cache))
        del cache[oldest_key]
```

Candidate:
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

---

## C6:d009  — score: ____

Query:
```
def run_sparql(query: str,
               endpoint: str = 'https://query.wikidata.org/sparql'
              ) -> list:
    resp = requests.get(
        endpoint,
        params={'query': query, 'format': 'json'},
        headers={'User-Agent': 'EvalBot/1.0'}
    )
    resp.raise_for_status()
    return resp.json()['results']['bindings']
```

Candidate:
```
def get_abstract_pages():
    qpoffset = None

    while True:
        params = {
            "action": "query",
            "list": "querypage",
            "qppage": "UnconnectedPages",
            "qplimit": "50",
            "format": "json"
        }

        if qpoffset:
            params["qpoffset"] = qpoffset

        resp = S_ab.get("https://abstract.wikipedia.org/w/api.php", params=params).json()

        for page in resp["query"]["querypage"]["results"]:
            if page["ns"] == 0:
                yield page["title"]

        if "continue" not in resp:
            break

        qpoffset = resp["continue"]["qpoffset"]
```

---

## B12:d002  — score: ____

Query:
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

Candidate:
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

---

## B12:d013  — score: ____

Query:
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

Candidate:
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

---

## D4:d008  — score: ____

Query:
```
public function run(string $hook, array $args = []): bool {
    foreach ($this->getHandlers($hook) as $handler) {
        $ret = $handler(...$args);
        if ($ret === false) {
            return false;
        }
    }
    return true;
}
```

Candidate:
```
/**
	 * Register hook and handler, allowing for easy removal.
	 * Intended for use in temporary registration e.g. testing
	 *
	 * @param string $hook Name of hook
	 * @param callable|string|array $handler Handler to attach
	 */
	#[\NoDiscard]
	public function scopedRegister( string $hook, $handler ): ScopedCallback {
		$handler = $this->normalizeHandler( $hook, $handler );
		if ( !$handler ) {
			throw new InvalidArgumentException( 'Bad hook handler!' );
		}

		$this->checkDeprecation( $hook, $handler );

		$id = 'TemporaryHook_' . $this->nextScopedRegisterId++;

		$this->getHandlers( $hook );

		$this->handlers[$hook][$id] = $handler;

		return new ScopedCallback( function () use ( $hook, $id ) {
			unset( $this->handlers[$hook][$id] );
		} );
	}
```

---

## B9:d008  — score: ____

Query:
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

Candidate:
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

---

## A5:d010  — score: ____

Query:
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

Candidate:
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

---

## B7:d003  — score: ____

Query:
```
def make_slug(title: str) -> str:
    slug = title.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_-]+', '-', slug)
    return slug.strip('-')
```

Candidate:
```
/**
	 * @param string $title
	 * @return string title text converted MediaWiki-friendly
	 */
	protected static function pageTitleForMW( string $title ): string {
		$title = preg_replace( '/ - [^-]+$/', '', $title );
		$title = preg_replace( '/ /', '_', $title );

		return ltrim( $title, '/' );
	}
```

---

## C1:d006  — score: ____

Query:
```
function computeFileHash(string $filepath): string {
    return hash_file('sha256', $filepath);
}
```

Candidate:
```
/**
	 * Remove executable bit from the file
	 *
	 * @param string $filepath File
	 */
	protected function minusX( string $filepath ): void {
		chmod( $filepath, fileperms( $filepath ) & ~0111 );
	}
```

---

