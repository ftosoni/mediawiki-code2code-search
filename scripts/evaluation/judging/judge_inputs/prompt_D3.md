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
def parse_irc_message(raw: str) -> dict:
    prefix, command, params = None, None, []
    if raw.startswith(':'):
        prefix, raw = raw[1:].split(' ', 1)
    parts = raw.split(' ', 1)
    command = parts[0]
    if len(parts) > 1:
        ti = parts[1].find(' :')
        if ti >= 0:
            params = parts[1][:ti].split()
            params.append(parts[1][ti+2:])
        else:
            params = parts[1].split()
    return {'prefix': prefix, 'command': command, 'params': params}
```

## Candidates

### d001
```
/**
   * Normalize spaces in cascade declaration group
   */
  reduceSpaces(decl) {
    let stop = false
    this.prefixes.group(decl).up(() => {
      stop = true
      return true
    })
    if (stop) {
      return
    }

    let parts = decl.raw('before').split('\n')
    let prevMin = parts[parts.length - 1].length
    /** @type {number|false} */
    let diff = false

    this.prefixes.group(decl).down(other => {
      parts = other.raw('before').split('\n')
      let last = parts.length - 1

      if (parts[last].length > prevMin) {
        if (diff === false) {
          diff = parts[last].length - prevMin
        }

        parts[last] = parts[last].slice(0, -diff)
        other.raws.before = parts.join('\n')
      }
    })
  }
```

### d002
```
def irc_RPL_NAMREPLY(self, prefix, params):
        "Receives the list of nicks in channel, params = [self.nickname, '=', '#channel', 'nick1 @nick2 +nick3 ...']"
        channel = irclower(params[2])
        if not channel in chanNicks:
            chanNicks[channel] = {}
        for nick in params[3].split():
            status = nick[0] == '@' and 2 or nick[0] == '+' and 1 or 0
            chanNicks[channel][nick.strip('@+')] = status
```

### d003
```
function splitProp(prop) {
      const parts = prop.split("-");
      if (prop[0] !== "-") {
        return {
          prefix: "",
          base: parts[0],
          rest: parts.slice(1)
        };
      }
      if (prop[1] === "-") {
        return {
          prefix: null,
          base: null,
          rest: [prop]
        };
      }
      return {
        prefix: parts[1],
        base: parts[2],
        rest: parts.slice(3)
      };
    }
```

### d004
```
def __init__(self, raw):
        self._raw = raw
        self._raw_words = raw.split()
        self.chain = None
        self.source = None
        self.destination = None
        self.protocol = None
        self.dport = None
        self.sport = None
        self.match = None
        self.state = None
        self.comments = []
        self.limit = None
        self.limit_burst = None
        self.pkt_type = None
        self.jump = None
        self._parse()
```

### d005
```
def nsNotice(msg):
    global nsTemp
    if msg.endswith('is not registered'):
        acc = re.search(r'\x02([^\x02])\x02 is not registered.', msg)
        if acc:
            callhook('ns not registered ' + acc.group(1))
    elif msg.startswith(('Information on')):
        nsTemp = msg
    elif msg == '\x02*** End of Info ***\x02':
        acc = re.search(r'Information on \x02([^\x02]+)\x02(?: \(account \x02([^\x02]+)\x02\))?:', nsTemp)
        frozen = re.search(r';(\w+) has been frozen by the freenode administration.', nsTemp)
        if frozen and acc and frozen.group(1) in acc.groups():
            callhook('ns frozen ' + acc.group(1))
        nsTemp = None
    elif nsTemp:
        nsTemp += ';' + msg
