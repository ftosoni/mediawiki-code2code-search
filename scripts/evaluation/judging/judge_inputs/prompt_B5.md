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
public function isRateLimited(string $action, UserIdentity $user): bool {
    $key = $this->makeKey($action, $user->getId());
    $count = $this->cache->get($key) ?? 0;
    return $count >= ($this->limits[$action] ?? PHP_INT_MAX);
}
```

## Candidates

### d001
```
/**
	 * Test that '&can-bypass' can be used to impose limits on users
	 * who are otherwise exempt from limits.
	 */
	public function testCanBypass() {
		$limits = [
			'edit' => [
				'user' => [ 1, 60 ],
			],
			'delete' => [
				'&can-bypass' => false,
				'user' => [ 1, 60 ],
			],
		];

		$user = new RateLimitSubject(
			new UserIdentityValue( 7, 'Garth' ),
			'127.0.0.1',
			[ RateLimitSubject::EXEMPT => true ]
		);

		$statsHelper = StatsFactory::newUnitTestingHelper();
		$limiter = $this->newRateLimiter( $limits, [] );
		$limiter->setStats( $statsHelper->getStatsFactory() );

		$this->assertFalse( $limiter->limit( $user, 'edit' ) );
		$this->assertFalse( $limiter->limit( $user, 'delete' ) );

		$this->assertFalse( $limiter->limit( $user, 'edit' ), 'bypass should be granted' );
		$this->assertTrue( $limiter->limit( $user, 'delete' ), 'bypass should be denied' );

		$actual = $statsHelper->count( 'RateLimiter_limit_actions_total{action="edit",result="exempt"}' );
		$this->assertSame( 2, $actual );
		$actual = $statsHelper->count( 'RateLimiter_limit_actions_total{action="delete",result="passed"}' );
		$this->assertSame( 1, $actual );
		$actual = $statsHelper->count( 'RateLimiter_limit_actions_total{action="delete",result="tripped"}' );
		$this->assertSame( 1, $actual );
	}
```

### d002
```
/**
	 * Hook: getUserPermissionsErrorsExpensive
	 * @param Title $title
	 * @param User $user
	 * @param string $action
	 * @param mixed &$result
	 * @return bool
	 */
	public static function lockedPagesCheck( Title $title, User $user, $action, &$result ) {
		if ( $action === 'read' ) {
			return true;
		}

		$cache = MediaWikiServices::getInstance()->getObjectCacheFactory()->getInstance( CACHE_ANYTHING );
		$key = $cache->makeKey( 'pt-lock', sha1( $title->getPrefixedText() ) );
		if ( $cache->get( $key ) === 'locked' ) {
			$result = [ 'pt-locked-page' ];

			return false;
		}

		return true;
	}
```

### d003
```
/** @inheritDoc */
	public function authorizeWrite(
		string $action,
		PageIdentity $target,
		?PermissionStatus $status = null
	): bool {
		// Any side-effects can be added here.

		// Note that we need to use RIGOR_SECURE here to ensure that we do not
		// miss a user block or page protection due to replication lag.
		return $this->internalCan(
			PermissionManager::RIGOR_SECURE,
			$action,
			$target,
			$status,
			1 // count a hit towards the rate limit
		);
	}
```

### d004
```
/**
 * This is a hook handler interface, see docs/Hooks.md.
 * Use the hook name "PingLimiter" to register handlers implementing this interface.
 *
 * @stable to implement
 * @ingroup Hooks
 */
interface PingLimiterHook {
	/**
	 * Use this hook to override the results of User::pingLimiter().
	 *
	 * @since 1.35
	 *
	 * @param User $user User performing the action
	 * @param string $action Action being performed
	 * @param bool &$result Whether or not the action should be prevented
	 *   Change $result and return false to give a definitive answer, otherwise
	 *   the built-in rate limiting checks are used, if enabled.
	 * @param int $incrBy Amount to increment counter by
	 * @return bool|void True or no return value to continue or false to abort
	 */
	public function onPingLimiter( $user, $action, &$result, $incrBy );
}
```

### d005
```
/**
	 * Check whether the user is allowed to perform the action, taking into account
	 * the user's block status as well as any rate limits.
	 *
	 * @param string $action
	 * @param PermissionStatus|null $status
	 * @param int|false $limitRate False means no check, 0 means check only,
	 *        and 1 means check and increment
	 * @param ?Block $userBlock
	 *
	 * @return bool
	 */
	private function internalAllowed(
		string $action,
		?PermissionStatus $status,
		$limitRate,
		?Block $userBlock
	): bool {
		if ( $status ) {
			Assert::precondition(
				$status->isGood(),
				'The PermissionStatus passed as $status parameter must still be good'
			);
		}

		if ( !$this->permissionManager->userHasRight( $this->actor, $action ) ) {
			if ( !$status ) {
				return false;
			}

			$status->setPermission( $action );
			$status->merge(
				$this->permissionManager->newFatalPermissionDeniedStatus(
					$action,
					$this->uiContext
				)
			);
		}

		if ( $userBlock ) {
			if ( !$status ) {
				return false;
			}

			$messages = $this->blockErrorFormatter->getMessages(
				$userBlock,
				$this->actor,
				$this->request->getIP()
			);

			$status->setPermission( $action );
			foreach ( $messages as $message ) {
				$status->fatal( $message );
			}
		}

		// Check and bump the rate limit.
		if ( $limitRate !== false ) {
			$isLimited = $this->limit( $action, $limitRate, $status );
			if ( $isLimited && !$status ) {
				return false;
			}
		}

		return !$status || $status->isOK();
	}
