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

## Candidates

### d001
```
public function findSubcats ( &$db , $root , &$subcats , $depth = -1 ) {
		$check = [] ;
		$c = [] ;
		foreach ( $root AS $r ) {
			if ( isset ( $subcats[$r] ) ) continue ;
			$subcats[$r] = $db->real_escape_string ( $r ) ;
			$c[] = $db->real_escape_string ( $r ) ;
		}
		if ( empty($c) ) return ;
		if ( $depth == 0 ) return ;
		$sql = "SELECT DISTINCT page_title FROM page,categorylinks WHERE page_id=cl_from AND cl_to IN ('" . implode ( "','" , $c ) . "') AND cl_type='subcat'" ;
		$result = $this->getSQL ( $db , $sql , 2 ) ;
		while($row = $result->fetch_assoc()){
			if ( isset ( $subcats[$row['page_title']] ) ) continue ;
			$check[] = $row['page_title'] ;
		}
		if ( empty($check) ) return ;
		$this->findSubcats ( $db , $check , $subcats , $depth - 1 ) ;
	}
```

### d002
```
function dfs(v, depth) {
    var children = g.children(v);
    if (children && children.length) {
      _.forEach(children, function(child) {
        dfs(child, depth + 1);
      });
    }
    depths[v] = depth;
  }
```

### d003
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

### d004
```
/**
	 * Recursively walks through tree array.
	 * Creates array containing each input's level.
	 * (array_walk_recursive doesn't like when the value is an array)
	 * A lower count indicates a closer ancestor to the page, that is
	 * supercategories are assigned higher numbers than subcategories
	 * @param string $value
	 * @param string $catName
	 * @param int $count
	 */
	private static function assignLevel( $value, $catName, $count = 0 ) {
		$count++;

		if ( !empty( $value ) ) {
			array_walk( $value, [ self::class, 'assignLevel' ], $count );
		}

		self::$catList[$catName] = $count;
	}
```

### d005
```
/**
	 * Collects self + child elements up to a given depth from a list of elements.
	 *
	 * @param  {djs.model.Base|Array<djs.model.Base>} elements the elements to select the children from
	 * @param  {boolean} unique whether to return a unique result set (no duplicates)
	 * @param  {number} maxDepth the depth to search through or -1 for infinite
	 *
	 * @return {Array<djs.model.Base>} found elements
	 */
	function selfAndChildren(elements, unique, maxDepth) {
		var result = [],
			processedChildren = [];

		eachElement(elements, function(element, i, depth) {
			add$1(result, element, unique);

			var children = element.children;

			// max traversal depth not reached yet
			if (maxDepth === -1 || depth < maxDepth) {

				// children exist && children not yet processed
				if (children && add$1(processedChildren, children, unique)) {
					return children;
				}
			}
		});

		return result;
	}
```

### d006
```
public function findSubcats ( &$db , $root , &$subcats , $depth = -1 ) {
		$check = [] ;
		$c = [] ;
		foreach ( $root AS $r ) {
			if ( isset ( $subcats[$r] ) ) continue ;
			$subcats[$r] = $db->real_escape_string ( $r ) ;
			$c[] = $db->real_escape_string ( $r ) ;
		}
		if ( count ( $c ) == 0 ) return ;
		if ( $depth == 0 ) return ;
		$sql = "SELECT DISTINCT page_title FROM page,categorylinks WHERE page_id=cl_from AND cl_to IN ('" . implode ( "','" , $c ) . "') AND cl_type='subcat'" ;
		$result = $this->getSQL ( $db , $sql , 2 ) ;
		while($row = $result->fetch_assoc()){
			if ( isset ( $subcats[$row['page_title']] ) ) continue ;
			$check[] = $row['page_title'] ;
		}
		if ( count ( $check ) == 0 ) return ;
		$this->findSubcats ( $db , $check , $subcats , $depth - 1 ) ;
	}
```

