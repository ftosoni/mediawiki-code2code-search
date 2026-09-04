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
func encodeJSON(v interface{}) ([]byte, error) {
    data, err := json.Marshal(v)
    if err != nil {
        return nil, fmt.Errorf("json encode: %w", err)
    }
    return data, nil
}
```

## Candidates

### d001
```
// MarshalJSON marshal this to JSON
func (s Schema) MarshalJSON() ([]byte, error) {
	if internal.UseOptimizedJSONMarshaling {
		return internal.DeterministicMarshal(s)
	}
	b1, err := json.Marshal(s.SchemaProps)
	if err != nil {
		return nil, fmt.Errorf("schema props %v", err)
	}
	b2, err := json.Marshal(s.VendorExtensible)
	if err != nil {
		return nil, fmt.Errorf("vendor props %v", err)
	}
	b3, err := s.Ref.MarshalJSON()
	if err != nil {
		return nil, fmt.Errorf("ref prop %v", err)
	}
	b4, err := s.Schema.MarshalJSON()
	if err != nil {
		return nil, fmt.Errorf("schema prop %v", err)
	}
	b5, err := json.Marshal(s.SwaggerSchemaProps)
	if err != nil {
		return nil, fmt.Errorf("common validations %v", err)
	}
	var b6 []byte
	if s.ExtraProps != nil {
		jj, err := json.Marshal(s.ExtraProps)
		if err != nil {
			return nil, fmt.Errorf("extra props %v", err)
		}
		b6 = jj
	}
	return swag.ConcatJSON(b1, b2, b3, b4, b5, b6), nil
}
```

### d002
```
func (Codec) Encode(v map[string]interface{}) ([]byte, error) {
	b, err := json.Marshal(v)
	if err != nil {
		return nil, err
	}

	// TODO: use printer.Format? Is the trailing newline an issue?

	ast, err := hcl.Parse(string(b))
	if err != nil {
		return nil, err
	}

	var buf bytes.Buffer

	err = printer.Fprint(&buf, ast.Node)
	if err != nil {
		return nil, err
	}

	return buf.Bytes(), nil
}
```

### d003
```
// MarshalJSON is a custom marshal function that knows how to encode Encoding as JSON
func (e *Encoding) MarshalJSON() ([]byte, error) {
	b1, err := json.Marshal(e.EncodingProps)
	if err != nil {
		return nil, err
	}
	b2, err := json.Marshal(e.VendorExtensible)
	if err != nil {
		return nil, err
	}
	return swag.ConcatJSON(b1, b2), nil
}
```

### d004
```
func (Codec) Encode(v map[string]any) ([]byte, error) {
	// TODO: expose prefix and indent in the Codec as setting?
	return json.MarshalIndent(v, "", "  ")
}
```

### d005
```
func appendJSONMarshal(buf *buffer.Buffer, v any) error {
	// Use a json.Encoder to avoid escaping HTML.
	var bb bytes.Buffer
	enc := json.NewEncoder(&bb)
	enc.SetEscapeHTML(false)
	if err := enc.Encode(v); err != nil {
		return err
	}
	bs := bb.Bytes()
	buf.Write(bs[:len(bs)-1]) // remove final newline
	return nil
}
```

### d006
```
func (s SamplePair) MarshalJSON() ([]byte, error) {
	t, err := json.Marshal(s.Timestamp)
	if err != nil {
		return nil, err
	}
	v, err := json.Marshal(s.Value)
	if err != nil {
		return nil, err
	}
	return []byte(fmt.Sprintf("[%s,%s]", t, v)), nil
}
```

### d007
```
// MarshalJSON is a custom marshal function that knows how to encode Parameter as JSON
func (p *Parameter) MarshalJSON() ([]byte, error) {
	b1, err := json.Marshal(p.Refable)
	if err != nil {
		return nil, err
	}
	b2, err := json.Marshal(p.ParameterProps)
	if err != nil {
		return nil, err
	}
	b3, err := json.Marshal(p.VendorExtensible)
	if err != nil {
		return nil, err
	}
	return swag.ConcatJSON(b1, b2, b3), nil
}
```

### d008
```
func (Codec) Encode(v map[string]interface{}) ([]byte, error) {
	// TODO: expose prefix and indent in the Codec as setting?
	return json.MarshalIndent(v, "", "  ")
}
```

### d009
```
// Encode writes the JSON encoding of v to the stream,
// followed by a newline character.
//
// See the documentation for Marshal for details about the
// conversion of Go values to JSON.
func (enc *Encoder) Encode(v interface{}) error {
	if enc.err != nil {
		return enc.err
	}
	e := newEncodeState()
	err := e.marshal(v, encOpts{escapeHTML: enc.escapeHTML})
	if err != nil {
		return err
	}

	// Terminate each value with a newline.
	// This makes the output look a little nicer
	// when debugging, and some kind of space
	// is required if the encoded value was a number,
	// so that the reader knows there aren't more
	// digits coming.
	e.WriteByte('\n')

	b := e.Bytes()
	if enc.indentPrefix != "" || enc.indentValue != "" {
		if enc.indentBuf == nil {
			enc.indentBuf = new(bytes.Buffer)
		}
		enc.indentBuf.Reset()
		err = Indent(enc.indentBuf, b, enc.indentPrefix, enc.indentValue)
		if err != nil {
			return err
		}
		b = enc.indentBuf.Bytes()
	}
	if _, err = enc.w.Write(b); err != nil {
		enc.err = err
	}
	encodeStatePool.Put(e)
	return err
}
```

### d010
```
// MarshalJSON is a custom marshal function that knows how to encode RequestBody as JSON
func (e *Example) MarshalJSON() ([]byte, error) {
	b1, err := json.Marshal(e.Refable)
	if err != nil {
		return nil, err
	}
	b2, err := json.Marshal(e.ExampleProps)
	if err != nil {
		return nil, err
	}
	b3, err := json.Marshal(e.VendorExtensible)
	if err != nil {
		return nil, err
	}
	return swag.ConcatJSON(b1, b2, b3), nil
}
```

### d011
```
func (s HistogramBucket) MarshalJSON() ([]byte, error) {
	b, err := json.Marshal(s.Boundaries)
	if err != nil {
		return nil, err
	}
	l, err := json.Marshal(s.Lower)
	if err != nil {
		return nil, err
	}
	u, err := json.Marshal(s.Upper)
	if err != nil {
		return nil, err
	}
	c, err := json.Marshal(s.Count)
	if err != nil {
		return nil, err
	}
	return []byte(fmt.Sprintf("[%s,%s,%s,%s]", b, l, u, c)), nil
}
```

### d012
```
// Marshal marshals the object into JSON then converts JSON to YAML and returns the
// YAML.
func Marshal(o interface{}) ([]byte, error) {
	j, err := json.Marshal(o)
	if err != nil {
		return nil, fmt.Errorf("error marshaling into JSON: %v", err)
	}

	y, err := JSONToYAML(j)
	if err != nil {
		return nil, fmt.Errorf("error converting JSON to YAML: %v", err)
	}

	return y, nil
}
```

### d013
```
// Encode encodes a value to JSON.
//
// If Encode cannot find a way to encode the type to JSON
// it will return an InvalidMarshalError.
func (enc *Encoder) Encode(v interface{}) error {
	if enc.isPooled == 1 {
		panic(InvalidUsagePooledEncoderError("Invalid usage of pooled encoder"))
	}
	switch vt := v.(type) {
	case string:
		return enc.EncodeString(vt)
	case bool:
		return enc.EncodeBool(vt)
	case MarshalerJSONArray:
		return enc.EncodeArray(vt)
	case MarshalerJSONObject:
		return enc.EncodeObject(vt)
	case int:
		return enc.EncodeInt(vt)
	case int64:
		return enc.EncodeInt64(vt)
	case int32:
		return enc.EncodeInt(int(vt))
	case int8:
		return enc.EncodeInt(int(vt))
	case uint64:
		return enc.EncodeUint64(vt)
	case uint32:
		return enc.EncodeInt(int(vt))
	case uint16:
		return enc.EncodeInt(int(vt))
	case uint8:
		return enc.EncodeInt(int(vt))
	case float64:
		return enc.EncodeFloat(vt)
	case float32:
		return enc.EncodeFloat32(vt)
	case *EmbeddedJSON:
		return enc.EncodeEmbeddedJSON(vt)
	default:
		return InvalidMarshalError(fmt.Sprintf(invalidMarshalErrorMsg, vt))
	}
}
```

### d014
```
// MarshalJSON is a custom marshal function that knows how to encode SecurityScheme as JSON
func (s *SecurityScheme) MarshalJSON() ([]byte, error) {
	b1, err := json.Marshal(s.SecuritySchemeProps)
	if err != nil {
		return nil, err
	}
	b2, err := json.Marshal(s.VendorExtensible)
	if err != nil {
		return nil, err
	}
	b3, err := json.Marshal(s.Refable)
	if err != nil {
		return nil, err
	}
	return swag.ConcatJSON(b1, b2, b3), nil
}
```

### d015
```
// MarshalJSON is a custom marshal function that knows how to encode Header as JSON
func (h *Header) MarshalJSON() ([]byte, error) {
	b1, err := json.Marshal(h.Refable)
	if err != nil {
		return nil, err
	}
	b2, err := json.Marshal(h.HeaderProps)
	if err != nil {
		return nil, err
	}
	b3, err := json.Marshal(h.VendorExtensible)
	if err != nil {
		return nil, err
	}
	return swag.ConcatJSON(b1, b2, b3), nil
}
```

### d016
```
func (enc *Encoder) encodeEmbeddedJSON(v *EmbeddedJSON) ([]byte, error) {
	enc.writeBytes(*v)
	return enc.buf, nil
}
```

### d017
```
func (Codec) Encode(v map[string]any) ([]byte, error) {
	b, err := json.Marshal(v)
	if err != nil {
		return nil, err
	}

	// TODO: use printer.Format? Is the trailing newline an issue?

	ast, err := hcl.Parse(string(b))
	if err != nil {
		return nil, err
	}

	var buf bytes.Buffer

	err = printer.Fprint(&buf, ast.Node)
	if err != nil {
		return nil, err
	}

	return buf.Bytes(), nil
}
```

### d018
```
func (enc *Encoder) encodeObject(v MarshalerJSONObject) ([]byte, error) {
	enc.grow(512)
	enc.writeByte('{')
	if !v.IsNil() {
		v.MarshalJSONObject(enc)
	}
	if enc.hasKeys {
		enc.hasKeys = false
		enc.keys = nil
	}
	enc.writeByte('}')
	return enc.buf, enc.err
}
```

## Output

Return raw JSON only. No preamble, no markdown fences, no commentary outside the
object.

```json
{
  "query_id": "A4",
  "labels": {
    "d001": {"score": 1.0, "rationale": "iterative binary search over sorted array"},
    "d002": {"score": 0.0, "rationale": "pytest case asserting search behaviour, not an implementation"}
  }
}
```

Every `doc_id` presented must appear exactly once in `labels`.