```

### d006
```
private function pruneExcessStashedEntries( BagOStuff $cache, UserIdentity $user, string $newKey ): void {
		$key = $cache->makeKey( 'visualeditor-serialization-recent', $user->getName() );

		$keyList = $cache->get( $key ) ?: [];
		if ( count( $keyList ) >= self::MAX_CACHE_RECENT ) {
			$oldestKey = array_shift( $keyList );
			$cache->delete( $oldestKey );
		}

		$keyList[] = $newKey;
		$cache->set( $key, $keyList, 2 * self::MAX_CACHE_TTL );
	}
```

### d007
```
/**
	 * Because fetching the amount of activity from db is quite expensive, this
	 * method will just increment the data that is in cache already (instead of
	 * purging the cache data to have it re-read from DB, which should be last-resort)
	 *
	 * @param string $feedbackId
	 * @param string $action
	 */
	public static function incrementActivityCount( $feedbackId, $action ) {
		$cache = MediaWikiServices::getInstance()->getMainWANObjectCache();

		// get permission level that should be updated
		$permission = self::$actions[$action]['permissions'];

		$key = $cache->makeKey(
			'articlefeedbackv5-getActivityCount',
			$permission,
			$feedbackId
		);
		$count = $cache->get( $key );

		/*
		 * if the data is not (yet) in cache, don't bother fetching it from db yet,
		 * that'll happen in due time, when it's actually requested
		 */
		if ( $count !== false ) {
			$cache->set( $key, $count + 1, 60 * 60 * 24 * 7 );
		}
	}
```

### d008
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

### d009
```
/**
	 * Helper method to load the current user's starred mentees, with caching.
	 * @param UserIdentity $user
	 * @return int[]
	 */
	private function getStarredMenteeIds( UserIdentity $user ): array {
		$key = $this->menteeCache->makeKey( 'starred', $user->getId() );
		if ( $this->menteeCache->hasKey( $key ) ) {
			return $this->menteeCache->get( $key );
		}

		$starredMentees = $this->starredMenteesStore->getStarredMentees( $user );
		$starredMenteeIds = array_map( static fn ( UserIdentity $user ) => $user->getId(), $starredMentees );

		$this->menteeCache->set( $key, $starredMenteeIds );
		return $starredMenteeIds;
	}
```

### d010
```
/**
	 * Test that the most permissive limit is used when a limit is defined for
	 * multiple groups a user belongs to.
	 */
	public function testGroupLimits() {
		$limits = [
			'edit' => [
				'user' => [ 1, 60 ],
				'autoconfirmed' => [ 2, 60 ],
			],
		];

		$user = $this->getTestUser( [ 'autoconfirmed' ] )->getUser();
		$user = new RateLimitSubject( $user, '127.0.0.1', [] );

		$statsHelper = StatsFactory::newUnitTestingHelper();
		$limiter = $this->newRateLimiter( $limits, [] );
		$limiter->setStats( $statsHelper->getStatsFactory() );

		$this->assertFalse( $limiter->limit( $user, 'edit' ) );
		$this->assertFalse( $limiter->limit( $user, 'edit' ), 'limit for autoconfirmed used' );
		$this->assertTrue( $limiter->limit( $user, 'edit' ), 'limit for autoconfirmed exceeded' );

		$actual = $statsHelper->count( 'RateLimiter_limit_actions_total{action="edit",result="passed"}' );
		$this->assertSame( 2, $actual );
		$actual = $statsHelper->count( 'RateLimiter_limit_actions_total{action="edit",result="tripped"}' );
		$this->assertSame( 1, $actual );
		$actual = $statsHelper->count( 'RateLimiter_limit_cause_total{action="edit",tripped_by="autoconfirmed"}' );
		$this->assertSame( 1, $actual );
	}
