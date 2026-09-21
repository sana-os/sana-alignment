"""Source-preserving extraction candidates, not semantic classifications."""
import math
import re
from .models import MAX_EXTRACTION_REFERENCES


def source_spans(text):
    """Keep fenced code whole; offer prose lines and simple sentence boundaries.

    Boundaries only control selectable excerpts. The complete source is still
    available, and no punctuation, markup, Unicode or internal space is changed.
    """
    spans = []
    offset = 0
    fence = None
    fence_start = 0
    for line in text.splitlines(keepends=True):
        marker = re.match(r'^\s*(`{3,}|~{3,})', line)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence):
                spans.append((fence_start, offset + len(line)))
                fence = None
        elif marker:
            fence = marker[1]
            fence_start = offset
        else:
            # Do not split inside inline code or Markdown labels/lists. A whole
            # line remains selectable when sentence boundaries are uncertain.
            cuts = [0]
            if not re.search(r'[`*]|^\s*(?:[-+#>]|\d+[.)])', line):
                cuts += [m.end() for m in re.finditer(r'(?<=[。！？])|(?<=[.!?])\s+(?=[A-Z])', line)]
            cuts.append(len(line))
            spans.extend((offset + a, offset + b) for a, b in zip(cuts, cuts[1:]) if line[a:b].strip())
        offset += len(line)
    if fence:
        spans.append((fence_start, len(text)))
    return spans


def extraction_index(payload):
    sources = {'input_message': payload['input_message']}
    if payload.get('ai_interpretation') is not None:
        sources['ai_interpretation'] = payload['ai_interpretation']
    sources.update({f'context.{i}': c['text'] for i, c in enumerate(payload.get('context', []))})
    registry = {}
    # Coarsen contiguous candidates instead of dropping text on large inputs.
    allowance = max(1, MAX_EXTRACTION_REFERENCES // len(sources) - 1)
    for source, text in sources.items():
        spans = source_spans(text)
        step = max(1, math.ceil(len(spans) / allowance))
        quotes = [text]
        for i in range(0, len(spans), step):
            group = spans[i:i + step]
            quotes.append(text[group[0][0]:group[-1][1]].strip())
        # Keep original lines AND offer semicolon-separated clauses. No semantic
        # label follows from punctuation; the parent remains available for scope.
        # Do not split code/inline-code or coarsened multi-line candidates.
        expanded = list(quotes)
        for quote in quotes[1:]:
            if '\n' not in quote and '`' not in quote and re.search('[;；]', quote):
                expanded.extend(part.strip() for part in re.split(r'(?<=[;；])', quote) if part.strip())
        if len(dict.fromkeys(expanded)) <= allowance + 1:
            quotes = expanded
        for quote in dict.fromkeys(quotes):
            if quote.strip():
                registry[f'x{len(registry)}'] = {'source': source, 'quote': quote}
    return registry


def excerpt_context(payload, registry):
    """Attach literal Markdown heading paths without changing selectable quotes.

    Headings are untrusted source context, not semantic labels. Repeated quotes
    retain every matching context; code-fence contents cannot create headings.
    """
    sources = {'input_message': payload['input_message']}
    if payload.get('ai_interpretation') is not None:
        sources['ai_interpretation'] = payload['ai_interpretation']
    sources.update({f'context.{i}': c['text'] for i, c in enumerate(payload.get('context', []))})
    outlines = {}
    for source, text in sources.items():
        outline, stack, offset, fence = [(0, ())], [], 0, None
        for line in text.splitlines(keepends=True):
            marker = re.match(r'^\s*(`{3,}|~{3,})', line)
            if fence:
                if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence):
                    fence = None
            elif marker:
                fence = marker[1]
            else:
                heading = re.match(r'^ {0,3}(#{1,6})\s+\S', line)
                if heading:
                    level = len(heading[1])
                    stack = [(n, h) for n, h in stack if n < level]
                    stack.append((level, line.strip()))
                    outline.append((offset, tuple(h for _, h in stack)))
            offset += len(line)
        outlines[source] = outline
    result = {}
    for ref, item in registry.items():
        text, quote = sources[item['source']], item['quote']
        # The entire source already carries all of its context.
        if quote == text:
            continue
        paths, parents, start = [], [], text.find(quote)
        outline = outlines[item['source']]
        while start >= 0:
            end = start + len(quote)
            if '\n' not in quote:
                line = text[text.rfind('\n', 0, start) + 1:text.find('\n', end) if '\n' in text[end:] else len(text)].strip()
                if line != quote and line not in parents:
                    parents.append(line)
            for i, (pos, path) in enumerate(outline):
                next_pos = outline[i + 1][0] if i + 1 < len(outline) else len(text)
                if pos < end and next_pos > start and path not in paths:
                    paths.append(path)
            start = text.find(quote, start + max(1, len(quote)))
        if any(paths) or parents:
            result[ref] = {'heading_paths': [list(path) for path in paths]}
            if parents:
                result[ref]['enclosing_lines'] = parents
    return result


def resolve_extraction(value, registry):
    from .provider import ProviderError
    if not isinstance(value, dict) or not isinstance(value.get('evidence'), list):
        raise ProviderError('provider_invalid_extraction_reference')
    if len(value['evidence']) > MAX_EXTRACTION_REFERENCES:
        # Bound expansion before copying source quotes; never truncate evidence.
        raise ProviderError('provider_excessive_extraction', issue={
            'path': 'evidence', 'rule': 'extraction_reference_budget',
            'max_items': MAX_EXTRACTION_REFERENCES, 'actual_items': len(value['evidence'])})
    resolved = []
    for i, entry in enumerate(value['evidence']):
        if (not isinstance(entry, dict) or set(entry) != {'ref', 'function'}
                or not isinstance(entry['ref'], str) or entry['ref'] not in registry):
            raise ProviderError('provider_invalid_extraction_reference', issue={
                'path': f'evidence.{i}', 'rule': 'select_supplied_extraction_reference'})
        resolved.append({**registry[entry['ref']], 'function': entry['function']})
    return {**value, 'evidence': resolved}
