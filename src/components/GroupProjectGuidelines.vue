<script setup lang="ts">
import { courseHref } from '../navigation'
</script>

<template>
  <article class="course-index project-guidelines">
    <header>
      <span class="eyebrow">GROUP PROJECT / FALL 2026</span>
      <h1>Submission Guidelines &amp; Deadlines</h1>
      <p>The project is worth <strong>40% of your final course grade</strong>.</p>
    </header>

    <section aria-labelledby="project-groups">
      <h2 id="project-groups">Groups and naming</h2>
      <ul>
        <li>
          Form a group of <strong>4–5 students</strong>. Use your assigned Moodle project group
          number; do not choose another number.
        </li>
        <li>
          Use <strong>one Kaggle team per group</strong>, with the same name as your Moodle group:
          <code>group_XX</code> (for example, <code>group_02</code>). Use lowercase letters, an
          underscore and a two-digit number, with no spaces or extra suffixes. Use this name for
          <code>GroupID</code> in the filenames below.
        </li>
        <li>
          Each member uses their own Kaggle account. One member submits the Moodle deliverables on
          behalf of the whole group.
        </li>
      </ul>
    </section>

    <section aria-labelledby="project-grading">
      <h2 id="project-grading">Project grading</h2>
      <table aria-label="Project grading weights">
        <thead>
          <tr>
            <th scope="col">Component</th>
            <th scope="col">Weight</th>
            <th scope="col">Assessed on</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <th scope="row">Proposal</th>
            <td>10%</td>
            <td>Soundness of the plan and preliminary validation baseline.</td>
          </tr>
          <tr>
            <th scope="row">Performance</th>
            <td>30%</td>
            <td>
              Both public and private leaderboard performance, supported by reproducible code.
            </td>
          </tr>
          <tr>
            <th scope="row">Written report</th>
            <td>35%</td>
            <td>Methodology, experimental analysis and clarity of writing.</td>
          </tr>
          <tr>
            <th scope="row">Oral presentation</th>
            <td>25%</td>
            <td>Clarity, structure and effectiveness of the presentation.</td>
          </tr>
        </tbody>
      </table>
      <p class="table-note">Weights are within the project, not the overall course grade.</p>
    </section>

    <section aria-labelledby="project-proposal">
      <h2 id="project-proposal">Proposal</h2>
      <p class="deadline">
        <time datetime="2026-11-12T23:59:00+08:00">12 November 2026, 23:59 HKT (UTC+8)</time>
      </p>
      <p>
        Upload <strong>one PDF directly to the Moodle proposal submission</strong>, named
        <code>GroupID.pdf</code> (for example, <code>group_02.pdf</code>). Include your group ID and
        members, proposed methods, validation strategy,
        <strong>preliminary baseline results on your validation set</strong>, and work plan.
      </p>
    </section>

    <section aria-labelledby="project-final">
      <h2 id="project-final">Final submission</h2>
      <p class="deadline">
        <time datetime="2026-12-06T23:59:00+08:00">6 December 2026, 23:59 HKT (UTC+8)</time>
      </p>
      <table aria-label="Final submission files">
        <thead>
          <tr>
            <th scope="col">Deliverable</th>
            <th scope="col">Where / filename</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <th scope="row">Final report (PDF)</th>
            <td>Moodle: <code>GroupID.pdf</code>, uploaded separately, not inside the ZIP.</td>
          </tr>
          <tr>
            <th scope="row">Supporting files (one ZIP)</th>
            <td>Moodle: <code>GroupID.zip</code>, with the contents listed below.</td>
          </tr>
          <tr>
            <th scope="row">Final predictions</th>
            <td>Kaggle: submit and select your final entries before the deadline.</td>
          </tr>
        </tbody>
      </table>
      <p><strong>ZIP contents:</strong></p>
      <ul>
        <li>Presentation slides (PDF).</li>
        <li>Presentation video: <strong>strictly no longer than 8 minutes</strong>.</li>
        <li>Code: Jupyter notebooks, a Python project or another runnable format.</li>
        <li>
          <code>README.md</code>: environment/dependencies, data locations, and instructions to
          reproduce your results and final predictions.
        </li>
      </ul>
    </section>

    <section aria-labelledby="project-templates">
      <h2 id="project-templates">Report templates</h2>
      <p>
        Use either template below. Keep its font size, margins and section headings, and export your
        report as a PDF.
      </p>
      <p>
        At the start of the report, include every member's
        <strong
          >full name, university ID, HKU email, contribution percentage and work contributed</strong
        >. The percentages must total <strong>exactly 100%</strong>.
      </p>
      <div class="template-downloads">
        <a class="button" :href="courseHref('group-project/report-template.tex')" download
          >LaTeX template (.tex)</a
        >
        <a class="button" :href="courseHref('group-project/report-template.docx')" download
          >Word template (.docx)</a
        >
      </div>
      <table aria-label="Final report structure">
        <thead>
          <tr>
            <th scope="col">Section</th>
            <th scope="col">Include</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <th scope="row">1. Introduction</th>
            <td>Motivation, objectives and main contributions.</td>
          </tr>
          <tr>
            <th scope="row">2. Related Work</th>
            <td>Relevant studies and approaches, with citations.</td>
          </tr>
          <tr>
            <th scope="row">3. Methodology</th>
            <td>Overall pipeline figure; Problem Formulation; Method Design.</td>
          </tr>
          <tr>
            <th scope="row">4. Experimental Setups</th>
            <td>
              Datasets, Tasks, and Evaluation; Baseline Methods; Implementation Details (model
              hyperparameters, tuning, random seeds, hardware and software configuration).
            </td>
          </tr>
          <tr>
            <th scope="row">5. Experimental Results and Analysis</th>
            <td>Quantitative comparisons, model behaviour, error analysis and ablations.</td>
          </tr>
          <tr>
            <th scope="row">6. Discussion</th>
            <td>Implications, limitations and potential improvements.</td>
          </tr>
          <tr>
            <th scope="row">7. Conclusion</th>
            <td>Main findings and takeaways.</td>
          </tr>
          <tr>
            <th scope="row">References; Appendix (optional)</th>
            <td>Cited sources; supplementary results or details, if needed.</td>
          </tr>
        </tbody>
      </table>
    </section>

    <section aria-labelledby="project-rules">
      <h2 id="project-rules">Data and academic integrity</h2>
      <ul>
        <li>
          Use only the data supplied through the course competition. No external datasets, labels or
          pretrained model weights; software libraries are allowed.
        </li>
        <li>
          Develop and tune models using your own validation split from the training data. Do not
          attempt to recover test labels by probing the leaderboard.
        </li>
        <li>
          Do not share solutions or prediction files across groups. Keep course data within the
          course and Kaggle notebooks containing it private. Cite any reused code or ideas.
        </li>
      </ul>
    </section>

    <section aria-labelledby="project-faq">
      <h2 id="project-faq">Frequently asked questions</h2>
      <dl>
        <dt>Can we use deep neural networks?</dt>
        <dd>Yes. Compare them with simpler baselines and justify your design choices.</dd>
        <dt>Do we need a GPU?</dt>
        <dd>
          Not necessarily; it depends on your model. Google Colab is an option if GPU resources are
          needed, subject to availability.
        </dd>
      </dl>
    </section>
  </article>
