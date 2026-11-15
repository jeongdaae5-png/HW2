const form = document.querySelector("#analyze-form");
const input = document.querySelector("#image-input");
const dropzone = document.querySelector("#dropzone");
const preview = document.querySelector("#preview");
const error = document.querySelector("#error");
const button = document.querySelector("#submit-button");

input.addEventListener("change", () => {
  const file = input.files[0];
  if (!file) return;
  preview.src = URL.createObjectURL(file);
  dropzone.classList.add("has-image");
  error.textContent = "";
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!input.files[0]) return;
  button.disabled = true;
  button.textContent = "분석 중...";
  error.textContent = "";
  try {
    const response = await fetch("/api/analyze", { method: "POST", body: new FormData(form) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "분석에 실패했습니다.");
    renderResult(data);
  } catch (err) { error.textContent = err.message; }
  finally { button.disabled = false; button.textContent = "이 사진으로 분석하기"; }
});

function renderResult(data) {
  document.querySelector("#result").hidden = false;
  document.querySelector("#result-type").textContent = data.type;
  document.querySelector("#confidence").textContent = `신뢰도 ${data.confidence}`;
  document.querySelector("#summary").textContent = data.face_detected ? "얼굴 영역을 찾아 분석했습니다." : "얼굴을 찾지 못해 중앙 영역을 기준으로 분석했습니다.";
  document.querySelector("#rgb").textContent = data.skin_rgb.join(", ");
  document.querySelector("#hsv").textContent = data.hsv.join(", ");
  fillSwatches("#recommended", data.recommended);
  fillSwatches("#avoid", data.avoid);
  document.querySelector("#result").scrollIntoView({ behavior: "smooth", block: "start" });
}

function fillSwatches(selector, colors) {
  document.querySelector(selector).innerHTML = colors.map(({ code, name }) => `<span class="swatch"><i style="background:${code}"></i>${name}<br>${code}</span>`).join("");
}
