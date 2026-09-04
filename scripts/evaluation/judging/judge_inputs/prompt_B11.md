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

## Candidates

### d001
```
def _get_all_pages(self, url_part: str) -> List[Dict]:
        """Get all pages relative to a query."""
        responses = []
        try:
            while True:
                # If this fails, an exception is raised.
                self.logger.debug("Fetching: %s", url_part)
                resp = self._request(url_part)
                responses.append(resp.json())
                if "next" not in resp.links:
                    return responses
                # now let's inject the pagination in the query
                url_part = resp.links["next"]["url"]
        except requests.exceptions.HTTPError as e:
            # Workaround for https://github.com/docker/distribution/issues/2747
            # When using a swift backend, we get a 404 response if no tags are present
            if e.response.status_code == 404 and url_part.endswith("/tags/list"):
                self.logger.info(
                    "Got a 404 not found for %s: possibly a case of https://github.com/docker/distribution/issues/2747",
                    url_part,
                )
                return responses
            else:
                self.logger.exception("Error getting data from the registry")
                raise RegistryError(url_part)
        except requests.RequestException:
            self.logger.exception("Error getting data from the registry")
            raise RegistryError(url_part)
```

### d002
```
def SearchPageGenerator(
    query: str,
    total: Optional[int] = None,
    namespaces: Optional[Sequence[NAMESPACE_OR_STR_TYPE]] = None,
    site: OPT_SITE_TYPE = None
) -> Iterable['pywikibot.page.Page']:
    """Yield pages from the MediaWiki internal search engine.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.search(query, total=total, namespaces=namespaces)
```

### d003
```
def _fetch_chunk(
            self,
            session: requests.Session,
            qids: List[str]
    ) -> List[Dict]:
        """Return list of rows (qid, lang, title, views)."""

        def retry_api_call_after_http_error(response, qids):
            wait_time = 0
            if response.status_code == 429:
                retry_after_value = response.headers.get("Retry-After", "2")
                wait_time = _get_retry_seconds(retry_after_value)
                logger.warning(f"429 error: Rate of request limited. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.warning("API SITELINKS got HTTP error that isn't 429: %s", err)
                raise err

            if wait_time:
                params = {
                    "action": "wbgetentities",
                    "format": "json",
                    "formatversion": 2,
                    "props": "labels",
                    "ids": "|".join(qids),
                }
                r = session.post(self.url, data=params, timeout=30)
                return r

        params = {
            "action": "wbgetentities",
            "format": "json",
            "formatversion": 2,
            "props": "labels",
            "ids": "|".join(qids),
        }
        r = session.post(self.url, data=params, timeout=30)
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as err:
            r = retry_api_call_after_http_error(r, qids)
        data = r.json()
        from_continue = False

        rows: List[Dict] = []

        while True:

            if from_continue:
                r = session.post(self.url, data=params, timeout=30)
                try:
                    r.raise_for_status()
                except requests.exceptions.HTTPError as err:
                    r = retry_api_call_after_http_error(r, qids)
                data = r.json()

            # ------------- API error handling ------------------------------
            if (err := data.get("error")) is not None:
                code = err.get("code")
                logger.warning(err)

            # ------------- Warning Handling --------------------------------
            if warnings := data.get("warnings", None):
                logger.warning("API LABELS - Pageviews warning:\n %s", warnings)

            # ------------- Success path ------------------------------------
            pages = data.get("entities", {})
            for page in pages.values():
                qid = int(page.get("id").strip("Qq"))
                labels = page.get("labels")
                for label in labels.values():
                    lang = label.get("language")
                    title = label.get("value")
                    if lang in DEFAULT_LANGUAGES_CODES.keys():
                        rows.append({DBEnum.QID: qid, DBEnum.LANGUAGE: lang, DBEnum.TITLE: title})

            if data.get('continue', None):
                params.update(data["continue"])
                from_continue = True
            else:
                break

        return rows
```

### d004
```
def _paginate_once(
        self, path: str, key: str, page_size: int
    ) -> tuple[list[dict[str, Any]], int | None]:
        items: list[dict[str, Any]] = []
        first_total: int | None = None
        offset = 0
        while True:
            data = self._request("GET", path, params={"limit": page_size, "offset": offset})
            if first_total is None:
                first_total = data.get("total")
            items.extend(data.get(key, []))
            if not data.get("hasMore"):
                break
            next_offset = data.get("nextOffset")
            if next_offset is None or next_offset <= offset:
                raise GrowthBookAPIError(
                    f"malformed pagination on {path}: hasMore=true but "
                    f"nextOffset={next_offset!r}, offset={offset}"
                )
            offset = next_offset
        return items, first_total
```

