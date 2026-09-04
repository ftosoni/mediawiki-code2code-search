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
def make_slug(title: str) -> str:
    slug = title.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_-]+', '-', slug)
    return slug.strip('-')
```

## Candidates

### d001
```
class Main(CustomValidator):
    """Main class referenced in the Netbox config"""

    def validate(self, instance, request):  # noqa: unused-argument
        """Mandatory entry point"""
        # Slug
        if len(instance.slug) != 5:
            self.fail("Invalid slug (must be 5 chars)", field="slug")
        if instance.slug != instance.slug.lower():
            self.fail("Invalid slug (must be lowercase)", field="slug")
```

### d002
```
async def team_create(
        request: Request,
        name: str = Form(...),
        slug: str = Form(...),
    ):
        slug = slug.strip().lower()
        if not _slug_valid(slug):
            return templates.TemplateResponse(request, "teams/form.html", {
                "page_title": "Create team",
                "form_title": "Create team",
                "form_action": "/teams/new",
                "team": None,
                "error": "Slug must contain only lowercase letters, numbers, and hyphens.",
            }, status_code=422)
        existing = store.get_team_by_slug(slug)
        if existing:
            return templates.TemplateResponse(request, "teams/form.html", {
                "page_title": "Create team",
                "form_title": "Create team",
                "form_action": "/teams/new",
                "team": None,
                "error": f"A team with slug '{slug}' already exists.",
            }, status_code=422)
        store.create_team(name=name.strip(), slug=slug)
        return RedirectResponse(f"/teams/{slug}", status_code=303)
```

### d003
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

### d004
```
protected static function cleanName( string $title ): string {
        if ( str_starts_with( strtolower( $title ), 'file:' ) ) {
            $title = substr( $title, 5 );
        }
        return trim( $title );
    }
```

### d005
```
async def team_update(
        request: Request,
        slug: str,
        name: str = Form(...),
    ):
        team = store.get_team_by_slug(slug)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        store.update_team(team.id, name=name.strip())
        return RedirectResponse(f"/teams/{slug}", status_code=303)
```

### d006
```
def check_slug():
    """Check if a slug is available."""
    slug = request.args.get("slug")
    if not slug:
        return jsonify({"available": False}), 400
    
    db = get_session()
    exists = db.query(SavedList).filter_by(slug=slug).first()
    return jsonify({"available": not bool(exists)})