```

### d011
```
/**
	 * Get the rate limits that apply to the user, or the rate limits
	 * that would apply if the user didn't have `noratelimit`
	 *
	 * @param bool $applyNoRateLimit
	 * @return array
	 */
	protected function getRateLimits( bool $applyNoRateLimit ) {
		$retval = [
			ApiResult::META_TYPE => 'assoc',
		];

		$user = $this->getUser();
		if ( $applyNoRateLimit && !$user->isPingLimitable() ) {
			return $retval; // No limits
		}

		// Find out which categories we belong to
		$categories = [];
		if ( !$user->isRegistered() ) {
			$categories[] = 'anon';
		} else {
			$categories[] = 'user';
		}
		if ( $user->isNewbie() ) {
			$categories[] = 'ip';
			$categories[] = 'subnet';
			if ( $user->isRegistered() ) {
				$categories[] = 'newbie';
			}
		}
		$categories = array_merge( $categories, $this->userGroupManager->getUserGroups( $user ) );

		// Now get the actual limits
		foreach ( $this->getConfig()->get( MainConfigNames::RateLimits ) as $action => $limits ) {
			foreach ( $categories as $cat ) {
				if ( isset( $limits[$cat] ) ) {
					$retval[$action][$cat]['hits'] = (int)$limits[$cat][0];
					$retval[$action][$cat]['seconds'] = (int)$limits[$cat][1];
				}
			}
		}

		return $retval;
	}
```

### d012
```
class UserCounter {

