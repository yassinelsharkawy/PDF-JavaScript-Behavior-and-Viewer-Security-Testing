# PDF JavaScript Behavior and Viewer-Security Testing

## Abstract

This repository provides a small, reproducible test artifact for examining how PDF viewers handle document-level JavaScript. It is intended for authorized application-security testing, security education, and controlled compatibility experiments. The generator supports two modes: a benign JavaScript alert intended to demonstrate viewer behavior, and a static PDF with no JavaScript action.

The artifact is deliberately non-collecting. It does not request credentials, define form fields, submit data, open external URLs, or send network traffic. It uses only the Python standard library.

## Research objective

The project is designed to support investigation of the following questions:

- Do different PDF viewers execute, restrict, or ignore document-level JavaScript?
- How do viewer configuration and security prompts affect the handling of active PDF content?
- What controls should an application apply when accepting, storing, transforming, or previewing user-supplied PDF files?

A JavaScript action inside a PDF is not, by itself, proof of cross-site scripting (XSS). An XSS finding requires evidence that untrusted content executes in a security context where it can affect a web application's origin, users, or data. Results should therefore identify the tested application, viewer, configuration, trust boundary, and demonstrated impact rather than treating all PDF JavaScript behavior as equivalent.

## Scope and safety properties

The generator intentionally produces a harmless demonstration payload. In `alert` mode, the document contains an `/OpenAction` JavaScript action whose only behavior is to display an informational alert in viewers that support PDF JavaScript. In `static` mode, the document contains no JavaScript action.

The project does **not** implement credential harvesting, hidden credential fields, remote form submission, webhooks, or exfiltration. Use synthetic documents and test accounts when assessing an upload or preview workflow. Testing should be performed only on systems for which explicit authorization has been obtained.

## Requirements

- Python 3.10 or later
- No third-party Python packages
- A PDF viewer for manual observation; viewer support for PDF JavaScript varies by product, version, and configuration

## Quick start

Generate a benign JavaScript demonstration PDF:

```bash
python3 gen_pdf.py --output artifacts/pdf-js-demo.pdf
```

Generate a static control PDF without JavaScript:

```bash
python3 gen_pdf.py --mode static --output artifacts/pdf-static-control.pdf
```

Customize the visible title and message:

```bash
python3 gen_pdf.py \
  --title "PDF Viewer Test" \
  --message "Controlled test: observe viewer behavior." \
  --output artifacts/viewer-test.pdf
```

The generator does not silently overwrite an existing file. To replace one explicitly, add `--force`:

```bash
python3 gen_pdf.py --output artifacts/pdf-js-demo.pdf --force
```

Use `python3 gen_pdf.py --help` to inspect all command-line options.

## Included examples

The [`examples/`](examples/) directory contains two generated files for a quick comparison:

- [`pdf-js-demo.pdf`](examples/pdf-js-demo.pdf) — contains only a benign informational alert action.
- [`pdf-static-control.pdf`](examples/pdf-static-control.pdf) — static control document with no JavaScript action.

Viewer behavior is not guaranteed: some products disable PDF JavaScript or do not support it.

## Experimental procedure

For a small and reproducible comparison:

1. Record the operating system, PDF viewer name and version, and relevant viewer security settings.
2. Open the `alert` artifact and record whether the viewer displays the alert, blocks the action, or ignores it.
3. Open the `static` control artifact in the same viewer and record the control result.
4. Repeat only in authorized, isolated test environments, keeping the viewer version and configuration consistent where possible.
5. Report observed behavior separately from conclusions about an application-level XSS vulnerability.

A useful results table includes: viewer and version, JavaScript settings, artifact mode, observed behavior, security prompt or warning, and notes on reproducibility. The repository does not claim that any particular viewer is vulnerable; results must be measured in the environment under study.

## Generator interface

| Option | Description |
|---|---|
| `-o`, `--output` | Destination PDF path; defaults to `pdf-js-demo.pdf` |
| `--title` | Short document heading; maximum 48 characters |
| `--message` | Demonstration text; maximum 350 characters |
| `--mode alert` | Adds a benign PDF JavaScript alert action (default) |
| `--mode static` | Omits the JavaScript action |
| `--force` | Allows replacement of an existing output file |

The script builds a minimal PDF structure directly so the project can be run without installing a PDF-generation library. This implementation is a test-artifact generator, not a general-purpose PDF authoring framework.

## Validation

Run the unit tests with Python's built-in test runner:

```bash
python3 -m unittest discover -s tests -v
```

The tests check basic PDF structure, the presence or absence of the expected JavaScript action, and the absence of form-submission and external-URI actions in generated output. Manual testing in target viewers is still required; a structurally valid file does not establish that every viewer will render or execute it identically.

## Defensive recommendations

For applications that accept or preview PDFs:

- Avoid rendering untrusted active content in a privileged application origin.
- Isolate document previews from authenticated application pages and sensitive browser state.
- Use maintained PDF-processing components and review the security configuration of the deployed viewer.
- Consider content disarm and reconstruction (CDR) or conversion to a safe preview format when active content is unnecessary.
- Apply authorization checks to uploaded files and ensure preview endpoints do not expose other users' documents.
- Treat external links, embedded files, actions, and JavaScript as separate review items during PDF handling.

These are general defensive considerations; the correct control set depends on the application's architecture and threat model.

## Limitations

- PDF JavaScript support varies substantially among viewers and may be disabled by default.
- The alert demonstration does not prove exploitability in a browser-based PDF preview or an upload pipeline.
- This minimal generator does not aim to cover the full PDF specification, accessibility, digital signatures, encryption, or production document workflows.
- Experimental conclusions require recorded versions, settings, and repeatable observations.

## Responsible use

Use this material for authorized testing, controlled experimentation, and education. Do not use it to solicit, collect, or transmit other people's credentials, or to test systems without permission. Findings from a real engagement should be disclosed through the applicable coordinated vulnerability disclosure process.

## License

Unless otherwise stated in the repository, source code is provided under the MIT License. Check all existing repository assets and inherited third-party material before assigning or changing a license for the complete repository.

## References

1. Adobe, *Acrobat JavaScript API Reference*. [Documentation](https://opensource.adobe.com/dc-acrobat-sdk-docs/library/jsapiref/index.html).
2. OWASP Foundation, *File Upload Cheat Sheet*. [Guidance](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html).
3. OWASP Foundation, *Cross Site Scripting Prevention Cheat Sheet*. [Guidance](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html).

These sources provide background for PDF-viewer behavior, secure file-upload design, and the distinction between active document content and an application-level XSS finding.
