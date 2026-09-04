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
function computeFileHash(string $filepath): string {
    return hash_file('sha256', $filepath);
}
```

## Candidates

### d001
```
/**
	 * @param string $filepath
	 * @return array|false
	 */
	public function parseFile( string $filepath ) {
		return parse_ini_file( $filepath, true );
	}
```

### d002
```
/**
	 * Data for the fake stdin
	 *
	 * @param string $filepath The string to be used instead of stdin
	 */
	public function mockStdin( string $filepath ) {
		$this->mockStdinFile = $filepath;
	}
```

### d003
```
/**
	 * Get the ultimate original storage path for a file
	 *
	 * Use this when putting a new file into the system
	 *
	 * @param string $sha1 File SHA-1 base36
	 * @return string
	 */
	public function getPathForSHA1( $sha1 ) {
		if ( strlen( $sha1 ) < 3 ) {
			throw new InvalidArgumentException( "Invalid file SHA-1." );
		}
		return $this->backend->getContainerStoragePath( "{$this->repoName}-original" ) .
			"/{$sha1[0]}/{$sha1[1]}/{$sha1[2]}/{$sha1}";
	}
```

### d004
```
/**
	 * Get a relative path including trailing slash, e.g. f/fa/
	 * If the repo is not hashed, returns an empty string
	 *
	 * @param string $suffix Basename of file from FileRepo::storeTemp()
	 * @return string
	 */
	public function getTempHashPath( $suffix ) {
		// format is <timestamp>!<name> or just <name>
		$parts = explode( '!', $suffix, 2 );
		// hash path is not based on timestamp
		$name = $parts[1] ?? $suffix;
		return static::getHashPathForLevel( $name, $this->hashLevels );
	}
```

### d005
```
func (v *Viper) searchInPath(in string) (filename string) {
	v.logger.Debug("searching for config in path", "path", in)
	for _, ext := range SupportedExts {
		v.logger.Debug("checking if file exists", "file", filepath.Join(in, v.configName+"."+ext))
		if b, _ := exists(v.fs, filepath.Join(in, v.configName+"."+ext)); b {
			v.logger.Debug("found file", "file", filepath.Join(in, v.configName+"."+ext))
			return filepath.Join(in, v.configName+"."+ext)
		}
	}

	if v.configType != "" {
		if b, _ := exists(v.fs, filepath.Join(in, v.configName)); b {
			return filepath.Join(in, v.configName)
		}
	}

	return ""
}
```

### d006
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

### d007
```
interface ReaddirSynchronousMethod {
    (filepath: string, options: {
        withFileTypes: true;
    }): Dirent[];
    (filepath: string): string[];
}
```

### d008
```
public static function hash2md5( $hash ) {
		// TODO: make MathRenderer::dbHash2md5 public
		$dbr = MediaWikiServices::getInstance()
			->getConnectionProvider()
			->getReplicaDatabase();
		$xhash = unpack( 'H32md5', $dbr->decodeBlob( $hash ) . "                " );
		return $xhash['md5'];
	}
```

### d009
```
/**
	 *
	 * @param SplFileInfo $oFileInfo
	 * @return string The hash
	 */
	public function getFileHash( $oFileInfo ) {
		return sha1_file( $oFileInfo->getPathname() );
	}
```

### d010
```
/**
	 * @param string $salt
	 * @param string $hash
	 * @return string
	 */
	public function imagePath( $salt, $hash ) {
		global $wgCaptchaDirectoryLevels;

		$file = $this->getBackend()->getRootStoragePath() . '/' . $this->getStorageDir() . '/';
		for ( $i = 0; $i < $wgCaptchaDirectoryLevels; $i++ ) {
			$file .= $hash[ $i ] . '/';
		}
		$file .= "image_{$salt}_{$hash}.png";

		return $file;
	}
