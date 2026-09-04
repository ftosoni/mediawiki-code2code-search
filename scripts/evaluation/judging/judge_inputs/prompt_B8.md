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
public function verifyCaptcha(string $token,
                              string $userAnswer): bool {
    $expected = $this->store->get($token);
    if ($expected === null) return false;
    $this->store->delete($token);
    return hash_equals($expected, strtolower(trim($userAnswer)));
}
```

## Candidates

### d001
```
/**
	 * Recover the value concealed with tokenize(), and delete it from the store.
	 *
	 * @param string $token The random key returned by tokenize().
	 * @param string|array $keyPrefix Namespace in the token store.
	 * @return mixed|false The value, or false if it was not found.
	 */
	public function detokenizeAndDelete( string $token, $keyPrefix ) {
		$key = $this->makeLegacyTokenKey( $keyPrefix, $token );
		$value = $this->detokenize( $token, $keyPrefix );
		if ( $value !== false ) {
			$this->tokenStore->delete( $key );
		}
		return $value;
	}
```

### d002
```
public static function provideGetToken() {
		$secret = 'foo';
		$token = strval( new Token( $secret, '' ) );

		foreach ( [
					  'missing token, not CSRF-safe' => [
						  'params' => [],
						  'body' => [],
						  'expected' => '',
					  ],
					  'missing token, CSRF-safe' => [
						  'params' => [],
						  'body' => [],
						  'safeAgainstCsrf' => true,
						  'expected' => null,
					  ],
					  'body token, not CSRF-safe' => [
						  'params' => [],
						  'body' => [ 'token' => $token ],
						  'expected' => $token,
					  ],
					  'body token, CSRF-safe' => [
						  'params' => [],
						  'body' => [ 'token' => $token ],
						  'safeAgainstCsrf' => true,
						  'expected' => null,
					  ],
					  'param token, not CSRF-safe' => [
						  'params' => [ 'csrf_token' => $token ],
						  'body' => [],
						  'expected' => $token,
					  ],
					  'param token, CSRF-safe' => [
						  'params' => [ 'csrf_token' => $token ],
						  'body' => [],
						  'safeAgainstCsrf' => true,
						  'expected' => null,
					  ],
					  'body and param tokens, not CSRF-safe' => [
						  'params' => [ 'csrf_token' => $token ],
						  'body' => [ 'token' => $token ],
						  'expected' => $token,
					  ],
					  'body and param tokens, CSRF-safe' => [
						  'params' => [ 'csrf_token' => $token ],
						  'body' => [ 'token' => $token ],
						  'safeAgainstCsrf' => true,
						  'expected' => null,
					  ],
				  ] as $name => $test ) {
			yield $name => array_merge( [
				'params' => null,
				'body' => null,
				'secret' => $secret,
				'safeAgainstCsrf' => false,
				'expected' => null,
			], $test );
		}
	}
```

### d003
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

### d004
```
func (r *Lexer) errInvalidToken(expected string) {
	if r.fatalError != nil {
		return
	}
	if r.UseMultipleErrors {
		r.pos = r.start
		r.consume()
		r.SkipRecursive()
		switch expected {
		case "[":
			r.token.delimValue = ']'
			r.token.kind = tokenDelim
		case "{":
			r.token.delimValue = '}'
			r.token.kind = tokenDelim
		}
		r.addNonfatalError(&LexerError{
			Reason: fmt.Sprintf("expected %s", expected),
			Offset: r.start,
			Data:   string(r.Data[r.start:r.pos]),
		})
		return
	}

	var str string
	if len(r.token.byteValue) <= maxErrorContextLen {
		str = string(r.token.byteValue)
	} else {
		str = string(r.token.byteValue[:maxErrorContextLen-3]) + "..."
	}
	r.fatalError = &LexerError{
		Reason: fmt.Sprintf("expected %s", expected),
		Offset: r.pos,
		Data:   str,
	}
}
```

### d005
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

### d006
```
/**
	 * @param string $staticToken
	 * @param \User $user
	 * @return bool
	 */
	protected function checkStaticToken( $staticToken, $user ) {
		$this->oWebDAVTokenizer->setUser( $user );
		return $this->oWebDAVTokenizer->checkStaticToken( $staticToken );
	}