	/** @var array */
	private $userLimits = [
		'4cb76833e743e9313ec7f0adb371c0fdbacf57ed' => 25,
		'9d3cc888b83410c13b1406f784fb55129c36b520' => 50,
		'a416fa165396d208d806b63ba409b86e23c2cb10' => 100,
		'7c3e5945d5e71bbdc17fda125e3e4d2591916e87' => 150,
		'330f0c275d554b3baac829758443511650b69dcf' => 200,
		'9d30f6794f1ee6bc3d8d4e7495aff9e6ffb12d75' => 250,
		'ec8da2fd187588cbc4a176d8fc831705e4c799e5' => 300,
		'7bb43796c1ac9456225c128c206f7455efd362e7' => 400,
		'88530acf24588b4b8ad0cae873ab22d19f77f959' => 500,
		'c9f9f6b1090aa7b4174443d295fe50e47a0b04c7' => 600,
		'10c0fa889b942b27368af58687b687f256e2665b' => 800,
		'20942e9dc9d1eed4c73f90add45f650b64d8f5e2' => 1000,
		'05a4e4fa3f8e6f0d01ddefa6d829daae7a3331eb' => 1200,
		'4d6279baaa388d34ff6e8b9abbb98b2357d69ca5' => 1400,
		'24b634bc4a6dccca835a5097e5147640870d611e' => 1600,
		'1686fff4675b28ac7bd8de086393b462d40880ae' => 1800,
		'c9ece401393ea5533037675658c4299826a02859' => 2000,
		'af9351be0196b7f0f0a68439a9cb7b90b91d97c9' => 2250,
		'2d5eddf952cfebd4966242c464acb3842f6f648c' => 2500,
		'ff948b41e7ae1dc2cb16795807e8c3d0eab48dd0' => 2750,
		'7a228aa99896c941169fd0074be0f6b4ba50aedc' => 3000,
		'1e27dd541e89b118eb391f8de16841d6beed0061' => 3250,
		'90873ce1d09615ed464a375be09f6a0550b9ee36' => 3500,
		'3b4a6f1d25d7542670e08962eebb05c2772d1012' => 3750,
		'b54b1f999f62f890a0b4d13042411fab5b8a20bc' => 4000,
		'd88506b8b634ee906e4ba1fb4517115e106b1830' => 4250,
		'097a1f302cb9a2758bc844b273c87b9cec4eb9e2' => 4500,
		'6219cce2cec631fa854dd006acd5e6250c888866' => 4750,
		'c0e5ea7b86dde728f5d33de195210bbad57d9b71' => 5000,
		'8514ab28bc7dfeb479dbfa0e6ee50088de73f786' => 5500,
		'7e1f975c849db45eae53df3ce167c74b0848cc93' => 6000,
		'7aa11657de8cb604b7c41c04ffe733f204517acd' => 6500,
		'7a6cbf452c41a0dce14b35710f9bc270488010bc' => 7000,
		'135b23d727f497c4d7643e348c56a078764132af' => 7500,
		'468e79ea1fe5ffe08e5087f33b86e0faa0083b1f' => 8000,
		'92410f868cc92ffeaf46fc20476317b97d0d897f' => 8500,
		'c72964d581bd861753821282c94c94170cf04325' => 9000,
		'21094e77e74e9c734338e8a69cfe5ccd6c4014ac' => 9500,
		'0a6d3a57ad1565dbd78f1126df3d315932fd5489' => 10000,
		'43fb790133c166c7eff59398c15890a8c78b174d' => 11000,
		'c83285a57cc84fb59a90453a0e4be427e8e302cf' => 12000,
		'26916b721289adff4a7df2735df0d364d31dfe3b' => 13000,
		'0ccf8def8015f22ac35fff233857207d1ef00217' => 14000,
		'95f00573754a9f9dd9b59cccc432be9181807448' => 15000,
		'e6a86a5f28f8f9a4e7ef062d2571e18b3322f7ef' => 16000,
		'ac259ff3cac6fd1ee7826c7de67409302dd9cdde' => 17000,
		'ea1e7052a0683ad864decb3b657ed1226f7d6da1' => 18000,
		'6dcdd6e9a5110e3f7047c30d9c871b02702cdea7' => 19000,
		'0aa4346c1c5ca8bb6818a94982466a029d35fdac' => 20000,
		'676bfe78bd64eab911c4eef020836749c2cbeb3d' => 21000,
		'ce1db2e186ac96db5ddf988f11d43bfbbd0eda8f' => 22000,
		'ac90c57e01220c34be4cfb604e9578e2f129056f' => 23000,
		'80df5580e5c9c98a1117a1f8c7f4fab14402f5fa' => 24000,
		'9446000de63e2f5868e9c87eb5d2d090a7b81480' => 25000,
		'57fe291fca575743fa841cbfdb19e0f77afb9474' => 26000,
		'06b66493df5ef34526a6fa90c9dc82bfe927a430' => 27000,
		'5cc04ae62851d9930142356a92910056661ad77e' => 28000,
		'69e743cca06ff557dc399fdec3a529e1ce01b047' => 29000,
		'126748f88b03f7c20250b0ebd1c035ca13f493be' => 30000,
		'950aeae7fa19cdfce73cd7bd4742af3339dc64ed' => 31000,
		'df0c5371b346d17def980d918256b97f0e5e51a8' => 32000,
		'09974bf714e29fba7e99a1f6aca8fa378536455f' => 33000,
		'c6119758d3d69eb184a7822be51e11ae47928e30' => 34000,
		'79ed98bc3b5ba83cbebbcf545b4bd24c23091935' => 35000,
		'2733ca3308577d8f63b05c25d0769acaac795c8e' => 36000,
		'fed0f794606bfe954813d8954aab2531069684ee' => 37000,
		'6a9abe51aeaf378cdc39060f8d69a3ba636c37d4' => 38000,
		'38f3c1c11fd2e17f1102d6ee55d0c16d198119ad' => 39000,
		'42c6e6df5e8849443deb6c3f210266c133535dc6' => 40000,
		'84ae1b0712da605d602d9d09a8e2a69ccb3d5a01' => 41000,
		'f282966b7e410da8f161a9f77ffbe9ab1103797e' => 42000,
		'5d921c26e6abd27263ead84dafc7728dc598e5fe' => 43000,
		'2a4375243d4e9ad779c304577d8b3b1524e9bd7e' => 44000,
		'9574c2599ba07ec983aeb53d02f819221cd46752' => 45000,
		'48450942b5642eea5ee89d4aa4ebdfba661422c6' => 46000,
		'a1a50df90fc8e886c7ac89e164b3aa05552d8d86' => 47000,
		'b471c6a2213c1072c6800f8e9a526117fd51460b' => 48000,
		'f5ca02a15c37975750f3927553b29f257ae784a9' => 49000,
		// Unlimited
		'5185bf3320c8930f2cd4b7bbbe500b7151ead181' => -1,
	];

	/** @var Config */
	protected $config;
	/** @var Config */
	protected $mainConfig;
	/** @var ILoadBalancer */
	protected $lb;

	/** @var EditionProvider */
	private $editionProvider;

	/** @var string[] */
	private $warningLevels = [
		70 => 'orange',
		90 => 'red'
	];

