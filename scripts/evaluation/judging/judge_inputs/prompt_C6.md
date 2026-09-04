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

## Candidates

### d001
```
async function lookupQidHaswbstatement(id: string): Promise<string | null> {
  const url = `https://www.wikidata.org/w/api.php?${new URLSearchParams({
    action: 'query',
    list: 'search',
    srsearch: `haswbstatement:P8286=${id}`,
    format: 'json',
    formatversion: '2',
    srlimit: '1',
  })}`;
  const resp = await fetchWithRetry(url, {
    headers: { 'User-Agent': 'olympians-tool/1.0 (noreply@toolforge.org)' },
  });
  if (resp.status !== 200) throw new Error(`haswbstatement failed: ${resp.status} for id=${id}`);
  const json = await resp.json() as any;
  const results = json.query?.search ?? [];
  if (!results.length) return null;
  return results[0].title;
}
```

### d002
```
def validate_page_exists(wiki: str, page_title: str) -> bool:
    """
    Check if a wiki page exists without requiring authentication.
    Used when user adds a FileMapping to validate the target page.
    """
    try:
        api_url = f"https://{wiki}/w/api.php"
        resp = requests.get(
            api_url,
            params={
                "action": "query",
                "titles": page_title,
                "format": "json",
                "formatversion": "2",
            },
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        pages = data.get("query", {}).get("pages", [])
        if not pages:
            return False
        return not pages[0].get("missing", False)
    except Exception as exc:
        logger.warning(
            "[bot] Page existence check failed for %s/%s: %s", wiki, page_title, exc
        )
        return False
```

### d003
```
def get_user_groups(username: str, wiki_domain: str) -> list:
    """
    Query the MediaWiki API and return the list of groups the user belongs to.
    Returns an empty list on any error.
    """
    url = f"https://{wiki_domain}/w/api.php"
    params = {
        "action": "query",
        "list": "users",
        "ususers": username,
        "usprop": "groups|rights",
        "format": "json"
    }
    try:
        resp = requests.get(url, params=params, timeout=8, headers={
            "User-Agent": "WikiSTAR/1.0 (https://wikistar.toolforge.org)"
        })
        data = resp.json()
        users = data.get("query", {}).get("users", [])
        if users and "invalid" not in users[0] and "missing" not in users[0]:
            return users[0].get("groups", [])
    except Exception as e:
        print(f"[wiki_rights] Error checking {username} on {wiki_domain}: {e}")
    return []
```

### d004
```
def fetch_extension_config(self):
        """
        Fetch the ExtensionDistributor configuration from the API
        Do not call this directly.
        """
        logging.debug('Fetching ExtensionDistributor config from API...')
        data = {
            'action': 'query',
            'meta': 'siteinfo',
            'format': 'json',
        }
        r = self.session.get(self.API_URL, params=data)
        r.raise_for_status()
        resp = r.json()
        self._extension_config = resp['query']['general']['extensiondistributor']

        return {
            'versions': resp['query']['general']['extensiondistributor']['snapshots'],
            'extension-list': resp['query']['general']['extensiondistributor']['list']
        }
```

### d005
```
class SparqlBase:
    """Load items from Wikidata SPARQL query service."""

    SPARQL_API = 'https://query.wikidata.org/sparql'

    @classmethod
    def get_sparql(cls, query):
        response = get_json(cls.SPARQL_API, {'query': query, 'format': 'json'}, get=True)
        return response['results']['bindings']
```

### d006
```
def select(self,
               query: str,
               full_data: bool = False,
               headers: Optional[Dict[str, str]] = None
               ) -> Optional[List[Dict[str, str]]]:
        """
        Run SPARQL query and return the result.

        The response is assumed to be in format defined by:
        https://www.w3.org/TR/2013/REC-sparql11-results-json-20130321/

        :param query: Query text
        :param full_data: Whether return full data objects or only values
        """
        if headers is None:
            headers = DEFAULT_HEADERS

        data = self.query(query, headers=headers)
        if not data or 'results' not in data:
            return None

        result = []
        qvars = data['head']['vars']
        for row in data['results']['bindings']:
            values = {}
            for var in qvars:
                if var not in row:
                    # var is not available (OPTIONAL is probably used)
                    values[var] = None
                elif full_data:
                    if row[var]['type'] not in VALUE_TYPES:
                        raise ValueError(f"Unknown type: {row[var]['type']}")
                    valtype = VALUE_TYPES[row[var]['type']]
                    values[var] = valtype(row[var],
                                          entity_url=self.entity_url)
                else:
                    values[var] = row[var]['value']
            result.append(values)
        return result
```