```

### d007
```
private function authenticatedEmailMatcher( array $token ) {
		if ( !isset( $token['email'] ) ) {
			return null;
		}
		if ( !isset( $token['email_verified'] ) || $token['email_verified'] !== true ) {
			return null;
		}
		$db = $this->loadBalancer->getConnection( DB_PRIMARY );

		$s = $db->select(
			'user',
			[ 'user_id' ],
			[
				'user_email' => $token['email'],
				'user_email_authenticated IS NOT NULL',
			],
			__METHOD__
		);

		if ( $s instanceof IResultWrapper && $s->numRows() === 1 ) {
			return User::newFromId( $s->current()->user_id );
		}
		return null;
	}
```

### d008
```
/**
     * Checks if the given string is matched, if so it consumes the token
     * 
     * @param string $expected String to check
     * 
     * @return Token|null
     */
    public function consume($expected)
    {
        //Do not call getToken if there's already a pending token for
        //performance reasons
        $token = $this->currentToken ?: $this->getToken();
        if ($token && $token->value === $expected) {
            $this->consumeToken();
            return $token;
        }
        return null;
    }
```

### d009
```
/**
	 * @param Token $token
	 * @param string|null $location_hintmsg
	 * @throws ExpressionException
	 */
	private function throwUnexpectedTokenError( Token $token, $location_hintmsg = null ) {
		if ( $token->getTokenType() === "T_RIGHTPAREN" ) {
			$expected = new ExceptionMessage( "expressions-expected-value" );

			throw new ExpressionException(
				"expressions-unexpected-token-message",
				[],
				"expressions-unexpected-token-submessage",
				[ $token->getMatch(), $expected ],
				"expressions-unexpected-token-rightparen-hint",
				[],
				$token->getOffset(),
				$token->getOffset() + strlen( $token->getMatch() )
			);
		}

		if ( $location_hintmsg === "expressions-before" ) {
			$expected = "expressions-expected-value-before";
		} else {
			$expected = "expressions-expected-value-after";
		}

		if ( in_array( $token->getTokenType(), self::VALUE_HINT_TOKEN_TYPES ) ) {
			if ( $location_hintmsg !== null ) {
				$location_hint = new ExceptionMessage( $location_hintmsg );
			} else {
				$location_hint = new ExceptionMessage( "expressions-before" );
			}

			$hint = "expressions-unexpected-token-operator-hint";
		} else {
			if ( $location_hintmsg !== null ) {
				$location_hint = new ExceptionMessage( $location_hintmsg );
			} else {
				$location_hint = new ExceptionMessage( "expressions-before" );
			}

			$hint = "expressions-unexpected-token-value-hint";
		}

		throw new ExpressionException(
			"expressions-unexpected-token-message",
			[],
			"expressions-unexpected-token-submessage",
			[ $token->getMatch(), new ExceptionMessage( $expected ) ],
			$hint,
			[ $location_hint ],
			$token->getOffset(),
			$token->getOffset() + strlen( $token->getMatch() )
		);
	}
```

### d010
```
/**
	 * Given a required captcha run, test form input for correct
	 * input on the open session.
	 * @param string|null $index Captcha identifier
	 * @param string|null $word Captcha solution
	 * @param User $user
	 * @return bool if passed, false if failed or new session
	 */
	protected function passCaptcha( $index, $word, $user ) {
		// Don't check the same CAPTCHA twice in one session,
		// if the CAPTCHA was already checked - Bug T94276
		if ( $this->isCaptchaSolved() !== null ) {
			return (bool)$this->isCaptchaSolved();
		}

		if ( $index === null ) {
			$this->log( "new captcha session" );
			// If no captcha ID was passed, we need to start a new session (T384858).
			return false;
		}

		$info = $this->retrieveCaptcha( $index );
		if ( $info ) {
			if ( $this->keyMatch( $word, $info ) ) {
				$this->log( "passed" );
				$this->clearCaptcha( $index );
				$this->setCaptchaSolved( true );
				return true;
			} else {
				$this->clearCaptcha( $index );
				$this->log( "bad form input" );
				$this->setCaptchaSolved( false );
				return false;
			}
		} else {
			$this->log( "new captcha session" );
			return false;
		}
	}
