#!/usr/bin/env python3
"""Build matching LaTeX and Word report templates using only the standard library."""
from html import escape
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / 'public/group-project'
SECTIONS = (
    ('Introduction', 'Introduce the motivation, project objectives and main contributions.', ()),
    ('Related Work', 'Discuss relevant studies and approaches, with citations.', ()),
    ('Methodology', 'Present your overall pipeline and explain your approach.', (
        ('Problem Formulation', 'Define the inputs, prediction target, notation and learning objective.'),
        ('Method Design', 'Describe preprocessing, feature engineering and your model or algorithm design.'),
    )),
    ('Experimental Setups', 'Describe the experimental protocol used for all comparisons.', (
        ('Datasets, Tasks, and Evaluation',
         'Describe the supplied datasets, prediction task, validation splits, leakage prevention and evaluation metrics.'),
        ('Baseline Methods', 'Describe the reference methods and how you compare them fairly.'),
        ('Implementation Details',
         'Report model hyperparameters, tuning procedure, random seeds, hardware and software configuration.'),
    )),
    ('Experimental Results and Analysis',
     'Present quantitative comparisons and analyse model behaviour, errors and ablations with tables or figures.', ()),
    ('Discussion', 'Discuss the implications, limitations and potential improvements.', ()),
    ('Conclusion', 'Summarise the main findings and takeaways.', ()),
)
BACK_MATTER = (
    ('References', 'List the sources, software and other work cited in the report.'),
    ('Appendix (Optional)', 'Include supplementary results or details, if needed; otherwise remove this section.'),
)
CITATION_EXAMPLE = (
    'Cite sources as [1], [2], etc., numbered in order of first citation. '
    'Replace these example citations and reference entries with your own.'
)
REFERENCES = (
    '[1] Trevor Hastie, Robert Tibshirani, and Jerome Friedman. '
    'The Elements of Statistical Learning: Data Mining, Inference, and Prediction. '
    'Springer, 2nd edition, 2009.',
    '[2] Christopher M. Bishop. Pattern Recognition and Machine Learning. Springer, 2006.',
)
BIBTEX = '''@book{hastie2009,
  author = {Trevor Hastie and Robert Tibshirani and Jerome Friedman},
  title = {The Elements of Statistical Learning: Data Mining, Inference, and Prediction},
  publisher = {Springer},
  edition = {2nd},
  year = {2009}
}
@book{bishop2006,
  author = {Christopher M. Bishop},
  title = {Pattern Recognition and Machine Learning},
  publisher = {Springer},
  year = {2006}
}
'''
PIPELINE_PROMPT = 'Show the flow from data and preprocessing to modelling and predictions.'
PIPELINE_CAPTION = 'Overall pipeline (replace the placeholder with your figure).'
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

    sections = []
    for title, prompt, subsections in SECTIONS:
        sections.append(f'\n\\section{{{title}}}\n{prompt}\n')
        if title == 'Related Work':
            sections.append('\n' + CITATION_EXAMPLE.replace('[1]', r'\cite{hastie2009}').replace(
                '[2]', r'\cite{bishop2006}'
            ) + '\n')
        if title == 'Methodology':
            sections.append(r'''
\begin{figure}[!ht]
\centering
\fbox{\parbox[c][30mm][c]{0.9\linewidth}{\centering
\textbf{Overall pipeline figure}\\[6pt]
''' + PIPELINE_PROMPT + r'''}}
\caption{''' + PIPELINE_CAPTION + r'''}
\label{fig:pipeline}
\end{figure}
''')
        for subtitle, description in subsections:
            sections.append(f'\n\\subsection{{{subtitle}}}\n{description}\n')
    for title, prompt in BACK_MATTER:
        if title == 'References':
            sections.append('\n\\bibliographystyle{unsrt}\n\\bibliography{references}\n')
        else:
            sections.append(f'\n\\section*{{{title}}}\n{prompt}\n')

    return r'''% Recommended editor: https://www.overleaf.com/ (upload this .tex file).
% Edit the sample BibTeX entries below; this block rewrites references.bib.
% Overleaf runs BibTeX automatically when you recompile.
\begin{filecontents*}[overwrite]{references.bib}
''' + BIBTEX + r'''\end{filecontents*}
\documentclass[11pt,a4paper]{article}
\usepackage[margin=25mm]{geometry}
\usepackage{mathptmx,array,tabularx,titlesec,url}
\usepackage[hidelinks]{hyperref}
\urlstyle{same}
\setlength{\parindent}{0pt}
\setlength{\parskip}{6pt}
\titleformat{\section}{\large\bfseries}{\thesection.}{0.5em}{}
\titlespacing*{\section}{0pt}{12pt}{6pt}
\titleformat{\subsection}{\normalsize\bfseries}{\thesubsection}{0.5em}{}
\titlespacing*{\subsection}{0pt}{10pt}{4pt}
\begin{document}
{\fontsize{16}{19}\selectfont\bfseries [Project Title]}\par
STAT / SDST 3612 -- Fall 2026\par
\textbf{Group ID:} [Group ID]\par
\textbf{Presentation video:} \url{[YouTube-Unlisted-URL]}

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
''' + ''.join(sections) + '\n\\end{document}\n'