### d007
```
/**
	 * Recursive function to populate a tree based on category information.
	 */
	private function populateChildren() {
		$subcats = self::getSubcategories( $this->top_category );
		foreach ( $subcats as $subcat ) {
			$childTree = new PFTree( $this->depth, $this->current_values );
			$childTree->top_category = $subcat;
			$childTree->title = $subcat;
			$childTree->populateChildren();
			$this->addChild( $childTree );
		}
	}
```

### d008
```
/**
	 * Get all children, grandchildren, etc. in a single flat array of entity
	 * objects.
	 * @return array
	 */
	public function getDescendants() {
		$descendants = [];
		$children = $this->getChildren();
		foreach ( $children as $child ) {
			$descendants[] = $child;
			$descendants = array_merge( $descendants, $child->getDescendants() );
		}

		return $descendants;
	}
```

### d009
```
function node_descendants() {
  return Array.from(this);
}
```

### d010
```
// Build category hierarchy structure
function buildCategoryHierarchy(categoryRelations, rootCategory) {
	const hierarchy = { name: rootCategory, children: new Map(), depth: 0 };
	const categoryMap = new Map([[rootCategory, hierarchy]]);

	// Create all category nodes with their parent relationships
	categoryRelations.forEach(({ category, parent }) => {
		if (!categoryMap.has(category)) {
			categoryMap.set(category, { name: category, children: new Map(), parent: parent });
		}
	});

	// Build parent-child relationships
	categoryMap.forEach((node, catName) => {
		if (node.parent && categoryMap.has(node.parent)) {
			const parentNode = categoryMap.get(node.parent);
			parentNode.children.set(catName, node);
		}
	});

	// Calculate depths
	function calculateDepth(node, depth = 0) {
		node.depth = depth;
		node.children.forEach(child => calculateDepth(child, depth + 1));
	}
	calculateDepth(hierarchy);

	return hierarchy;
}
```

### d011
```
function dfs(v, depth) {
    var children = g.children(v);
    if (children && children.length) {
      _.each(children, function(child) {
        dfs(child, depth + 1);
      });
    }
    depths[v] = depth;
  }
```

### d012
```
function treeDepths(g) {
  var depths = {};
  function dfs(v, depth) {
    var children = g.children(v);
    if (children && children.length) {
      _.forEach(children, function(child) {
        dfs(child, depth + 1);
      });
    }
    depths[v] = depth;
  }
  _.forEach(g.children(), function(v) { dfs(v, 1); });
  return depths;
}
```

### d013
```
/**
	 * Get the collection of the section's subsections.
	 *
	 * @param {boolean} [indirect] Whether to include subsections of subsections and so on
	 *   (return descendants, in a word).
	 * @returns {Section[]}
	 */
	getChildren(indirect = false) {
		/** @type {Section[]} */
		const children = []
		let haveMetDirect = false
		this.manager
			.getAll()
			.slice(this.index + 1)
			.some((section) => {
				if (section.level > this.level) {
					// If, say, a level 4 section directly follows a level 2 section, it should be considered
					// a child. This is why we need the haveMetDirect variable.
					if (section.level === this.level + 1) {
						haveMetDirect = true
					}

					if (indirect || section.level === this.level + 1 || !haveMetDirect) {
						children.push(section)
					}

					return false
				}

				return true
			})

		return children
	}
```

### d014
```
private void fetchSubCategories(Stream<String> catStream, Set<String> result, int depth) {
        catStream.forEach(s -> result.addAll(self.getSubCategories(s, depth - 1)));
    }
```

### d015
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

### d016
```
/**
   * Collects self + child elements up to a given depth from a list of elements.
   *
   * @param {Element|Element[]} elements the elements to select the children from
   * @param {boolean} unique whether to return a unique result set (no duplicates)
   * @param {number} maxDepth the depth to search through or -1 for infinite
   *
   * @return {Element[]} found elements
   */
  function selfAndChildren(elements, unique, maxDepth) {
    var result = [],
        processedChildren = [];

    eachElement(elements, function(element, i, depth) {
      add$1(result, element, unique);

      var children = element.children;

      // max traversal depth not reached yet
      {

        // children exist && children not yet processed
        if (children && add$1(processedChildren, children, unique)) {
          return children;
        }
      }
    });

    return result;
  }
```