	/**
	 * @param Config $config
	 * @param Config $mainConfig
	 * @param ILoadBalancer $lb
	 * @param EditionProvider $editionProvider
	 */
	public function __construct(
		Config $config, Config $mainConfig, ILoadBalancer $lb, EditionProvider $editionProvider
	) {
		$this->config = $config;
		$this->mainConfig = $mainConfig;
		$this->lb = $lb;
		$this->editionProvider = $editionProvider;
	}

	/**
	 * Get the maximum allowed active user from license
	 *
	 * @return int
	 */
	public function getUserLimit() {
		if ( !$this->editionProvider->checkRequiresLicense() ) {
			return -1;
		}
		$licenseKey = $this->normalizeLicenseKey( (string)$this->config->get( 'LicenseKey' ) );
		if ( !$licenseKey || !isset( $this->userLimits[$licenseKey] ) ) {
			return array_values( $this->userLimits )[0];
		}
		return $this->userLimits[$licenseKey];
	}

	/**
	 * Get the current number of active user.
	 * Bots and an additional whitelist are ignored.
	 *
	 * @return int
	 */
	public function getCurrentNumberOfUser() {
		$whitelist = $this->getUserNameWhitelist();
		$userCount = 0;

		$dbr = $this->lb->getConnection( DB_REPLICA );
		$result = $dbr->select(
			'user',
			[ '*' ],
			[ 'user_name NOT IN (' . $dbr->makeList( $whitelist ) . ')' ],
			__METHOD__
		);

		if ( !$result ) {
			return $userCount;
		}

		foreach ( $result as $row ) {
			$user = User::newFromRow( $row );
			$block = $user->getBlock();

			if ( $block === null ) {
				$userCount++;
			}
		}

		return (int)$userCount;
	}

	/**
	 * Get the formatted status sentence as HTML
	 * @return string
	 */
	public function getSentenceHtml() {
		return $this->getSentenceInternal( true );
	}

	/**
	 * Get status sentence
	 * @return string
	 */
	public function getSentence() {
		return $this->getSentenceInternal( false );
	}

	/**
	 * Get ratio of usage
	 *
	 * @param int|null $currentCount
	 * @param int|null $limit
	 * @return int|null
	 */
	public function getRatio( ?int $currentCount = null, ?int $limit = null ) {
		if ( $currentCount === null ) {
			$currentCount = $this->getCurrentNumberOfUser();
		}
		if ( $limit === null ) {
			$limit = $this->getUserLimit();
			if ( $limit < 1 ) {
				return null;
			}
		}
		return intval( ( $currentCount * 100 ) / $limit );
	}

	/**
	 * @param bool|null $html
	 * @return string
	 */
	protected function getSentenceInternal( $html = false ) {
		$currentCount = $this->getCurrentNumberOfUser();
		$limit = $this->getUserLimit();
		$percent = null;

		if ( $limit === 0 ) {
			$status = Message::newFromKey(
				'bs-pro-distribution-instance-status-number-of-users-unknown'
			)->params( $currentCount )->parse();
		} elseif ( $limit === -1 ) {
			$status = Message::newFromKey(
				'bs-pro-distribution-instance-status-number-of-users-unlimited'
			)->params( $currentCount )->parse();
		} else {
			$percent = $this->getRatio( $currentCount, $limit );
			if ( $percent > 99 ) {
				$status = Message::newFromKey(
					'bs-pro-distribution-instance-status-number-of-users-limited-full'
				)->params( $currentCount )->parse();
			} else {
				$status = Message::newFromKey(
					'bs-pro-distribution-instance-status-number-of-users-limited'
				)->params( $currentCount, $limit, $percent )->parse();
			}
		}

		if ( !$html ) {
			return $status;
		}

		if ( $percent !== null ) {
			$color = 'green';
			foreach ( $this->warningLevels as $level => $levelColor ) {
				if ( $level <= $percent ) {
					$color = $levelColor;
				}
			}

			$html = Html::openElement( 'span', [
				'style' => "color: $color",
			] );
		} else {
			$html = Html::openElement( 'span' );
		}

		$html .= $status;
		$html .= Html::closeElement( 'span' );

		return $html;
	}

	/**
	 * Get a whitelist with user which are not counted for the limit
	 *
	 * @return array
	 */
	private function getUserNameWhitelist() {
		return array_merge(
			$this->mainConfig->get( 'ReservedUsernames' ) ?? [],
			$this->config->get( 'UserLimitWhitelist' ) ?? []
		);
	}

