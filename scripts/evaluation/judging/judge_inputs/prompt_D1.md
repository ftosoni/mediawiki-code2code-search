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

## Candidates

### d001
```
class WikiTextLinksHelper {

	/**
	 *
	 * @var string
	 */
	protected $wikitext = '';

	protected $categories = null;
	protected $links = null;
	protected $files = null;
	protected $interwikiLinks = null;
	protected $interlanguageLinks = null;

	/**
	 *
	 * @param string &$wikitext
	 */
	public function __construct( &$wikitext ) {
		$this->wikitext =& $wikitext;
	}

	/**
	 *
	 * @return CategoryLinksHelper
	 */
	public function getCategoryLinksHelper() {
		if ( $this->categories ) {
			return $this->categories;
		}
		$this->categories = new CategoryLinksHelper( $this->wikitext );
		return $this->categories;
	}

	/**
	 *
	 * @return InternalLinksHelper
	 */
	public function getInternalLinksHelper() {
		if ( $this->links ) {
			return $this->links;
		}
		$this->links = new InternalLinksHelper( $this->wikitext );
		return $this->links;
	}

	/**
	 *
	 * @return FileLinksHelper
	 */
	public function getFileLinksHelper() {
		if ( $this->files ) {
			return $this->files;
		}
		$this->files = new FileLinksHelper( $this->wikitext );
		return $this->files;
	}

	/**
	 *
	 * @return InterwikiLinksHelper
	 */
	public function getInterwikiLinksHelper() {
		if ( $this->interwikiLinks ) {
			return $this->interwikiLinks;
		}
		$this->interwikiLinks = new InterwikiLinksHelper(
			$this->wikitext,
			MediaWikiServices::getInstance()
		);
		return $this->interwikiLinks;
	}

	/**
	 *
	 * @return InterlanguageLinksHelper
	 */
	public function getLanguageLinksHelper() {
		if ( $this->interlanguageLinks ) {
			return $this->interlanguageLinks;
		}
		$this->interlanguageLinks = new InterlanguageLinksHelper(
			$this->wikitext,
			MediaWikiServices::getInstance()
		);
		return $this->interlanguageLinks;
	}
}
```

### d002
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

### d003
```
/**
	 * @param string $wikitext unparsed wikitext
	 * @param int $namespace namespace of the page from which the wikitext was passed
	 * @return Link[] array of links in the text
	 */
	public function getLinksToNamespace( $wikitext, $namespace ) {
		preg_match_all( '/\[\[(.*?)(\|(.*?)|)\]\]/i', $wikitext, $textLinks, PREG_PATTERN_ORDER );
		$links = [];
		$textLinksCount = count( $textLinks[1] );
		for ( $i = 0; $i < $textLinksCount; $i++ ) {
			try {
				$title = Title::newFromTextThrow( $textLinks[1][$i] );
				if ( $title->inNamespace( $namespace ) ) {
					if ( $textLinks[3][$i] === '' ) {
						$links[] = new Link( $title, $title->getSubpageText() );
					} else {
						$links[] = new Link( $title, $textLinks[3][$i] );
					}
				}
			} catch ( MalformedTitleException ) {
				// We ignore invalid links
			}
		}
		return $links;
	}
```

### d004
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

### d005
```
/**
	 * @return string[]
	 */
	private function getItemList( string $wikitext ): array {
		// Extract non-empty first-level list elements, exclude 2nd and deeper levels
		preg_match_all( '/^\*\h*([^\s*#:;].*?)\h*$/mu', $wikitext, $matches );
		return $matches[1];
	}
```

### d006
```
/**
	 * @param string $wikitext
	 * @return Title[]
	 */
	private function getFilesFromWikiText( $wikitext ): array {
		$titles = [];
		$tags = preg_match_all(
			"#\[\[(.*?)\]\]#is",
			$wikitext,
			$matches
		);
		if ( $tags ) {
			foreach ( $matches[1] as $match ) {
				$title = $this->getTitle( $match );
				$titles[] = $title;
			}
		}
		return $titles;
	}
```

