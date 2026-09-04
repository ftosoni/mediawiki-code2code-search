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
def parse_iso_date(date_str: str) -> datetime:
    return datetime.fromisoformat(
        date_str.replace('Z', '+00:00')
    )
```

## Candidates

### d001
```
def from_wiki_text(self, text) -> Optional[date]:
        match = re.search(r'(?P<date>\d{2}:\d{2}, \d{1,2} (?P<month>\w{3,4}) \d{4}) \(CES?T\)', text)
        if match:
            wiki_month = match.group('month')
            date_str = match.group('date').replace(wiki_month, self.get(wiki_month))
            return datetime.strptime(date_str, '%H:%M, %d %b %Y')
```

### d002
```
def _parse_iso(ts: str):
    """Parse an ISO-8601 timestamp string to a timezone-aware datetime."""
    from datetime import datetime
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))
```

### d003
```
def get_relevant_daily_date_strs(self):
        today = datetime.date.today()

        for day_offset in range(-10, 0):
            date = (today + datetime.timedelta(days=day_offset))
            date_str = date.isoformat()
            yield date_str
```

### d004
```
def _from_iso8601(cls, timestr: str) -> Timestamp:
        """Convert a string in ISO8601 format to a Timestamp object.

        ISO8601 format:
        ``YYYY-MM-DD[T ]HH:MM:SS[[.,]ffffff][Z|±HH[MM[SS[.ffffff]]]]``

        .. version-added:: 7.5
        """
        RE_ISO8601 = (r'(?:\d{4}-\d{2}-\d{2})(?P<sep>[T ])'  # noqa: N806
                      r'(?:\d{2}:\d{2}:\d{2})(?P<u>[.,]\d{1,6})?'
                      r'(?P<tz>Z|[+\-]\d{2}:?\d{,2})?'
                      )
        m = re.fullmatch(RE_ISO8601, timestr)

        if not m:
            raise ValueError(
                f'time data {timestr!r} does not match ISO8601 format.')

        strpfmt = f'%Y-%m-%d{m["sep"]}%H:%M:%S'
        strpstr = timestr[:19]

        if m['u']:
            strpfmt += '.%f'
            strpstr += m['u'].replace(',', '.')  # .ljust(7, '0')

        if m['tz']:
            if m['tz'] == 'Z':
                strpfmt += 'Z'
                strpstr += 'Z'
            else:
                strpfmt += '%z'
                # strptime wants HHMM, without ':'
                strpstr += (m['tz'].replace(':', '')).ljust(5, '0')

        ts = cls.strptime(strpstr, strpfmt)
        if ts.tzinfo is not None:
            ts = ts.astimezone(datetime.timezone.utc).replace(tzinfo=None)

        return ts
```

### d005
```
def get_relevant_weekly_date_strs(self):
        today = datetime.date.today()

        for day_offset in range(-30, 0):
            date = (today + datetime.timedelta(days=day_offset))
            if date.weekday() == 6:
                date_str = date.strftime('%GW%V')
                yield date_str
```

### d006
```
def extract_since(response):
    json_response = response.json()
    date_str = json_response['_source']['timestamp']
    date = datetime.utcfromtimestamp(date_str, )
    lag = datetime.utcnow() - date
    return lag
```

### d007
```
def parse_date(date: str) -> WbTime:
    time = WbTime.fromTimestamp(
        Timestamp.fromISOformat(date),
        precision=WbTime.PRECISION["day"],
    )
    time.hour = 0
    time.minute = 0
    time.second = 0
    return time
```

### d008
```
def parse_date(date_str: Optional[str]) -> Optional[datetime]:
        if date_str:
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
        return None
```

### d009
```
def _from_iso8601(cls: Type['Timestamp'], timestr: str) -> 'Timestamp':
        """Convert a string in ISO8601 format to a Timestamp object.

        ISO8601 format:
        - YYYY-MM-DD[T ]HH:MM:SS[[.,]ffffff][Z|±HH[MM[SS[.ffffff]]]]

        .. versionadded:: 7.5
        """
        RE_ISO8601 = (r'(?:\d{4}-\d{2}-\d{2})(?P<sep>[T ])'  # noqa: N806
                      r'(?:\d{2}:\d{2}:\d{2})(?P<u>[.,]\d{1,6})?'
                      r'(?P<tz>Z|[+\-]\d{2}:?\d{,2})?'
                      )
        m = re.fullmatch(RE_ISO8601, timestr)

        if not m:
            raise ValueError(
                f'time data {timestr!r} does not match ISO8601 format.')

        strpfmt = f'%Y-%m-%d{m["sep"]}%H:%M:%S'
        strpstr = timestr[:19]

        if m['u']:
            strpfmt += '.%f'
            strpstr += m['u'].replace(',', '.')  # .ljust(7, '0')

        if m['tz']:
            if m['tz'] == 'Z':
                strpfmt += 'Z'
                strpstr += 'Z'
            else:
                strpfmt += '%z'
                # strptime wants HHMM, without ':'
                strpstr += (m['tz'].replace(':', '')).ljust(5, '0')

        ts = cls.strptime(strpstr, strpfmt)
        if ts.tzinfo is not None:
            ts = ts.astimezone(datetime.timezone.utc).replace(tzinfo=None)
            # why pytest in py35/py37 fails without this?
            ts = cls._from_datetime(ts)

        return ts