```

### d011
```
/**
     * Checks if one of the given strings is matched, if so it consumes the
     * token
     * 
     * @param array $expected Strings to check
     * 
     * @return Token|null
     */
    public function consumeOneOf($expected)
    {
        //Do not call getToken if there's already a pending token for
        //performance reasons
        $token = $this->currentToken ?: $this->getToken();
        if ($token && in_array($token->value, $expected)) {
            $this->consumeToken();
            return $token;
        }
        return null;
    }
```

### d012
```
/** @inheritDoc */
	public function verify( OATHUser $user, array $data ): bool {
		if ( !isset( $data['token'] ) ) {
			return false;
		}

		foreach ( self::getTOTPKeys( $user ) as $key ) {
			if ( $key->verify( $user, $data ) ) {
				return true;
			}
		}

		// Check recovery codes
		// TODO: We should deprecate (T408043) logging in on the TOTP form using recovery codes, and eventually
		// remove this ability (T408044).

		/** @var RecoveryCodes $recoveryCodes */
		$recoveryCodes = OATHAuthServices::getInstance()->getModuleRegistry()
			->getModuleByKey( RecoveryCodes::MODULE_NAME );
		$validRecoveryCode = $recoveryCodes->verify( $user, [ 'recoverycode' => $data['token'] ?? '' ] );
		if ( $validRecoveryCode ) {
			LoggerFactory::getInstance( 'authentication' )->info(
				// phpcs:ignore
				"OATHAuth {user} used a recovery code from {clientip} on TOTP form.", [
					'user' => $user->getUser()->getName(),
					'clientip' => RequestContext::getMain()->getRequest()->getIP()
				]
			);
			return true;
		}

		return false;
	}
```

### d013
```
/**
	 * Verify whether the token has been included on the remote wiki.
	 * @param string $remoteUsername
	 * @param string $token
	 * @return StatusValue
	 */
	public function verifyToken( string $remoteUsername, string $token ) {
		$status = StatusValue::newGood();
		$wanKey = $this->wanCache->makeKey( 'migrateuseraccount', 'verify', $remoteUsername, $token );

		if ( $this->wanCache->get( $wanKey ) ) {
			// Token was verified within the last 10 mins, no need to redo our work
			return $status;
		}

		$un = rawurlencode( $remoteUsername );
		$textToTest = '';

		$pageUrl = $this->getRemoteUrl( $remoteUsername );
		$apiUrl = $this->config->get( 'MUARemoteWikiAPI' ) .
			'?format=json&formatversion=2&action=query&prop=revisions&titles=User:' . $un .
			'&rvprop=comment|content|timestamp|user&rvlimit=1&rvslots=main';
		$res = $this->httpRequestFactory->get( $apiUrl );

		if ( $res ) {
			$data = json_decode( $res, true );

			// Get the first page
			if ( isset( $data['query']['pages'] ) ) {
				$firstPage = current( $data['query']['pages'] );

				// Get the first revision
				if ( isset( $firstPage['revisions'] ) ) {
					$revision = current( $firstPage['revisions'] );

					// If the most recent edit was more than 10 minutes ago, show a special error message
					if ( isset( $revision['timestamp'] ) ) {
						$currTimestamp = time();
						$editTimestamp = strtotime( $revision['timestamp'] );

						if ( $editTimestamp && ( $editTimestamp < ( $currTimestamp - 10 * 60 ) ) ) {
							return $status->fatal( 'migrateuseraccount-token-no-recent-edit',
								'[' . $pageUrl . ' ' . urlencode( $remoteUsername ) . ']' );
						}
					}

					// If the username of the most recent edit is not the target user, show a special error message
					if ( !isset( $revision['user'] ) || $revision['user'] !== $remoteUsername ) {
						return $status->fatal( 'migrateuseraccount-token-username-no-match',
							'[' . $pageUrl . ' ' . urlencode( $remoteUsername ) . ']' );
					}

					// Get the slots (for the revision content)
					if ( isset( $revision['slots'] ) ) {
						$textToTest = $textToTest . trim( $revision['slots']['main']['content'] );
					}

					// Get the edit summary
					if ( isset( $revision['comment'] ) ) {
						$textToTest = $textToTest . trim( $revision['comment'] );
					}
				}
			}
		} else {
			$this->logger->error( 'Got an invalid response from ' . $apiUrl );
		}

		// If the token is present in the text we're testing, then this was successful
		if ( str_contains( $textToTest, $token ) ) {
			// Set a temporary WAN cache key so that we can verify the token for the next 10 min without more API calls
			$this->wanCache->set(
				$wanKey,
				true,
				ExpirationAwareness::TTL_MINUTE * 10,
			);

			return $status;
		} else {
			return $status->fatal( 'migrateuseraccount-token-no-token',
				'[' . $pageUrl . ' ' . urlencode( $remoteUsername ) . ']' );
		}
	}