	/**
	 * @param string $key
	 *
	 * @return string
	 */
	private function normalizeLicenseKey( string $key ): string {
		if ( !$key ) {
			return '';
		}
		$key = trim( strtolower( str_replace( '-', '', $key ) ) );
		return sha1( $key );
	}
}
```

### d013
```
private function recentStashEntryCount( UserIdentity $user ): int {
		$key = $this->cache->makeKey( 'stash-edit-recent', sha1( $user->getName() ) );

		return count( $this->cache->get( $key ) ?: [] );
	}
```

### d014
```
/**
	 * @param UserIdentity $user
	 * @param string $newKey
	 */
	private function pruneExcessStashedEntries( UserIdentity $user, string $newKey ): void {
		$key = $this->cache->makeKey( 'stash-edit-recent', sha1( $user->getName() ) );

		$keyList = $this->cache->get( $key ) ?: [];
		if ( count( $keyList ) >= self::MAX_CACHE_RECENT ) {
			$oldestKey = array_shift( $keyList );
			$this->cache->delete( $oldestKey, BagOStuff::WRITE_ALLOW_SEGMENTS );
		}

		$keyList[] = $newKey;
		$this->cache->set( $key, $keyList, 2 * self::MAX_CACHE_TTL );
	}
```

### d015
```
/**
	 * @param User $user
	 * @param string $action
	 * @param bool &$result
	 * @param null|string $ip
	 *
	 * @return bool
	 */
	public function doPingLimiter( $user, $action, &$result, $ip = null ) {
		$rateLimits = $this->config->get( MainConfigNames::RateLimits );
		if ( $action !== 'actcreate' && !isset( $rateLimits[$action] ) ) {
			return true;
		}

		if ( $user->isAnon() && IPUtils::isValid( $user->getName() ) ) {
			$ip = $user->getName();
		} elseif ( $ip === null ) {
			$ip = RequestContext::getMain()->getRequest()->getIP();
		}
		$hexIp = IPUtils::toHex( $ip );

		$fname = __METHOD__;
		$utils = $this->utils;
		$expiry = $this->cache->getWithSetCallback(
			$this->cache->makeGlobalKey(
				'throttle_override',
				$this->config->get( 'ThrottleOverrideCentralWiki' ),
				$action,
				$hexIp
			),
			$this->cache::TTL_HOUR,
			static function ( $cValue, &$ttl, &$setOpts, $asOf ) use ( $utils, $hexIp, $action, $fname ) {
				$dbr = $utils->getCentralDB( DB_REPLICA );
				$setOpts += Database::getCacheSetOptions( $dbr );

				$expiry = $dbr->newSelectQueryBuilder()
					->select( 'thr_expiry' )
					->from( 'throttle_override' )
					->where( [
						$dbr->expr( 'thr_range_start', '<=', $hexIp ),
						$dbr->expr( 'thr_range_end', '>=', $hexIp ),
						$dbr->expr( 'thr_expiry', '>', $dbr->timestamp() ),
						$dbr->expr( 'thr_type', IExpression::LIKE,
							new LikeValue( $dbr->anyString(), $action, $dbr->anyString() ) ),
					] )
					->orderBy( 'thr_expiry', SelectQueryBuilder::SORT_DESC )
					->caller( $fname )
					->fetchField();

				if ( $expiry !== false ) {
					// An override exists; cache for the override's
					// current-time-left. Cache will be purged via checkKey
					// updates on record modification. Avoid "0" (infinite)
					// and negative numbers for sanity.
					$ttl = max( (int)wfTimestamp( TS_UNIX, $expiry ) - time(), 1 );
				}

				// If we return false the value will not be cached
				return ( $expiry === false ) ? self::NO_OVERRIDE : $expiry;
			},
			[
				'checkKeys' => [ $utils->getBucketKey( $this->cache, $ip ) ]
			]
		);

		if ( $expiry === self::NO_OVERRIDE ) {
			// We checked the database and found no record
			return true;
		} elseif ( wfTimestamp( TS_UNIX, $expiry ) > time() ) {
			// Valid exemption. Disable the throttle.
			$logger = LoggerFactory::getInstance( 'throttleOverride' );
			$logger->info( 'User {user} (ip: {ip}) exempted from throttle {action}', [
				'user' => $user,
				'ip' => $ip,
				'action' => $action,
			] );

			$result = false;
			return false;
		}

		return true;
	}
```

### d016
```
/**
	 * @param User &$user
	 * @param string $action
	 * @param bool &$result
	 * @param int $incrBy
	 * @return bool|void
	 */
	public static function onPingLimiter( &$user, $action, &$result, $incrBy ) {
		// @FIXME use $incrBy if necessary
		// *** necessary to make the hook below work
		if ( $action === 'mailpassword' ) {
			$result = false;
			return false;
		}
	}