### d005
```
def query(self) -> Generator[str]:
        """Query PagePile.

        :raises ServerError: Either ReadTimeout or server status error
        :raises APIError: Error response from petscan
        """
        url = 'https://pagepile.toolforge.org/api.php'

        req = http.fetch(url, params=self.opts)

        data = req.json()
        if 'error' in data:
            raise APIError('PagePile', data['error'], **self.opts)

        self.site = pywikibot.site.APISite.fromDBName(data['wiki'])
        raw_pages = data['pages']
        yield from raw_pages
```

### d006
```
class GrowthBookClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: tuple[float, float] = (5.0, 20.0),
        session: requests.Session | None = None,
        max_retries: int = 3,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers["User-Agent"] = "ldap-sync/1.0 (wmf-dpe)"
        self.session.auth = HTTPBasicAuth(api_key, "")
        retry = Retry(
            total=max_retries,
            backoff_factor=1.0,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def list_projects(self) -> list[dict[str, Any]]:
        """List all GrowthBook projects."""
        return self._paginated("/projects", "projects")

    def list_members(self) -> list[dict[str, Any]]:
        """List all GrowthBook members."""
        return self._paginated("/members", "members")

    def update_member_role(self, member_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Update a member's global and per-project role assignments."""
        return self._request("POST", f"/members/{member_id}/role", json={"member": payload})

    def _paginated(self, path: str, key: str, page_size: int = 100) -> list[dict[str, Any]]:
        """Fetch all pages; retry once if the first pass's item count disagrees with
        the first-page `total`. Abort if still inconsistent."""
        first_pass, first_total = self._paginate_once(path, key, page_size)
        if first_total is None or len(first_pass) == first_total:
            return first_pass

        logger.warning(
            "pagination total mutated during traversal; retrying",
            extra={"first_total": first_total, "emitted": len(first_pass), "path": path},
        )
        second_pass, second_total = self._paginate_once(path, key, page_size)
        if second_total is None or len(second_pass) != second_total:
            raise GrowthBookAPIError(
                f"pagination inconsistency on {path}: still drifting after retry"
            )
        return second_pass

    def _paginate_once(
        self, path: str, key: str, page_size: int
    ) -> tuple[list[dict[str, Any]], int | None]:
        items: list[dict[str, Any]] = []
        first_total: int | None = None
        offset = 0
        while True:
            data = self._request("GET", path, params={"limit": page_size, "offset": offset})
            if first_total is None:
                first_total = data.get("total")
            items.extend(data.get(key, []))
            if not data.get("hasMore"):
                break
            next_offset = data.get("nextOffset")
            if next_offset is None or next_offset <= offset:
                raise GrowthBookAPIError(
                    f"malformed pagination on {path}: hasMore=true but "
                    f"nextOffset={next_offset!r}, offset={offset}"
                )
            offset = next_offset
        return items, first_total

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            resp = self.session.request(method, url, params=params, json=json, timeout=self.timeout)
            if resp.status_code in (401, 403):
                raise GrowthBookAuthError(
                    f"auth rejected on {method} {path}: HTTP {resp.status_code}"
                )
            resp.raise_for_status()
            return resp.json() if resp.content else {}
        except requests.RequestException as e:
            raise GrowthBookAPIError(f"{method} {path} failed: {e}") from e
```

