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
public function canUserEdit(User $user, Title $title): bool {
    return $user->isAllowed('edit')
        && !$title->isProtected('edit');
}
```

## Candidates

### d001
```
/**
	 * @param Title $title
	 * @param User $user
	 * @param string $action
	 * @param array &$errors
	 * @param bool $doExpensiveQueries
	 * @param bool $short
	 * @return bool
	 */
	public static function onTitleQuickPermissions( $title, $user, $action, &$errors, $doExpensiveQueries, $short ) {
		if ( $action !== 'delete' || count( $errors ) > 0 ) {
			return true;
		}

		$ns = $title->getNamespace();
		$userName = $user->getName();
		$root = $title->getRootText();
		$text = $title->getText();

		if ( class_exists( 'MediaWiki\Permissions\PermissionManager' ) ) {
			// MW 1.33+
			$userCan = MediaWikiServices::getInstance()
				->getPermissionManager()
				->userCan( 'edit', $user, $title );
		} else {
			$userCan = $title->userCan( 'edit' );
		}

		if (
			( $ns === NS_USER || $ns === NS_USER_TALK )
			&& $userName === $root
			&& $userCan
		) {
			if ( $root === $text && $user->isAllowed( 'delete-rootuserpages' ) ) {
				return false;
			} elseif ( $root !== $text && $user->isAllowed( 'delete-usersubpages' ) ) {
				return false;
			}
		}

		return true;
	}
```

### d002
```
/**
	 * @since 2.4
	 */
	public function hasUserPermission( Title $title, User $user, string $action ): bool {
		$this->errors = [];

		if ( $title->getNamespace() === SMW_NS_SCHEMA ) {
			return $this->checkSchemaNamespacePermission( $title, $user, $action );
		}

		$actions = [ 'edit', 'delete', 'move', 'upload' ];

		if ( !in_array( $action, $actions ) ) {
			return true;
		}

		if ( $title->getNamespace() === NS_MEDIAWIKI ) {
			return $this->checkMwNamespacePatternEditPermission( $title, $user );
		}

		if ( $this->protectionValidator->getCreateProtectionRight() && $title->getNamespace() === SMW_NS_PROPERTY ) {
			return $this->checkPropertyNamespaceCreatePermission( $title, $user );
		}

		if ( $title->getNamespace() === NS_CATEGORY ) {
			return $this->checkChangePropagationProtection( $title );
		}

		if ( !$title->exists() ) {
			return true;
		}

		if ( $title->getNamespace() === SMW_NS_PROPERTY ) {
			return $this->checkPropertyNamespaceEditPermission( $title, $user );
		}

		if ( $this->protectionValidator->hasEditProtectionOnNamespace( $title ) ) {
			return $this->checkEditPermission( $title, $user );
		}

		return true;
	}
```

### d003
```
/**
	 * @param Title|MediaWiki\Title\Title $title
	 * @param User|null $user
	 * @return bool
	 */
	public static function isEditor( $title, $user = null ) {
		if ( !self::isKnownArticle( $title ) ) {
			return false;
		}
		if ( !$user ) {
			$user = self::getUser();
		}
		$page = self::getWikiPage( $title );
		return $page->getUser() === $user->getId();
	}
```

### d004
```
private function checkEditPermission( Title $title, User $user ): bool {
		$editProtectionRight = $this->protectionValidator->getEditProtectionRight();

		// @see https://www.semantic-mediawiki.org/wiki/Help:Special_property_Is_edit_protected
		if (
			!$this->protectionValidator->hasProtection( $title ) ||
			$this->permissionManager->userHasRight( $user, $editProtectionRight ) ) {
			return true;
		}

		$this->errors[] = [ 'smw-edit-protection', $editProtectionRight ];

		return false;
	}