```

### d011
```
/**
	 * Usage {{filepath|300}}, {{filepath|nowiki}}, {{filepath|nowiki|300}}
	 * or {{filepath|300|nowiki}} or {{filepath|300px}}, {{filepath|200x300px}},
	 * {{filepath|nowiki|200x300px}}, {{filepath|200x300px|nowiki}}.
	 *
	 * @param Parser $parser
	 * @param string $name
	 * @param string $argA
	 * @param string $argB
	 * @return array|string
	 */
	public static function filepath( $parser, $name = '', $argA = '', $argB = '' ) {
		$file = MediaWikiServices::getInstance()->getRepoGroup()->findFile( $name );

		if ( $argA == 'nowiki' ) {
			// {{filepath: | option [| size] }}
			$isNowiki = true;
			$parsedWidthParam = $parser->parseWidthParam( $argB );
		} else {
			// {{filepath: [| size [|option]] }}
			$parsedWidthParam = $parser->parseWidthParam( $argA );
			$isNowiki = ( $argB == 'nowiki' );
		}

		if ( $file ) {
			$url = $file->getFullUrl();

			// If a size is requested...
			if ( count( $parsedWidthParam ) ) {
				$mto = $file->transform( $parsedWidthParam );
				// ... and we can
				if ( $mto && !$mto->isError() ) {
					// ... change the URL to point to a thumbnail.
					$urlUtils = MediaWikiServices::getInstance()->getUrlUtils();
					$url = $urlUtils->expand( $mto->getUrl(), PROTO_RELATIVE ) ?? false;
				}
			}
			if ( $isNowiki ) {
				return [ $url, 'nowiki' => true ];
			}
			return $url;
		} else {
			return '';
		}
	}
```

### d012
```
type Resolved =
  | { loader: "require"; filepath: string }
  | { loader: "import"; filepath: string };
```

### d013
```
/**
	 * Get a relative path including trailing slash, e.g. f/fa/
	 * If the repo is not hashed, returns an empty string
	 *
	 * @param string $suffix Basename of file from FileRepo::storeTemp()
	 * @return string
	 */
	public function getTempHashPath( $suffix ) {
		$parts = explode( '!', $suffix, 2 ); // format is <timestamp>!<name> or just <name>
		$name = $parts[1] ?? $suffix; // hash path is not based on timestamp
		return self::getHashPathForLevel( $name, $this->hashLevels );
	}
```

### d014
```
/**
	 * Compute a non-cryptographic string hash of a file's contents.
	 * If the file does not exist or cannot be read, returns an empty string.
	 *
	 * @since 1.26 Uses MD4 instead of SHA1.
	 * @param string $filePath
	 * @return string Hash
	 */
	protected static function safeFileHash( $filePath ) {
		return FileContentsHasher::getFileContentsHash( $filePath );
	}
```

### d015
```
/** @param {string} filepath */
function validateFilePath(filepath) {
	if (!filepath) throw new Error('load must pass a non-empty string');
}
```

### d016
```
function getFileUrl( $filename ) {
    $hash = md5( $filename );
    return 'https://upload.wikimedia.org/wikipedia/commons/' .
        substr( $hash, 0, 1 ) . '/' .
        substr( $hash, 0, 2 ) . '/' .
        $filename;
}
```

### d017
```
// narrowPath reduces full path to file name and parent dir only.
func narrowPath(fp string) string {
	if !filepath.IsAbs(fp) {
		if abs, err := filepath.Abs(fp); err != nil {
			// seems to be reduced already
			return fp
		} else {
			fp = abs
		}
	}
	return filepath.Join(filepath.Base(filepath.Dir(fp)), filepath.Base(fp))
}
```

### d018
```
/**
	 * @return mixed|string
	 */
	protected function getConfigVar() {
		$filepath = $GLOBALS['IP'] . "/composer.lock";
		if ( !file_exists( $filepath ) ) {
			return '';
		}
		$ts = date( "YmdHis", filemtime( $filepath ) );
		return is_string( $ts ) ? $ts : '';
	}
```

### d019
```
/**
	 * Get the base 36 SHA-1 of a string, padded to 31 digits.
	 * Before hashing, the path will be prefixed with the domain ID.
	 * This should be used internally for lock key or file names.
	 *
	 * @param string $path
	 * @return string
	 */
	final protected function sha1Base36Absolute( $path ) {
		return \Wikimedia\base_convert( sha1( "{$this->domain}:{$path}" ), 16, 36, 31 );
	}
```

### d020
```
function calculateETag($path, $files){
    $etag = '';

    foreach($files as $file){
        $etag .= md5_file($path.$file);
    }

    return $etag;
}
```

## Output

Return raw JSON only. No preamble, no markdown fences, no commentary outside the
object.

```json
{
  "query_id": "C1",
  "labels": {
    "d001": {"score": 1.0, "rationale": "iterative binary search over sorted array"},
    "d002": {"score": 0.0, "rationale": "pytest case asserting search behaviour, not an implementation"}
  }
}
```

Every `doc_id` presented must appear exactly once in `labels`.