### d007
```
def results():
    try:
        type_of_search = request.args.get("type_of_search")
        search_request = request.args.get("query")
        language = request.args.get("language")
        page = request.args.get("page", 1, type=int)

        # Ensure page is at least 1
        if page < 1:
            page = 1

        # Calculate offset for pagination (50 items per page)
        page_size = 50
        offset = (page - 1) * page_size

        # Show results when there is no query (for example in case of changing the language)
        if search_request is None:
            referer = request.headers.get('Referer')
            if referer is not None:
                if referer.startswith(url_for('home', _external=True)):
                    query_parameters = referer.split("?")[-1].split("&")
                    query_parameters_without_language = [parameter for parameter in query_parameters
                                                          if not parameter.startswith("language=")]
                    path_string = "&".join(query_parameters_without_language)
                    return redirect(url_for('results') + "?" + path_string + "&" + "language=" + language )
                else:
                    return redirect(url_for('home'))
            else:
                return redirect(url_for('home'))

        if type_of_search == "author":
            gender = request.args.get("gender")
            nationality = request.args.get("nationality")
            creative_area = request.args.get("creative_area")
            in_public_domain = request.args.get("in_public_domain")
            search_result, complete, continue_offset, results_quantity = search.search_author(search_request, gender, nationality,
                                                           creative_area, in_public_domain, offset)
            if results_quantity > 10000:
                results_quantity = 10000
            
            page_range = {"start": offset + 1,
                          "end": offset + page_size if (offset + page_size) <= results_quantity else results_quantity}

            if len(search_result) > 0:
                # Calculate pagination info
                has_next = continue_offset is not None
                has_prev = page > 1
                return render_template('results.html',
                                        title=_("Results"),
                                        list_of_authors=search_result,
                                        search_request=search_request,
                                        type_of_search=type_of_search,
                                        complete=complete,
                                        results_quantity=results_quantity,
                                        page_range=page_range,
                                        page=page,
                                        has_next=has_next,
                                        has_prev=has_prev)
            else:
                return render_template("no-results.html",
                                        title=_("No results found"),
                                        search_request=search_request,
                                        type_of_search=type_of_search)
        elif type_of_search == "work":
            type_of_work = request.args.get("type_of_work")
            country_of_origin = request.args.get("country_of_origin")
            search_result, complete, continue_offset, results_quantity = search.search_work(search_request, type_of_work, 
                                                                                            country_of_origin, offset)
            if results_quantity > 10000:
                results_quantity = 10000
            
            page_range = {"start": offset + 1,
                          "end": offset + page_size if (offset + page_size) <= results_quantity else results_quantity}

            if len(search_result) > 0:
                # Calculate pagination info
                has_next = continue_offset is not None
                has_prev = page > 1
                return render_template('results.html',
                                        title=_("Results"),
                                        list_of_works=search_result,
                                        search_request=search_request,
                                        type_of_search=type_of_search,
                                        complete=complete,
                                        results_quantity=results_quantity,
                                        page_range=page_range,
                                        page=page,
                                        has_next=has_next,
                                        has_prev=has_prev)
            else:
                return render_template("no-results.html",
                                        title=_("No results found"),
                                        search_request=search_request,
                                        type_of_search=type_of_search)
        else:
            return render_template("no-results.html",
                                        title=_("No results found"),
                                        search_request=search_request)
    except:
        abort(404)
```

### d008
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

### d009
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

### d010
```
private function serveUnifiedDashboardTranslations( array $params ): void {
		$status = $params['type'];

		$sectionTranslations = [];
		$user = $this->getUser();
		$translatorUserId = $this->userService->getGlobalUserId( $user );

		if ( $status === SectionTranslationStore::TRANSLATION_STATUS_PUBLISHED ) {
			$sectionTranslations = $this->sectionTranslationStore->findPublishedSectionTranslationsByUser(
				$translatorUserId,
				$params['from'],
				$params['to'],
				$params['limit'],
				$params['offset']
			);
		} elseif ( $status === SectionTranslationStore::TRANSLATION_STATUS_DRAFT ) {
			$sectionTranslations = $this->sectionTranslationStore->findDraftSectionTranslationsByUser(
				$translatorUserId,
				$params['from'],
				$params['to'],
				$params['limit'],
				$params['offset']
			);
		}

		$translations = array_map( static function ( $sectionTranslation ) {
			return $sectionTranslation->toArray();
		}, $sectionTranslations );

		// We will have extra "continue" in case the last batch is exactly the size of the limit
		$count = count( $sectionTranslations );

		if ( $count === $params['limit'] ) {
			$offset = $sectionTranslations[$count - 1]->getLastUpdatedTimestamp();
			// We will have extra "continue" in case the last batch is exactly the size of the limit
			if ( $offset ) {
				$this->setContinueEnumParameter( 'offset', $offset );
			}
		}

		$result = $this->getResult();
		$result->addValue( [ 'query', 'contenttranslation' ], 'translations', $translations );
	}
```