### d007
```
/**
	 *
	 * @param Title[] $links
	 * @param bool|false $removeAllOccurrences
	 * @return InternalLinksHelper
	 */
	public function removeTargets( $links, $removeAllOccurrences = false ) {
		$replaced = $this->maskParserFunctions();
		foreach ( $links as $linkText => $target ) {
			if ( !$target instanceof Title ) {
				continue;
			}
			$this->removeTarget( $target, $removeAllOccurrences );
		}
		$this->unmaskParserFunctions( $replaced );
		return $this;
	}
```

### d008
```
pub fn extract_links(&mut self, wikitext: &str) -> Result<Vec<WikiLink>, &'static str> {
        let parse_opts = ParseOptions::new();
        let tree = self.parser.parse_with_options(
            &mut |i, _| {
                if i < wikitext.len() {
                    &wikitext[i..]
                } else {
                    ""
                }
            },
            None,
            Some(parse_opts),
        );
        if let Some(tree) = tree {
            let root_node = tree.root_node();
            let mut query_cursor = QueryCursor::new();
            let mut captures =
                query_cursor.captures(&self.link_query, root_node, wikitext.as_bytes());

            let mut links = Vec::new();
            while let Some((mat, _capture_index)) = captures.next() {
                let mut current_link_label = None;
                let mut current_link_title: WikiTitle = WikiTitle::new("", String::from("en"));
                let mut current_link_range = mat.captures[0].node.range();
                // Process all captures in this match
                for capture in mat.captures {
                    let capture_name = &self.link_query.capture_names()[capture.index as usize];
                    let node_text = get_node_text(capture.node, wikitext);

                    match *capture_name {
                        "link.title" => {
                            let title = node_text.trim_matches('"').trim_matches('\'');
                            if !title.contains(':') && !title.contains('.') {
                                current_link_title = WikiTitle::new(title,String::from("en"));
                                current_link_range = capture.node.range();
                            }
                        }
                        "link.label" => {
                            current_link_label = Some(node_text);
                        }
                        _ => {}
                    }
                }
                let current_link = WikiLink {
                    title: current_link_title,
                    range: current_link_range,
                    label: current_link_label,
                };

                // Only add if we found a valid title
                if current_link.title.is_valid() {
                    links.push(current_link);
                }
            }
            Ok(links)
        } else {
            Err("Parse error")
        }
    }
```

### d009
```
/**
	 * Extract & count links from wikitext
	 *
	 * @param $num_articles int
	 * @param $wikitext string article text
	 * @return array with links and their weights
	 */
	private function getWeightedLinks( $num_articles, $wikitext ) {
		global $wgCollectionSuggestCheapWeightThreshhold;

		$allLinks = array();
		preg_match_all(
			'/\[\[(.+?)\]\]/',
			$wikitext,
			$allLinks,
			PREG_SET_ORDER
		);

		$linkmap = array();
		foreach ( $allLinks as $link ) {
			$link = $link[1];

			if ( preg_match( '/[:#]/', $link ) ) { // skip links with ':' and '#'
				continue;
			}

			// handle links with a displaytitle
			$matches = array();
			if ( preg_match( '/(.+?)\|(.+)/', $link, $matches ) ) {
				$link = $matches[1];
				$alias = $matches[2];
			} else {
				$alias = $link;
			}

			// check & normalize title
			$title = Title::makeTitleSafe( NS_MAIN, $link );
			if ( is_null( $title ) || !$title->exists() ) {
				continue;
			}
			$resolved = $this->resolveRedirects( $title );
			if ( !$resolved ) {
				continue;
			}
			$link = $resolved->getText();

			if ( isset ( $linkmap[$link] ) ) {
				$linkmap[$link][$link] = true;
			} else {
				$linkmap[$link] = array( $link => true );
			}
			if ( $link != $alias ) {
				if ( isset( $linkmap[$alias] ) ) {
					$linkmap[$alias][$link] = true;
				} else {
					$linkmap[$alias] = array( $link => true );
				}
			}
		}

		$linkcount = array();
		if ( $num_articles < $wgCollectionSuggestCheapWeightThreshhold ) {
			// more expensive algorithm: count words
			foreach ( $linkmap as $alias => $linked ) {
				$matches = array();
				preg_match_all(
					'/\W' . preg_quote( $alias, '/' ) . '\W/i',
					$wikitext,
					$matches
				);
				$num = count( $matches[0] );

				foreach ( $linked as $link => $dummy ) {
					if ( isset( $linkcount[$link] ) ) {
						$linkcount[$link] += $num;
					} else {
						$linkcount[$link] = $num;
					}
				}
			}

			if ( count( $linkcount ) == 0 ) {
				return array();
			}

			// normalize:
			$lc_max = 0;
			foreach ( $linkcount as $count ) {
				if ( $count > $lc_max ) {
					$lc_max = $count;
				}
			}
			$norm = log( $lc_max );
			$result = array();
			if ( $norm > 0 ) {
				foreach ( $linkcount as $link => $count ) {
					$result[$link] = 1 + 0.5 * log( $count ) / $norm;
				}
			} else {
				foreach ( $linkcount as $link => $count ) {
					$result[$link] = 1;
				}
			}

			return $result;
		} else {
			// cheaper algorithm: just count links
			foreach ( $linkmap as $linked ) {
				foreach ( $linked as $link => $dummy ) {
					$linkcount[$link] = 1;
				}
			}

			return $linkcount;
		}
	}
```

