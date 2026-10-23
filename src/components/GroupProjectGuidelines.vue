<template>
  <article class="course-index project-guidelines">
    <header>
      <span class="eyebrow">GROUP PROJECT / FALL 2026</span>
      <h1>Submission Guidelines &amp; Deadlines</h1>
      <p class="project-intro">
        Work in groups of <strong>4–5 students</strong> to benchmark and develop statistical machine
        learning algorithms for a real-world prediction problem. The group project contributes
        <strong>40% of your final course grade</strong>.
      </p>
      <p>
        Build a convincing story through your proposal, performance and results, model analysis, and
        presentation. This year's task is predicting a short-term pause in learning-platform
        activity. All groups compete on the same task; there are no separate tracks. Refer to the
        project guideline PDF on Moodle and the competition's Data page for the task definition,
        permitted data and prediction format.
      </p>
    </header>

    <section aria-labelledby="project-deadlines">
      <h2 id="project-deadlines">1. Deadlines at a glance</h2>
      <p>All deadlines are at <strong>23:59 Hong Kong Time (HKT, UTC+8)</strong>.</p>
      <dl class="deadline-list">
        <div>
          <dt>Project proposal</dt>
          <dd>
            <time datetime="2026-11-12T23:59:00+08:00">Thursday, 12 November 2026, 23:59 HKT</time>
            <span>One PDF submitted on Moodle.</span>
          </dd>
        </div>
        <div>
          <dt>Final submission</dt>
          <dd>
            <time datetime="2026-12-06T23:59:00+08:00">Sunday, 6 December 2026, 23:59 HKT</time>
            <span>
              Kaggle predictions; final report, code, presentation slides and presentation video on
              Moodle.
            </span>
          </dd>
        </div>
      </dl>
      <p>
        Submit all deliverables <strong>as a group</strong>. The group leader or another member may
        submit on the group's behalf; do not submit duplicate copies for each member. Use your
        assigned Moodle group ID consistently.
      </p>
    </section>

    <section aria-labelledby="project-grading">
      <h2 id="project-grading">2. Grading criteria</h2>
      <p>
        The weights below apply within the group project. The last column shows the equivalent
        contribution to the overall course grade, out of 100.
      </p>
      <div class="table-scroll" role="region" aria-label="Project grading weights" tabindex="0">
        <table>
          <thead>
            <tr>
              <th scope="col">Component</th>
              <th scope="col">Project weight</th>
              <th scope="col">Course marks</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <th scope="row">Proposal</th>
              <td>10%</td>
              <td>4 / 100</td>
            </tr>
            <tr>
              <th scope="row">Performance</th>
              <td>30%</td>
              <td>12 / 100</td>
            </tr>
            <tr>
              <th scope="row">Written report</th>
              <td>35%</td>
              <td>14 / 100</td>
            </tr>
            <tr>
              <th scope="row">Oral presentation (video)</th>
              <td>25%</td>
              <td>10 / 100</td>
            </tr>
          </tbody>
        </table>
      </div>
      <ul>
        <li>
          <strong>Proposal:</strong> soundness and feasibility of the plan, including a preliminary
          baseline model's performance on your validation set.
        </li>
        <li>
          <strong>Performance:</strong> predictive quality of your final model, considering both
          public and private leaderboard performance and verified by running your code.
        </li>
        <li>
          <strong>Written report:</strong> methodology, depth of analysis, model comparisons,
          interpretation, and clarity. Discuss issues such as class imbalance, probability
          calibration, leakage and limitations where relevant.
        </li>
        <li>
          <strong>Oral presentation:</strong> clarity, structure, effective communication of
          results, and the quality of your story-telling within the time limit.
        </li>
      </ul>
    </section>

    <section aria-labelledby="project-proposal">
      <h2 id="project-proposal">3. Project proposal</h2>
      <p>
        <strong>Due: 12 November 2026, 23:59 HKT.</strong> Please upload a
        <strong>single PDF</strong> of your proposal to the project proposal assignment on Moodle.
        Name your PDF <code>GroupID.pdf</code>, replacing <code>GroupID</code> with your assigned
        Moodle group ID; for example, <code>group_02.pdf</code>.
      </p>
      <p>Your proposal should include:</p>
      <ol>
        <li>Your group ID, all members' names and student IDs, and planned responsibilities.</li>
        <li>
          The prediction problem, the available inputs and your initial understanding of the data.
        </li>
        <li>
          Your preprocessing and feature ideas, proposed algorithms, and reasons for choosing them.
        </li>
        <li>
          A justified validation strategy using the labeled training data, accounting for repeated
          students and the later test presentation. Do not use
          <code>student_group</code> as a predictor or allow the same student's examples into both
          training and validation partitions.
        </li>
        <li>
          <strong>Preliminary baseline results on your validation set</strong>, including binary log
          loss, how the baseline was trained, and how you formed the split. A plan without a
          measured baseline is not sufficient.
        </li>
        <li>A feasible work plan, timeline, and anticipated challenges.</li>
      </ol>
    </section>

    <section aria-labelledby="project-final">
      <h2 id="project-final">4. Final report, code and presentation</h2>
      <p>
        <strong>Due: 6 December 2026, 23:59 HKT.</strong> Upload the following to the final project
        assignment on Moodle. Use your group ID in each filename, for example
        <code>group_02_report.pdf</code> and <code>group_02_code.zip</code>.
      </p>
      <h3>Final report — PDF</h3>
      <p>
        Explain the problem, data exploration, preprocessing, feature engineering, validation
        design, models and tuning procedure. Compare your baseline and improved models using clear
        tables or figures, report validation and leaderboard results, and justify the final model
        choice. Include model analysis or interpretability, error analysis, limitations,
        conclusions, references and each member's contributions. Distinguish local validation
        results from public and private test scores; report private scores only if available before
        submission.
      </p>
      <h3>Code — ZIP attachment</h3>
      <p>
        Attach your code as a ZIP file. There is <strong>no required code format</strong>: Jupyter
        notebooks, a Python code project, or another reproducible project structure are all
        acceptable. You do not need to convert your work into a notebook.
      </p>
      <p>The ZIP must include:</p>
      <ul>
        <li>All source code needed for preprocessing, training and final prediction.</li>
        <li>
          A README with environment and dependency versions, expected data locations, random seeds,
          and exact commands or notebook execution order.
        </li>
        <li>
          Instructions to reproduce your reported results and generate the final Kaggle CSV from the
          supplied project data, identifying the final model/configuration and selected Kaggle
          submission.
        </li>
      </ul>
      <p>
        Check your code in a fresh environment, not just your current interactive session. Do not
        include credentials, API keys or unnecessary copies of the course dataset. The teaching team
        will execute your submitted code to verify results.
      </p>
      <h3>Presentation slides — PDF</h3>
      <p>
        Submit one PDF of the slides used in your presentation. Prioritize the task, approach, key
        results, model analysis and take-home message rather than a walkthrough of every experiment.
      </p>
      <h3>Oral presentation — video, maximum 8 minutes</h3>
      <p>
        Submit one recorded group presentation video on Moodle. The time limit is
        <strong>strictly 8 minutes or less for the entire video</strong>, including any introduction
        and closing. Check the exported video's duration and ensure that the narration is audible
        and the slides are readable before uploading.
      </p>
    </section>

    <section aria-labelledby="project-kaggle">
      <h2 id="project-kaggle">5. Kaggle submission and performance evaluation</h2>
      <p><strong>Final predictions due: 6 December 2026, 23:59 HKT.</strong></p>
      <ul>
        <li>
          Use <strong>one Kaggle team per project group</strong>. Your team name must exactly match
          your Moodle group name: <code>group_XX</code>, with your assigned two-digit group number
          (for example, <code>group_02</code>). Do not add track suffixes. Each member should use
          their own account; do not share credentials.
        </li>
        <li>
          Submit predictions through the competition's <strong>Submit Predictions</strong>
          page and confirm that Kaggle accepts your CSV. Follow the competition's team-size and
          submission limits.
        </li>
        <li>
          Use <code>sample_submission.csv</code> as your template: exactly
          <code>sample_id,prediction</code>, one row per test ID in the supplied order, with no
          index column. Predict the probability of <code>target = 1</code> (a recorded activity
          pause), not a hard class label. Clip probabilities to
          <code>[0.000001, 0.999999]</code> before saving.
        </li>
        <li>
          The metric is <strong>binary log loss; lower is better</strong>. The public leaderboard
          uses approximately 30% of test examples; the private leaderboard uses the remaining
          examples. These are dataset proportions, not grading weights.
        </li>
        <li>
          The private leaderboard determines the final competition ranking. For the course
          performance component,
          <strong>both public and private performance will be weighed</strong>, with results
          verified against your submitted code. Any detailed weighting or score-to-mark rules will
          be communicated on Moodle. Leaderboard rank alone is not your overall project grade.
        </li>
        <li>
          Select your final submission using your own validation evidence and document the exact
          submission and model in your README. Avoid tuning solely to the public leaderboard; public
          scores are not a substitute for a sound validation design.
        </li>
      </ul>
    </section>

    <section aria-labelledby="project-faq">
      <h2 id="project-faq">6. Frequently asked questions</h2>
      <h3>Can we use deep neural networks or time-series models?</h3>
      <p>
        Yes. Choose methods that suit the data and justify them through validation. A neural network
        or sequence model is not required; compare against a simple baseline, and consider whether
        aggregated activity features are sufficient.
      </p>
      <h3>Can we use extra data or pretrained models?</h3>
      <p>
        Use only data supplied through the course competition. Do not retrieve original records,
        hidden outcomes or external labels, and do not use external pretrained model weights.
        Software libraries are allowed. Keep course data and any Kaggle notebooks containing it
        private; do not share predictions or solutions across teams.
      </p>
      <h3>Do we need a GPU?</h3>
      <p>
        Not necessarily. Many suitable statistical learning methods run on a CPU. If needed, a
        notebook service such as Google Colab can be used, subject to its availability; your
        submission must still include reproducible setup and execution instructions.
      </p>
      <h3>Where should we check for course arrangements or updates?</h3>
      <p>
        Check Moodle announcements and the relevant submission assignments. Submit reports, code,
        slides and video on Moodle, not to this public website. Submit prediction CSVs to Kaggle.
      </p>
    </section>

    <section class="submission-checklist" aria-labelledby="project-checklist">
      <h2 id="project-checklist">Before you submit</h2>
      <ul>
        <li>
          <strong>12 November:</strong> one proposal PDF named <code>GroupID.pdf</code> on Moodle.
        </li>
        <li><strong>6 December:</strong> accepted final prediction CSV on Kaggle.</li>
        <li><strong>6 December:</strong> report PDF, code ZIP, slides PDF and video on Moodle.</li>
        <li>Video duration is at most 8 minutes; code runs from the supplied instructions.</li>
        <li>All uploads are complete by <strong>23:59 HKT</strong> on the respective date.</li>
      </ul>
    </section>
  </article>