```

### d005
```
/**
	 * @throws MWException
	 * @covers \LockAuthor\LockAuthor::isAllowed
	 */
	public function testIsAllowed() {
		$user = $this->getTestUser()->getUser();
		// Existing is not allowed for non creator
		$title = $this->getExistingTestPage( 'TestLockAuthorExisting1' )->getTitle();
		$result = $this->la->isAllowed( $title, $user, 'edit' );
		$this->assertFalse( $result );
		// Non-existing is allowed
		$title = $this->getNonexistingTestPage( 'TestLockAuthorNonExisting1' )->getTitle();
		$result = $this->la->isAllowed( $title, $user, 'edit' );
		$this->assertTrue( $result );
		// Existing is allowed for  creator
		$user = $this->getTestSysop()->getUser();
		$title = $this->getExistingTestPage( 'TestLockAuthorExisting2' )->getTitle();
		$result = $this->la->isAllowed( $title, $user, 'edit' );
		$this->assertTrue( $result );
		// Editor is allowed to edit all
		$user = $this->getTestUser( 'editor' )->getUser();
		$title = $this->getExistingTestPage( 'TestLockAuthorExisting2' )->getTitle();
		$result = $this->la->isAllowed( $title, $user, 'edit' );
		$this->assertTrue( $result );
		// Excluded namespaces
		$user = $this->getTestUser()->getUser();
		$title = $this->getExistingTestPage( Title::newFromText( 'TestFile', NS_FILE ) )->getTitle();
		$result = $this->la->isAllowed( $title, $user, 'edit' );
		$this->assertTrue( $result );
		// Not related actions
		$user = $this->getTestUser()->getUser();
		$title = $this->getExistingTestPage( 'TestLockAuthorExisting1' )->getTitle();
		$result = $this->la->isAllowed( $title, $user, 'read' );
		$this->assertTrue( $result );
	}
```

### d006
```
/**
	 * @param Title $title
	 * @param User $user
	 * @param WebRequest $req
	 * @return bool
	 */
	private function isSupportedEditPage( Title $title, User $user, WebRequest $req ): bool {
		if (
			$req->getVal( 'action' ) !== 'edit' ||
			!MediaWikiServices::getInstance()->getPermissionManager()->quickUserCan( 'edit', $user, $title )
		) {
			return false;
		}

		foreach ( self::UNSUPPORTED_EDIT_PARAMS as $param ) {
			if ( $req->getVal( $param ) !== null ) {
				return false;
			}
		}

		switch ( self::getEditPageEditor( $user, $req ) ) {
			case 'visualeditor':
				return $this->visualEditorAvailabilityLookup->isAvailable( $title, $req, $user ) ||
					self::isWikitextAvailable( $title, $user );
			case 'wikitext':
			default:
				return self::isWikitextAvailable( $title, $user );
		}
	}
```

### d007
```
/**
	 * @param File|null $img
	 * @param Parser $parser
	 * @return bool
	 */
	private function isReadOnly( $img, $parser ) {
		$user = RequestContext::getMain()->getUser();
		$permissionManager = $this->services->getPermissionManager();
		$pageRef = $parser->getPage();
		$title = Title::castFromPageReference( $pageRef );
		if ( !$title ) {
			return true;
		}

		$isProtected = $this->services->getRestrictionStore()->isProtected( $title, 'edit' );
		$uploadsEnabled = $this->config->get( 'EnableUploads' );
		$canUpload = $permissionManager->userCan( 'upload', $user, $title );
		$canReupload = $permissionManager->userCan( 'reupload', $user, $title );

		return !$uploadsEnabled || !$canUpload || !$canReupload || $isProtected;
	}
```

### d008
```
/**
	 * Check whether the blacklist restricts given user
	 * performing a specific action on the given Title
	 *
	 * @param Title $title Title to check
	 * @param User $user User to check
	 * @param string $action Action to check; 'edit' if unspecified
	 * @param bool $override If set to true, overrides work
	 * @return TitleBlacklistEntry|bool The corresponding TitleBlacklistEntry if
	 * blacklisted; otherwise false
	 */
	public function userCannot( $title, $user, $action = 'edit', $override = true ) {
		$entry = $this->isBlacklisted( $title, $action );
		if ( !$entry ) {
			return false;
		}
		$params = $entry->getParams();
		if ( isset( $params['autoconfirmed'] ) && $user->isAllowed( 'autoconfirmed' ) ) {
			return false;
		}
		if ( $override && self::userCanOverride( $user, $action ) ) {
			return false;
		}
		return $entry;
	}
```

### d009
```
/**
	 * @param Title|MediaWiki\Title\Title $title
	 * @param User $user
	 * @param string $action
	 * @param array|string|MessageSpecifier &$result
	 * @return bool
	 * @see https://www.mediawiki.org/wiki/Manual:Hooks/getUserPermissionsErrors
	 */
	public static function onGetUserPermissionsErrors( $title, $user, $action, &$result ) {
		// if ( \PageEncryption::isAuthorized( $user ) ) {
		// 	return true;
		// }

		if ( !\PageEncryption::isEncryptedNamespace( $title ) ) {
			return true;
		}

		if ( $action !== 'edit' && $action !== 'create' ) {
			return true;
		}

		if ( !$title->isKnown() && $user->isAllowed( 'pageencryption-can-manage-encryption' ) ) {
			return true;
		}

		if ( \PageEncryption::isEditor( $title, $user ) ) {
			return true;
		}

		$result = [ 'badaccess-group0' ];
		return false;
	}