### d010
```
/**
	 *
	 * @return array
	 */
	protected function parse() {
		$replaced = $this->maskParserFunctions();
		$pattern = $this->getPattern();
		$matches = [];
		$matchCount = preg_match_all(
			$pattern,
			$this->wikitext,
			$matches,
			PREG_SET_ORDER
		);
		$links = [];
		foreach ( $matches as $match ) {
			[ $fullMatch, $leadingColon, $titleText ] = $match;
			$title = $this->makeTitleFromMatch(
				$fullMatch,
				$leadingColon,
				$titleText
			);
			if ( !$title ) {
				continue;
			}
			$links[$fullMatch] = $title;
		}
		$this->unmaskParserFunctions( $replaced );
		return $links;
	}
```

### d011
```
/**
 * @license GPL-2.0-or-later
 *
 * Utility class to extract links for wikitext pages
 */
class WikitextLinksExtractor {

	/**
	 * @param string $wikitext unparsed wikitext
	 * @param int $namespace namespace of the page from which the wikitext was passed
	 * @return Link[] array of links in the text
	 */
	public function getLinksToNamespace( $wikitext, $namespace ) {
		preg_match_all( '/\[\[(.*?)(\|(.*?)|)\]\]/i', $wikitext, $textLinks, PREG_PATTERN_ORDER );
		$links = [];
		$textLinksCount = count( $textLinks[1] );
		for ( $i = 0; $i < $textLinksCount; $i++ ) {
			try {
				$title = Title::newFromTextThrow( $textLinks[1][$i] );
				if ( $title->inNamespace( $namespace ) ) {
					if ( $textLinks[3][$i] === '' ) {
						$links[] = new Link( $title, $title->getSubpageText() );
					} else {
						$links[] = new Link( $title, $textLinks[3][$i] );
					}
				}
			} catch ( MalformedTitleException ) {
				// We ignore invalid links
			}
		}
		return $links;
	}
}
```

