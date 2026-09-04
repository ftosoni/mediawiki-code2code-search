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
public function invalidateUserSession(User $user): void {
    $user->setToken();
    $user->saveSettings();
    SessionManager::singleton()->invalidateSessionsForUser($user);
}
```

## Candidates

### d001
```
/**
	 * @param User $user
	 * @return bool
	 */
	public function onUserSaveSettings( $user ) {
		$ca = CentralAuthUser::getPrimaryInstance( $user );
		if ( $ca->isAttached() ) {
			$ca->saveSettings();
		}

		return true;
	}
```

### d002
```
// @codeCoverageIgnoreEnd

/**
 * Invalidate the sessions of certain users on the wiki.
 * If you want to invalidate all sessions, use $wgAuthenticationTokenVersion instead.
 *
 * @ingroup Maintenance
 */
class InvalidateUserSessions extends Maintenance {
	public function __construct() {
		parent::__construct();
		$this->addDescription(
			'Invalidate the sessions of certain users on the wiki.'
		);
		$this->addOption( 'user', 'Username', false, true, 'u' );
		$this->addOption( 'file', 'File with one username per line', false, true, 'f' );
		$this->setBatchSize( 1000 );
	}

	public function execute() {
		$username = $this->getOption( 'user' );
		$file = $this->getOption( 'file' );

		if ( $username === null && $file === null ) {
			$this->fatalError( 'Either --user or --file is required' );
		} elseif ( $username !== null && $file !== null ) {
			$this->fatalError( 'Cannot use both --user and --file' );
		}

		if ( $username !== null ) {
			$usernames = [ $username ];
		} else {
			$usernames = is_readable( $file ) ?
				file( $file, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES ) : false;
			if ( $usernames === false ) {
				$this->fatalError( "Could not open $file", 2 );
			}
		}

		$i = 0;
		$sessionManager = SessionManager::singleton();
		foreach ( $usernames as $username ) {
			$i++;
			$user = User::newFromName( $username );
			try {
				$sessionManager->invalidateSessionsForUser( $user );
				if ( $user->isRegistered() ) {
					$this->output( "Invalidated sessions for user $username\n" );
				} else {
					# session invalidation might still work if there is a central identity provider
					$this->output( "Could not find user $username, tried to invalidate anyway\n" );
				}
			} catch ( Exception $e ) {
				$this->output( "Failed to invalidate sessions for user $username | "
					. str_replace( [ "\r", "\n" ], ' ', $e->getMessage() ) . "\n" );
			}

			if ( $i % $this->getBatchSize() ) {
				$this->waitForReplication();
			}
		}
	}
}
```

### d003
```
/**
	 * Invalidate existing sessions for a user
	 *
	 * If the provider has its own equivalent of CookieSessionProvider's Token
	 * cookie (and doesn't use User::getToken() to implement it), it should
	 * reset whatever token it does use here.
	 *
	 * @stable to override
	 * @note For use by \MediaWiki\Session\SessionManager only
	 * @param User $user
	 */
	public function invalidateSessionsForUser( User $user ) {
	}
```

### d004
```
/** @inheritDoc */
	public function invalidateSessionsForUser( User $user ) {
		$centralUser = CentralAuthUser::getPrimaryInstance( $user );
		if ( $centralUser->exists() && ( $centralUser->isAttached() || !$user->isRegistered() ) ) {
			$centralUser->resetAuthToken();
		}
	}
```

### d005
```
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
```

### d006
```
class TerminateUserSession extends Maintenance {
	public function __construct() {
		parent::__construct();
		$this->addOption( 'user', 'User to invalidate', false, true, 'u' );
	}

	public function execute() {
		$user = $this->getOption( 'user' );
		if ( $user ) {
			$userFactory = MediaWikiServices::getInstance()->getUserFactory();
			$this->invalidateForUser( $userFactory->newFromName( $user ) );
			return;
		}
		$db = MediaWikiServices::getInstance()->getDBLoadBalancer()->getConnection( DB_PRIMARY );
		$res = $db->delete(
			'objectcache',
			[ "keyname LIKE '%MWSession%'" ],
			__METHOD__
		);
		if ( $res ) {
			$this->output( "Deleted all sessions\n" );
		} else {
			$this->output( "Failed to delete sessions\n" );
		}
	}