### d011
```
/**
	 * Determine the title, parameters, API endpoint and format
	 *
	 * @param Parser $parser Parser object
	 * @param string $query Search query
	 * @return string Search results
	 */
	public static function onFunctionHook( Parser $parser, $query = '' ) {
		// This is required unless we come up with a good fallback or default
		$query = trim( $query );
		if ( !$query ) {
			return self::error( 'searchparserfunction-no-query' );
		}

		// Get and process params
		$params = array_slice( func_get_args(), 2 );
		$params = self::parseParams( $params );

		// Build the query
		$search = MediaWikiServices::getInstance()->getSearchEngineFactory()->create();

		$namespace = $params['namespace'] ?? null;
		if ( $namespace ) {
			if ( $namespace === '*' ) {
				$namespaces = MediaWikiServices::getInstance()->getNamespaceInfo()->getValidNamespaces();
			} else {
				$namespaces = explode( ',', $namespace );
			}
			$search->setNamespaces( $namespaces );
		}

		$sort = $params['sort'] ?? null;
		if ( $sort ) {
			$search->setSort( $sort );
		}

		$limit = $params['limit'] ?? null;
		$offset = $params['offset'] ?? null;
		if ( $limit || $offset ) {
			$limit = (int)$limit;
			$offset = (int)$offset;
			$search->setLimitOffset( $limit, $offset );
		}

		$rewrite = $params['rewrite'] ?? null;
		if ( $rewrite ) {
			$rewrite = (bool)$rewrite;
			$search->setFeatureData( 'rewrite', $rewrite );
		}

		$interwiki = $params['interwiki'] ?? null;
		if ( $interwiki ) {
			$interwiki = (bool)$interwiki;
			$search->setFeatureData( 'interwiki', $interwiki );
		}

		// Allow others to modify the query
		$hookContainer = MediaWikiServices::getInstance()->getHookContainer();
		$hookContainer->run( 'SearchParserFunctionQuery', [ &$search, &$params ] );

		// Do the search
		$what = $params['what'] ?? null;
		if ( $what === 'title' ) {
			$results = $search->searchTitle( $query );
		} else {
			$results = $search->searchText( $query );
		}

		if ( !$results ) {
			return;
		}

		if ( $results instanceof Status ) {
			$status = $results;
			$results = $status->getValue();
		}

		if ( !$results ) {
			return;
		}

		// Filter the current page
		$titles = $results->extractTitles();
		$titles = array_filter( $titles, static function ( $title ) use ( $parser ) {
			return !$parser->getTitle()->equals( $title );
		} );

		// Build the output according to the preferred format
		$output = '';
		$format = $params['format'] ?? null;
		switch ( $format ) {

			default:
				$links = $params['links'] ?? true;
				$links = filter_var( $links, FILTER_VALIDATE_BOOLEAN );
				$output = '<ul>';
				foreach ( $titles as $title ) {
					$titleText = $title->getFullText();
					if ( $links ) {
						$titleText = "[[:$titleText]]";
					}
					$output .= "<li>$titleText</li>";
				}
				$output .= '</ul>';
				break;

			case 'count':
				$output = count( $titles );
				break;

			case 'plain':
				$separator = $params['separator'] ?? ', ';
				$titleTexts = [];
				foreach ( $titles as $title ) {
					$titleText = $title->getFullText();
					$titleTexts[] = $titleText;
				}
				$output = implode( $separator, $titleTexts );
				break;

			case 'json':
				$output = json_encode( $data );
				break;

			case 'template':
				$template = $params['template'] ?? null;
				if ( !$template ) {
					return self::error( 'searchparserfunction-no-template' );
				}
				foreach ( $titles as $title ) {
					$titleText = $title->getFullText();
					$output .= "{{ $template
					| 1 = $titleText
					}}";
				}
				$output = $parser->recursivePreprocess( $output );
				break;
		}

		// Allow others to add formats or otherwise modify the output
		$hookContainer->run( 'SearchParserFunctionOutput', [ &$output, $format, $results, $params, &$parser ] );

		return $output;
	}
```

### d012
```
/**
 * Get search results.
 *
 * @param {string} searchTerm
 * @param {number} offset Optional result offset
 *
 * @return {Promise}
 */
function search( searchTerm, offset ) {
	const params = {
		action: 'query',
		list: 'prefixsearch',
		format: 'json',
		pssearch: searchTerm,
	};
	if ( offset ) {
		params.set( 'continue', String( offset ) );
	}
	return new mw.Api().get( params );
}
```

