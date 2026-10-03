# Research AI and Survey Infrastructure Demo

A small, independent portfolio project showing how a research team can call an LLM API, track processing steps and usage, and prepare a survey study through a research platform API. All bundled records are fictional and synthetic.

**The default run is offline.** Tests replace HTTP with local fakes. Live calls require explicit command-line flags and credentials. The Prolific adapter can create an unpublished draft only; this project has no publish or participant-recruitment operation.

## What it demonstrates

- **LLM integration:** OpenAI Responses API request, bounded output, `store: false`, response parsing, token/latency records, and optional cost estimates using rates you provide.
- **Survey research workflow:** Prolific API adapter for creating a draft study with a placeholder survey URL. Review and publish manually in Prolific if you later adapt the example.
- **Reproducible processing:** newline-delimited JSON audit events identify each synthetic record and processing step without logging its source text.
- **Credential hygiene:** keys come from environment variables, `.env` is ignored by Git, and CI uses no credentials.
- **Testing and automation:** mocked provider tests run on GitHub Actions; no paid API call is made by CI.

The companion repository [`API-ssb-life-expectancy`](https://github.com/fttjuki/API-ssb-life-expectancy) demonstrates a public-data API pipeline. This repository focuses on LLM and survey-platform workflows.

## Run locally

Requires Python 3.11 or later. The offline demo and its tests need no API keys.

```bash
python -m venv .venv
source .venv/bin/activate
PYTHONPATH=src python -m research_demo.cli
PYTHONPATH=src python -m unittest discover -s tests -v
```

The default output is an audit trail with placeholder LLM results. It does not make network requests.

## Optional live LLM example

Set `OPENAI_API_KEY` in your shell or local environment manager. Do not put a real key in source code or commit it. Set `OPENAI_MODEL` if you want another supported model.

```bash
export OPENAI_API_KEY='your-key'
python -m research_demo.cli --live-llm
```

Only the fictional snippets in `data/synthetic_texts.json` are sent. The request sets `store: false`; that setting does not by itself change provider abuse-monitoring or other data-retention terms. Review the provider's current data controls before sending real research data. The example records response text and token counts in its local stdout audit output; treat live output as research data and avoid sharing it indiscriminately.

To estimate costs, set both `INPUT_USD_PER_MILLION` and `OUTPUT_USD_PER_MILLION` using current provider pricing. No prices are hardcoded because they change.

## Optional Prolific draft example

Set `PROLIFIC_API_TOKEN` in your environment, then run:

```bash
python -m research_demo.cli --create-prolific-draft
```

This sends a request that creates a small, unpublished draft at Prolific. The external survey URL is a placeholder (`https://example.org/synthetic-survey`) and is not a working questionnaire. No participants are recruited and no study is published. Before adapting this for real research, replace the URL, review the study fields and compensation, verify the current API docs, and complete institutional ethics and consent review.

The two live flags can be combined, but neither is enabled by default:

```bash
python -m research_demo.cli --live-llm --create-prolific-draft
```

## Privacy, access, and research integrity

- Synthetic data only; do not upload participant responses or personal data to this demo.
- Use least-privilege API credentials, keep them outside Git, rotate exposed keys, and revoke unused tokens.
- Restrict who can access secrets in the provider dashboard and GitHub settings; never add secrets to Actions for the current tests.
- The audit output records record IDs, step names, model metadata, usage and latency, not source text. LLM output itself may still contain information and should be handled appropriately.
- A real study needs informed consent, ethics review where applicable, a data-management plan, retention/deletion rules, and a human review of model outputs.
- Prolific credentials can perform account actions. This example's function only creates a draft; inspect the request and dashboard before using it with a real token.

## References

- [OpenAI Responses API quickstart](https://platform.openai.com/docs/quickstart)
- [OpenAI API data controls](https://platform.openai.com/docs/guides/your-data)
- [Prolific API documentation](https://docs.prolific.com/)
- [Prolific API: create a study](https://docs.prolific.com/api-reference/studies/create-a-study)

## 中文简介

这是一个独立的研究基础设施演示仓库：用合成文本演示 LLM API 调用、处理步骤和用量记录，并通过 Prolific API 准备一份未发布的问卷研究草稿。默认运行完全离线；测试使用模拟响应；不会发布研究或招募参与者。真实研究前需要替换占位问卷链接，并完成伦理、知情同意、隐私和数据保留审查。