### d017
```
class DetectCategoryRecursion extends BSMaintenance {

	/** @var array */
	private $dupes = [];

	public function execute() {
		$categoriesRes = $this->getDB( DB_REPLICA )->select( 'category', 'cat_title', [], __METHOD__ );

		foreach ( $categoriesRes as $row ) {
			$this->getSubCategoriesFromPath( [ $row->cat_title ] );
		}

		if ( empty( $this->dupes ) ) {
			$this->output( "No recursion detected\n" );
			return;
		}
		$this->output( "Recursion detected:\n" );
		foreach ( $this->dupes as $dupe ) {
			$this->output( implode( ' -> ', $dupe ) . "\n" );
		}
	}

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

	/**
	 * @param array $nodes
	 *
	 * @return bool
	 */
	private function detectRecursion( array $nodes ) {
		$processed = [];
		foreach ( $nodes as $node ) {
			if ( in_array( $node, $processed ) ) {
				return true;
			}
			$processed[] = $node;
		}
		return false;
	}

	/**
	 * @param string $last
	 * @return array
	 */
	private function getSubCategoriesFromDB( string $last ): array {
		$dbr = $this->getDB( DB_REPLICA );
		$resSubCategories = $dbr->select(
			[ 'page', 'categorylinks', 'linktarget' ],
			[ 'page_title' ],
			[
				'lt_title' => $last,
				'page_namespace' => NS_CATEGORY
			],
			__METHOD__,
			[],
			[
				'categorylinks' => [
					'INNER JOIN',
					'page_id = cl_from',
				],
				'linktarget' => [
					'INNER JOIN',
					'cl_target_id = lt_id',
				],
			]
		);

		$subcategories = [];
		foreach ( $resSubCategories as $row ) {
			$subcategories[] = $row->page_title;
		}

		asort( $subcategories );

		return $subcategories;
	}
}
```

### d018
```
/**
	 * Get all replies to the comment.
	 *
	 * @param {boolean} [indirect] Whether to include children of children and so on (return
	 *   descendants, in a word).
	 * @param {boolean} [visual] Whether to use visual levels instead of logical.
	 * @param {boolean} [allowSiblings] When `visual` is `true`, allow comments of the same
	 *   level to be considered children (if they are outdented).
	 * @returns {this[]}
	 */
	getChildren(indirect = false, visual = false, allowSiblings = true) {
		/** @type {this[]} */
		const children = []
		const prop = visual ? 'level' : 'logicalLevel'
		const comments = /** @type {this[]} */ (/** @type {unknown} */ (cd.comments))
		comments.slice(this.index + 1).some((comment) => {
			if (
				comment.section === this.section &&
				(comment[prop] > this[prop] ||
					// This comment is visually a child, although it's of the same level as the parent.
					(prop === 'level' &&
						allowSiblings &&
						comment[prop] === this[prop] &&
						comment.isOutdented()))
			) {
				// `comment.getParent() === this` to allow comments mistakenly indented with more than one
				// level.
				if (comment[prop] === this[prop] + 1 || indirect || comment.getParent() === this) {
					children.push(comment)
				}

				return false
			}
			if (prop === 'logicalLevel' && this.parser.context.areThereOutdents()) {
				// Outdented comments that are separated from their parents by interjected comments of
				// higher level than the parent.
				comments.slice(comment.index + 1).some((c) => {
					if (/** @type {CommentSkeleton<N> | null} */ (c.cachedParent.logicalLevel) === this) {
						children.push(c)

						return true
					}

					return c.section !== this.section
				})
			}

			return true
		})

		return children
	}
```

## Output

Return raw JSON only. No preamble, no markdown fences, no commentary outside the
object.

```json
{
  "query_id": "B10",
  "labels": {
    "d001": {"score": 1.0, "rationale": "iterative binary search over sorted array"},
    "d002": {"score": 0.0, "rationale": "pytest case asserting search behaviour, not an implementation"}
  }
}
```

Every `doc_id` presented must appear exactly once in `labels`.
