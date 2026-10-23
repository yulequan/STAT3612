<script setup lang="ts">
import { courseHref } from '../navigation'
</script>

<template>
  <article class="course-index project-guidelines">
    <header>
      <span class="eyebrow">GROUP PROJECT / FALL 2026</span>
      <h1>Submission Guidelines &amp; Deadlines</h1>
      <p>
        Groups of <strong>4–5 students</strong>. The project is worth
        <strong>40% of your final course grade</strong>. Submit once per group.
      </p>
    </header>

    <section aria-labelledby="project-grading">
      <h2 id="project-grading">Project grading</h2>
      <table aria-label="Project grading weights">
        <thead>
          <tr>
            <th scope="col">Component</th>
            <th scope="col">Weight</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <th scope="row">Proposal</th>
            <td>10%</td>
          </tr>
          <tr>
            <th scope="row">Performance (public and private leaderboards)</th>
            <td>30%</td>
          </tr>
          <tr>
            <th scope="row">Written report</th>
            <td>35%</td>
          </tr>
          <tr>
            <th scope="row">Oral presentation</th>
            <td>25%</td>
          </tr>
        </tbody>
      </table>
    </section>

    <section aria-labelledby="project-proposal">
      <h2 id="project-proposal">Proposal</h2>
      <p class="deadline">
        <time datetime="2026-11-12T23:59:00+08:00">12 November 2026, 23:59 HKT (UTC+8)</time>
      </p>
      <p>
        Upload a single PDF to Moodle, named <code>GroupID.pdf</code> (for example,
        <code>group_02.pdf</code>). Include your group ID and members, proposed methods, validation
        strategy, <strong>preliminary baseline results on your validation set</strong>, and work
        plan.
      </p>
    </section>

    <section aria-labelledby="project-final">
      <h2 id="project-final">Final submission</h2>
      <p class="deadline">
        <time datetime="2026-12-06T23:59:00+08:00">6 December 2026, 23:59 HKT (UTC+8)</time>
      </p>
      <p>
        Submit your final predictions on Kaggle. Upload <strong>one ZIP</strong> to Moodle, named
        <code>GroupID.zip</code>, containing:
      </p>
      <ul>
        <li>Final report (PDF).</li>
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
.project-guidelines th:last-child,
.project-guidelines td:last-child {
  width: 80px;
  white-space: nowrap;
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
  margin: 20px 0 48px;
}
</style>