```

### d010
```
/**
	 *
	 * @param Title $title
	 * @return bool
	 */
	protected function userCanRead( Title $title ) {
		if ( $this->isSystemUser ) {
			return true;
		}
		return MediaWikiServices::getInstance()
			->getPermissionManager()
			->userCan( 'read', $this->context->getUser(), $title );
	}
```

### d011
```
class UserPageEditProtection implements GetUserPermissionsErrorsHook {

	/** @inheritDoc */
	public function onGetUserPermissionsErrors( $title, $user, $action, &$result ) {
		global $wgOnlyUserEditUserPage;

		if (
			$wgOnlyUserEditUserPage &&
			( $action === 'edit' || $action === 'move' ) &&
			$title->getNamespace() === NS_USER &&
			$title->getRootText() !== $user->getName() &&
			!$user->isAllowed( 'editalluserpages' )
		) {
			// TODO: This really should return a message
			$result = false;
			return false;
		}
		return true;
	}
}
```

### d012
```
/**
	 *
	 * @param Title $title
	 * @param User $user
	 * @return bool
	 */
	public function applies( Title $title, User $user ) {
		$userGroupManager = $this->services->getUserGroupManager();
		if ( in_array( 'sysop', $userGroupManager->getUserGroups( $user ) ) ) {
			// ERM:20238 Never lockdown sysops or there could be a page that can
			// never be edited again
			return false;
		}
		return $title->exists() && $title->getNamespace() >= 0;
	}
```

### d013
```
private function checkPropertyNamespaceEditPermission( Title $title, User $user ): bool {
		// This renders full protection until the ChangePropagationDispatchJob was run
		if ( !$this->protectionValidator->hasChangePropagationProtection( $title ) ) {
			return $this->checkEditPermission( $title, $user );
		}

		$this->errors[] = [ 'smw-change-propagation-protection' ];

		return false;
	}
```

### d014
```
class DeleteUserPages {

	/**
	 * @param Title $title
	 * @param User $user
	 * @param string $action
	 * @param array &$errors
	 * @param bool $doExpensiveQueries
	 * @param bool $short
	 * @return bool
	 */
	public static function onTitleQuickPermissions( $title, $user, $action, &$errors, $doExpensiveQueries, $short ) {
		if ( $action !== 'delete' || count( $errors ) > 0 ) {
			return true;
		}

		$ns = $title->getNamespace();
		$userName = $user->getName();
		$root = $title->getRootText();
		$text = $title->getText();

		if ( class_exists( 'MediaWiki\Permissions\PermissionManager' ) ) {
			// MW 1.33+
			$userCan = MediaWikiServices::getInstance()
				->getPermissionManager()
				->userCan( 'edit', $user, $title );
		} else {
			$userCan = $title->userCan( 'edit' );
		}

		if (
			( $ns === NS_USER || $ns === NS_USER_TALK )
			&& $userName === $root
			&& $userCan
		) {
			if ( $root === $text && $user->isAllowed( 'delete-rootuserpages' ) ) {
				return false;
			} elseif ( $root !== $text && $user->isAllowed( 'delete-usersubpages' ) ) {
				return false;
			}
		}

		return true;
	}
}
```

### d015
```
private function checkMwNamespacePatternEditPermission( Title $title, User $user ): bool {
		// @see https://www.semantic-mediawiki.org/wiki/Help:Special_property_Allows_pattern
		if (
			$title->getDBKey() !== AllowsPatternValue::REFERENCE_PAGE_ID ||
			$this->permissionManager->userHasRight( $user, 'smw-patternedit' ) ) {
			return true;
		}

		$this->errors[] = [ 'smw-patternedit-protection', 'smw-patternedit' ];

		return false;
	}
```

### d016
```
/**
	 * Ensure that the user has the 'edit' permission for the given title
	 *
	 * @param User $user
	 * @param Title $title
	 * @throws PermissionsError if the user does not have the necessary permission
	 */
	private function ensureUserCanEdit( User $user, Title $title ): void {
		$userCanEdit = $this->permissionManager->userCan( 'edit', $user, $title );
		if ( !$userCanEdit ) {
			$editPermissionErrors = $this->permissionManager->getPermissionErrors( 'edit', $user, $title );
			throw new PermissionsError( 'edit', $editPermissionErrors );
		}
	}
```

### d017
```
/**
 * Class LockAuthorTest
 * @group Database
 */
class LockAuthorTest extends MediaWikiLangTestCase {

	/**
	 * @var LockAuthor
	 */
	private $la;

