"""Render the shared teaching flows as standalone SVGs for Jupyter outputs."""
from html import escape
import re
import textwrap


def flow_svg(flow, values=None):
    """Use actual audit values; keep diagram text selectable and code monospaced."""
    def resolve(text):
        def replace(match):
            value = values
            for key in match[1].split('.'):
                value = value[key]
            return f'{value:,}' if isinstance(value, int) else str(value)
        return re.sub(r'\{([\w.]+)\}', replace, text)

    def lines(text, width):
        # Inline code delimiters are represented by the node's code field in SVG.
        text = resolve(text).replace('`', '')
        return [line for paragraph in text.splitlines()
                for line in textwrap.wrap(paragraph, width=width, break_long_words=True,
                                          replace_whitespace=False)] if text else []

    width, gap, margin = 1000, 34, 18
    horizontal = flow['layout'] == 'horizontal'
    stage_width = ((width - 2 * margin - gap * (len(flow['stages']) - 1)) /
                   len(flow['stages'])) if horizontal else width - 2 * margin
    # Lay out every node before drawing so wrapped text never overlaps.
    stages = []
    for stage in flow['stages']:
        node_width = (stage_width - 14 * (len(stage['nodes']) - 1)) / len(stage['nodes'])
        nodes = []
        for node in stage['nodes']:
            groups = [(lines(node['label'], max(12, int((node_width - 28) / 9))), 'label'),
                      (lines(node['code'], max(12, int((node_width - 28) / 8))), 'code'),
                      (lines(node['text'], max(12, int((node_width - 28) / 8))), 'body')]
            height = 24 + sum(len(rows) * 22 + (8 if rows else 0) for rows, _ in groups)
            nodes.append((node_width, height, groups))
        stages.append((stage, nodes, max(n[1] for n in nodes) + 28))

    caption = lines(flow['caption'], 110)
    diagram_height = (max(s[2] for s in stages) if horizontal else
                      sum(s[2] for s in stages) + gap * (len(stages) - 1))
    height = 72 + diagram_height + (24 + 22 * len(caption) if caption else 0)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
             f'role="img" class="t5-notebook-flow" aria-label="{escape(flow["title"])}" style="max-width:100%;height:auto">',
             f'<title>{escape(flow["title"])}</title>',
             '<rect width="100%" height="100%" fill="white"/>',
             '<style>.t5-notebook-flow text{font-family:Arial,sans-serif;fill:#283e4c;font-size:16px}'
             '.t5-notebook-flow .label{font-weight:600}.t5-notebook-flow .code{font-family:Consolas,monospace;font-size:14px}'
             '.t5-notebook-flow .stage{font-size:14px;fill:#45657e}.t5-notebook-flow .caption{font-size:15px;fill:#526570}</style>',
             f'<text x="18" y="28" class="label">{escape(flow["title"])}</text>']
    x, y = margin, 54
    for index, (stage, nodes, stage_height) in enumerate(stages):
        parts.append(f'<text x="{x}" y="{y}" class="stage">{escape(stage["title"])}</text>')
        nx = x
        for node_width, node_height, groups in nodes:
            parts.append(f'<rect x="{nx}" y="{y + 12}" width="{node_width}" height="{node_height}" '
                         'rx="5" fill="#f3f6f8" stroke="#d9e2e9"/>')
            ty = y + 36
            for rows, kind in groups:
                for row in rows:
                    parts.append(f'<text x="{nx + 14}" y="{ty}" class="{kind}">{escape(row)}</text>')
                    ty += 22
                if rows:
                    ty += 8
            nx += node_width + 14
        if index < len(stages) - 1:
            if horizontal:
                parts.append(f'<text x="{x + stage_width + 8}" y="{y + 58}">→</text>')
            else:
                parts.append(f'<text x="{width / 2}" y="{y + stage_height + 20}">↓</text>')
        if horizontal:
            x += stage_width + gap
        else:
            y += stage_height + gap
    for i, row in enumerate(caption):
        parts.append(f'<text x="18" y="{72 + diagram_height + i * 22}" class="caption">{escape(row)}</text>')
    return ''.join(parts) + '</svg>'


def draw_flow(flow, values=None):
    from IPython.display import SVG, display
    display(SVG(flow_svg(flow, values)))