### d007
```
def _wikidata_sparql(query: str, batch_label: str, retries: int = 3) -> list[dict] | None:
    """POST a SPARQL query to Wikidata. Returns result bindings or None on error.

    Retries on transient failures (timeouts, 5xx) with exponential backoff.
    """
    import time
    post_data = urllib.parse.urlencode({"query": query}).encode()
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(
                "https://query.wikidata.org/sparql",
                data=post_data,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/sparql-results+json",
                    "User-Agent": "abstract-data/1.0 (Toolforge)",
                },
            )
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.loads(resp.read())
            return data.get("results", {}).get("bindings", [])
        except Exception as e:
            if attempt < retries:
                delay = 20 * attempt
                print(f"  SPARQL error ({batch_label}, attempt {attempt}/{retries}): {e} — retrying in {delay}s")
                time.sleep(delay)
            else:
                print(f"  SPARQL error ({batch_label}): {e}")
    return None
```

### d008
```
def sparql_endpoint(self) -> str | None:
        """Return the sparql endpoint url, if any has been set.

        :return: sparql endpoint url
        """
        return self.siteinfo.get('wikibase-sparql')
```

### d009
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

### d010
```
def fetch_commons_info(yt_id):
    r = s.get('https://commons.wikimedia.org/w/api.php', params={
        'action': 'query',
        'generator': 'exturlusage',
        'geuquery': 'www.youtube.com/watch?v=' + yt_id,
        'prop': 'globalusage',
        'format': 'json',
        'formatversion': '2'
    })
    r.raise_for_status()
    resp = r.json()

    if 'query' not in resp:
        # no results
        return False

    if len(resp['query']['pages']) != 1:
        # TODO: emit some warning
        pass
    return resp['query']['pages'][0]
```

### d011
```
def get_sparql_query_results(endpoint_url, query, wikidata_flag=False):
    """
    Query a SPARQL endpoint and save results to a data frame
        Parameters:
            endpoint_url (str): SPARQL endpoint URL
            query (str): SPARQL query
            wikidata_flag (str): Whether or not the SPARQL endpoint queried is for WikiData
        Returns:
            (pd.DataFrame): DataFrame of SPARQL query results
    """
    sparql = SPARQLWrapper(endpoint=endpoint_url, agent=wiki_headers["User-Agent"])
    sparql.setQuery(query)
    sparql.setReturnFormat(CSV)
    if wikidata_flag:
        sparql.setOnlyConneg(True)
        sparql.addCustomHttpHeader("Content-type", "application/sparql-query")
        sparql.addCustomHttpHeader("Accept", "text/csv")
        sparql.setMethod(POST)
        sparql.setRequestMethod(POSTDIRECTLY)
    results = sparql.query().convert()
    results = results.decode("utf-8")
    df = pd.read_csv(StringIO(results))
    return df
```

### d012
```
def _search_categories_api(query: str, wiki: str, limit: int) -> list:
    """Fallback: search categories via MediaWiki API."""
    url = f"https://{wiki}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "allcategories",
        "acprefix": query,
        "aclimit": limit,
        "acprop": "size",
        "format": "json",
    }
    headers = {"User-Agent": "Wikiget/1.0 (https://wikiget.toolforge.org/)"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        categories = data.get("query", {}).get("allcategories", [])
        return [
            {
                "title": cat["*"],
            }
            for cat in categories
        ]
    except Exception as e:
        logger.error(f"MediaWiki API fallback also failed: {e}")
        return []
```