	/**
	 * @param User|bool $user
	 */
	private function invalidateForUser( $user ) {
		if ( !( $user instanceof User ) ) {
			$this->fatalError( "User $user is invalid\n" );
		}
		$sessionManager = SessionManager::singleton();
		try {
			$sessionManager->invalidateSessionsForUser( $user );
			if ( $user->getId() ) {
				$this->output( 'Invalidated session for user ' . $user->getName() . "\n" );
			} else {
				$this->output( "Cannot find user {$user->getName()}, tried to invalidate anyways\n" );
			}
		} catch ( Exception $ex ) {
			$this->output( "Failed to invalidate sessions for user {$user->getName()} | "
				. str_replace( [ "\r", "\n" ], ' ', $ex->getMessage() ) . "\n" );
		}
	}
}
```

### d007
```
/**
	 * @param User $user
	 * @return void
	 */
	public function unset( User $user );
```

### d008
```
public function invalidateSessionsForUser( User $user ) {
		$user->setToken();
		$user->saveSettings();

		foreach ( $this->getProviders() as $provider ) {
			$provider->invalidateSessionsForUser( $user );
		}
	}
```

### d009
```
/**
	 * Invalidate sessions for a user
	 *
	 * After calling this, existing sessions should be invalid. For mutable
	 * session providers, this generally means the user has to log in again;
	 * for immutable providers, it generally means the loss of session data.
	 */
	public function invalidateSessionsForUser( User $user );
```

### d010
```
/**
	 * @param User|bool $user
	 */
	private function invalidateForUser( $user ) {
		if ( !( $user instanceof User ) ) {
			$this->fatalError( "User $user is invalid\n" );
		}
		$sessionManager = SessionManager::singleton();
		try {
			$sessionManager->invalidateSessionsForUser( $user );
			if ( $user->getId() ) {
				$this->output( 'Invalidated session for user ' . $user->getName() . "\n" );
			} else {
				$this->output( "Cannot find user {$user->getName()}, tried to invalidate anyways\n" );
			}
		} catch ( Exception $ex ) {
			$this->output( "Failed to invalidate sessions for user {$user->getName()} | "
				. str_replace( [ "\r", "\n" ], ' ', $ex->getMessage() ) . "\n" );
		}
	}
```

### d011
```
public function execute() {
		$username = $this->getOption( 'user' );
		$file = $this->getOption( 'file' );

		if ( $username === null && $file === null ) {
			$this->fatalError( 'Either --user or --file is required' );
		} elseif ( $username !== null && $file !== null ) {
			$this->fatalError( 'Cannot use both --user and --file' );
		}

		if ( $username !== null ) {
			$usernames = [ $username ];
		} else {
			$usernames = is_readable( $file ) ?
				file( $file, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES ) : false;
			if ( $usernames === false ) {
				$this->fatalError( "Could not open $file", 2 );
			}
		}

		$i = 0;
		$sessionManager = SessionManager::singleton();
		foreach ( $usernames as $username ) {
			$i++;
			$user = User::newFromName( $username );
			try {
				$sessionManager->invalidateSessionsForUser( $user );
				if ( $user->isRegistered() ) {
					$this->output( "Invalidated sessions for user $username\n" );
				} else {
					# session invalidation might still work if there is a central identity provider
					$this->output( "Could not find user $username, tried to invalidate anyway\n" );
				}
			} catch ( Exception $e ) {
				$this->output( "Failed to invalidate sessions for user $username | "
					. str_replace( [ "\r", "\n" ], ' ', $e->getMessage() ) . "\n" );
			}

			if ( $i % $this->getBatchSize() ) {
				$this->waitForReplication();
			}
		}
	}
```

### d012
```
/**
	 * Clear the in-process permission cache for one or all users.
	 *
	 * @since 1.34
	 * @param UserIdentity|null $user If a specific user is provided it will clear
	 *  the permission cache only for that user.
	 */
	public function invalidateUsersRightsCache( $user = null ): void {
		if ( $user !== null ) {
			$rightsCacheKey = $this->getRightsCacheKey( $user );
			unset( $this->usersRights[ $rightsCacheKey ] );
		} else {
			$this->usersRights = [];
		}
	}
```

### d013
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

## Output

Return raw JSON only. No preamble, no markdown fences, no commentary outside the
object.

```json
{
  "query_id": "B3",
  "labels": {
    "d001": {"score": 1.0, "rationale": "iterative binary search over sorted array"},
    "d002": {"score": 0.0, "rationale": "pytest case asserting search behaviour, not an implementation"}
  }
}
```

Every `doc_id` presented must appear exactly once in `labels`.
