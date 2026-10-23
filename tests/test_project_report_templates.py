"""Validate the public report templates without office/TeX dependencies in CI."""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('report_templates', ROOT / 'scripts/build_report_templates.py')
templates = importlib.util.module_from_spec(spec)
spec.loader.exec_module(templates)
NS = {'w': templates.W}
EXPECTED_SECTIONS = (
    'Introduction', 'Related Work', 'Methodology', 'Experimental Setups',
    'Experimental Results and Analysis', 'Discussion', 'Conclusion',
)
EXPECTED_SUBSECTIONS = (
    '3.1 Problem Formulation', '3.2 Method Design',
    '4.1 Datasets, Tasks, and Evaluation', '4.2 Baseline Methods', '4.3 Implementation Details',
)


class ReportTemplateTests(unittest.TestCase):
    def test_downloads_match_reproducible_generator(self):
        with TemporaryDirectory() as temporary:
            templates.build(Path(temporary))
            for name in ('report-template.tex', 'report-template.docx'):
                self.assertEqual((templates.DESTINATION / name).read_bytes(),
                                 (Path(temporary) / name).read_bytes())

    def test_word_structure_contributions_and_matching_sections(self):
        with ZipFile(templates.DESTINATION / 'report-template.docx') as archive:
            for name in archive.namelist():
                ET.fromstring(archive.read(name))
            root = ET.fromstring(archive.read('word/document.xml'))
            styles = ET.fromstring(archive.read('word/styles.xml'))
        body = root.find('w:body', NS)
        elements = list(body)
        table_index = next(i for i, element in enumerate(elements) if element.tag == f'{{{templates.W}}}tbl')
        rows = elements[table_index].findall('w:tr', NS)

        def text(node):
            return ''.join(node.itertext())

        self.assertEqual([text(cell) for cell in rows[0].findall('w:tc', NS)], list(templates.HEADERS))
        shares = [int(text(row.findall('w:tc', NS)[3]).rstrip('%')) for row in rows[1:-1]]
        self.assertEqual(len(shares), 5)
        self.assertEqual(sum(shares), 100)
        self.assertEqual(text(rows[-1].findall('w:tc', NS)[3]), '100%')
        self.assertIn('Percentages must total exactly 100%.', text(root))
        self.assertIn('four-person group', text(root))

        headings = [text(element) for element in elements
                    if element.find('w:pPr/w:pStyle[@w:val="Heading1"]', NS) is not None]
        self.assertEqual(headings, ['Group Members and Contributions', *(
            f'{index}. {title}' for index, title in enumerate(EXPECTED_SECTIONS, start=1)
        ), 'References', 'Appendix (Optional)'])
        for index, title in enumerate(EXPECTED_SECTIONS, start=1):
            heading_index = next(i for i, element in enumerate(elements) if text(element) == f'{index}. {title}')
            self.assertGreater(heading_index, table_index)
        subheadings = [text(element) for element in elements
                       if element.find('w:pPr/w:pStyle[@w:val="Heading2"]', NS) is not None]
        self.assertEqual(subheadings, list(EXPECTED_SUBSECTIONS))
        self.assertEqual(styles.find('.//w:rFonts', NS).get(f'{{{templates.W}}}ascii'), 'Times New Roman')
        self.assertEqual(styles.find('.//w:sz', NS).get(f'{{{templates.W}}}val'), '22')
        self.assertEqual(root.find('.//w:pgSz', NS).get(f'{{{templates.W}}}w'), '11906')
        margins = root.find('.//w:pgMar', NS)
        for edge in ('top', 'bottom', 'left', 'right'):
            self.assertEqual(margins.get(f'{{{templates.W}}}{edge}'), '1417')

    def test_latex_layout_and_contribution_table_precede_report_sections(self):
        source = (templates.DESTINATION / 'report-template.tex').read_text()
        self.assertIn(r'\documentclass[11pt,a4paper]{article}', source)
        self.assertIn(r'\usepackage[margin=25mm]{geometry}', source)
        self.assertIn(r'Percentages must total exactly 100\%.', source)
        self.assertEqual(source.count(r'20\%'), 5)
        self.assertEqual(source.count(r'\url{[HKU-email]}'), 5)
        self.assertIn(r'\urlstyle{same}', source)
        end = source.index(r'\end{tabularx}')
        self.assertEqual([title for title, _, _ in templates.SECTIONS], list(EXPECTED_SECTIONS))
        for title in EXPECTED_SECTIONS:
            self.assertGreater(source.index(f'\\section{{{title}}}'), end)
        self.assertIn(r'\section*{References}', source)
        self.assertIn(r'\section*{Appendix (Optional)}', source)
        for heading in EXPECTED_SUBSECTIONS:
            self.assertIn('\\subsection{' + heading.split(' ', 1)[1] + '}', source)

    def test_pipeline_figure_precedes_problem_formulation_in_both_templates(self):
        source = (templates.DESTINATION / 'report-template.tex').read_text()
        self.assertLess(source.index(r'\section{Methodology}'), source.index(r'\begin{figure}'))
        self.assertLess(source.index(r'\end{figure}'), source.index(r'\subsection{Problem Formulation}'))
        self.assertIn(r'\label{fig:pipeline}', source)
        self.assertIn(templates.PIPELINE_CAPTION, source)
        with ZipFile(templates.DESTINATION / 'report-template.docx') as archive:
            root = ET.fromstring(archive.read('word/document.xml'))
        elements = list(root.find('w:body', NS))
        tables = root.findall('w:body/w:tbl', NS)
        self.assertEqual(len(tables), 2)
        pipeline = tables[1]
        self.assertIn('Overall pipeline figure', ''.join(pipeline.itertext()))
        self.assertIn(templates.PIPELINE_PROMPT, ''.join(pipeline.itertext()))
        self.assertEqual(pipeline.find('.//w:trHeight', NS).get(f'{{{templates.W}}}val'), '1701')
        texts = [''.join(element.itertext()) for element in elements]
        self.assertLess(texts.index('3. Methodology'), elements.index(pipeline))
        self.assertLess(elements.index(pipeline), texts.index('3.1 Problem Formulation'))
        self.assertIn(f'Figure 1. {templates.PIPELINE_CAPTION}', texts)
        for detail in ('hyperparameters', 'hardware', 'software configuration', 'random seeds'):
            self.assertIn(detail, source)
            self.assertIn(detail, ''.join(root.itertext()))


if __name__ == '__main__':
    unittest.main()
