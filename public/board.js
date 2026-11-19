function dismissNotice(dialog) {
  dialog.close();
  const chosen = document.querySelector(".chosen .card-hit");
  if (chosen) chosen.focus();
}
new MutationObserver(() => {
  const dialog = document.querySelector("#notice dialog:not([open])");
  if (dialog && !dialog.dataset.opened) {
    dialog.dataset.opened = "1";
    dialog.showModal();
  }
}).observe(document.documentElement, {subtree:true,childList:true});
document.addEventListener("click", event => {
  const cases = document.querySelector("#cases");
  const choice = event.target.closest("[data-puzzle]");
  if (choice) window.dash_clientside.set_props("puzzle", {value:choice.dataset.puzzle});
  if (cases && (choice || !cases.contains(event.target))) cases.open = false;
  const dialog = event.target.closest("dialog");
  if (dialog && event.target.closest(".dismiss")) dismissNotice(dialog);
  const menu = document.querySelector("#menu-popup");
  if (menu && menu.style.display === "block" && !event.target.closest(".tools")) document.querySelector("#menu-toggle").click();
  if (event.target.matches("#board,.slot,.grid,.coordinate,.desk")) document.querySelector("#clear").click();
});
document.addEventListener("keydown", event => {
  if (event.target.matches(".clue-reference") && (event.key === "Enter" || event.key === " ")) {
    event.preventDefault();
    if (!event.repeat) event.target.click();
    return;
  }
  if (event.key !== "Escape" || document.querySelector("dialog[open]")) return;
  const cases = document.querySelector("#cases");
  if (cases.open) cases.open = false;
  else if (document.querySelector("#menu-popup").style.display === "block") document.querySelector("#menu-toggle").click();
  else document.querySelector("#clear").click();
});

// Fit revealed statements using the same bounded font search as the desktop card.
function fitStatement(node) {
  const slot = node.closest(".slot");
  const scale = Math.max(.58, Math.min(1.65, slot.clientHeight / 200));
  const narrow = slot.clientWidth - 8 < 260;
  const max = Math.max(narrow ? 13 : 15, Math.round((narrow ? 15.5 : 19) * scale));
  const min = Math.max(narrow ? 11 : 12, Math.round((narrow ? 11.8 : 12.5) * scale));
  for (let size = max; size >= min; size--) {
    node.style.fontSize = size + "px";
    if (node.scrollHeight <= node.clientHeight) break;
  }
}
const resizeStatements = new ResizeObserver(entries => {
  for (const {target} of entries) fitStatement(target);
});
const observed = new Set();
let followJournal = true;
new MutationObserver(() => {
  for (const node of observed) {
    if (!node.isConnected) { resizeStatements.unobserve(node); observed.delete(node); }
  }
  for (const node of document.querySelectorAll(".statement")) {
    if (!observed.has(node)) { observed.add(node); resizeStatements.observe(node); }
    fitStatement(node);
  }
  const journal = document.querySelector("#journal");
  if (journal && followJournal) journal.scrollTop = journal.scrollHeight;
}).observe(document.documentElement, {childList:true, subtree:true});
document.addEventListener("scroll", event => {
  if (event.target.id !== "journal") return;
  const journal = event.target;
  followJournal = journal.scrollTop + journal.clientHeight >= journal.scrollHeight - 24;
  document.querySelector("#latest").hidden = followJournal;
}, true);
document.addEventListener("click", event => {
  if (event.target.id === "latest") {
    const journal = document.querySelector("#journal");
    journal.scrollTop = journal.scrollHeight;
  }
});
let panelDrag;
function floatPanel(panel, x, y) {
  panel.classList.add("floating");
  const left = Math.max(0, Math.min(x, innerWidth-panel.offsetWidth));
  const top = Math.max(0, Math.min(y, innerHeight-panel.offsetHeight));
  panel.style.setProperty("--dock-x", left+"px");
  panel.style.setProperty("--dock-y", top+"px");
}
document.addEventListener("dblclick", event => {
  if (!event.target.closest("#journal-panel>header") || event.target.closest("button")) return;
  const panel = document.querySelector("#journal-panel");
  if (panel.classList.contains("floating")) panel.classList.remove("floating");
  else floatPanel(panel, panel.offsetLeft-24, 35);
});
document.addEventListener("pointerdown", event => {
  if (!event.target.closest(".dock-grip,#journal-panel>header") || event.target.closest("button")) return;
  const panel = document.querySelector("#journal-panel");
  panelDrag = {panel, x:event.clientX, y:event.clientY, rect:panel.getBoundingClientRect(),
               resize:event.target.matches(".dock-grip")};
  event.target.setPointerCapture(event.pointerId);
});
document.addEventListener("pointermove", event => {
  if (!panelDrag) return;
  const {panel,x,y,rect,resize} = panelDrag;
  if (resize) panel.style.setProperty("--dock-width", Math.min(460,Math.max(360,rect.width+x-event.clientX))+"px");
  else if (Math.abs(x-event.clientX)+Math.abs(y-event.clientY)>4)
    floatPanel(panel,rect.left+event.clientX-x,rect.top+event.clientY-y);
});
document.addEventListener("pointerup", () => { panelDrag = null; });
document.addEventListener("pointercancel", () => { panelDrag = null; });
let selectedCell;
new MutationObserver(() => {
  const chosen = document.querySelector(".chosen");
  if (selectedCell !== chosen?.dataset.cell) {
    selectedCell = chosen?.dataset.cell;
    const sprite = chosen?.querySelector(".portrait .sprite");
    if (sprite) {
      sprite.classList.add("reacting");
      setTimeout(() => sprite.classList.remove("reacting"), 520);
    }
  }
}).observe(document.documentElement, {subtree:true,childList:true,attributes:true,attributeFilter:["class"]});