### d012
```
class InternalLinksHelper {

	/**
	 *
	 * @var string
	 */
	protected $wikitext = '';

	/**
	 *
	 * @param string &$wikitext
	 */
	public function __construct( &$wikitext ) {
		$this->wikitext =& $wikitext;
	}

	/**
	 *
	 * @return array
	 */
	protected function parse() {
		$replaced = $this->maskParserFunctions();
		$pattern = $this->getPattern();
		$matches = [];
		$matchCount = preg_match_all(
			$pattern,
			$this->wikitext,
			$matches,
			PREG_SET_ORDER
		);
		$links = [];
		foreach ( $matches as $match ) {
			[ $fullMatch, $leadingColon, $titleText ] = $match;
			$title = $this->makeTitleFromMatch(
				$fullMatch,
				$leadingColon,
				$titleText
			);
			if ( !$title ) {
				continue;
			}
			$links[$fullMatch] = $title;
		}
		$this->unmaskParserFunctions( $replaced );
		return $links;
	}

	/**
	 * Parser functions like "{{#ask:[[Category:ABC]]}}" will be recognized as internal links
	 * So to preserve them they are masked with "###$id###" and saved in this array.
	 * These queries are restored to original view when adding category to page.
	 *
	 * @return array Array with information about what was replaced and replacement that was used.
	 * Has next structure:
	 * <dl>
	 *   <dt>Index 0</dt><dd>Original parser function</dd>
	 *   <dt>Index 1</dt><dd>Parser function replacement.
	 * 		Used as a key to return it to original view</dd>
	 * </dl>
	 * @see CategoryLinksHelper::unmaskParserFunctions()
	 */
	public function maskParserFunctions(): array {
		$replacedQueries = [];
		// Mask semantic queries to prevent them from changing
		$this->wikitext = preg_replace_callback(
			"#\{\{[^}]+\}\}#is",
			static function ( $matches ) use( &$replacedQueries ) {
				$id = count( $replacedQueries );
				$replacement = "###$id###";

				$replacedQueries[] = [ $matches[0], $replacement ];

				return $replacement;
			},
			$this->wikitext
		);

		return $replacedQueries;
	}

	/**
	 * Restores parser functions to original view after masking them.
	 * Must be used after {@link CategoryLinksHelper::maskParserFunctions()}.
	 *
	 * @param array $replacedQueries Array with information about replacements done.
	 * 	Got from {@link CategoryLinksHelper::maskParserFunctions()}
	 */
	public function unmaskParserFunctions( array $replacedQueries ) {
		if ( empty( $replacedQueries ) ) {
			return;
		}
		// Replace semantic queries masks back with original queries
		$maskedQueryPattern = "\#\#\#([0-9]+)\#\#\#";

		$this->wikitext = preg_replace_callback(
			"#" . $maskedQueryPattern . "#",
			static function ( $matches ) use( $replacedQueries ) {
				return $replacedQueries[$matches[1]][0];
			},
			$this->wikitext
		);
	}

	/**
	 *
	 * @return string
	 */
	public function getWikitext() {
		return $this->wikitext;
	}

	/**
	 *
	 * @param string $fullMatch
	 * @param string $leadingColon
	 * @param string $titleText
	 * @return Title|null
	 */
	protected function makeTitleFromMatch( $fullMatch, $leadingColon, $titleText ) {
		return Title::newFromText( $titleText );
	}

	/**
	 *
	 * @return string
	 */
	protected function getPattern() {
		return "#\[\[([ :])?(.*?)([\|].*?\]\]|\]\])#si";
	}

	/**
	 *
	 * @return array
	 */
	public function getTargets() {
		return $this->parse();
	}

	/**
	 *
	 * @param Title $target
	 * @param bool $removeAllOccurrences
	 */
	protected function removeTarget( Title $target, $removeAllOccurrences ) {
		foreach ( $this->getTargets() as $match => $title ) {
			if ( !$target->equals( $title ) ) {
				continue;
			}
			$this->wikitext = preg_replace(
				"#" . preg_quote( $match, '/' ) . "#si",
				'',
				$this->wikitext,
				$removeAllOccurrences ? -1 : 1
			);
			break;
		}
	}

	/**
	 *
	 * @param Title $target
	 * @param string|false $text
	 * @param bool $addDuplicates
	 * @param bool $leadingColon
	 * @param string $separator
	 */
	protected function addTarget( Title $target, $text, $addDuplicates, $leadingColon = true,
		$separator = "\n" ) {
		if ( !$addDuplicates ) {
			foreach ( $this->getTargets() as $match => $title ) {
				if ( !$target->equals( $title ) ) {
					continue;
				}
				return;
			}
		}
		$linkWikiText = "[[";
		if ( !empty( $this->wikitext ) ) {
			$linkWikiText = $separator . $linkWikiText;
		}

		if ( $target->getNamespace() !== NS_MAIN ) {
			if ( $leadingColon && in_array( $target->getNamespace(), [ NS_FILE, NS_CATEGORY ] ) ) {
				$linkWikiText .= ':';
			}
			$linkWikiText .= MediaWikiServices::getInstance()
				->getNamespaceInfo()
				->getCanonicalName( $target->getNamespace() );
			$linkWikiText .= ':';
		}
		$linkWikiText .= $target->getText();
		if ( $text ) {
			$linkWikiText .= "|$text";
		}
		$linkWikiText .= "]]";
		$this->wikitext .= $linkWikiText;
	}

	/**
	 *
	 * @param Title[] $links
	 * @param bool|false $removeAllOccurrences
	 * @return InternalLinksHelper
	 */
	public function removeTargets( $links, $removeAllOccurrences = false ) {
		$replaced = $this->maskParserFunctions();
		foreach ( $links as $linkText => $target ) {
			if ( !$target instanceof Title ) {
				continue;
			}
			$this->removeTarget( $target, $removeAllOccurrences );
		}
		$this->unmaskParserFunctions( $replaced );
		return $this;
	}

	/**
	 *
	 * @param Title[] $links
	 * @param bool|true $addDuplicates
	 * @param string $separator
	 * @return InternalLinksHelper
	 */
	public function addTargets( $links, $addDuplicates = true, $separator = "\n" ) {
		foreach ( $links as $linkText => $target ) {
			if ( !$target instanceof Title ) {
				continue;
			}
			if ( empty( $linkText ) || is_numeric( $linkText ) ) {
				$linkText = false;
			}
			$this->addTarget( $target, $linkText, $addDuplicates, true, $separator );
		}
		return $this;
	}
}
```