```

### d006
```
def parsecmd(msg, here=None):
    words = []
    quote = False
    for word in msg.strip('?').split():
        if not quote and word[0] in ('"', '\''):
            quote = word[0]
            words.append(word[1:])
        elif quote:
            if word[-1] == quote:
                words[-1] += word[0:-1]
            else:
                words[-1] += word
        else:
            words.append(word.rstrip(','))
    command = {}
    prev = ''
    _filter = False
    _not = False
    alias = {'identifi': 'reg', 'register': 'reg', 'mask': 'match', 'ISP': 'isp', 'wikiblock': 'block', 'said': 'talk'}
    filters = alias.viewkeys() | alias.viewvalues() | {'ban', 'quiet', 'account', 'country', 'op', 'voic', 'affiliat',
            'cloak', 'wmcloak'}
    i = 0
    if words[i].lower() in ('list', 'which', 'who'):
        i += 1
    word = words[i].rstrip('s').lower()
    if word in ('channel', 'account', 'cloak', 'ip', 'host', 'ident', 'nick', 'realname', 'connection', 'user'):
        command['type'] = word
        i += 1
    if words[i] == 'here':
        if not here:
          return {'error': 'can not use "here" in pm'}
        command['channels'] = [here]
        i += 1
    for count in range(100):
        word = words[i]
        if _filter:
            _filter -= 1
        if word in ('not', 'non', 'without') or word.endswith('n\'t'):
            _not = True
        elif wordRoot(word) in filters:
            if word[0:2] == 'un':
                _not = True
            word = word in ('opped', 'voiced') and word or wordRoot(word)
            if word in alias:
                word = alias[word]
            command.setdefault('filters', []).append((_not and '!' or '') + word)
            _not, Filter = False, True
            if word in ('match', 'country', 'isp') and len(words) > i + 1:
                i += 1
                command['filters'][-1] += ' ' + words[i]
        elif word == 'score' and len(words) > i + 2 and words[i + 1] in '=><' and words[i + 2].isdigit():
            command.setdefault('filters', []).append((_not and '!' or '') + ' '.join(words[i:i + 3]))
            i += 2
        elif word[0] in '+-' and (len(word) == 2 or prev in ('flag', 'flags')):
            command.setdefault('filters', []).append((_not and '!' or '') + 'flag ' + word + '')
            _not, Filter = False, False
        elif word == 'or' and 'filters' in command:
            command['filters'].append('or')
        elif ' '.join(words[i:i + 2]).lower() in ('in range', 'ip range', 'with ip') and len(words) > i + 2 \
                and reIP.match(words[i + 2]) or word.lower() == 'ip' and len(words) > i + 1 and reIP.match(words[i + 1]):
            if ' '.join(words[i:i + 2]).lower() in ('in range', 'ip range', 'with ip'):
                ip = words[i + 2]
                i += 2
            else:
                ip = words[i + 1]
                i += 1
            command.setdefault('filters', []).append((_not and '!' or '') + 'ip ' + ip)
        elif word == 'in':
            channels = []
            j = i + 1
            _not = i > 0 and words[i - 1] == 'not'
            while j < len(words):
                chan = words[j].strip(',')
                if channels and chan == 'and':
                    continue
                if chan[0] == '#':
                    channels.append(chan)
                if chan in ('somewhere', 'anywhere') or (chan in ('any', 'some') and len(word) > j and word[j + 1] == 'channel'):
                    channels.append('anychan')
                    if chan in ('any', 'some'):
                        j += 1
                elif chan[0] == '-':
                    autochans = sorted([(c, len(n)) for c, n in chanNicks.iteritems() if c.endswith(chan)],
                            key=lambda i:i[1], reverse=True)
                    if not autochans:
                        return {'error': 'I don\'t know a channel that ends with ' + chan}
                    channels.append(autochans[0][0])
                else:
                    i = j - 1
                    break
                j += 1
            if 'filters' in command and command['filters'][-1].strip('!').startswith(('op', 'voiced', 'ban', 'quiet', 'flag +')):
                command['filters'][-1] += ' ' + ' '.join(channels)
            else:
                command[(_not and 'not ' or '') + 'channels'] = channels
            _not = False
        elif word in ('with', 'within', 'has', 'have') and len(words) > i + 2 and words[i + 1] == 'more':
            i += 2
            word = words[i]
            if word == 'than' and len(words) > i + 2 and (words[i + 1].isdigit() or words[i + 1] in ('one', 'two')):
                word += ' %s %s' % ({'one': '1', 'two': '2'}.get(words[i + 1], words[i + 1]), words[i + 2])
                i += 2
            command['with more'] = word
        i += 1
        prev = word
        if i == len(words):
            return command
    else:
        return {'error': 'Sorry, I didn\'t understand your command'}
```

### d007
```
def create_users_and_groups(user_and_groups):

  import params

  parts = re.split('\s+', user_and_groups)
  if len(parts) == 1:
    parts.append("")

  users_list = parts[0].strip(",").split(",") if parts[0] else []
  groups_list = parts[1].strip(",").split(",") if parts[1] else []

  # skip creating groups and users if * is provided as value.
  users_list = filter(lambda x: x != '*' , users_list)
  groups_list = filter(lambda x: x != '*' , groups_list)

  if users_list:
    User(users_list,
          fetch_nonlocal_groups = params.fetch_nonlocal_groups
    )

  if groups_list:
    Group(copy(groups_list),
    )
  return groups_list