</template>

<style scoped>
.project-guidelines {
  max-width: 1060px;
  overflow-wrap: anywhere;
}
.project-guidelines h1 {
  margin: 12px 0 24px;
}
.project-intro {
  font-size: 1.12rem;
}
.project-guidelines section {
  margin-top: 44px;
  padding-top: 8px;
  border-top: 1px solid var(--line);
}
.project-guidelines h2 {
  font-size: 1.4rem;
  margin: 24px 0 16px;
}
.project-guidelines h3 {
  font-size: 1.05rem;
  margin: 28px 0 8px;
}
.project-guidelines p,
.project-guidelines li {
  font-size: 0.95rem;
}
.project-guidelines li {
  margin: 10px 0;
}
.project-guidelines ul,
.project-guidelines ol {
  padding-left: 24px;
}
.deadline-list {
  border-left: 3px solid var(--accent);
  background: var(--surface);
  margin: 24px 0;
  padding: 4px 24px;
}
.deadline-list > div {
  padding: 16px 0;
}
.deadline-list > div + div {
  border-top: 1px solid var(--line);
}
.deadline-list dt {
  font-weight: 650;
}
.deadline-list dd {
  margin: 4px 0 0;
}
.deadline-list time {
  color: var(--accent);
  font-weight: 600;
}
.deadline-list dd span {
  display: block;
  font-size: 0.9rem;
  margin-top: 4px;
}
.project-guidelines table {
  min-width: 370px;
}
.project-guidelines th,
.project-guidelines td {
  font-size: 0.85rem;
}
.project-guidelines tbody th {
  color: var(--ink);
  border-color: var(--line);
}
.project-guidelines code {
  font-size: 0.88em;
  background: var(--soft);
  border-radius: 3px;
  padding: 2px 5px;
}
.submission-checklist {
  margin-bottom: 48px;
}
</style>