```

### d007
```
def sluggify(text):
    """Generate a URL-safe slug from text."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9_-]+', '-', text)
    return text.strip('-_')
```

### d008
```
private function normalize( string $title ): string {
		$title = str_replace( '_', ' ', $title );
		$title = mb_strtolower( $title );
		$title = preg_replace( '/\s+/u', ' ', $title ) ?? $title;
		return trim( $title );
	}
```

### d009
```
function slugifyTitle() {
		return ( $( '#title' ).val() || 'untitled' )
			.toLowerCase()
			.split( /[\t !"#$%&'()*-/<=>?@[\\\]^_`{|},.]+/g )
			.filter( ( word ) => word )
			.join( '-' );
	}
```

### d010
```
def slugify(value):
    """Convert a string to a slug."""
    value = unicodedata.normalize("NFKC", value)
    value = RE_SLUG_REMOVE.sub("", value).strip().lower()
    return RE_SLUG_REPLACE.sub("-", value)
```

### d011
```
/**
	 * Derive a human-readable title from the last path segment of a URL.
	 * e.g. "/posts/my-article-slug" → "My article slug"
	 *
	 * @param string $url
	 * @return string|null
	 */
	private function titleFromPath( string $url ): ?string {
		$path = parse_url( $url, PHP_URL_PATH ) ?? '';
		$slug = basename( $path );
		if ( $slug === '' ) {
			return null;
		}
		return ucfirst( str_replace( [ '-', '_' ], ' ', $slug ) );
	}
```

### d012
```
def buildTitle(photo_id, metadata):
    title = u'FEMA - ' + str(photo_id) + u' - ' + metadata['title'] + '.jpg'

    title = re.sub(u"[<{\\[]", u"(", title)
    title = re.sub(u"[>}\\]]", u")", title)
    title = re.sub(u"[ _]?\\(!\\)", u"", title)
    title = re.sub(u",:[ _]", u", ", title)
    title = re.sub(u"[;:][ _]", u", ", title)
    title = re.sub(u"[\t\n ]+", u" ", title)
    title = re.sub(u"[\r\n ]+", u" ", title)
    title = re.sub(u"[\n]+", u"", title)
    title = re.sub(u"[?!]([.\"]|$)", u"\\1", title)
    title = re.sub(u"[&#%?!]", u"^", title)
    title = re.sub(u"[;]", u",", title)
    title = re.sub(u"[/+\\\\:]", u"-", title)
    title = re.sub(u"--+", u"-", title)
    title = re.sub(u",,+", u",", title)
    title = re.sub(u"[-,^]([.]|$)", u"\\1", title)
    title = title.replace(u" ", u"_")   
    
    return title
```

### d013
```
def get_slug_PHID(slug):
    try:
        rq = list(
            phab.request('project.query', {'slugs': [slug]})['slugMap']
                .values()
        )
    except AttributeError:
        # If slugMap is empty, an empty list rather than an empty dict is
        # returned by Phabricator.
        raise Exception("No PHID found for slug #%s!" % slug)
    if rq:
        logging.debug(
            "Slug {slug} = PHID {phid}".format(slug=slug, phid=rq[0])
        )
        return rq[0]
    raise Exception("No PHID found for slug #%s!" % slug)
```

### d014
```
/// Converts the title to URL-safe format (spaces to underscores)
    pub fn to_url_format(&self) -> String {
        self.normalized.replace(' ', "_")
    }
```

### d015
```
/**
	 * @param string $title
	 * @return string
	 */
	private function makePrefix( $title ) {
		$title = str_replace( '_', ' ', $title );
		return $title;
	}
```

### d016
```
async def member_create(
        request: Request,
        slug: str,
        display_name: str = Form(...),
        gitlab_username: str = Form(""),
        gerrit_username: str = Form(""),
    ):
        team = store.get_team_by_slug(slug)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        store.add_team_member(
            team_id=team.id,
            display_name=display_name.strip(),
            gitlab_username=gitlab_username.strip() or None,
            gerrit_username=gerrit_username.strip() or None,
        )
        return RedirectResponse(f"/teams/{slug}", status_code=303)
```

### d017
```
public static String normalizedFilename(String title) {
        return title.replace("File:", "").replace(' ', '_');
    }
```

### d018
```
def validate(self, instance, request):  # noqa: unused-argument
        """Mandatory entry point"""
        # Slug
        if len(instance.slug) != 5:
            self.fail("Invalid slug (must be 5 chars)", field="slug")
        if instance.slug != instance.slug.lower():
            self.fail("Invalid slug (must be lowercase)", field="slug")
```

### d019
```
function _fixSpecialName(title, siteInfo) {
    var parts = title.split('/');
    var first = parts[0].toUpperCase();
    var alias = arrayFind(siteInfo.specialpagealiases || [], function(o) {
        return arrayFind(o.aliases, function(a) {
            return a.toUpperCase() === first;
        }) !== undefined;
    });
    if (alias) {
        parts[0] = alias.aliases[0];
        title = parts.join('/');
    }
    return title;
}
```

### d020
```
/// Normalizes a Wikipedia title according to Wikipedia conventions
    fn normalize_title(title: &str) -> String {
        if title == "WE_WILL_FIGURE_OUT_LATER" {
            return title.to_string();
        }
        let mut normalized = title.trim().to_string();

        // Replace underscores with spaces
        normalized = normalized.replace('_', " ");

        // Normalize whitespace (collapse multiple spaces to single space)
        normalized = normalized
            .split_whitespace()
            .collect::<Vec<&str>>()
            .join("_");

        // Capitalize first letter of each word for title case
        if !normalized.is_empty() {
            let mut chars: Vec<char> = normalized.chars().collect();
            chars[0] = chars[0].to_uppercase().next().unwrap_or(chars[0]);
            normalized = chars.into_iter().collect();
        }

        normalized
    }
```

## Output

Return raw JSON only. No preamble, no markdown fences, no commentary outside the
object.

```json
{
  "query_id": "B7",
  "labels": {
    "d001": {"score": 1.0, "rationale": "iterative binary search over sorted array"},
    "d002": {"score": 0.0, "rationale": "pytest case asserting search behaviour, not an implementation"}
  }
}
```

Every `doc_id` presented must appear exactly once in `labels`.