def paragraph(text, style=None):
    keep = '<w:keepNext/><w:keepLines/>' if style in ('Title', 'Heading1', 'Heading2') else ''
    properties = f'<w:pPr><w:pStyle w:val="{style}"/>{keep}</w:pPr>' if style else ''
    return f'<w:p>{properties}<w:r><w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>'


def document():
    body = [paragraph('[Project Title]', 'Title'),
            paragraph('STAT / SDST 3612 - Fall 2026'), paragraph('Group ID: [Group ID]'),
            paragraph('Presentation video: [YouTube Unlisted URL]'),
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
    for index, (title, prompt, subsections) in enumerate(SECTIONS, start=1):
        body.extend([paragraph(f'{index}. {title}', 'Heading1'), paragraph(prompt)])
        if title == 'Related Work':
            body.append(paragraph(CITATION_EXAMPLE))
        if title == 'Methodology':
            body.append('<w:tbl><w:tblPr><w:tblW w:w="9072" w:type="dxa"/>'
                        '<w:tblBorders>' + ''.join(
                            f'<w:{edge} w:val="single" w:sz="4" w:color="000000"/>'
                            for edge in ('top', 'left', 'bottom', 'right')
                        ) + '</w:tblBorders></w:tblPr><w:tblGrid><w:gridCol w:w="9072"/>'
                        '</w:tblGrid><w:tr><w:trPr><w:cantSplit/><w:trHeight w:val="1701" '
                        'w:hRule="atLeast"/></w:trPr><w:tc><w:tcPr><w:tcW w:w="9072" '
                        'w:type="dxa"/><w:vAlign w:val="center"/></w:tcPr>' +
                        paragraph('Overall pipeline figure', 'FigurePlaceholder') +
                        paragraph(PIPELINE_PROMPT, 'FigurePlaceholder') + '</w:tc></w:tr></w:tbl>')
            body.append(paragraph(f'Figure 1. {PIPELINE_CAPTION}', 'Caption'))
        for subindex, (subtitle, description) in enumerate(subsections, start=1):
            body.extend([paragraph(f'{index}.{subindex} {subtitle}', 'Heading2'), paragraph(description)])
    for title, prompt in BACK_MATTER:
        body.extend([paragraph(title, 'Heading1'), paragraph(prompt)])
        if title == 'References':
            body.extend(paragraph(reference) for reference in REFERENCES)
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
<w:pPr><w:keepNext/><w:spacing w:before="240" w:after="120" w:line="288" w:lineRule="exact"/><w:outlineLvl w:val="0"/></w:pPr>
<w:rPr><w:b/><w:sz w:val="24"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/>
<w:pPr><w:keepNext/><w:spacing w:before="200" w:after="80"/><w:outlineLvl w:val="1"/></w:pPr>
<w:rPr><w:b/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="FigurePlaceholder"><w:name w:val="Figure Placeholder"/><w:basedOn w:val="Normal"/>
<w:pPr><w:jc w:val="center"/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="Caption"><w:name w:val="caption"/><w:basedOn w:val="Normal"/>
<w:pPr><w:jc w:val="center"/></w:pPr></w:style>
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