```

### d014
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

### d015
```
/**
	 * Check if the user solved the captcha.
	 *
	 * Based on reference implementation:
	 * https://developers.cloudflare.com/turnstile/get-started/server-side-validation/
	 *
	 * @param mixed $_ Not used
	 * @param string $word captcha solution
	 * @param UserIdentity $user
	 * @return bool
	 */
	protected function passCaptcha( $_, $word, $user ) {
		global $wgRequest, $wgTurnstileSecretKey, $wgTurnstileSendRemoteIP;

		$url = 'https://challenges.cloudflare.com/turnstile/v0/siteverify';
		// Build data to append to request
		$data = [
			'secret' => $wgTurnstileSecretKey,
			'response' => $word,
		];
		if ( $wgTurnstileSendRemoteIP ) {
			$data['remoteip'] = $wgRequest->getIP();
		}
		$request = MediaWikiServices::getInstance()->getHttpRequestFactory()
			->create( $url, [ 'method' => 'POST' ], __METHOD__ );
		$request->setData( $data );
		$status = $request->execute();
		if ( !$status->isOK() ) {
			$this->error = 'http';
			$this->logCheckError( $status );
			return false;
		}
		$response = FormatJson::decode( $request->getContent(), true );
		if ( !$response ) {
			$this->error = 'json';
			$this->logCheckError( $this->error );
			return false;
		}
		// Turnstile always returns the "error-codes" array, so we should just
		// check whether it is empty or not.
		if ( !empty( $response['error-codes'] ) ) {
			$this->error = 'turnstile-api';
			$this->logCheckError( $response['error-codes'] );
			return false;
		}

		return $response['success'];
	}
```

### d016
```
/**
	 * Retrieve the hCaptcha session score safely.
	 *
	 * Returns -1 if a score cannot be retrieved.
	 */
	private function getRiskScore( HCaptcha $hCaptcha, UserIdentity $user ): float {
		$score = $hCaptcha->retrieveSessionScore( 'hCaptcha-score', $user->getName() );
		if ( is_numeric( $score ) ) {
			return (float)$score;
		}

		return -1.0;
	}
```

### d017
```
def _get_category_key_token(category='F', key='key1', operator='=', value='value1'):
    """Generate and return a category token string and it's expected dictionary of tokens when parsed."""
    expected = {'category': category, 'key': key, 'operator': operator, 'quoted': value}
    token = '{category}:{key} {operator} {quoted}'.format(**expected)
    return token, expected