### d013
```
/**
	 * @dataProvider getLinksToNamespaceProvider
	 */
	public function testGetLinksToNamespace( $wikitext, $namespace, $expectedLinks ) {
		$links = [];
		foreach ( $expectedLinks as [ $link, $label ] ) {
			$links[] = new Link( Title::newFromText( $link ), $label );
		}
		$this->assertArrayEquals(
			$links,
			( new WikitextLinksExtractor() )->getLinksToNamespace( $wikitext, $namespace )
		);
	}
```

### d014
```
private function getLinksMissingInTarget( string $source, string $target ): array {
		global $wgLegalTitleChars;
		$tc = $wgLegalTitleChars . '#%{}';
		$matches = $links = [];

		preg_match_all( "/\[\[([{$tc}]+)(\\|(.+?))?]]/sDu", $source, $matches );
		$count = count( $matches[0] );
		for ( $i = 0; $i < $count; $i++ ) {
			$backMatch = preg_quote( $matches[1][$i], '/' );
			if ( preg_match( "/\[\[$backMatch/", $target ) !== 1 ) {
				$links[] = "[[{$matches[1][$i]}{$matches[2][$i]}]]";
			}
		}

		return $links;
	}
```

### d015
```
/**
	 *
	 * @param Title[] $links
	 * @param bool|true $addDuplicates
	 * @param string $separator
	 * @return InternalLinksHelper
	 */
	public function addTargets( $links, $addDuplicates = true, $separator = "\n" ) {
		foreach ( $links as $linkText => $target ) {
			if ( !$target instanceof Title ) {
				continue;
			}
			if ( empty( $linkText ) || is_numeric( $linkText ) ) {
				$linkText = false;
			}
			$this->addTarget( $target, $linkText, $addDuplicates, true, $separator );
		}
		return $this;
	}
```

### d016
```
/**
	 * Returns all links in a given namespace
	 *
	 * @param int $namespace the default namespace id
	 * @return Link[]
	 */
	public function getLinksToNamespace( int $namespace ): array {
		$linksExtractor = new WikitextLinksExtractor();
		$links = [];
		foreach ( $this->fields as $field ) {
			$wikitext = $field->serialize( CONTENT_FORMAT_WIKITEXT );
			$links = array_merge(
				$links, $linksExtractor->getLinksToNamespace( $wikitext, $namespace )
			);
		}
		return $links;
	}
```

### d017
```
/**
	 * Extract a list of all recognized HTTP links in the text.
	 * @param Title $title
	 * @param string $text
	 * @return string[]
	 */
	private function findLinks( $title, $text ) {
		$parser = MediaWikiServices::getInstance()->getParser();
		$user = $parser->getUserIdentity();
		$options = new ParserOptions( $user );
		$text = $parser->preSaveTransform( $text, $title, $user, $options );
		$out = $parser->parse( $text, $title, $options );

		return array_keys( $out->getExternalLinks() );
	}
```

## Output

Return raw JSON only. No preamble, no markdown fences, no commentary outside the
object.

```json
{
  "query_id": "D1",
  "labels": {
    "d001": {"score": 1.0, "rationale": "iterative binary search over sorted array"},
    "d002": {"score": 0.0, "rationale": "pytest case asserting search behaviour, not an implementation"}
  }
}
```

Every `doc_id` presented must appear exactly once in `labels`.
