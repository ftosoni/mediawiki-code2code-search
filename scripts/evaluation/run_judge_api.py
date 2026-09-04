"""Send the blinded judge prompts to a judge model's API and save raw responses.

Supports two API shapes:

  --provider gemini   Google Generative Language REST (Google AI Studio key)
  --provider openai   any OpenAI-compatible /chat/completions endpoint
                      (Moonshot/Kimi, DeepSeek, OpenRouter, OpenAI, Together, ...)

The API key is read from an ENVIRONMENT VARIABLE, never a command-line argument,
so it never lands in your shell history or this file. Set it first, e.g.:

    # PowerShell
    $env:GEMINI_API_KEY = "..."
    $env:OPENAI_API_KEY = "..."     # or MOONSHOT_API_KEY / DEEPSEEK_API_KEY / OPENROUTER_API_KEY

Raw responses are written one-per-query to --out-raw; feed that directory to
assemble_judge_output.py afterwards. Already-written queries are skipped, so a
failed run can simply be re-run to resume.

Examples
--------
    # Gemini 2.5 Flash
    python run_judge_api.py --provider gemini --model gemini-2.5-flash \
        --api-key-env GEMINI_API_KEY --out-raw judging/raw_gemini

    # Kimi K2 via Moonshot
    python run_judge_api.py --provider openai --base-url https://api.moonshot.ai/v1 \
        --model kimi-k2-0711-preview --api-key-env MOONSHOT_API_KEY --out-raw judging/raw_kimi

    # Kimi K2 (or DeepSeek/Qwen) via OpenRouter — one key for many models
    python run_judge_api.py --provider openai --base-url https://openrouter.ai/api/v1 \
        --model moonshotai/kimi-k2 --api-key-env OPENROUTER_API_KEY --out-raw judging/raw_kimi

    # DeepSeek
    python run_judge_api.py --provider openai --base-url https://api.deepseek.com \
        --model deepseek-chat --api-key-env DEEPSEEK_API_KEY --out-raw judging/raw_deepseek

Then:
    python assemble_judge_output.py --judge gemini-2.5-flash --raw-dir judging/raw_gemini
"""
import argparse
import glob
import json
import os
import re
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))


def load_env_file(path):
    """Load NAME="value" / NAME=value lines from a dotenv-style file into the
    environment (comments and blanks ignored). Real environment variables win."""
    if not path or not os.path.isfile(path):
        return 0
    n = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.lower().startswith("export "):
                line = line[7:]
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k and k not in os.environ:      # don't override an already-set var
                os.environ[k] = v
                n += 1
    return n


def call_gemini(model, key, prompt, temperature, timeout, max_tokens):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature, "responseMimeType": "application/json",
                             "maxOutputTokens": max_tokens},
    }
    req = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": key}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.load(r)
    return data["candidates"][0]["content"]["parts"][0]["text"]


def call_openai(base_url, model, key, prompt, temperature, timeout, json_mode, max_tokens):
    url = base_url.rstrip("/") + "/chat/completions"
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    req = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.load(r)
    return data["choices"][0]["message"]["content"]


def call_with_retry(fn, retries, base_delay):
    last = None
    for attempt in range(retries + 1):
        try:
            return fn()
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            last = f"HTTP {e.code}: {detail}"
            # don't retry client errors except rate-limit
            if e.code not in (429, 500, 502, 503, 504):
                break
        except (urllib.error.URLError, TimeoutError, KeyError, IndexError) as e:
            last = repr(e)
        if attempt < retries:
            delay = base_delay * (2 ** attempt)
            print(f"    retry in {delay:.0f}s ({last})")
            time.sleep(delay)
    raise RuntimeError(last)


def qid_of(path):
    m = re.search(r"prompt_([A-Za-z]+\d+)\.md$", os.path.basename(path))
    return m.group(1) if m else os.path.splitext(os.path.basename(path))[0]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--provider", choices=["gemini", "openai"], required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--api-key-env", required=True, help="NAME of the env var holding the API key")
    ap.add_argument("--env-file", default=os.path.join(HERE, ".env"),
                    help="dotenv-style file with NAME=\"value\" keys (default: ./.env, git-ignored)")
    ap.add_argument("--base-url", help="base URL for --provider openai (e.g. https://api.moonshot.ai/v1)")
    ap.add_argument("--inputs", default=os.path.join(HERE, "judging", "judge_inputs"))
    ap.add_argument("--out-raw", required=True, help="directory to write raw per-query responses")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--json-mode", action="store_true",
                    help="request response_format=json_object (openai provider; some endpoints reject it)")
    ap.add_argument("--max-tokens", type=int, default=16384,
                    help="max output tokens per response (must be under the provider's cap)")
    ap.add_argument("--timeout", type=float, default=120)
    ap.add_argument("--retries", type=int, default=4)
    ap.add_argument("--sleep", type=float, default=0.5, help="pause between queries (rate-limit friendly)")
    ap.add_argument("--limit", type=int, default=0, help="only process the first N queries (for testing)")
    args = ap.parse_args()

    loaded = load_env_file(args.env_file)
    if loaded:
        print(f"Loaded {loaded} key(s) from {args.env_file}")
    key = os.environ.get(args.api_key_env)
    if not key:
        raise SystemExit(f"Environment variable {args.api_key_env} is not set "
                         f"(looked in {args.env_file} too). Add a line "
                         f'{args.api_key_env}="..." to that file, or set the env var.')
    if args.provider == "openai" and not args.base_url:
        raise SystemExit("--base-url is required for --provider openai.")

    prompts = sorted(glob.glob(os.path.join(args.inputs, "prompt_*.md")),
                     key=lambda p: (qid_of(p)[0], int(re.sub(r"\D", "", qid_of(p)) or 0)))
    if args.limit:
        prompts = prompts[: args.limit]
    os.makedirs(args.out_raw, exist_ok=True)

    done = errs = 0
    for path in prompts:
        qid = qid_of(path)
        out = os.path.join(args.out_raw, f"{qid}.json")
        if os.path.exists(out) and os.path.getsize(out) > 0:
            print(f"  {qid}: already done, skipping")
            done += 1
            continue
        prompt = open(path, encoding="utf-8").read()
        try:
            if args.provider == "gemini":
                text = call_with_retry(
                    lambda: call_gemini(args.model, key, prompt, args.temperature,
                                        args.timeout, args.max_tokens),
                    args.retries, args.sleep + 2)
            else:
                text = call_with_retry(
                    lambda: call_openai(args.base_url, args.model, key, prompt,
                                        args.temperature, args.timeout, args.json_mode,
                                        args.max_tokens),
                    args.retries, args.sleep + 2)
            open(out, "w", encoding="utf-8").write(text)
            print(f"  {qid}: ok ({len(text)} chars)")
            done += 1
        except Exception as e:
            print(f"  {qid}: FAILED - {e}")
            errs += 1
        time.sleep(args.sleep)

    print(f"\nDone: {done} ok, {errs} failed -> {args.out_raw}")
    print(f"Next: python assemble_judge_output.py --judge {args.model} --raw-dir {args.out_raw}")


if __name__ == "__main__":
    main()