```

### d018
```
/**
	 * @param User $user
	 * @param string $token
	 * @return array{0:Message,1:string,2:string,3:string}|bool
	 *   [ form message, email subject, email body text, email body HTML ] or false if
	 *   no verification should happen
	 */
	protected function runEmailAuthRequireToken( User $user, $token ) {
		global $wgSitename;

		// We need an email (confirmed or unconfirmed) to do something.
		if ( !$user->getEmail() ) {
			LoggerFactory::getInstance( 'EmailAuth' )->info( '{user} without email logging in', [
				'user' => $user->getName(),
				'ip' => $user->getRequest()->getIP(),
				'eventType' => 'emailauth-login-no-email',
				'ua' => $user->getRequest()->getHeader( 'User-Agent' ),
			] );
			return false;
		}

		$verificationRequired = false;

		$maskedEmail = $this->maskEmail( $user->getEmail() );
		$formMessage = wfMessage( 'emailauth-login-message', wfEscapeWikiText( $maskedEmail ) );

		$helpUrl = wfMessage( 'emailauth-email-help-url' )->text();
		// Do not allow on-wiki modification of these messages (except the help URL above).
		// A malicious email text could trick the user into sending the code to the attacker.
		$subject = wfMessage( 'emailauth-email-subject', $wgSitename )->useDatabase( false )->text();
		$introMessage = wfMessage( 'emailauth-email-body-intro', $user->getName(), $wgSitename );
		$codeTextMessage = wfMessage( 'emailauth-email-body-code-text' );
		$warningMessage = wfMessage( 'emailauth-email-body-warning',
			Message::durationParam( $this->config->get( MainConfigNames::ObjectCacheSessionExpiry ) ) );
		$attackHeadingMessage = wfMessage( 'emailauth-email-body-attack-heading' );
		$attackP1Message = wfMessage( 'emailauth-email-body-attack-p1' );
		$attackP2Message = wfMessage( 'emailauth-email-body-attack-p2' );
		$helpTextMessage = wfMessage( 'emailauth-email-body-help-text', $helpUrl );
		$helpHtmlMessage = wfMessage( 'emailauth-email-body-help-text',
			Html::element( 'a', [ 'href' => $helpUrl ], $helpUrl ) );
		$templateData = [
			'code' => $token,
			'subject' => $subject,
			'intro' => $introMessage->useDatabase( false )->text(),
			'code-text' => $codeTextMessage->useDatabase( false )->text(),
			'warning' => $warningMessage->useDatabase( false )->text(),
			'attack-heading' => $attackHeadingMessage->useDatabase( false )->text(),
			'attack-p1' => $attackP1Message->useDatabase( false )->text(),
			'attack-p2' => $attackP2Message->useDatabase( false )->text(),
			'help-text' => $helpTextMessage->useDatabase( false )->text(),
			'help-html' => $helpHtmlMessage->useDatabase( false )->text(),
		];
		$templateParser = new TemplateParser( __DIR__ . '/../templates' );
		$body = $templateParser->processTemplate( 'email-text', $templateData );
		$bodyHtml = $templateParser->processTemplate( 'email-html', $templateData );

		MediaWikiServices::getInstance()->getHookContainer()->run(
			'EmailAuthRequireToken',
			[ $user, &$verificationRequired, &$formMessage, &$subject, &$body, &$bodyHtml ]
		);

		// @phan-suppress-next-line PhanImpossibleCondition
		return $verificationRequired ? [ $formMessage, $subject, $body, $bodyHtml ] : false;
	}
```

### d019
```
function pushKeywordIf(keywordList, token, ...expected) {
    if (token && contains(expected, token.kind)) {
      keywordList.push(token);
      return true;
    }
    return false;
  }
```

### d020
```
/**
 * @covers \MediaWiki\Extension\ReadingLists\Rest\ReadingListsTokenAwareHandlerTrait
 */
class ReadingListsTokenAwareHandlerTraitTest extends MediaWikiUnitTestCase {

	/**
	 * @dataProvider provideGetToken
	 */
	public function testGetToken(
		array $params,
		array $body,
		?string $secret,
		bool $safeAgainstCsrf,
		?string $expected
	) {
		$handler = $this->getHandler( $params, $body, $secret, $safeAgainstCsrf );
		$this->assertEquals( $expected, $handler->getToken() );
	}