### d013
```
# POST /embodiments/:embodiment_id/aboutnesses/search
  # AJAX endpoint to search for subject headings
  def search
    source = params[:source]
    query = params[:query]
    page = (params[:page] || 1).to_i
    per_page = (params[:per_page] || 20).to_i

    # Calculate offset from page number (1-based to 0-based)
    offset = (page - 1) * per_page

    response = case source
               when 'LCSH'
                 SubjectHeadings::LcshClient.new.search(query, count: per_page, offset: offset)
               when 'Wikidata'
                 SubjectHeadings::WikidataClient.new.search(query, count: per_page, offset: offset)
               else
                 { results: [], has_more: false }
               end

    respond_to do |format|
      format.json do
        render json: {
          results: response[:results],
          has_more: response[:has_more],
          page: page,
          per_page: per_page
        }
      end
    end
  end
```

### d014
```
async def query_with_continue(params: dict, list_key: str, subkey: str | None = None) -> list:
        """Fetch all pages with continuation and return flattened list of items under list_key/subkey."""
        base = {
            "action": "query",
            "format": "json",
            "formatversion": 2,
            "titles": page_title,
            "redirects": 1,
        }
        base.update(params)
        out: list = []
        async with httpx.AsyncClient(timeout=60) as c:
            cont: dict | None = None
            while True:
                req_params = base.copy()
                if cont:
                    req_params.update(cont)
                resp = await c.get("https://sw.wikipedia.org/w/api.php", params=req_params)
                resp.raise_for_status()
                js = resp.json()
                pages = js.get("query", {}).get("pages", [])
                if pages:
                    page = pages[0]
                    item = page.get(list_key, []) if subkey is None else page.get(list_key, {}).get(subkey, [])
                    if item:
                        out.extend(item)
                cont = js.get("continue")
                if not cont:
                    break
        return out
```

### d015
```
async def fetch_batch(batch):
        batch_fixed = [t.replace(" ", "_") for t in batch]
        params = {
            "action": "query",
            "format": "json",
            "prop": "revisions",
            "rvprop": "ids",
            "titles": "|".join(batch_fixed),
            "redirects": 1,
            "normalize": 1,
        }
        async with LIMITER:
            r = await client.get(
                url, params=params, headers={"User-Agent": HEADERS["User-Agent"]}
            )
        r.raise_for_status()
        return r.json(), batch
```

### d016
```
def _fetch_pending_pages(self) -> list[Page]:
        self.log(f"fetching pending pages (max {self.limit})", level=logging.INFO)
        return Page.pending(self.namespaces, self.limit)
```

### d017
```
def _paginated(self, path: str, key: str, page_size: int = 100) -> list[dict[str, Any]]:
        """Fetch all pages; retry once if the first pass's item count disagrees with
        the first-page `total`. Abort if still inconsistent."""
        first_pass, first_total = self._paginate_once(path, key, page_size)
        if first_total is None or len(first_pass) == first_total:
            return first_pass

        logger.warning(
            "pagination total mutated during traversal; retrying",
            extra={"first_total": first_total, "emitted": len(first_pass), "path": path},
        )
        second_pass, second_total = self._paginate_once(path, key, page_size)
        if second_total is None or len(second_pass) != second_total:
            raise GrowthBookAPIError(
                f"pagination inconsistency on {path}: still drifting after retry"
            )
        return second_pass
```

### d018
```
def fetch_wiki_list(session: requests.Session) -> list[dict]:
    """Fetch the list of public wikis from WikiDiscover."""
    url = 'https://meta.miraheze.org/w/api.php'
    params = {
        'action': 'query',
        'format': 'json',
        'list': 'wikidiscover',
        'wdlimit': '500',
        'wdprop': '',
        'wdstate': 'open|public|unlocked',
    }

    wikis = []
    offset = 0

    while True:
        if offset > 0:
            params['wdoffset'] = str(offset)

        print(f'Fetching with offset: {offset}')

        response = session.get(url, params=params)
        response.raise_for_status()

        data = response.json().get('query', {}).get('wikidiscover', {})
        wikis_data = data.get('wikis', {})
        count = data.get('count', 0)

        wikis.extend(wikis_data.values())

        if count == 0:
            break

        offset += len(wikis_data)

    return wikis
```

## Output

Return raw JSON only. No preamble, no markdown fences, no commentary outside the
object.

```json
{
  "query_id": "B11",
  "labels": {
    "d001": {"score": 1.0, "rationale": "iterative binary search over sorted array"},
    "d002": {"score": 0.0, "rationale": "pytest case asserting search behaviour, not an implementation"}
  }
}
```

Every `doc_id` presented must appear exactly once in `labels`.
