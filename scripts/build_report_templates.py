#!/usr/bin/env python3
"""Build matching LaTeX and Word report templates using only the standard library."""
from html import escape
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / 'public/group-project'
SECTIONS = (
    ('Introduction', 'State the prediction problem and project objectives.'),
    ('Data and Preprocessing', 'Describe the data, preprocessing and feature engineering.'),
    ('Methods and Validation', 'Explain the baseline, candidate models, validation design and tuning.'),
    ('Results and Model Analysis', 'Compare results and analyse model behaviour with tables or figures.'),
    ('Discussion and Conclusion', 'Summarise findings, limitations and conclusions.'),
    ('References', 'List the sources, software and other work cited in the report.'),
)
HEADERS = ('Full name', 'University ID', 'HKU email', 'Share (%)', 'Work contributed')
MEMBERS = tuple((f'[Member {i}]', '[University ID]', '[HKU-email]', '20%', '[Work completed]')
                for i in range(1, 6))
CONTRIBUTION_NOTE = (
    'Replace the example entries with every member\'s full name, university ID, HKU email, '
    'contribution percentage and work contributed. Percentages must total exactly 100%. '
    'For a four-person group, remove one row and adjust the percentages.'
)
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'


def latex():
    def row(cells):
        values = [cell.replace('%', r'\%') for cell in cells]
        if cells in MEMBERS:
            values[2] = r'\url{' + values[2] + '}'
        return ' & '.join(values) + r' \\ \hline'

    return r'''\documentclass[11pt,a4paper]{article}
\usepackage[margin=25mm]{geometry}
\usepackage{mathptmx,array,tabularx,titlesec,url}
\urlstyle{same}
\setlength{\parindent}{0pt}
\setlength{\parskip}{6pt}
\titleformat{\section}{\large\bfseries}{\thesection.}{0.5em}{}
\titlespacing*{\section}{0pt}{12pt}{6pt}
\begin{document}
{\fontsize{16}{19}\selectfont\bfseries [Project Title]}\par
STAT / SDST 3612 -- Fall 2026\par
\textbf{Group ID:} [Group ID]

\section*{Group Members and Contributions}
''' + CONTRIBUTION_NOTE.replace('%', r'\%') + r'''

\begingroup
\fontsize{10}{12}\selectfont
\setlength{\tabcolsep}{4pt}
\renewcommand{\arraystretch}{1.35}
\begin{tabularx}{\textwidth}{|>{\raggedright\arraybackslash}p{23mm}|>{\raggedright\arraybackslash}p{22mm}|>{\raggedright\arraybackslash}p{32mm}|>{\centering\arraybackslash}p{13mm}|>{\raggedright\arraybackslash}X|}
\hline
''' + row(HEADERS) + '\n' + '\n'.join(row(member) for member in MEMBERS) + '\n' + row(
        ('Total', '', '', '100%', '')
    ) + r'''
\end{tabularx}
\endgroup
''' + ''.join(f'\n\\section{{{title}}}\n{prompt}\n' for title, prompt in SECTIONS) + '\n\\end{document}\n'


def paragraph(text, style=None):
    properties = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ''
    return f'<w:p>{properties}<w:r><w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>'


def document():
    body = [paragraph('[Project Title]', 'Title'),
            paragraph('STAT / SDST 3612 - Fall 2026'), paragraph('Group ID: [Group ID]'),
            paragraph('Group Members and Contributions', 'Heading1'), paragraph(CONTRIBUTION_NOTE)]
    widths = (1464, 1407, 1974, 897, 3330)
    rows = (HEADERS, *MEMBERS, ('Total', '', '', '100%', ''))
    table = ['<w:tbl><w:tblPr><w:tblW w:w="9072" w:type="dxa"/>'
             '<w:tblLayout w:type="fixed"/><w:tblCellMar>'
             '<w:left w:w="80" w:type="dxa"/><w:right w:w="80" w:type="dxa"/>'
             '</w:tblCellMar><w:tblBorders>' + ''.join(
                 f'<w:{edge} w:val="single" w:sz="4" w:color="000000"/>'
                 for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV')
             ) + '</w:tblBorders></w:tblPr><w:tblGrid>' + ''.join(
                 f'<w:gridCol w:w="{width}"/>' for width in widths
             ) + '</w:tblGrid>']
    for index, row in enumerate(rows):
        table.append('<w:tr><w:trPr><w:cantSplit/>' +
                     ('<w:tblHeader/>' if index == 0 else '') + '</w:trPr>')
        for width, text in zip(widths, row):
            table.append(f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/></w:tcPr>' +
                         paragraph(text, 'TableText') + '</w:tc>')
        table.append('</w:tr>')
    body.extend([''.join(table) + '</w:tbl>'])
    for index, (title, prompt) in enumerate(SECTIONS, start=1):
        body.extend([paragraph(f'{index}. {title}', 'Heading1'), paragraph(prompt)])
    body.append('<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
                '<w:pgMar w:top="1417" w:right="1417" w:bottom="1417" w:left="1417"/>'
                '</w:sectPr>')
    return f'<w:document xmlns:w="{W}"><w:body>{"".join(body)}</w:body></w:document>'


STYLES = f'''<w:styles xmlns:w="{W}">
<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>
<w:sz w:val="22"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr>
<w:spacing w:after="120" w:line="272" w:lineRule="exact"/>
</w:pPr></w:pPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>
<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/>
<w:pPr><w:keepNext/><w:spacing w:line="380" w:lineRule="exact"/></w:pPr>
<w:rPr><w:b/><w:sz w:val="32"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/>
<w:pPr><w:keepNext/><w:spacing w:before="240" w:after="240" w:line="288" w:lineRule="exact"/><w:outlineLvl w:val="0"/></w:pPr>
<w:rPr><w:b/><w:sz w:val="24"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="TableText"><w:name w:val="Table Text"/><w:basedOn w:val="Normal"/>
<w:pPr><w:spacing w:after="80" w:line="240" w:lineRule="exact"/></w:pPr>
<w:rPr><w:sz w:val="20"/></w:rPr></w:style>
</w:styles>'''


def build(destination=DESTINATION):
    destination.mkdir(parents=True, exist_ok=True)
    (destination / 'report-template.tex').write_text(latex(), encoding='utf-8')
    content_types = '''<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>'''
    rels = 'http://schemas.openxmlformats.org/package/2006/relationships'
    office = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
    parts = {
        '[Content_Types].xml': content_types,
        '_rels/.rels': f'<Relationships xmlns="{rels}"><Relationship Id="rId1" Type="{office}/officeDocument" Target="word/document.xml"/></Relationships>',
        'word/document.xml': document(),
        'word/styles.xml': STYLES,
        'word/_rels/document.xml.rels': f'<Relationships xmlns="{rels}"><Relationship Id="rId1" Type="{office}/styles" Target="styles.xml"/></Relationships>',
    }
    with ZipFile(destination / 'report-template.docx', 'w') as archive:
        for name, xml in parts.items():
            # Fixed metadata keeps the downloadable binary reproducible.
            info = ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' + xml)


if __name__ == '__main__':
    build()