```

### d008
```
/**
 * Parse accept params `str` returning an
 * object with `.value`, `.quality` and `.params`.
 * also includes `.originalIndex` for stable sorting
 *
 * @param {String} str
 * @return {Object}
 * @api private
 */

function acceptParams(str, index) {
  var parts = str.split(/ *; */);
  var ret = { value: parts[0], quality: 1, params: {}, originalIndex: index };

  for (var i = 1; i < parts.length; ++i) {
    var pms = parts[i].split(/ *= */);
    if ('q' === pms[0]) {
      ret.quality = parseFloat(pms[1]);
    } else {
      ret.params[pms[0]] = pms[1];
    }
  }

  return ret;
}
```

### d009
```
def _format_jenkins_message(body: str) -> Tuple[str, List[str], Optional[str]]:
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    if not lines:
        return "(no details)", [], None
    status_emoji: Optional[str] = None
    first = lines[0]
    if "verified" in first.lower():
        status_emoji = _jenkins_status_emoji(first)
        lines = lines[1:]
    lines = _drop_patch_prefix(lines)
    if not lines:
        return first, [], status_emoji
    action = lines[0]
    remainder = lines[1:]
    return action, remainder, status_emoji
```

### d010
```
/**
	 * @param string $filename
	 * @param string $relPath
	 * @return string
	 */
	private function extractPageName( $filename, $relPath ) {
		$parts = explode( '.', $filename, 2 );
		$baseName = $parts[0];

		$parts = explode( '/', $relPath );
		$namespace = array_shift( $parts );
		$prefix = $parts ? array_shift( $parts ) : '';

		$segments = array_merge( $parts, [ $baseName ] );
		$namePart = ucfirst( $this->toCamelCase( implode( '-', $segments ) ) );

		$ret = $namespace . ':'
			. ( $prefix ? "$prefix/" : '' )
			. $namePart;

		$parts[] = $filename;

		$title = TitleClass::newFromText( $ret );
		$this->filenameMap[implode( '/', $parts )] = $title->getLocalURL( [ 'action' => 'raw' ] );

		return $ret;
	}
```

### d011
```
/**
       * Normalize spaces in cascade declaration group
       */
      reduceSpaces(decl) {
        let stop = false;
        this.prefixes.group(decl).up(() => {
          stop = true;
          return true;
        });
        if (stop) {
          return;
        }
        let parts = decl.raw("before").split("\n");
        let prevMin = parts[parts.length - 1].length;
        let diff = false;
        this.prefixes.group(decl).down((other) => {
          parts = other.raw("before").split("\n");
          let last = parts.length - 1;
          if (parts[last].length > prevMin) {
            if (diff === false) {
              diff = parts[last].length - prevMin;
            }
            parts[last] = parts[last].slice(0, -diff);
            other.raws.before = parts.join("\n");
          }
        });
      }
```

### d012
```
def parse_line(line, prefix):
    prefixlen = len(prefix)

    try:
        parsed = json.loads(line)
    except json.decoder.JSONDecodeError:
        return (None, None)

    text = parsed.get("msg")
    name = parsed.get("program")
    if not text or not name:
        return (None, None)

    name = str.translate(name, UNSAFE_CHARS)
    if not name.startswith(prefix):
        return (None, None)
    name = name[prefixlen:]

    if not ASCII_PRINTABLE_RE.match(name):
        return (None, None)

    return (name, text)
```

### d013
```
private boolean voiceGetFullAudioEffect(String inputLine) {
			String prefix = "MARY VOICE GETFULLAUDIOEFFECT ";
			assert inputLine.startsWith(prefix);
			String effectPlusParams = inputLine.substring(prefix.length()).trim();
			String[] parts = effectPlusParams.split("\\s", 2);
			String effectName = parts[0];
			String params = "";
			if (parts.length > 1) {
				params = parts[1]; // request contains effect params
			}
			AudioEffect effect = AudioEffects.getEffect(effectName);
			if (effect == null) {
				logger.error("Effect name missing in request!");
				return false;
			}
			// the request is about the parameters of a specific audio effect
			logger.debug("InfoRequest " + inputLine);
			effect.setParams(params);
			clientOut.println(effect.getFullEffectAsString());
			clientOut.println();
			return true;
		}