```

### d017
```
/**
	 * Use this hook to override the results of User::pingLimiter().
	 *
	 * @since 1.35
	 *
	 * @param User $user User performing the action
	 * @param string $action Action being performed
	 * @param bool &$result Whether or not the action should be prevented
	 *   Change $result and return false to give a definitive answer, otherwise
	 *   the built-in rate limiting checks are used, if enabled.
	 * @param int $incrBy Amount to increment counter by
	 * @return bool|void True or no return value to continue or false to abort
	 */
	public function onPingLimiter( $user, $action, &$result, $incrBy );
```

### d018
```
/**
 * @license GPL-2.0-or-later
 * @author Christoph Jauera <christoph.jauera@wikimedia.de>
 */
class SubmittedTextCache {

	private const CACHE_KEY = 'twoColConflict_yourText';

	public function __construct( private readonly BagOStuff $cache ) {
	}

	/**
	 * @param string $titleDbKey
	 * @param UserIdentity $user
	 * @param SessionId|null $sessionId
	 * @param string $text
	 *
	 * @return bool If caching was successful or not.
	 */
	public function stashText( string $titleDbKey, UserIdentity $user, ?SessionId $sessionId, string $text ): bool {
		$key = $this->makeCacheKey( $titleDbKey, $user, $sessionId );
		return $this->cache->set( $key, $text, ExpirationAwareness::TTL_DAY );
	}

	/**
	 * @param string $titleDbKey
	 * @param UserIdentity $user
	 * @param SessionId|null $sessionId
	 *
	 * @return string|false Returns false when the cache expired
	 */
	public function fetchText( string $titleDbKey, UserIdentity $user, ?SessionId $sessionId ) {
		$key = $this->makeCacheKey( $titleDbKey, $user, $sessionId );
		return $this->cache->get( $key );
	}

	private function makeCacheKey( string $titleDbKey, UserIdentity $user, ?SessionId $sessionId ): string {
		$components = [
			self::CACHE_KEY,
			$titleDbKey,
			$user->getId(),
		];
		// The user ID is specific enough for registered users
		if ( !$user->isRegistered() ) {
			if ( !$sessionId ) {
				throw new UnexpectedValueException( 'Must provide a session for anonymous users' );
			}
			// Warning, the session ID should not use the same spot as the user ID
			$components[] = $sessionId->getId();
		}
		return $this->cache->makeKey( ...$components );
	}

}
```

### d019
```
/**
	 * Helper method to load the current user's unstarred mentees, with caching.
	 * @param UserIdentity $user
	 * @return int[]
	 */
	private function getUnstarredMenteeIds( UserIdentity $user ): array {
		$key = $this->menteeCache->makeKey( 'unstarred', $user->getId() );
		if ( $this->menteeCache->hasKey( $key ) ) {
			return $this->menteeCache->get( $key );
		}

		$mentees = $this->mentorStore->getMenteesByMentor(
			$user,
			MentorStore::ROLE_PRIMARY,
			false,
			false
		);
		$menteeIds = array_map( static fn ( UserIdentity $user ) => $user->getId(), $mentees );
		$starredMenteeIds = $this->getStarredMenteeIds( $user );
		$unstarredMenteeIds = array_diff( $menteeIds, $starredMenteeIds );

		$this->menteeCache->set( $key, $unstarredMenteeIds );
		return $unstarredMenteeIds;
	}
