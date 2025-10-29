const classSection = document.getElementById("class-section");
const subjectSection = document.getElementById("subject-section");
const subSubjectSection = document.getElementById("subsubject-section");
const chapterSection = document.getElementById("chapter-section");

const classList = document.getElementById("class-list");
const subjectList = document.getElementById("subject-list");
const subSubjectList = document.getElementById("subsubject-list");
const chapterList = document.getElementById("chapter-list");

let ncertData = {};
let selectedClass = null;
let selectedSubject = null;
let selectedSubSubject = null;

// Hide all
function hideAll() {
  [classSection, subjectSection, subSubjectSection, chapterSection].forEach(sec =>
    sec.classList.add("hidden")
  );
}

// Load structure
fetch("/get_structure")
  .then(res => res.json())
  .then(data => {
    ncertData = data;
    showClasses();
  })
  .catch(() => {
    classList.innerHTML = "<p>⚠️ Failed to load NCERT data.</p>";
  });

// Show classes
function showClasses() {
  hideAll();
  classSection.classList.remove("hidden");
  classList.innerHTML = "";
  Object.keys(ncertData).forEach(cls => {
    const div = document.createElement("div");
    div.className = "card";
    div.textContent = "Class " + cls;
    div.onclick = () => showSubjects(cls);
    classList.appendChild(div);
  });
}

// Show subjects
function showSubjects(cls) {
  hideAll();
  subjectSection.classList.remove("hidden");
  selectedClass = cls;
  subjectList.innerHTML = "";

  Object.keys(ncertData[cls]).forEach(subject => {
    const div = document.createElement("div");
    div.className = "card";
    div.textContent = subject;
    div.onclick = () => {
      const subSubjects = ncertData[cls][subject];
      if (Array.isArray(subSubjects)) {
        showChapters(subject, subSubjects);
      } else {
        showSubSubjects(subject, subSubjects);
      }
    };
    subjectList.appendChild(div);
  });
}

// Show sub-subjects
function showSubSubjects(subject, subSubjects) {
  hideAll();
  subSubjectSection.classList.remove("hidden");
  selectedSubject = subject;
  subSubjectList.innerHTML = "";

  Object.keys(subSubjects).forEach(sub => {
    const div = document.createElement("div");
    div.className = "card";
    div.textContent = sub;
    div.onclick = () => showChapters(sub, subSubjects[sub]);
    subSubjectList.appendChild(div);
  });
}

// Show chapters
function showChapters(subject, chapters) {
  hideAll();
  chapterSection.classList.remove("hidden");
  selectedSubSubject = subject;
  chapterList.innerHTML = "";

  chapters.forEach(chapter => {
    const div = document.createElement("div");
    div.className = "card";
    div.textContent = chapter;
    div.onclick = () => loadSolution(chapter);
    chapterList.appendChild(div);
  });
}

// Load solution
async function loadSolution(chapter) {
  chapterList.innerHTML = `<p class="loading">🧠 Generating solutions for <b>${chapter}</b>...</p>`;
  try {
    const subjectPath = selectedSubSubject
      ? `${selectedSubject} - ${selectedSubSubject}`
      : selectedSubject;
    const res = await fetch("/get_solution", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        class: selectedClass,
        subject: subjectPath,
        chapter,
      }),
    });
    const data = await res.json();
    if (data.solution) {
      chapterList.innerHTML = renderSolution(data.solution);
      if (window.MathJax) MathJax.typesetPromise();
    } else {
      chapterList.innerHTML = `<p>⚠️ ${data.error || "No solution found."}</p>`;
    }
  } catch (err) {
    chapterList.innerHTML = `<p>⚠️ Failed to fetch solution.</p>`;
  }
}

// Render solution
function renderSolution(sol) {
  let html = `<div class="solution"><h2>${sol.chapter}</h2>`;
  sol.exercises.forEach(ex => {
    html += `<h3>${ex.exercise}</h3>`;
    ex.questions.forEach(q => {
      html += `
        <div class="qa">
          <p class="question"><b>Q${q.qno}:</b> ${q.question}</p>
          <p class="answer"><b>Ans:</b> ${q.answer}</p>
        </div>`;
    });
  });
  return html + "</div>";
}