	public function setUp(): void {
		$this->overrideConfigValues( [
			'LockAuthorExcludedNamespaces' => [
				NS_FILE,
			],
			'LockAuthorActions' => [
				'edit',
				'create',
			],
		] );
		$this->setGroupPermissions( '*', 'edit', false );
		$this->setGroupPermissions( '*', 'createpage', false );

		$this->setGroupPermissions( 'user', 'edit', true );
		$this->setGroupPermissions( 'user', 'createpage', true );

		$this->setGroupPermissions( 'editor', 'edit', true );
		$this->setGroupPermissions( 'editor', 'createpage', true );
		$this->setGroupPermissions( 'editor', 'editall', true );
		$services = $this->getServiceContainer();
		$this->la = new LockAuthor(
			$services->getConfigFactory()->makeConfig( 'LockAuthor' ),
			$services->getPermissionManager(),
			$services->getRevisionLookup()
		);
	}

	/**
	 * @throws MWException
	 * @covers \LockAuthor\LockAuthor::isAuthor
	 */
	public function testIsAuthor() {
		$user = $this->getTestUser()->getUser();
		$title = $this->getExistingTestPage( 'TestLockAuthorExisting1' )->getTitle();
		$result = $this->la->isAuthor( $title, $user );
		$this->assertFalse( $result );
		$result = $this->la->isAuthor( $title, $this->getTestSysop()->getUser() );
		$this->assertTrue( $result );
	}

	/**
	 * @throws MWException
	 * @covers \LockAuthor\LockAuthor::isAllowed
	 */
	public function testIsAllowed() {
		$user = $this->getTestUser()->getUser();
		// Existing is not allowed for non creator
		$title = $this->getExistingTestPage( 'TestLockAuthorExisting1' )->getTitle();
		$result = $this->la->isAllowed( $title, $user, 'edit' );
		$this->assertFalse( $result );
		// Non-existing is allowed
		$title = $this->getNonexistingTestPage( 'TestLockAuthorNonExisting1' )->getTitle();
		$result = $this->la->isAllowed( $title, $user, 'edit' );
		$this->assertTrue( $result );
		// Existing is allowed for  creator
		$user = $this->getTestSysop()->getUser();
		$title = $this->getExistingTestPage( 'TestLockAuthorExisting2' )->getTitle();
		$result = $this->la->isAllowed( $title, $user, 'edit' );
		$this->assertTrue( $result );
		// Editor is allowed to edit all
		$user = $this->getTestUser( 'editor' )->getUser();
		$title = $this->getExistingTestPage( 'TestLockAuthorExisting2' )->getTitle();
		$result = $this->la->isAllowed( $title, $user, 'edit' );
		$this->assertTrue( $result );
		// Excluded namespaces
		$user = $this->getTestUser()->getUser();
		$title = $this->getExistingTestPage( Title::newFromText( 'TestFile', NS_FILE ) )->getTitle();
		$result = $this->la->isAllowed( $title, $user, 'edit' );
		$this->assertTrue( $result );
		// Not related actions
		$user = $this->getTestUser()->getUser();
		$title = $this->getExistingTestPage( 'TestLockAuthorExisting1' )->getTitle();
		$result = $this->la->isAllowed( $title, $user, 'read' );
		$this->assertTrue( $result );
	}

}
```

### d018
```
/**
	 *
	 * @return bool
	 */
	protected function userCanEdit() {
		$title = $this->context->getTitle();
		$user = $this->context->getUser();
		if ( \MediaWiki\MediaWikiServices::getInstance()
			->getPermissionManager()
			->userCan( 'edit', $user, $title )
		) {
			return true;
		}
		return false;
	}
```

### d019
```
/**
	 * Should the editor links trigger on this page?
	 *
	 * @param Title $title
	 * @param User $user
	 * @return bool
	 */
	private static function trigger( Title $title, User $user ) {
		if ( $title && $title->getNamespace() == NS_FILE ) {
			if ( class_exists( 'MediaWiki\Permissions\PermissionManager' ) ) {
				// MW 1.33+
				$pm = MediaWikiServices::getInstance()->getPermissionManager();
				return $pm->userCan( 'edit', $user, $title ) &&
					$pm->userCan( 'upload', $user, $title );
			} else {
				return $title->userCan( 'edit' ) && $title->userCan( 'upload' );
			}
		}
		return false;
	}
```

## Output

Return raw JSON only. No preamble, no markdown fences, no commentary outside the
object.

```json
{
  "query_id": "B1",
  "labels": {
    "d001": {"score": 1.0, "rationale": "iterative binary search over sorted array"},
    "d002": {"score": 0.0, "rationale": "pytest case asserting search behaviour, not an implementation"}
  }
}
```

Every `doc_id` presented must appear exactly once in `labels`.