### d013
```
def _resolve_qids_api(page_ids: list[int], wiki: str) -> list:
    """Fallback: resolve QIDs via the Wikidata API."""
    url = f"https://{wiki}.wikipedia.org/w/api.php"
    results = []

    for batch in batch_list(page_ids, size=50):
        params = {
            "action": "query",
            "pageids": "|".join(str(pid) for pid in batch),
            "prop": "pageprops",
            "ppprop": "wikibase_item",
            "format": "json",
        }
        headers = {"User-Agent": "Wikiget/1.0 (https://wikiget.toolforge.org/)"}
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            pages = data.get("query", {}).get("pages", {})
            for pid, page_data in pages.items():
                qid = page_data.get("pageprops", {}).get("wikibase_item")
                if qid:
                    results.append({
                        "page_id": int(pid),
                        "title": page_data.get("title", ""),
                        "qid": qid,
                    })
        except Exception as e:
            logger.error(f"Wikidata API fallback failed: {e}")

    return results
```

### d014
```
def sparql_endpoint(self):
        """
        Return the sparql endpoint url, if any has been set.

        :return: sparql endpoint url
        :rtype: str|None
        """
        return self.siteinfo['general'].get('wikibase-sparql')
```

### d015
```
def _handle_sparql(self, value: str) -> HANDLER_RETURN_TYPE:
        """Handle `-sparql` argument."""
        if not value:
            value = pywikibot.input('SPARQL query:')
        return WikidataSPARQLPageGenerator(
            value, site=self.site, endpoint=self._sparql)
```

### d016
```
def retrieve_query(query: str, **kwargs: str) -> list[dict]:
    """Takes a SPARQL query, sends it to the Wikidata Query Service and returns a list of results."""
    query_url_prefix = 'https://query.wikidata.org/sparql?query='
    query = query.format(**kwargs)
    query = requests.utils.quote(query)  # URL encoded
    request_json_format = '&format=json'
    query_url = query_url_prefix + query + request_json_format
    headers = {'user-agent': current_app.config['USER_AGENT']}
    query_results = requests.get(query_url, headers=headers
                                 # , timeout=1  # If IPv6 doesn't work, force time out and use IPv4
                                 )
    query_results = query_results.json()
    query_results = query_results["results"]["bindings"]
    return query_results
```

### d017
```
async def query_wikidata(
    session: Any,
    query_str: str,
    variables: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute a GraphQL query against the Wikidata endpoint and return parsed results.

    Sends an async HTTP request using an existing session obtained from
    ``async with client as session:`` where *client* was created by
    :func:`create_wikidata_client`.  The required User-Agent header is set on
    the transport at client creation time per the Wikimedia Foundation policy.

    Args:
        session: An active gql async session (obtained via ``async with client as session:``).
        query_str: A raw GraphQL query string, optionally with ``$id`` style parameters.
        variables: Optional dict of variables for parameterized queries.

    Returns:
        The parsed response data as a dict.

    Raises:
        gql.transport.exceptions.TransportError: On network or protocol-level failures.
        graphql.error.GraphQLError: If the query is malformed or the server returns errors.
    """
    parsed_query = gql(query_str)
    result = await session.execute(parsed_query, variable_values=variables)
    return result
```

### d018
```
# Query
def query_wikidata(query):
    url = "https://query.wikidata.org/sparql"
    params = {
        "query": query,
        "format": "json"
    }
    result = SESSION.post(url=url, params=params, headers={'User-agent': 'Wiki Museu do Ipiranga - Quantos tem? 1.0'})
    data = result.json()
    SESSION.close()
    return data
```

## Output

Return raw JSON only. No preamble, no markdown fences, no commentary outside the
object.

```json
{
  "query_id": "C6",
  "labels": {
    "d001": {"score": 1.0, "rationale": "iterative binary search over sorted array"},
    "d002": {"score": 0.0, "rationale": "pytest case asserting search behaviour, not an implementation"}
  }
}
```

Every `doc_id` presented must appear exactly once in `labels`.