</template>

<style scoped>
.project-guidelines {
  max-width: 1000px;
  overflow-wrap: anywhere;
}
.project-guidelines h1 {
  margin: 12px 0 24px;
}
.project-guidelines section {
  margin-top: 32px;
  padding-top: 8px;
  border-top: 1px solid var(--line);
}
.project-guidelines h2 {
  font-size: 1.4rem;
  margin: 20px 0 12px;
}
.project-guidelines p,
.project-guidelines li {
  font-size: 0.95rem;
}
.project-guidelines li {
  margin: 8px 0;
}
.project-guidelines ul {
  padding-left: 24px;
}
.deadline {
  color: var(--accent);
  font-weight: 650;
}
.project-guidelines th,
.project-guidelines td {
  font-size: 0.9rem;
}
.project-guidelines tbody th {
  color: var(--ink);
  border-color: var(--line);
  font-weight: 500;
}
.project-guidelines [aria-label='Project grading weights'] :is(th, td):nth-child(2) {
  white-space: nowrap;
}
.project-guidelines th,
.project-guidelines td {
  vertical-align: top;
}
.project-guidelines th:first-child {
  width: 31%;
}
.table-note {
  color: var(--muted);
}
.project-guidelines dt {
  margin-top: 16px;
  font-weight: 650;
}
.project-guidelines dd {
  margin: 6px 0 0;
}
.project-guidelines code {
  font-size: 0.88em;
  background: var(--soft);
  border-radius: 3px;
  padding: 2px 5px;
}
.template-downloads {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin: 20px 0;
}
</style>
