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
-- Lua
local function serialize(val, indent)
    indent = indent or 0
    if type(val) == "table" then
        local parts = {}
        for k, v in pairs(val) do
            parts[#parts+1] = string.rep("  ", indent+1)
                .. tostring(k) .. " = " .. serialize(v, indent+1)
        end
        return "{\n" .. table.concat(parts, ",\n")
            .. "\n" .. string.rep("  ", indent) .. "}"
    end
    return tostring(val)
end
```

## Candidates

### d001
```
-- Renders a serialized Snak value to wikitext escaped plain text.
-- This is useful for displaying References or Qualifiers.
function UnlinkedWikibase.renderSnak( snak )
	return php.renderSnak( snak )
end
```

### d002
```
/**
 * Converts PHP data into a Lua (Scribunto) module
 */
class LuaSerializer implements LoggerAwareInterface {

	use LoggerAwareTrait;

	private const RESERVED = [
		'and', 'break', 'do', 'else', 'elseif',
		'end', 'false', 'for', 'function', 'if',
		'in', 'local', 'nil', 'not', 'or',
		'repeat', 'return', 'then', 'true', 'until', 'while'
	];

	public function __construct() {
		$this->logger = new NullLogger();
	}

	/**
	 * Convert JSON data into a Lua module. The return from the call is suitable
	 * for writing to a Module: namespace page and loading with mw.loadData.
	 * @param array $stuff
	 * @return string
	 */
	public function serialize( array $stuff ) {
		return 'return ' . $this->convertToLua( $stuff );
	}

	/**
	 * Convert to an unquoted name if possible, otherwise do normal string.
	 *
	 * @param string $stuff
	 * @return bool
	 */
	private function convertToLuaIdentifier( $stuff ) {
		if (
			is_string( $stuff ) &&
			preg_match( "/^[a-zA-Z][a-zA-Z0-9_]*$/", $stuff ) &&
			!in_array( $stuff, self::RESERVED )
		) {
			return $stuff;
		} else {
			return '[' . $this->convertToLua( $stuff ) . ']';
		}
	}

	/**
	 * Convert JSON data into a Lua table.
	 * @param array|string|int|float|bool|null $stuff
	 * @param int $level Indentation level
	 * @return string
	 */
	protected function convertToLua( $stuff, $level = 1 ) {
		if ( is_string( $stuff ) ) {
			return '"' . addcslashes( $stuff, "\0..\37\"\\" ) . '"';
		}

		if ( is_int( $stuff ) || is_float( $stuff ) ) {
			return (string)$stuff;
		}
		if ( is_bool( $stuff ) ) {
			return $stuff ? 'true' : 'false';
		}
		if ( $stuff === null ) {
			return 'nil';
		}

		if ( is_array( $stuff ) ) {
			$out = "{\n";
			// Bit hacky, try and figure out if it is numeric array.
			if ( isset( $stuff[0] ) && isset( $stuff[count( $stuff ) - 1] ) ) {
				foreach ( $stuff as $value ) {
					$out .= $this->convertToLua( $value ) . ',';
				}
			} else {
				foreach ( $stuff as $key => $value ) {
					// $out .= str_repeat( "\t", $level );
					if ( is_int( $key ) ) {
						// lua is 1-based.
						$key++;
					}
					$out .= $this->convertToLuaIdentifier( $key ) . '='
						. $this->convertToLua( $value, $level + 1 ) . ",\n";
				}
			}
			// We are running out of space, don't pretty print.
			// $out .= str_repeat( "\t", $level - 1 );
			$out .= "}";
			return $out;
		}
		$this->logger->error( "$stuff is invalid type" );
		die();
	}

}
```

### d003
```
local function sub_print_r(t,indent)
            if (type(t)=="table") then
                for pos,val in pairs(t) do
                    if (type(val)=="table") then
                        mw.log(indent.."["..pos.."] => "..tostring(t).." {")
                        sub_print_r(val,indent..string.rep(" ",string.len(pos)+8))
                        mw.log(indent..string.rep(" ",string.len(pos)+6).."}")
                    else
                        mw.log(indent.."["..pos.."] => "..tostring(val))
                    end
                end
            else
                mw.log(indent..tostring(t))
            end
    end
```

### d004
```
/**
	 * Emit $val as JSON, with $indent extra indentations on each line.
	 * @param array $val
	 * @param int $indent
	 * @return string the JSON string for $val
	 */
	public function encode( $val, $indent ) {
		$str = json_encode( $val, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES );
		// Strip outermost open/close braces/brackets
		$str = preg_replace( '/^[[{]\n?|\n?[}\]]$/', '', $str );

		if ( $indent > 0 ) {
			// add extra indentation
			$str = preg_replace( '/^/m', str_repeat( '    ', $indent ), $str );
		}

		return $str;
	}
```

### d005
```
--- An implementation of tostring() which does not expose pointers.
function MWServer:tostring(val)
	local mt = getmetatable( val )
	if mt and mt.__tostring then
		return mt.__tostring(val)
	end
	local typeName = type(val)
	local nonPointerTypes = {number = true, string = true, boolean = true, ['nil'] = true}
	if nonPointerTypes[typeName] then
		return tostring(val)
	else
		return typeName
	end
end
```

### d006
```
function mw.dumpObject( object )
	local doneTable = {}
	local doneObj = {}
	local ct = {}
	local function sorter( a, b )
		local ta, tb = type( a ), type( b )
		if ta ~= tb then
			return ta < tb
		end
		if ta == 'string' or ta == 'number' then
			return a < b
		end
		if ta == 'boolean' then
			return tostring( a ) < tostring( b )
		end
		return false -- Incomparable
	end
	local function _dumpObject( object, indent, expandTable )
		local tp = type( object )
		if tp == 'number' or tp == 'nil' or tp == 'boolean' then
			return tostring( object )
		elseif tp == 'string' then
			return string.format( "%q", object )
		elseif tp == 'table' then
			if not doneObj[object] then
				local s = tostring( object )
				if s == 'table' then
					ct[tp] = ( ct[tp] or 0 ) + 1
					doneObj[object] = 'table#' .. ct[tp]
				else
					doneObj[object] = s
					doneTable[object] = true
				end
			end
			if doneTable[object] or not expandTable then
				return doneObj[object]
			end
			doneTable[object] = true

			local ret = { doneObj[object], ' {\n' }
			local mt = getmetatable( object )
			local indentString = "  "
			if mt then
				ret[#ret + 1] = string.rep( indentString, indent + 2 )
				ret[#ret + 1] = 'metatable = '
				ret[#ret + 1] = _dumpObject( mt, indent + 2, false )
				ret[#ret + 1] = "\n"
			end

			local doneKeys = {}
			for key, value in ipairs( object ) do
				doneKeys[key] = true
				ret[#ret + 1] = string.rep( indentString, indent + 2 )
				ret[#ret + 1] = _dumpObject( value, indent + 2, true )
				ret[#ret + 1] = ',\n'
			end
			local keys = {}
			for key in pairs( object ) do
				if not doneKeys[key] then
					keys[#keys + 1] = key
				end
			end
			table.sort( keys, sorter )
			for i = 1, #keys do
				local key = keys[i]
				ret[#ret + 1] = string.rep( indentString, indent + 2 )
				ret[#ret + 1] = '['
				ret[#ret + 1] = _dumpObject( key, indent + 3, false )
				ret[#ret + 1] = '] = '
				ret[#ret + 1] = _dumpObject( object[key], indent + 2, true )
				ret[#ret + 1] = ",\n"
			end
			ret[#ret + 1] = string.rep( indentString, indent )
			ret[#ret + 1] = '}'
			return table.concat( ret )
		else
			if not doneObj[object] then
				ct[tp] = ( ct[tp] or 0 ) + 1
				doneObj[object] = tostring( object ) .. '#' .. ct[tp]
			end
			return doneObj[object]
		end
	end
	return _dumpObject( object, 0, true )
end
```

### d007
```
function linkedwiki.concatWithComma(tab,tabOrder)
    local html = ""
    local comma = ""
    if tabOrder then
		for id, iri in ipairs(tabOrder) do
			if tab[iri] then
				html = html .. comma .. tab[iri]
				comma=", "
			end
		end
    else
        for key, value in pairs(tab) do
            html = html .. comma .. value
            comma=", "
        end
    end
    return html
end
```

### d008
```
function Linkedwiki:printItemInWiki(valueInWiki, valueInDB, tagLang)
        --mw.log("linkedwiki.printTitleInWiki(valueInWiki "..valueInWiki..",valueInDB ".. valueInDB..")")
        local listIri = nil
        local listValue = nil
        local text = ""
        local titleInDB = ""

        local tabIriInDB = {}
        local tabTitleInDB = {}
        local tabHtmlInDB = {}

        local tabHtmlInWiki = {}
        local cleanId =""
        local titleInWiki =""
        local idInWiki=""

        local tabOrder = {}

        local isDifferent = false
        local html = ''
        local comma = ''
        local listValueInDB = ''

        if not linkedwiki.isEmpty(valueInDB) then
            listIri = linkedwiki.explode(";", valueInDB)
            for i, iri in ipairs(listIri) do
                self:initConfig()
                titleInDB = linkedwiki.getString("http://www.w3.org/2000/01/rdf-schema#label", tagLang, iri)

                --text = '<span class="plainlinks">[' .. iri .. ' ' .. titleInDB .. ']</span>'
                cleanId = string.match(iri, "(Q.*)")
                text = ""
                text = '<span class="plainlinks">'
                            .. '[https://www.wikidata.org/wiki/Special:GoToLinkedPage/'.. self:getLang(tagLang)
                            ..'wiki/' ..cleanId
                            ..' '
                            ..  titleInDB
                            .. ']</span>'
                text = text.. '<span class="plainlinks"><small>([' .. iri .. ' '..cleanId..'])</small></span>'

                tabIriInDB[iri]= true

                tabTitleInDB[iri]= titleInDB
                tabHtmlInDB[iri]= text
                table.insert(tabOrder, iri)
            end
        end

        if not linkedwiki.isEmpty(valueInWiki) then
            listValue = linkedwiki.explode(";", valueInWiki)
            local wikidata
            local iriInWikidata

            for i, id in ipairs(listValue) do
                idInWiki = mw.text.trim( id )
                cleanId = string.match(idInWiki, "(Q.*)")
                text = ""
                --mw.log(idInWiki)
                if not linkedwiki.isEmpty(cleanId) then
                    iriInWikidata = "http://www.wikidata.org/entity/" .. cleanId
                    wikidata = linkedwiki.new(iriInWikidata,"http://www.wikidata.org",self:getLang(tagLang))
                    titleInWiki = wikidata:getString("http://www.w3.org/2000/01/rdf-schema#label", self:getLang(tagLang))
                    text = '<span class="plainlinks">'
                            .. '[https://www.wikidata.org/wiki/Special:GoToLinkedPage/'.. self:getLang(tagLang)
                            ..'wiki/' ..cleanId
                            ..' '
                            ..  titleInWiki
                            .. ']</span>'

                    text = text.. '<span class="plainlinks"><small>([' .. iriInWikidata .. ' '..cleanId..'])</small></span>'

                    --mw.log(text..'EE')
                else -- it is not a ID
                    tabTitleInWiki = idInWiki
                    iriInWikidata = idInWiki
                    text = idInWiki
                end

                tabHtmlInWiki[iriInWikidata]= text

                if not tabIriInDB[iriInWikidata] then
                     tabIriInDB[iriInWikidata]= false
                     isDifferent = true
                     table.insert(tabOrder, iriInWikidata)
                elseif tabTitleInDB[iriInWikidata] ~= titleInWiki then
                    tabHtmlInDB[iriInWikidata]= text
                   isDifferent = true
                --   tabTitleInDB[iriInWikidata] = titleInWiki
                end
            end
        end

        if isDifferent then
            self.databaseIsUpdate = false
        end

        for id, iri in ipairs(tabOrder) do

            if tabIriInDB[iri] then
               html = html .. comma .. tabHtmlInDB[iri]
               listValueInDB  = listValueInDB .. comma .. tabTitleInDB[iri]
            else
               html = html .. comma .. tabHtmlInWiki[iri]
            end
            comma = ', '
        end
        return linkedwiki.buildDivSimple(isDifferent,html,listValueInDB)
    end
```

### d009
```
-- Return a string represetation of a value, including the deep structure of a table
local function deepToString( val, indent, done )
	done = done or {}
	indent = indent or 0

	local tp = type( val )
	if tp == 'string' then
		return string.format( "%q", val )
	elseif tp == 'table' then
		if done[val] then return '{ ... }' end
		done[val] = true
		local sb = { '{\n' }
		local donekeys = {}
		for key, value in ipairs( val ) do
			donekeys[key] = true
			sb[#sb + 1] = string.rep( " ", indent + 2 )
			sb[#sb + 1] = deepToString( value, indent + 2, done )
			sb[#sb + 1] = ",\n"
		end
		local keys = {}
		for key in pairs( val ) do
			if not donekeys[key] then
				keys[#keys + 1] = key
			end
		end
		table.sort( keys )
		for i = 1, #keys do
			local key = keys[i]
			sb[#sb + 1] = string.rep( " ", indent + 2 )
			if type( key ) == 'table' then
				sb[#sb + 1] = '[{ ... }] = '
			else
				sb[#sb + 1] = '['
				sb[#sb + 1] = deepToString( key, indent + 3, done )
				sb[#sb + 1] = '] = '
			end
			sb[#sb + 1] = deepToString( val[key], indent + 2, done )
			sb[#sb + 1] = ",\n"
		end
		sb[#sb + 1] = string.rep( " ", indent )
		sb[#sb + 1] = "}"
		return table.concat( sb )
	else
		return tostring( val )
	end
end
```

### d010
```
-- Render a list of Snak values from their serialization as wikitext escaped plain text.
	--
	-- @param {table} snaksSerialization
	function wikibase.renderSnaks( snaksSerialization )
		incrementStatsKey( 'renderSnaks' )

		checkType( 'renderSnaks', 1, snaksSerialization, 'table' )

		return php.renderSnaks( snaksSerialization )
	end
```

### d011
```
-- Render a Snak value from its serialization as rich wikitext.
	--
	-- @param {table} snakSerialization
	function wikibase.formatValue( snakSerialization )
		incrementStatsKey( 'formatValue' )

		checkType( 'formatValue', 1, snakSerialization, 'table' )

		return php.formatValue( snakSerialization )
	end
```

### d012
```
/**
	 * @param mixed $var
	 * @param string $indent
	 * @return string
	 */
	public static function formatVar( $var, string $indent = '' ): string {
		if ( $var === [] ) {
			return '[]';
		} elseif ( is_array( $var ) ) {
			$ret = '[';
			$indent .= "\t";
			foreach ( $var as $key => $val ) {
				$ret .= "\n$indent" . self::formatVar( $key, $indent ) .
					' => ' . self::formatVar( $val, $indent ) . ',';
			}
			// Strip trailing commas
			return substr( $ret, 0, -1 ) . "\n" . substr( $indent, 0, -1 ) . ']';
		} elseif ( is_string( $var ) ) {
			// Don't escape the string (specifically backslashes) to avoid displaying wrong stuff
			return "'$var'";
		} elseif ( $var === null ) {
			return 'null';
		} elseif ( is_float( $var ) ) {
			// Don't let float precision produce weirdness
			return (string)$var;
		}
		return var_export( $var, true );
	}
```

### d013
```
local function _dumpObject( object, indent, expandTable )
		local tp = type( object )
		if tp == 'number' or tp == 'nil' or tp == 'boolean' then
			return tostring( object )
		elseif tp == 'string' then
			return string.format( "%q", object )
		elseif tp == 'table' then
			if not doneObj[object] then
				local s = tostring( object )
				if s == 'table' then
					ct[tp] = ( ct[tp] or 0 ) + 1
					doneObj[object] = 'table#' .. ct[tp]
				else
					doneObj[object] = s
					doneTable[object] = true
				end
			end
			if doneTable[object] or not expandTable then
				return doneObj[object]
			end
			doneTable[object] = true

			local ret = { doneObj[object], ' {\n' }
			local mt = getmetatable( object )
			local indentString = "  "
			if mt then
				ret[#ret + 1] = string.rep( indentString, indent + 2 )
				ret[#ret + 1] = 'metatable = '
				ret[#ret + 1] = _dumpObject( mt, indent + 2, false )
				ret[#ret + 1] = "\n"
			end

			local doneKeys = {}
			for key, value in ipairs( object ) do
				doneKeys[key] = true
				ret[#ret + 1] = string.rep( indentString, indent + 2 )
				ret[#ret + 1] = _dumpObject( value, indent + 2, true )
				ret[#ret + 1] = ',\n'
			end
			local keys = {}
			for key in pairs( object ) do
				if not doneKeys[key] then
					keys[#keys + 1] = key
				end
			end
			table.sort( keys, sorter )
			for i = 1, #keys do
				local key = keys[i]
				ret[#ret + 1] = string.rep( indentString, indent + 2 )
				ret[#ret + 1] = '['
				ret[#ret + 1] = _dumpObject( key, indent + 3, false )
				ret[#ret + 1] = '] = '
				ret[#ret + 1] = _dumpObject( object[key], indent + 2, true )
				ret[#ret + 1] = ",\n"
			end
			ret[#ret + 1] = string.rep( indentString, indent )
			ret[#ret + 1] = '}'
			return table.concat( ret )
		else
			if not doneObj[object] then
				ct[tp] = ( ct[tp] or 0 ) + 1
				doneObj[object] = tostring( object ) .. '#' .. ct[tp]
			end
			return doneObj[object]
		end
	end
```

### d014
```
-- Render a Snak value from its serialization as wikitext escaped plain text.
	--
	-- @param {table} snakSerialization
	function wikibase.renderSnak( snakSerialization )
		incrementStatsKey( 'renderSnak' )

		checkType( 'renderSnak', 1, snakSerialization, 'table' )

		return php.renderSnak( snakSerialization )
	end
```

### d015
```
function convertResultTableToString( queryResult )

    local queryResult = queryResult

    if queryResult == nil or #queryResult == 0 then
        return "(no values)"
    end

    if type( queryResult ) == "table" then
        local myResult = "<ul>"
        for num, row in ipairs( queryResult ) do
            myResult = myResult .. '<li> This is result #' .. num .. '\n<ul>'
            for property, data in pairs( row ) do
                local dataOutput = data
                if type( data ) == 'table' then
                    dataOutput = mw.text.listToText( data, ', ', ' and ')
                end
                myResult = myResult .. '<li> ' .. property .. ': ' .. dataOutput .. '</li>'
            end
            myResult = myResult .. '</ul></li>\n'
        end
        myResult = myResult .. '</ul>\n'
        return myResult
    end
    return queryResult
end
```

### d016
```
function parseSerializedBuckets( serialized ) {

		const parsedBuckets = {};

		serialized.split( '*' ).forEach( ( strBucket ) => {
			const parts = strBucket.split( '!' ),
				key = decodeCampaignName( parts[ 0 ] ),
				start = parseInt( parts[ 1 ], 10 ) + 14e8,
				end = start + parseInt( parts[ 2 ], 10 ),
				val = parseInt( parts[ 3 ], 10 );

			if ( key && start && end && !isNaN( val ) ) {
				parsedBuckets[ key ] = {
					start: start,
					end: end,
					val: val
				};
			}
		} );

		return parsedBuckets;
	}
```

### d017
```
function linkedwiki.print_r ( t )
    local print_r_cache={}
    local function sub_print_r(t,indent)
            if (type(t)=="table") then
                for pos,val in pairs(t) do
                    if (type(val)=="table") then
                        mw.log(indent.."["..pos.."] => "..tostring(t).." {")
                        sub_print_r(val,indent..string.rep(" ",string.len(pos)+8))
                        mw.log(indent..string.rep(" ",string.len(pos)+6).."}")
                    else
                        mw.log(indent.."["..pos.."] => "..tostring(val))
                    end
                end
            else
                mw.log(indent..tostring(t))
            end
    end
    sub_print_r(t,"  ")
end
```

### d018
```
-- Render a list of Snak values from their serialization as rich wikitext.
	--
	-- @param {table} snaksSerialization
	function wikibase.formatValues( snaksSerialization )
		incrementStatsKey( 'formatValues' )

		checkType( 'formatValues', 1, snaksSerialization, 'table' )

		return php.formatValues( snaksSerialization )
	end
```

## Output

Return raw JSON only. No preamble, no markdown fences, no commentary outside the
object.

```json
{
  "query_id": "C5",
  "labels": {
    "d001": {"score": 1.0, "rationale": "iterative binary search over sorted array"},
    "d002": {"score": 0.0, "rationale": "pytest case asserting search behaviour, not an implementation"}
  }
}
```

Every `doc_id` presented must appear exactly once in `labels`.