```

### d010
```
def convert_nomlist_to_dicts(nominations,nom_date_dict):
    date_nums_dict = {}
    date_i = now
    print(date_i)
    while date_i>=now+datetime.timedelta(days=-7):
        print(date_i)
        date_nums_dict[monthday_from_dt(date_i)] = [0,0]
        date_i += datetime.timedelta(days=-1)
    
    for nom in nominations:
        date_str = monthday_from_dt(nom.date)
        if date_str not in date_nums_dict:
             date_nums_dict[date_str] = [0,0]
        date_nums_dict[date_str][nom.is_approved] += 1

    for title in list(nom_date_dict.keys()):
        expansion_date = datetime.datetime.strptime(nom_date_dict[title][0],"%Y-%m-%d").replace(tzinfo=datetime.timezone.utc)
        if nom_date_dict[title][1] is not None:
            close_date = datetime.datetime.strptime(nom_date_dict[title][1],"%Y-%m-%d").replace(tzinfo=datetime.timezone.utc)
            if nom_date_dict[title][2]:
                article_talk_page = pwb.Page(site,"Talk:"+title[34:])
                if article_talk_page.text: 
                    article_talk_DYK_date = re.search("\{\{DYK talk\|(.*? .*?(?:\|| ).*?)\|",article_talk_page.text) #this is so much effort for a single edge case
                    if article_talk_DYK_date:
                        try:
                            article_talk_DYK_date = datetime.datetime.strptime(article_talk_DYK_date.group(1),"%d %B|%Y").replace(tzinfo=datetime.timezone.utc)
                        except ValueError as e:
                            article_talk_DYK_date = datetime.datetime.strptime(article_talk_DYK_date.group(1),"%d %B %Y").replace(tzinfo=datetime.timezone.utc)
                        if article_talk_DYK_date>=expansion_date:
                            print("nomination appeared on DYK, removing from nominations.json")
                            del nom_date_dict[title]
                if now-close_date>datetime.timedelta(days=60): #at that point it's a lost cause
                    del nom_date_dict[title]
            else:
                if now-close_date>datetime.timedelta(days=5): #if Jesus can resurrect in three days...
                    del nom_date_dict[title]

    return date_nums_dict, nom_date_dict, min(nom.date for nom in nominations)
```

### d011
```
def replace_date_if_needed(title, col_b_date_str):
    """Replace date in title if difference > 7 days"""
    col_b_match = re.search(r'(\d{4}-\d{2}-\d{2})', col_b_date_str)
    if not col_b_match:
        return title

    col_b_date_str_clean = col_b_match.group(1)
    col_b_date = datetime.strptime(col_b_date_str_clean, '%Y-%m-%d')

    title_dates = re.findall(r'\d{4}-\d{2}-\d{2}', title)
    if not title_dates:
        return title

    closest_date = None
    min_diff = float('inf')

    for date_str in title_dates:
        title_date = datetime.strptime(date_str, '%Y-%m-%d')
        diff_days = abs((title_date - col_b_date).days)

        if diff_days > 7 and diff_days < min_diff:
            min_diff = diff_days
            closest_date = date_str

    if closest_date:
        title = title.replace(closest_date, col_b_date_str_clean, 1)

    return title
```

### d012
```
def parse_iso_dt(timestamp: str) -> datetime:
    """Parse a datetime in iso8601 format.

    @param timestamp: the string to parse
    @return: the datetime representation
    @raise ValueError if the parsed datetime is not UTC
    """
    # Workaround python limitations not supporting trailing Z
    # TODO: remove once running python > 3.11
    timestamp = re.sub(r"(?<=\d)Z$", "+00:00", timestamp)
    dt = datetime.fromisoformat(timestamp)
    if dt.tzinfo != timezone.utc:
        raise ValueError(f'Parsed a suspicious datetime "{timestamp}" that is not UTC')
    return dt
```

### d013
```
def parse_string_to_date(date_str):
    """Parse a string into a datetime.date.

    If the string cannot get parsed to a date, a ValueError is raised.

    :param date_str: String to parse to a datetime.date
    """
    if date_str == 'yesterday':
        return datetime.date.today() - datetime.timedelta(days=1)

    # Try to parse ISO date
    try:
        return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError("Could not parse '%s' as date" % (date_str))
```

### d014
```
def _convert_date(isodate: str) -> datetime.datetime:
    """Convert an ISO format string to a date.

    Handles the format 2020-01-22T14:24:01Z (trailing Z)
    which is not supported by older versions of fromisoformat.
    """
    return datetime.datetime.fromisoformat(isodate.replace("Z", "+00:00"))
```

### d015
```
def parse_string_to_date(date_str):
    """Parse a string into a datetime.date.

    If the string cannot get parsed to a date, a ValueError is raised.

    :param date_str: String to parse to a datetime.date
    """
    if date_str == 'yesterday':
        return datetime.utcnow().date() - timedelta(days=1)

    # Try to parse ISO date
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError("Could not parse '%s' as date" % (date_str))
```

## Output

Return raw JSON only. No preamble, no markdown fences, no commentary outside the
object.

```json
{
  "query_id": "C2",
  "labels": {
    "d001": {"score": 1.0, "rationale": "iterative binary search over sorted array"},
    "d002": {"score": 0.0, "rationale": "pytest case asserting search behaviour, not an implementation"}
  }
}
```

Every `doc_id` presented must appear exactly once in `labels`.