```

### d020
```
class ThrottleOverrideHooks implements
	PingLimiterHook,
	ExemptFromAccountCreationThrottleHook,
	SetupAfterCacheHook,
	SpecialPage_initListHook
{

	private const NO_OVERRIDE = -1;

	private ThrottleOverrideUtils $utils;

	public function __construct(
		private readonly Config $config,
		LBFactory $lbFactory,
		private readonly WANObjectCache $cache,
	) {
		$this->utils = new ThrottleOverrideUtils(
			$config,
			$lbFactory
		);
	}

	/**
	 * @param string $ip
	 * @return bool
	 */
	public function onExemptFromAccountCreationThrottle( $ip ) {
		$result = false;
		$user = RequestContext::getMain()->getUser();
		return $this->doPingLimiter( $user, 'actcreate', $result, $ip );
	}

	/**
	 * @throws InvalidArgumentException If $action is invalid
	 *
	 * @param User $user
	 * @param string $action
	 * @param bool &$result
	 * @param int $incrBy
	 *
	 * @return bool
	 */
	public function onPingLimiter( $user, $action, &$result, $incrBy ) {
		return $this->doPingLimiter( $user, $action, $result );
	}

	/**
	 * @param User $user
	 * @param string $action
	 * @param bool &$result
	 * @param null|string $ip
	 *
	 * @return bool
	 */
	public function doPingLimiter( $user, $action, &$result, $ip = null ) {
		$rateLimits = $this->config->get( MainConfigNames::RateLimits );
		if ( $action !== 'actcreate' && !isset( $rateLimits[$action] ) ) {
			return true;
		}

		if ( $user->isAnon() && IPUtils::isValid( $user->getName() ) ) {
			$ip = $user->getName();
		} elseif ( $ip === null ) {
			$ip = RequestContext::getMain()->getRequest()->getIP();
		}
		$hexIp = IPUtils::toHex( $ip );

		$fname = __METHOD__;
		$utils = $this->utils;
		$expiry = $this->cache->getWithSetCallback(
			$this->cache->makeGlobalKey(
				'throttle_override',
				$this->config->get( 'ThrottleOverrideCentralWiki' ),
				$action,
				$hexIp
			),
			$this->cache::TTL_HOUR,
			static function ( $cValue, &$ttl, &$setOpts, $asOf ) use ( $utils, $hexIp, $action, $fname ) {
				$dbr = $utils->getCentralDB( DB_REPLICA );
				$setOpts += Database::getCacheSetOptions( $dbr );

				$expiry = $dbr->newSelectQueryBuilder()
					->select( 'thr_expiry' )
					->from( 'throttle_override' )
					->where( [
						$dbr->expr( 'thr_range_start', '<=', $hexIp ),
						$dbr->expr( 'thr_range_end', '>=', $hexIp ),
						$dbr->expr( 'thr_expiry', '>', $dbr->timestamp() ),
						$dbr->expr( 'thr_type', IExpression::LIKE,
							new LikeValue( $dbr->anyString(), $action, $dbr->anyString() ) ),
					] )
					->orderBy( 'thr_expiry', SelectQueryBuilder::SORT_DESC )
					->caller( $fname )
					->fetchField();

				if ( $expiry !== false ) {
					// An override exists; cache for the override's
					// current-time-left. Cache will be purged via checkKey
					// updates on record modification. Avoid "0" (infinite)
					// and negative numbers for sanity.
					$ttl = max( (int)wfTimestamp( TS_UNIX, $expiry ) - time(), 1 );
				}

				// If we return false the value will not be cached
				return ( $expiry === false ) ? self::NO_OVERRIDE : $expiry;
			},
			[
				'checkKeys' => [ $utils->getBucketKey( $this->cache, $ip ) ]
			]
		);

		if ( $expiry === self::NO_OVERRIDE ) {
			// We checked the database and found no record
			return true;
		} elseif ( wfTimestamp( TS_UNIX, $expiry ) > time() ) {
			// Valid exemption. Disable the throttle.
			$logger = LoggerFactory::getInstance( 'throttleOverride' );
			$logger->info( 'User {user} (ip: {ip}) exempted from throttle {action}', [
				'user' => $user,
				'ip' => $ip,
				'action' => $action,
			] );

			$result = false;
			return false;
		}

		return true;
	}

	public function onSetupAfterCache() {
		global $wgThrottleOverrideCentralWiki;
		if ( $wgThrottleOverrideCentralWiki === false ) {
			$wgThrottleOverrideCentralWiki = WikiMap::getCurrentWikiId();
		}
	}

	/** @inheritDoc */
	public function onSpecialPage_initList( &$specialPages ) {
		if ( $this->utils->isCentralWiki() ) {
			$specialPages['OverrideThrottle'] = [
				'class' => SpecialOverrideThrottle::class,
				'services' => [
					'MainConfig',
					'ContentLanguage',
					'JobQueueGroup',
					'DBLoadBalancerFactory',
					'MainWANObjectCache',
				],
			];
			$specialPages['ThrottleOverrideList'] = [
				'class' => SpecialThrottleOverrideList::class,
				'services' => [
					'CommentFormatter',
					'LinkRenderer',
				],
			];
		}
	}
}
```

## Output

Return raw JSON only. No preamble, no markdown fences, no commentary outside the
object.

```json
{
  "query_id": "B5",
  "labels": {
    "d001": {"score": 1.0, "rationale": "iterative binary search over sorted array"},
    "d002": {"score": 0.0, "rationale": "pytest case asserting search behaviour, not an implementation"}
  }
}
```

Every `doc_id` presented must appear exactly once in `labels`.