```

### d014
```
class Event(object):

    sse_line_pattern = re.compile('(?P<name>[^:]*):?( ?(?P<value>.*))?')

    def __init__(self, data='', event='message', id=None, retry=None):
        self.data = data
        self.event = event
        self.id = id
        self.retry = retry

    def dump(self):
        lines = []
        if self.id:
            lines.append('id: %s' % self.id)

        # Only include an event line if it's not the default already.
        if self.event != 'message':
            lines.append('event: %s' % self.event)

        if self.retry:
            lines.append('retry: %s' % self.retry)

        lines.extend('data: %s' % d for d in self.data.split('\n'))
        return '\n'.join(lines) + '\n\n'

    @classmethod
    def parse(cls, raw):
        """
        Given a possibly-multiline string representing an SSE message, parse it
        and return a Event object.
        """
        msg = cls()
        for line in raw.splitlines():
            m = cls.sse_line_pattern.match(line)
            if m is None:
                # Malformed line.  Discard but warn.
                warnings.warn('Invalid SSE line: "%s"' % line, SyntaxWarning)
                continue

            name = m.group('name')
            if name == '':
                # line began with a ":", so is a comment.  Ignore
                continue
            value = m.group('value')

            if name == 'data':
                # If we already have some data, then join to it with a newline.
                # Else this is it.
                if msg.data:
                    msg.data = '%s\n%s' % (msg.data, value)
                else:
                    msg.data = value
            elif name == 'event':
                msg.event = value
            elif name == 'id':
                msg.id = value
            elif name == 'retry':
                msg.retry = int(value)

        return msg

    def __str__(self):
        return self.data
```

### d015
```
def parseLogParams(self, logParams: bytes) -> tuple[list[str], list[str]]:
        params = phpserialize.loads(logParams, decode_strings=True)
        if params is str:
            oldGroups, newGroups = params.split('\n')
            return (oldGroups.split(','), newGroups.split(','))
        elif isinstance(params, dict):
            return (
                list(params.get('4::oldgroups', {}).values()),
                list(params.get('5::newgroups', {}).values())
            )
        # Just in case
        return ([], [])
```

### d016
```
/**
 * Parse accept params `str` returning an
 * object with `.value`, `.quality` and `.params`.
 *
 * @param {String} str
 * @return {Object}
 * @api private
 */

function acceptParams (str) {
  var parts = str.split(/ *; */);
  var ret = { value: parts[0], quality: 1, params: {} }

  for (var i = 1; i < parts.length; ++i) {
    var pms = parts[i].split(/ *= */);
    if ('q' === pms[0]) {
      ret.quality = parseFloat(pms[1]);
    } else {
      ret.params[pms[0]] = pms[1];
    }
  }

  return ret;
}
```

### d017
```
def _split_action_message(body: str) -> Tuple[str, List[str]]:
    lines = _drop_patch_prefix(body.splitlines())
    if not lines:
        return "(no details)", []
    action = lines[0].strip() or "(no details)"
    remainder = lines[1:]
    return action, remainder
```

### d018
```
def parse_mime_type(mime_type):
    """Carves up a mime_type and returns a tuple of the
       (type, subtype, params) where 'params' is a dictionary
       of all the parameters for the media range.
       For example, the media range 'application/xhtml;q=0.5' would
       get parsed into:

       ('application', 'xhtml', {'q', '0.5'})
       """
    parts = mime_type.split(";")
    params = dict([tuple([s.strip() for s in param.split("=")])\
            for param in parts[1:] ])
    (type, subtype) = parts[0].split("/")
    return (type.strip(), subtype.strip(), params)
```

### d019
```
def parse_headers(message):
    """
    Turn a Message object into a list of WSGI-style headers.
    """
    headers_out = []        
    for full_header in message.headers:
        if not full_header:            
            # Shouldn't happen, but we'll just ignore
            continue                     
        if full_header[0].isspace():
            # Continuation line, add to the last header
            if not headers_out:                        
                raise ValueError(
                    "First header starts with a space (%r)" % full_header)
            last_header, last_value = headers_out.pop()                   
            value = last_value + ' ' + full_header.strip()
            headers_out.append((last_header, value))      
            continue                                
        try:        
            header, value = full_header.split(':', 1)
        except:                                      
            raise ValueError("Invalid header: %r" % full_header)
        value = value.strip()                                   
        if header.lower() not in filtered_headers:
            headers_out.append((header, value))   
    return headers_out
```

## Output

Return raw JSON only. No preamble, no markdown fences, no commentary outside the
object.

```json
{
  "query_id": "D3",
  "labels": {
    "d001": {"score": 1.0, "rationale": "iterative binary search over sorted array"},
    "d002": {"score": 0.0, "rationale": "pytest case asserting search behaviour, not an implementation"}
  }
}
```

Every `doc_id` presented must appear exactly once in `labels`.