	public static function provideGetToken() {
		$secret = 'foo';
		$token = strval( new Token( $secret, '' ) );

		foreach ( [
					  'missing token, not CSRF-safe' => [
						  'params' => [],
						  'body' => [],
						  'expected' => '',
					  ],
					  'missing token, CSRF-safe' => [
						  'params' => [],
						  'body' => [],
						  'safeAgainstCsrf' => true,
						  'expected' => null,
					  ],
					  'body token, not CSRF-safe' => [
						  'params' => [],
						  'body' => [ 'token' => $token ],
						  'expected' => $token,
					  ],
					  'body token, CSRF-safe' => [
						  'params' => [],
						  'body' => [ 'token' => $token ],
						  'safeAgainstCsrf' => true,
						  'expected' => null,
					  ],
					  'param token, not CSRF-safe' => [
						  'params' => [ 'csrf_token' => $token ],
						  'body' => [],
						  'expected' => $token,
					  ],
					  'param token, CSRF-safe' => [
						  'params' => [ 'csrf_token' => $token ],
						  'body' => [],
						  'safeAgainstCsrf' => true,
						  'expected' => null,
					  ],
					  'body and param tokens, not CSRF-safe' => [
						  'params' => [ 'csrf_token' => $token ],
						  'body' => [ 'token' => $token ],
						  'expected' => $token,
					  ],
					  'body and param tokens, CSRF-safe' => [
						  'params' => [ 'csrf_token' => $token ],
						  'body' => [ 'token' => $token ],
						  'safeAgainstCsrf' => true,
						  'expected' => null,
					  ],
				  ] as $name => $test ) {
			yield $name => array_merge( [
				'params' => null,
				'body' => null,
				'secret' => $secret,
				'safeAgainstCsrf' => false,
				'expected' => null,
			], $test );
		}
	}

	private function getHandler(
		array $params,
		array $body,
		?string $secret,
		bool $safeAgainstCsrf
	) {
		$session = $this->createNoOpMock( Session::class,
			[ 'getProvider', 'isPersistent', 'hasToken', 'getToken', 'getUser' ] );
		$sessionProvider = $this->createNoOpMock( SessionProvider::class, [ 'safeAgainstCsrf' ] );
		$sessionProvider->method( 'safeAgainstCsrf' )->willReturn( $safeAgainstCsrf );
		$session->method( 'getProvider' )->willReturn( $sessionProvider );
		$session->method( 'isPersistent' )->willReturn( true );
		$session->method( 'hasToken' )->willReturn( $secret !== null );
		$session->method( 'getToken' )->willReturn( new Token( $secret, '' ) );
		$user = $this->createNoOpMock( User::class, [ 'isAnon' ] );
		$session->method( 'getUser' )->willReturn( $user );

		// PHPUnit can't mock a class and a trait at the same time
		return new class( $session, $params, $body ) extends Handler {
			use ReadingListsTokenAwareHandlerTrait {
				ReadingListsTokenAwareHandlerTrait::getToken as public;
			}

			private Session $session;
			private array $validatedParams;
			private array $validatedBody;

			public function __construct( Session $session, array $validatedParams, array $validatedBody ) {
				$this->session = $session;
				$this->validatedParams = $validatedParams;
				$this->validatedBody = $validatedBody;
			}

			public function execute() {
			}

			public function getSession(): Session {
				return $this->session;
			}

			public function getValidatedParams() {
				return $this->validatedParams;
			}

			public function getValidatedBody() {
				return $this->validatedBody;
			}
		};
	}

}
```

## Output

Return raw JSON only. No preamble, no markdown fences, no commentary outside the
object.

```json
{
  "query_id": "B8",
  "labels": {
    "d001": {"score": 1.0, "rationale": "iterative binary search over sorted array"},
    "d002": {"score": 0.0, "rationale": "pytest case asserting search behaviour, not an implementation"}
  }
}
```

Every `doc_id` presented must appear exactly once in `labels`.
