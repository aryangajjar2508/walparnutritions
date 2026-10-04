// Walpar Clinical Pro Frontend Application

let currentSupplements = [];
let currentConditions = [];
let currentCategories = [];
let currentGuides = [];
let currentFeedTopic = "all";
let hasApiKey = false;
let currentTab = "supplements";
let lastValidatedFormula = null;
let currentLetter = "all";
let currentItemType = "all";
let currentCatalogSearch = "";
let currentSupplementMatrix = [];
let currentHemCategory = "all";

// Router and History Navigation State
let currentDetailView = null; // null | "supplement" | "condition" | "guide"
let currentDetailSlug = null;
let isInternalNavigation = false;
let navHistoryStack = []; // In-memory navigation history stack of states
let supplementReferrer = null; // { type: 'condition' | 'guide' | 'category' | 'tab', slug?, name? }

function slugify(text) {
  if (!text) return "";
  return text.toString().toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/[^\w\-]+/g, '')
    .replace(/\-\-+/g, '-')
    .replace(/^-+/, '')
    .replace(/-+$/, '');
}

function findSupplementSlug(name) {
  if (!name) return "";
  const clean = name.toLowerCase().trim();
  const direct = currentSupplements.find(s => 
    s.name.toLowerCase() === clean || 
    clean.includes(s.name.toLowerCase()) || 
    s.name.toLowerCase().includes(clean)
  );
  if (direct) return direct.slug;
  return slugify(clean);
}

// Record navigation state into our internal history stack
function recordNavigationState(state) {
  if (isInternalNavigation) return;
  const last = navHistoryStack[navHistoryStack.length - 1];
  if (last && last.type === state.type && last.slug === state.slug && last.tab === state.tab) {
    return;
  }
  navHistoryStack.push(state);
  if (navHistoryStack.length > 50) navHistoryStack.shift();
  updateNavControlStates();
}

function pushRoute(state, hash) {
  if (isInternalNavigation) return;
  try {
    if (window.location.hash !== hash) {
      window.history.pushState(state, "", hash);
    }
  } catch (e) {
    console.warn("history.pushState failed:", e);
  }
  updateNavControlStates();
}

function updateNavControlStates() {
  const backBtn = document.getElementById("global-back-btn");
  const forwardBtn = document.getElementById("global-forward-btn");
  const floatingBackBtn = document.getElementById("floating-back-btn");

  const canGoBack = navHistoryStack.length > 0 || currentDetailView !== null || currentTab !== "supplements";

  if (backBtn) {
    backBtn.disabled = false;
    if (canGoBack) {
      backBtn.classList.add("can-go-back");
      backBtn.title = "Go back to previous page (Alt + Left Arrow)";
    } else {
      backBtn.classList.remove("can-go-back");
      backBtn.title = "At Walpar Home (Supplements Directory)";
    }
  }

  if (forwardBtn) {
    forwardBtn.disabled = false;
  }

  if (floatingBackBtn) {
    if (currentDetailView !== null) {
      floatingBackBtn.classList.remove("hidden");
    } else {
      floatingBackBtn.classList.add("hidden");
    }
  }
}

// Master navigateBack function - 100% reliable, never hangs or fails silently
function navigateBack() {
  // If we have an in-memory stack entry, pop and restore it immediately
  if (navHistoryStack.length > 0) {
    const prevState = navHistoryStack.pop();
    isInternalNavigation = true;
    try {
      if (prevState.type === "condition" && prevState.slug) {
        viewCondition(prevState.slug, true, false);
      } else if (prevState.type === "guide" && prevState.slug) {
        viewGuide(prevState.slug, true, false);
      } else if (prevState.type === "supplement" && prevState.slug) {
        viewSupplement(prevState.slug, true, null, false);
      } else if (prevState.type === "tab" && prevState.tab) {
        switchMainTab(prevState.tab, true, false);
      } else {
        switchMainTab("supplements", true, false);
      }
    } finally {
      isInternalNavigation = false;
      updateNavControlStates();
    }
    return;
  }

  // Fallback if stack is empty (e.g. direct link entry or refreshed page)
  if (currentDetailView === "supplement") {
    backFromSupplement();
  } else if (currentDetailView === "condition") {
    backToConditions();
  } else if (currentDetailView === "guide") {
    backToGuides();
  } else if (currentTab !== "supplements") {
    switchMainTab("supplements", true, false);
  } else {
    // Already on supplements home view
    const catSection = document.getElementById("category-results-section");
    if (catSection && !catSection.classList.contains("hidden")) {
      filterByCategory("all");
    } else {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }
}

function navigateForward() {
  try {
    window.history.forward();
  } catch (e) {}
}

// Direct Back Handlers with immediate synchronous DOM switching:
function backFromSupplement() {
  if (supplementReferrer) {
    const ref = supplementReferrer;
    supplementReferrer = null;
    if (ref.type === "condition" && ref.slug) {
      viewCondition(ref.slug, true, false);
      return;
    }
    if (ref.type === "guide" && ref.slug) {
      viewGuide(ref.slug, true, false);
      return;
    }
    if (ref.type === "category" && ref.name) {
      switchMainTab("supplements", false, false);
      filterByCategory(ref.name);
      return;
    }
    if (ref.type === "tab" && ref.tab) {
      switchMainTab(ref.tab, true, false);
      return;
    }
  }

  // Default return to Supplements directory
  backToSupplements();
}

function backToSupplements() {
  currentDetailView = null;
  currentDetailSlug = null;
  supplementReferrer = null;

  // Hide all detail views immediately
  const dv = document.getElementById("detail-view");
  const cdv = document.getElementById("condition-detail-view");
  const gdv = document.getElementById("guide-detail-view");
  if (dv) dv.classList.add("hidden");
  if (cdv) cdv.classList.add("hidden");
  if (gdv) gdv.classList.add("hidden");

  // Reset category results if open
  const catSection = document.getElementById("category-results-section");
  const overviewSection = document.getElementById("supplements-overview-section");
  if (catSection) catSection.classList.add("hidden");
  if (overviewSection) overviewSection.classList.remove("hidden");

  // Show home view
  const homeView = document.getElementById("home-view");
  if (homeView) homeView.classList.remove("hidden");

  // Update tabs
  currentTab = "supplements";
  document.querySelectorAll(".nav-tab").forEach(btn => {
    if (btn.id === "tab-btn-supplements") btn.classList.add("active");
    else btn.classList.remove("active");
  });

  try {
    window.history.pushState({ type: "tab", tab: "supplements" }, "", "#/tab/supplements");
  } catch (e) {}

  updateNavControlStates();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function backToConditions() {
  currentDetailView = null;
  currentDetailSlug = null;

  const dv = document.getElementById("detail-view");
  const cdv = document.getElementById("condition-detail-view");
  const gdv = document.getElementById("guide-detail-view");
  if (dv) dv.classList.add("hidden");
  if (cdv) cdv.classList.add("hidden");
  if (gdv) gdv.classList.add("hidden");

  switchMainTab("conditions", true, false);
}

function backToGuides() {
  currentDetailView = null;
  currentDetailSlug = null;

  const dv = document.getElementById("detail-view");
  const cdv = document.getElementById("condition-detail-view");
  const gdv = document.getElementById("guide-detail-view");
  if (dv) dv.classList.add("hidden");
  if (cdv) cdv.classList.add("hidden");
  if (gdv) gdv.classList.add("hidden");

  switchMainTab("guides", true, false);
}

// Global Keyboard Navigation (Alt+Left, Backspace, Escape)
document.addEventListener("keydown", (e) => {
  const tag = (e.target.tagName || "").toLowerCase();
  if (tag === "input" || tag === "textarea" || e.target.isContentEditable) return;

  if (e.key === "Escape") {
    const loadingModal = document.getElementById("synthesis-loading-modal");
    if (loadingModal && !loadingModal.classList.contains("hidden")) return;
    if (currentDetailView) {
      e.preventDefault();
      navigateBack();
      return;
    }
  }

  if ((e.altKey && e.key === "ArrowLeft") || (e.key === "Backspace" && currentDetailView)) {
    e.preventDefault();
    navigateBack();
  } else if (e.altKey && e.key === "ArrowRight") {
    e.preventDefault();
    navigateForward();
  }
});

async function handleRoute(isPop = false) {
  isInternalNavigation = true;
  const hash = window.location.hash || "#/";

  try {
    if (hash.startsWith("#/supplement/")) {
      const slug = decodeURIComponent(hash.replace("#/supplement/", "")).trim();
      if (slug) await viewSupplement(slug, false, null, false);
    } else if (hash.startsWith("#/condition/")) {
      const slug = decodeURIComponent(hash.replace("#/condition/", "")).trim();
      if (slug) await viewCondition(slug, false, false);
    } else if (hash.startsWith("#/guide/")) {
      const slug = decodeURIComponent(hash.replace("#/guide/", "")).trim();
      if (slug) await viewGuide(slug, false, false);
    } else if (hash.startsWith("#/tab/")) {
      const tab = hash.replace("#/tab/", "").trim();
      switchMainTab(tab, false, false);
    } else if (hash === "#/conditions") {
      switchMainTab("conditions", false, false);
    } else if (hash === "#/categories") {
      switchMainTab("categories", false, false);
    } else if (hash === "#/guides") {
      switchMainTab("guides", false, false);
    } else if (hash === "#/symptoms") {
      switchMainTab("symptoms", false, false);
    } else if (hash === "#/formulator") {
      switchMainTab("formulator", false, false);
    } else if (hash === "#/feed") {
      switchMainTab("feed", false, false);
    } else if (hash === "#/ai") {
      switchMainTab("ai", false, false);
    } else {
      switchMainTab("supplements", false, false);
    }
  } finally {
    isInternalNavigation = false;
    updateNavControlStates();
  }
}

window.addEventListener("popstate", () => {
  handleRoute(true);
});

// Initialize app on page load
document.addEventListener("DOMContentLoaded", () => {
  checkStatus();
  loadSupplements().then(() => {
    if (window.location.hash && window.location.hash !== "#/" && window.location.hash !== "#/supplements") {
      handleRoute(false);
    }
  });
  setupSearch();
  initFormulator();
  updateNavControlStates();
});

// Main Tab Navigation
function switchMainTab(tab, push = true, record = true) {
  if (record && !isInternalNavigation) {
    if (currentDetailView) {
      recordNavigationState({ type: currentDetailView, slug: currentDetailSlug });
    } else if (currentTab !== tab) {
      recordNavigationState({ type: "tab", tab: currentTab });
    }
  }

  currentTab = tab;
  currentDetailView = null;
  currentDetailSlug = null;
  const tabs = ["supplements", "conditions", "categories", "guides", "symptoms", "formulator", "feed", "ai"];
  
  tabs.forEach(t => {
    const btn = document.getElementById(`tab-btn-${t}`);
    if (btn) {
      if (t === tab) btn.classList.add("active");
      else btn.classList.remove("active");
    }
  });

  // Views mapping
  const views = {
    supplements: document.getElementById("home-view"),
    conditions: document.getElementById("conditions-view"),
    categories: document.getElementById("categories-view"),
    guides: document.getElementById("guides-view"),
    symptoms: document.getElementById("symptoms-view"),
    formulator: document.getElementById("formulator-view"),
    feed: document.getElementById("feed-view"),
    ai: document.getElementById("ai-view")
  };

  // Hide detail views
  const dv = document.getElementById("detail-view");
  const cdv = document.getElementById("condition-detail-view");
  const gdv = document.getElementById("guide-detail-view");
  if (dv) dv.classList.add("hidden");
  if (cdv) cdv.classList.add("hidden");
  if (gdv) gdv.classList.add("hidden");

  // Toggle main views
  Object.keys(views).forEach(k => {
    if (views[k]) {
      if (k === tab) views[k].classList.remove("hidden");
      else views[k].classList.add("hidden");
    }
  });

  if (push) {
    pushRoute({ type: "tab", tab: tab }, `#/tab/${tab}`);
  }

  // Lazy load data on tab activation
  if (tab === "conditions" && currentConditions.length === 0) loadConditions();
  if (tab === "categories" && currentCategories.length === 0) loadCategories();
  if (tab === "guides" && currentGuides.length === 0) loadGuides();
  if (tab === "feed") loadLatestFeed(false);
  if (tab === "formulator") loadSavedFormulas();

  updateNavControlStates();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// Check API key configuration status
async function checkStatus() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();
    hasApiKey = data.has_api_key;
    const dot = document.getElementById("api-status-dot");
    if (hasApiKey) {
      dot.classList.add("active");
      dot.title = `Gemini API Active (${data.gemini_preview}) | PubMed API Active (${data.ncbi_preview})`;
    } else {
      dot.classList.remove("active");
      dot.title = "No API Key Set (Click to configure keys)";
    }
  } catch (e) {
    console.error("Status check failed:", e);
  }
}

// =======================================================
// 1. SUPPLEMENTS DIRECTORY
// =======================================================
async function loadSupplements() {
  try {
    const res = await fetch("/api/supplements");
    currentSupplements = await res.json();
    updateEncyclopediaCounts();
    applyCatalogFilters();
  } catch (e) {
    console.error("Failed to load supplements:", e);
  }
}

function updateEncyclopediaCounts() {
  const counts = {
    all: currentSupplements.length,
    supplements: 0,
    foods: 0,
    diets: 0,
    other: 0
  };

  currentSupplements.forEach(s => {
    const type = s.item_type || "supplements";
    if (counts[type] !== undefined) counts[type]++;
    else counts.other++;
  });

  const elAll = document.getElementById("count-type-all");
  const elSupp = document.getElementById("count-type-supplements");
  const elFood = document.getElementById("count-type-foods");
  const elDiet = document.getElementById("count-type-diets");
  const elOther = document.getElementById("count-type-other");

  if (elAll) elAll.innerText = counts.all;
  if (elSupp) elSupp.innerText = counts.supplements;
  if (elFood) elFood.innerText = counts.foods;
  if (elDiet) elDiet.innerText = counts.diets;
  if (elOther) elOther.innerText = counts.other;
}

function filterByItemType(type) {
  currentItemType = type;
  document.querySelectorAll(".encyclopedia-type-tabs .type-tab-btn").forEach(btn => {
    if (btn.dataset.type === type) btn.classList.add("active");
    else btn.classList.remove("active");
  });
  applyCatalogFilters();
}

function filterByLetter(letter) {
  currentLetter = letter;
  document.querySelectorAll(".alphabet-ribbon .letter-btn").forEach(btn => {
    if (btn.dataset.letter === letter) btn.classList.add("active");
    else btn.classList.remove("active");
  });
  applyCatalogFilters();
}

function onQuickFilterInput(val) {
  currentCatalogSearch = (val || "").trim().toLowerCase();
  applyCatalogFilters();
}

function applyCatalogFilters() {
  let filtered = currentSupplements;

  // 1. Filter by Item Type
  if (currentItemType !== "all") {
    if (currentItemType === "other") {
      filtered = filtered.filter(s => s.item_type === "other" || s.item_type === "medication");
    } else {
      filtered = filtered.filter(s => s.item_type === currentItemType);
    }
  }

  // 2. Filter by Letter
  if (currentLetter !== "all") {
    if (currentLetter === "0-9") {
      filtered = filtered.filter(s => s.letter_index === "0-9" || /^\d/.test(s.name.trim()));
    } else {
      filtered = filtered.filter(s => (s.letter_index || "").toUpperCase() === currentLetter.toUpperCase());
    }
  }

  // 3. Filter by Search input
  if (currentCatalogSearch) {
    filtered = filtered.filter(s => 
      s.name.toLowerCase().includes(currentCatalogSearch) ||
      (s.summary && s.summary.toLowerCase().includes(currentCatalogSearch))
    );
  }

  // Update header count badge
  const countBadge = document.getElementById("supplements-count");
  if (countBadge) {
    if (currentLetter !== "all" || currentItemType !== "all" || currentCatalogSearch) {
      countBadge.innerText = `Showing ${filtered.length} of ${currentSupplements.length} items`;
    } else {
      countBadge.innerText = `${filtered.length} Interventions`;
    }
  }

  renderSupplementsGrid(filtered);
}

function renderSupplementsGrid(supplements) {
  const grid = document.getElementById("supplements-grid");
  grid.innerHTML = "";

  if (!supplements || supplements.length === 0) {
    grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--gray-500); padding: 3rem; background: #ffffff; border-radius: 12px; border: 1px dashed var(--gray-300);">
      <div style="font-size: 2rem; margin-bottom: 0.5rem;">🔍</div>
      <h3 style="color: var(--navy); margin-bottom: 0.25rem;">No interventions found</h3>
      <p style="font-size: 0.85rem;">No items match the selected letter or filter criteria. Try choosing "All" or a different category.</p>
    </div>`;
    return;
  }

  // Helper for type tag
  const getTypeBadge = (type) => {
    switch (type) {
      case "foods":
        return `<span class="type-tag type-food">🥑 Functional Food</span>`;
      case "diets":
        return `<span class="type-tag type-diet">🥗 Diet Protocol</span>`;
      case "other":
        return `<span class="type-tag type-other">🧘 Clinical Therapy</span>`;
      case "medication":
        return `<span class="type-tag type-med">💉 Pharmaceutical</span>`;
      default:
        return `<span class="type-tag type-supp">💊 Supplement</span>`;
    }
  };

  const htmlChunks = [];

  // If viewing ALL letters and NO search query, render grouped with alphabet section headers
  if (currentLetter === "all" && !currentCatalogSearch) {
    const groups = {};
    supplements.forEach(supp => {
      let l = supp.letter_index || supp.name.trim()[0].toUpperCase();
      if (/^\d/.test(l)) l = "0-9";
      if (!groups[l]) groups[l] = [];
      groups[l].push(supp);
    });

    const sortedLetters = Object.keys(groups).sort((a, b) => {
      if (a === "0-9") return -1;
      if (b === "0-9") return 1;
      return a.localeCompare(b);
    });

    sortedLetters.forEach(letter => {
      htmlChunks.push(`
        <div class="letter-section-container" id="letter-sec-${letter}">
          <div class="letter-section-header">
            <div class="letter-badge-circle">${letter}</div>
            <span class="letter-section-title">Section ${letter}</span>
            <span class="letter-section-count">(${groups[letter].length} items)</span>
          </div>
        </div>
      `);

      groups[letter].forEach(supp => {
        htmlChunks.push(createSupplementCardHtml(supp, getTypeBadge));
      });
    });
  } else {
    // Filtered view by letter or search
    supplements.forEach(supp => {
      htmlChunks.push(createSupplementCardHtml(supp, getTypeBadge));
    });
  }

  grid.innerHTML = htmlChunks.join("");
}

function createSupplementCardHtml(supp, getTypeBadge) {
  const dose = supp.dosage_guide?.recommended_dose || 
               supp.dosage_guide?.standard_dose || 
               (supp.item_type === "diets" ? "Dietary Protocol" : 
               (supp.item_type === "other" ? "Therapeutic Intervention" : "Standard clinical guideline"));

  const badgeHtml = getTypeBadge(supp.item_type);

  return `
    <div class="supp-card" onclick="viewSupplement('${escapeHtml(supp.slug)}')">
      <div>
        <div class="supp-card-header">
          ${badgeHtml}
          <span style="font-size: 0.72rem; color: var(--gray-400); font-family: monospace;">#${escapeHtml(supp.slug)}</span>
        </div>
        <h3 class="supp-card-title">${escapeHtml(supp.name)}</h3>
        <p class="supp-card-desc">${escapeHtml(supp.summary || "Clinical biochemical monograph, human evidence matrix, and trial references.")}</p>
      </div>
      <div class="supp-card-footer">
        <span title="${escapeHtml(dose)}">📋 ${escapeHtml(dose.slice(0, 24))}${dose.length > 24 ? '...' : ''}</span>
        <span class="supp-card-link">View Clinical Matrix →</span>
      </div>
    </div>
  `;
}

async function viewSupplement(slug, push = true, referrer = null, record = true) {
  if (referrer) {
    supplementReferrer = referrer;
  } else if (!supplementReferrer) {
    if (currentDetailView === "condition" && currentDetailSlug) {
      const condName = document.getElementById("cond-name")?.innerText || currentDetailSlug;
      supplementReferrer = { type: "condition", slug: currentDetailSlug, name: condName };
    } else if (currentDetailView === "guide" && currentDetailSlug) {
      const guideName = document.getElementById("guide-title")?.innerText || currentDetailSlug;
      supplementReferrer = { type: "guide", slug: currentDetailSlug, name: guideName };
    } else {
      supplementReferrer = { type: "tab", tab: currentTab, name: "Supplements" };
    }
  }

  if (record && !isInternalNavigation) {
    if (currentDetailView === "condition") {
      recordNavigationState({ type: "condition", slug: currentDetailSlug, name: document.getElementById("cond-name")?.innerText });
    } else if (currentDetailView === "guide") {
      recordNavigationState({ type: "guide", slug: currentDetailSlug, name: document.getElementById("guide-title")?.innerText });
    } else if (currentDetailView === "supplement" && currentDetailSlug !== slug) {
      recordNavigationState({ type: "supplement", slug: currentDetailSlug });
    } else {
      recordNavigationState({ type: "tab", tab: currentTab });
    }
  }

  currentDetailView = "supplement";
  currentDetailSlug = slug;
  updateNavControlStates();

  const modal = document.getElementById("synthesis-loading-modal");
  const modalTitle = document.getElementById("synthesis-modal-title");
  const modalDesc = document.getElementById("synthesis-modal-desc");
  
  let stepTimer = null;
  const showModalTimer = setTimeout(() => {
    if (modal) {
      modal.classList.remove("hidden");
      if (modalTitle) modalTitle.innerText = "Synthesizing Clinical Evidence";
      if (modalDesc) modalDesc.innerText = `Connecting to PubMed, PubChem & ClinicalTrials.gov for ${slug.replace(/-/g, " ")}...`;
      let step = 1;
      stepTimer = setInterval(() => {
        step = (step % 3) + 1;
        document.querySelectorAll(".syn-step").forEach((el, idx) => {
          if (idx + 1 === step) el.classList.add("active");
          else el.classList.remove("active");
        });
      }, 1500);
    }
  }, 1200);

  try {
    const res = await fetch(`/api/supplement/${slug}`);
    clearTimeout(showModalTimer);
    if (stepTimer) clearInterval(stepTimer);
    if (modal) modal.classList.add("hidden");

    if (!res.ok) {
      const err = await res.json();
      alert(err.detail || "Failed to load supplement details");
      return;
    }
    const data = await res.json();
    renderSupplementDetail(data);

    // Hide all other views
    document.querySelectorAll(".main-content > div").forEach(el => el.classList.add("hidden"));
    document.getElementById("detail-view").classList.remove("hidden");
    if (push) {
      pushRoute({ type: "supplement", slug: slug }, `#/supplement/${slug}`);
    }
    updateNavControlStates();
    window.scrollTo({ top: 0, behavior: "smooth" });
  } catch (e) {
    clearTimeout(showModalTimer);
    if (stepTimer) clearInterval(stepTimer);
    if (modal) modal.classList.add("hidden");
    console.error("Error loading supplement:", e);
    alert("Could not load supplement details.");
  }
}

function renderSupplementDetail(data) {
  // Update back button and breadcrumbs based on referrer origin
  const backLabel = document.getElementById("detail-back-label");
  const middleCrumb = document.getElementById("crumb-middle-link");

  if (supplementReferrer && supplementReferrer.type === "condition") {
    if (backLabel) backLabel.innerText = `Back to Condition (${supplementReferrer.name || "Condition"})`;
    if (middleCrumb) {
      middleCrumb.innerText = supplementReferrer.name || "Condition";
      middleCrumb.onclick = () => viewCondition(supplementReferrer.slug);
    }
  } else if (supplementReferrer && supplementReferrer.type === "guide") {
    if (backLabel) backLabel.innerText = `Back to Guide (${supplementReferrer.name || "Guide"})`;
    if (middleCrumb) {
      middleCrumb.innerText = supplementReferrer.name || "Guide";
      middleCrumb.onclick = () => viewGuide(supplementReferrer.slug);
    }
  } else if (supplementReferrer && supplementReferrer.type === "category") {
    if (backLabel) backLabel.innerText = `Back to Category (${supplementReferrer.name || "Category"})`;
    if (middleCrumb) {
      middleCrumb.innerText = supplementReferrer.name || "Category";
      middleCrumb.onclick = () => filterByCategory(supplementReferrer.name);
    }
  } else {
    if (backLabel) backLabel.innerText = "Back to Supplements";
    if (middleCrumb) {
      middleCrumb.innerText = "Encyclopedia";
      middleCrumb.onclick = () => switchMainTab("supplements");
    }
  }

  // Breadcrumbs
  const crumb = document.getElementById("crumb-current");
  if (crumb) crumb.innerText = data.name;

  document.getElementById("detail-name").innerText = data.name;

  const synContainer = document.getElementById("detail-synonyms");
  synContainer.innerHTML = "";
  (data.pubchem_data?.synonyms || []).forEach(s => {
    const tag = document.createElement("span");
    tag.className = "synonym-tag";
    tag.innerText = s;
    synContainer.appendChild(tag);
  });

  // 1. PubChem & Classification Ribbon
  const pubchemBadge = document.getElementById("pubchem-badge");
  const label1 = document.getElementById("chem-label-1");
  const val1 = document.getElementById("chem-formula");
  const label2 = document.getElementById("chem-label-2");
  const val2 = document.getElementById("chem-weight");
  const unit2 = document.getElementById("chem-weight-unit");
  const label3 = document.getElementById("chem-label-3");
  const cidLink = document.getElementById("chem-cid-link");

  const itemType = data.item_type || "supplements";
  const pData = data.pubchem_data || {};

  if (itemType === "diets") {
    if (pubchemBadge) { pubchemBadge.innerText = "🥗 Dietary Protocol"; pubchemBadge.className = "badge badge-type-cond"; }
    if (label1) label1.innerText = "Protocol Class:";
    if (val1) val1.innerText = "Structured Nutritional Intervention";
    if (label2) label2.innerText = "Target Endpoint:";
    if (val2) val2.innerText = "Metabolism & Body Composition";
    if (unit2) unit2.innerText = "";
    if (label3) label3.innerText = "Evidence Base:";
    if (cidLink) { cidLink.innerText = "Human Clinical Cohorts"; cidLink.removeAttribute("href"); cidLink.style.textDecoration = "none"; }
  } else if (itemType === "other") {
    if (pubchemBadge) { pubchemBadge.innerText = "🧘 Clinical Therapy"; pubchemBadge.className = "badge badge-type-cat"; }
    if (label1) label1.innerText = "Therapeutic Modality:";
    if (val1) val1.innerText = "Non-Pharmacological Intervention";
    if (label2) label2.innerText = "Clinical Scope:";
    if (val2) val2.innerText = "Therapeutic Lifestyle Protocol";
    if (unit2) unit2.innerText = "";
    if (label3) label3.innerText = "Evidence Base:";
    if (cidLink) { cidLink.innerText = "Controlled Clinical Trials"; cidLink.removeAttribute("href"); cidLink.style.textDecoration = "none"; }
  } else if (itemType === "foods") {
    if (pubchemBadge) { pubchemBadge.innerText = "🥑 Functional Food"; pubchemBadge.className = "badge badge-type-supp"; }
    if (label1) label1.innerText = "Food Classification:";
    if (val1) val1.innerText = "Whole Dietary Food Matrix";
    if (label2) label2.innerText = "Nutrient Profile:";
    if (val2) val2.innerText = "Bioactive Food Constituents";
    if (unit2) unit2.innerText = "";
    if (label3) label3.innerText = "Scientific Base:";
    if (cidLink) { cidLink.innerText = "Nutritional Cohort Trials"; cidLink.removeAttribute("href"); cidLink.style.textDecoration = "none"; }
  } else {
    // Supplements
    if (pData && (pData.cid || pData.formula)) {
      if (pubchemBadge) { pubchemBadge.innerText = pData.cid ? `🔬 PubChem CID: ${pData.cid}` : "🔬 PubChem Indexed"; pubchemBadge.className = "badge badge-pubchem"; }
      if (label1) label1.innerText = "Chemical Formula:";
      if (val1) val1.innerText = pData.formula || "Biochemical Molecule";
      if (label2) label2.innerText = "Molecular Weight:";
      if (val2) val2.innerText = pData.weight ? `${pData.weight}` : "N/A";
      if (unit2) unit2.innerText = "g/mol";
      if (label3) label3.innerText = "PubChem CID:";
      if (cidLink) {
        if (pData.cid) {
          cidLink.innerText = `CID ${pData.cid} ↗`;
          cidLink.href = `https://pubchem.ncbi.nlm.nih.gov/compound/${pData.cid}`;
          cidLink.style.textDecoration = "underline";
        } else {
          cidLink.innerText = "Biochemical Compound";
          cidLink.removeAttribute("href");
          cidLink.style.textDecoration = "none";
        }
      }
    } else {
      if (pubchemBadge) { pubchemBadge.innerText = "🌿 Botanical Extract"; pubchemBadge.className = "badge badge-safety-high"; }
      if (label1) label1.innerText = "Source:";
      if (val1) val1.innerText = "Standardized Botanical Phytocomplex";
      if (label2) label2.innerText = "Active Constituents:";
      if (val2) val2.innerText = "Synergistic Bioactive Bioflavonoids/Extracts";
      if (unit2) unit2.innerText = "";
      if (label3) label3.innerText = "Pharmacopeia:";
      if (cidLink) { cidLink.innerText = "Natural Medicine Monograph"; cidLink.removeAttribute("href"); cidLink.style.textDecoration = "none"; }
    }
  }

  document.getElementById("detail-summary").innerText = data.summary;

  // 2. Things to Know Card (At a Glance)
  const ttkCard = document.getElementById("things-to-know-card");
  const ttkVerdict = document.getElementById("ttk-verdict");
  const ttkBenefits = document.getElementById("ttk-benefits-list");
  const ttkDrawbacks = document.getElementById("ttk-drawbacks-list");
  const ttk = data.things_to_know;

  if (ttk && (ttk.verdict || (ttk.primary_benefits && ttk.primary_benefits.length > 0))) {
    if (ttkCard) ttkCard.classList.remove("hidden");
    if (ttkVerdict) {
      let cleanVerdict = (ttk.verdict || "Clinical evidence synthesis complete.")
        .replace(/at a standard daily dose of Follow structured dietary protocol guidelines\.?/gi, "following standard dietary protocol guidelines.")
        .replace(/at a standard daily dose of Follow/gi, "following");
      ttkVerdict.innerText = cleanVerdict;
    }
    
    if (ttkBenefits) {
      ttkBenefits.innerHTML = "";
      (ttk.primary_benefits || []).forEach(b => {
        const li = document.createElement("li");
        li.innerText = b;
        ttkBenefits.appendChild(li);
      });
    }

    if (ttkDrawbacks) {
      ttkDrawbacks.innerHTML = "";
      (ttk.potential_drawbacks || []).forEach(d => {
        const li = document.createElement("li");
        li.innerText = d;
        ttkDrawbacks.appendChild(li);
      });
    }
  } else if (ttkCard) {
    ttkCard.classList.add("hidden");
  }

  // 3. Human Effect Matrix
  currentSupplementMatrix = data.effect_matrix || [];
  currentHemCategory = "all";
  document.querySelectorAll(".hem-filter-btn").forEach(btn => {
    if (btn.dataset.cat === "all") btn.classList.add("active");
    else btn.classList.remove("active");
  });
  renderHemTable(currentSupplementMatrix);

  // 4. Dosage & Safety
  const dosage = data.dosage_guide || {};
  document.getElementById("dosage-rec").innerText = dosage.recommended_dose || dosage.standard_dose || "Standard clinical dose";
  document.getElementById("dosage-timing").innerText = dosage.timing || dosage.optimal_timing || "With meals or as directed";
  document.getElementById("dosage-forms").innerText = dosage.forms || "Standard pharmaceutical grade";
  document.getElementById("dosage-cycling").innerText = dosage.cycling_needed || dosage.cycling || "No cycling required";

  const safety = data.safety_data || {};
  const safetyRatingText = safety.safety_rating || safety.status || "High Safety Profile";
  document.getElementById("safety-rating").innerText = safetyRatingText;

  // Dynamic Safety Badge on Top
  const safetyBadge = document.getElementById("safety-badge");
  if (safetyBadge) {
    safetyBadge.innerText = `Safety: ${safetyRatingText}`;
    safetyBadge.className = "badge";
    const srLower = safetyRatingText.toLowerCase();
    if (srLower.includes("caution") || srLower.includes("risk") || srLower.includes("supervision") || srLower.includes("adverse")) {
      safetyBadge.classList.add("badge-safety-caution");
    } else if (srLower.includes("moderate") || srLower.includes("monitor")) {
      safetyBadge.classList.add("badge-safety-mod");
    } else {
      safetyBadge.classList.add("badge-safety-high");
    }
  }

  // Tolerable Upper Limit (UL)
  const safetyUlEl = document.getElementById("safety-upper-limit");
  if (safetyUlEl) {
    safetyUlEl.innerText = safety.upper_limit || "Not established / Follow standard recommended dose";
  }

  // Common Side Effects list
  const sideEffectsList = document.getElementById("side-effects-list");
  sideEffectsList.innerHTML = "";
  let sideEffects = [];
  if (Array.isArray(safety.common_side_effects)) {
    sideEffects = safety.common_side_effects;
  } else if (Array.isArray(safety.side_effects)) {
    sideEffects = safety.side_effects;
  } else if (typeof safety.side_effects === "string" && safety.side_effects.trim()) {
    sideEffects = safety.side_effects.split(/[,;\n]+/).map(s => s.trim()).filter(s => s.length > 0);
  } else if (typeof safety.common_side_effects === "string" && safety.common_side_effects.trim()) {
    sideEffects = safety.common_side_effects.split(/[,;\n]+/).map(s => s.trim()).filter(s => s.length > 0);
  }
  if (sideEffects.length === 0) {
    sideEffects = ["Generally well tolerated at clinical dosages with low adverse event rates."];
  }
  sideEffects.forEach(effect => {
    const li = document.createElement("li");
    li.innerText = effect;
    sideEffectsList.appendChild(li);
  });
  document.getElementById("contraindications").innerText = safety.contraindications || "Consult a physician before use if you have pre-existing medical conditions.";

  // Interactive FAQs Accordion
  const faqsSection = document.getElementById("faqs-section");
  const faqsAccordion = document.getElementById("faqs-accordion");
  if (faqsAccordion) {
    faqsAccordion.innerHTML = "";
    const faqs = data.faqs || [];
    if (faqs.length > 0) {
      if (faqsSection) faqsSection.classList.remove("hidden");
      faqs.forEach((faq, idx) => {
        const item = document.createElement("div");
        item.className = "faq-item";
        if (idx === 0) item.classList.add("open");

        const qBtn = document.createElement("button");
        qBtn.type = "button";
        qBtn.className = "faq-question-btn";
        qBtn.innerHTML = `<span>❓ ${escapeHtml(faq.question)}</span><span class="faq-icon">${idx === 0 ? "−" : "+"}</span>`;
        qBtn.onclick = () => {
          const isOpen = item.classList.toggle("open");
          qBtn.querySelector(".faq-icon").innerText = isOpen ? "−" : "+";
        };

        const ansBox = document.createElement("div");
        ansBox.className = "faq-answer-box";
        ansBox.innerHTML = `<p>${escapeHtml(faq.answer)}</p>`;

        item.appendChild(qBtn);
        item.appendChild(ansBox);
        faqsAccordion.appendChild(item);
      });
    } else {
      if (faqsSection) faqsSection.classList.add("hidden");
    }
  }

  // Studies List (PubMed)
  const studiesList = document.getElementById("studies-list");
  studiesList.innerHTML = "";
  const studies = data.studies || [];
  document.getElementById("studies-count").innerText = `${studies.length} studies`;

  if (studies.length === 0) {
    studiesList.innerHTML = `<div style="color: var(--gray-500); padding: 1rem;">PubMed citations compiled in Human Effect Matrix above.</div>`;
  } else {
    studies.forEach(s => {
      const item = document.createElement("div");
      item.className = "study-item";
      item.innerHTML = `
        <a href="${s.url}" target="_blank" class="study-title">${escapeHtml(s.title)}</a>
        <div class="study-meta">
          <span>📚 ${escapeHtml(s.journal || "PubMed")}</span>
          <span>📅 ${s.year || "Peer-reviewed"}</span>
          <span>🔗 PMID: <strong>${s.pmid}</strong></span>
        </div>
      `;
      studiesList.appendChild(item);
    });
  }

  // ClinicalTrials.gov Human Trial Registry List
  const ctList = document.getElementById("clinical-trials-list");
  const ctCount = document.getElementById("clinical-trials-count");
  if (ctList && ctCount) {
    ctList.innerHTML = "";
    const trials = data.clinical_trials || [];
    ctCount.innerText = `${trials.length} registered trials`;

    if (trials.length === 0) {
      ctList.innerHTML = `<div style="color: var(--gray-500); padding: 1rem;">No registered human interventional trials retrieved for this query.</div>`;
    } else {
      trials.forEach(t => {
        const item = document.createElement("div");
        item.className = "study-item";
        const outcomesHtml = (t.primary_outcomes || []).map(o => `<div style="font-size:0.8rem; color:var(--gray-600); margin-top:4px;">🎯 Primary Endpoint: ${escapeHtml(o)}</div>`).join("");
        item.innerHTML = `
          <a href="${t.url}" target="_blank" class="study-title">🏛️ ${escapeHtml(t.title)}</a>
          <div class="study-meta" style="flex-wrap: wrap; gap: 8px; margin-top: 6px;">
            <span class="grade-badge grade-a" style="font-size: 0.75rem;">NCT: ${escapeHtml(t.nct_id)}</span>
            <span class="badge" style="background:#e0f2fe; color:#0369a1; font-weight:600;">👥 N=${t.sample_size || "N/A"}</span>
            <span class="badge" style="background:#f1f5f9; color:#475569;">🔬 ${escapeHtml(t.study_design || "Interventional")}</span>
            <span style="color: var(--gray-500); font-size: 0.8rem;">🏛️ ${escapeHtml(t.sponsor || "")}</span>
          </div>
          ${outcomesHtml}
        `;
        ctList.appendChild(item);
      });
    }
  }
}

function renderHemTable(matrixRows) {
  const matrixBody = document.getElementById("effect-matrix-body");
  if (!matrixBody) return;
  matrixBody.innerHTML = "";

  if (!matrixRows || matrixRows.length === 0) {
    matrixBody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--gray-500); padding: 2rem;">No effect matrix entries matching this category filter.</td></tr>`;
    return;
  }

  matrixRows.forEach(row => {
    const tr = document.createElement("tr");
    const grade = (row.evidence_grade || "B").toUpperCase();
    let gradeClass = "grade-b";
    if (grade === "A") gradeClass = "grade-a";
    if (grade === "C") gradeClass = "grade-c";
    if (grade === "D") gradeClass = "grade-d";

    const mag = row.magnitude || "Moderate";
    let magClass = "mag-mod";
    const magLower = mag.toLowerCase();
    if (magLower.includes("high") || magLower.includes("notable") || magLower.includes("strong")) magClass = "mag-high";
    if (magLower.includes("minor") || magLower.includes("small") || magLower.includes("modest")) magClass = "mag-min";
    if (magLower.includes("ineffective") || magLower.includes("no effect") || magLower.includes("none")) magClass = "mag-none";

    // Direction arrow
    let dir = (row.direction || "").toLowerCase();
    let dirBadge = "";
    if (dir === "increase" || dir === "up" || dir === "positive") {
      dirBadge = `<span class="dir-arrow dir-up" title="Increases / Improves outcome">⬆️</span>`;
    } else if (dir === "decrease" || dir === "down" || dir === "reduction") {
      dirBadge = `<span class="dir-arrow dir-down" title="Decreases / Reduces outcome">⬇️</span>`;
    } else if (dir === "neutral" || dir === "none") {
      dirBadge = `<span class="dir-arrow dir-neutral" title="Neutral / No significant change">➖</span>`;
    } else {
      if (magLower.includes("increase") || magLower.includes("enhance") || magLower.includes("boost")) {
        dirBadge = `<span class="dir-arrow dir-up" title="Increases / Improves outcome">⬆️</span>`;
      } else if (magLower.includes("decrease") || magLower.includes("reduc") || magLower.includes("lower")) {
        dirBadge = `<span class="dir-arrow dir-down" title="Decreases / Reduces outcome">⬇️</span>`;
      } else {
        dirBadge = `<span class="dir-arrow dir-up" title="Improves outcome">⬆️</span>`;
      }
    }

    const pmidLinks = (row.pmids || []).map(pmid => 
      `<a href="https://pubmed.ncbi.nlm.nih.gov/${pmid}/" target="_blank" class="pmid-badge" title="View PubMed Study">${pmid}</a>`
    ).join(" ");

    tr.innerHTML = `
      <td><strong>${escapeHtml(row.outcome)}</strong></td>
      <td><span class="synonym-tag">${escapeHtml(row.category || "General")}</span></td>
      <td><span class="mag-badge ${magClass}">${dirBadge} ${escapeHtml(mag)}</span></td>
      <td><span class="grade-badge ${gradeClass}" title="Evidence Level ${grade}">${grade}</span></td>
      <td>${row.study_count || 1} RCTs</td>
      <td>${escapeHtml(row.clinical_notes || "Clinical trial observed consistent outcome.")}</td>
      <td>${pmidLinks || "<span style='color: var(--gray-400);'>Direct citation</span>"}</td>
    `;
    matrixBody.appendChild(tr);
  });
}

function filterHemCategory(category) {
  currentHemCategory = category;
  document.querySelectorAll(".hem-filter-btn").forEach(btn => {
    if (btn.dataset.cat === category) btn.classList.add("active");
    else btn.classList.remove("active");
  });

  if (category === "all") {
    renderHemTable(currentSupplementMatrix);
    return;
  }

  const catLower = category.toLowerCase();
  const filtered = currentSupplementMatrix.filter(row => {
    const rowCat = (row.category || "").toLowerCase();
    if (category === "Physical Performance") {
      return rowCat.includes("performance") || rowCat.includes("exercise") || rowCat.includes("muscle") || rowCat.includes("power") || rowCat.includes("strength") || rowCat.includes("endurance");
    }
    if (category === "Brain & Focus") {
      return rowCat.includes("brain") || rowCat.includes("focus") || rowCat.includes("cognit") || rowCat.includes("memory") || rowCat.includes("mental") || rowCat.includes("mood");
    }
    if (category === "Sleep & Mood") {
      return rowCat.includes("sleep") || rowCat.includes("mood") || rowCat.includes("anxiety") || rowCat.includes("stress") || rowCat.includes("depress");
    }
    if (category === "Metabolic Health") {
      return rowCat.includes("metabol") || rowCat.includes("glucose") || rowCat.includes("lipid") || rowCat.includes("insulin") || rowCat.includes("weight") || rowCat.includes("fat");
    }
    if (category === "Heart & Longevity") {
      return rowCat.includes("heart") || rowCat.includes("cardio") || rowCat.includes("vascular") || rowCat.includes("blood pressure") || rowCat.includes("longevity");
    }
    return rowCat.includes(catLower);
  });

  renderHemTable(filtered);
}

// Category filter on directory
async function filterByCategory(category) {
  const pills = document.querySelectorAll(".category-pills .pill");
  pills.forEach(p => {
    if (category === "all" && p.innerText.includes("All")) p.classList.add("active");
    else if (category !== "all" && p.getAttribute("onclick")?.includes(category)) p.classList.add("active");
    else p.classList.remove("active");
  });

  const catSection = document.getElementById("category-results-section");
  const overviewSection = document.getElementById("supplements-overview-section");

  if (category === "all") {
    catSection.classList.add("hidden");
    overviewSection.classList.remove("hidden");
    return;
  }

  try {
    const res = await fetch(`/api/category/${encodeURIComponent(category)}`);
    const outcomes = await res.json();
    renderCategoryResults(category, outcomes);
    overviewSection.classList.add("hidden");
    catSection.classList.remove("hidden");
  } catch (e) {
    console.error("Failed to load category:", e);
  }
}

function renderCategoryResults(category, outcomes) {
  document.getElementById("category-title").innerText = `Outcomes for ${category}`;
  const tbody = document.getElementById("category-table-body");
  tbody.innerHTML = "";

  if (!outcomes || outcomes.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--gray-500); padding: 2rem;">No outcomes recorded under "${escapeHtml(category)}" yet.</td></tr>`;
    return;
  }

  outcomes.forEach(row => {
    const tr = document.createElement("tr");
    const grade = (row.evidence_grade || "B").toUpperCase();
    let gradeClass = "grade-b";
    if (grade === "A") gradeClass = "grade-a";
    if (grade === "C") gradeClass = "grade-c";

    const mag = row.magnitude || "Moderate";
    let magClass = "mag-mod";
    if (mag.toLowerCase().includes("high") || mag.toLowerCase().includes("notable")) magClass = "mag-high";
    if (mag.toLowerCase().includes("minor")) magClass = "mag-min";

    tr.innerHTML = `
      <td><a href="javascript:void(0)" onclick="viewSupplement('${row.supplement_slug}', true, { type: 'category', name: '${escapeHtml(category)}' })" style="font-weight: 700; color: var(--navy); text-decoration: underline;">${escapeHtml(row.supplement_name)}</a></td>
      <td><strong>${escapeHtml(row.outcome)}</strong></td>
      <td><span class="mag-badge ${magClass}">${escapeHtml(mag)}</span></td>
      <td><span class="grade-badge ${gradeClass}">${grade}</span></td>
      <td>${row.study_count || 1} RCTs</td>
      <td>${escapeHtml(row.clinical_notes || "")}</td>
    `;
    tbody.appendChild(tr);
  });
}

// =======================================================
// 2. CONDITIONS DIRECTORY
// =======================================================
async function loadConditions() {
  try {
    const res = await fetch("/api/conditions");
    currentConditions = await res.json();
    renderConditionsGrid(currentConditions);
  } catch (e) {
    console.error("Failed to load conditions:", e);
  }
}

function renderConditionsGrid(conditions) {
  const grid = document.getElementById("conditions-grid");
  grid.innerHTML = "";

  conditions.forEach(c => {
    const card = document.createElement("div");
    card.className = "condition-card";
    card.onclick = () => viewCondition(c.slug);

    const t1Names = (c.tier1_supplements || []).map(s => s.name).join(", ") || "Clinical interventions";

    card.innerHTML = `
      <div>
        <span class="condition-category-badge">${escapeHtml(c.category)}</span>
        <h3 class="condition-title">${escapeHtml(c.name)}</h3>
        <p class="condition-snippet">${escapeHtml(c.overview)}</p>
      </div>
      <div class="condition-preview-supps">
        <strong>Primary Interventions:</strong> ${escapeHtml(t1Names)}
      </div>
    `;
    grid.appendChild(card);
  });
}

async function viewCondition(slug, push = true, record = true) {
  if (record && !isInternalNavigation) {
    if (currentDetailView === "supplement") {
      recordNavigationState({ type: "supplement", slug: currentDetailSlug });
    } else if (currentDetailView === "condition" && currentDetailSlug !== slug) {
      recordNavigationState({ type: "condition", slug: currentDetailSlug });
    } else {
      recordNavigationState({ type: "tab", tab: currentTab });
    }
  }

  currentDetailView = "condition";
  currentDetailSlug = slug;
  updateNavControlStates();

  try {
    const res = await fetch(`/api/condition/${slug}`);
    if (!res.ok) return;
    const cond = await res.json();
    renderConditionDetail(cond);

    document.querySelectorAll(".main-content > div").forEach(el => el.classList.add("hidden"));
    document.getElementById("condition-detail-view").classList.remove("hidden");
    if (push) {
      pushRoute({ type: "condition", slug: slug }, `#/condition/${slug}`);
    }
    updateNavControlStates();
    window.scrollTo({ top: 0, behavior: "smooth" });
  } catch (e) {
    console.error("Error loading condition:", e);
  }
}

function renderConditionDetail(c) {
  document.getElementById("cond-name").innerText = c.name;
  document.getElementById("cond-category-badge").innerText = c.category;
  document.getElementById("cond-overview").innerText = c.overview;

  const condCrumb = document.getElementById("cond-crumb-name");
  if (condCrumb) condCrumb.innerText = c.name;

  // Tier 1
  const t1List = document.getElementById("cond-tier1-list");
  t1List.innerHTML = "";
  (c.tier1_supplements || []).forEach(s => {
    const suppSlug = findSupplementSlug(s.name);
    t1List.innerHTML += `
      <div class="tier-card clickable-supp" onclick="viewSupplement('${suppSlug}', true, { type: 'condition', slug: '${c.slug}', name: '${escapeHtml(c.name)}' })" title="Click to view full clinical monograph for ${escapeHtml(s.name)}">
        <div class="tier-card-header">
          <span class="tier-card-name">${escapeHtml(s.name)} →</span>
          <span class="grade-badge grade-a">${s.evidence || "A"}</span>
        </div>
        <div class="tier-card-dose">💊 ${escapeHtml(s.dose || "")}</div>
        <p class="tier-card-notes">${escapeHtml(s.notes || "")}</p>
        <div style="margin-top: 6px; font-size: 0.75rem; color: var(--primary-dark); font-weight: 700;">View Clinical Monograph & Matrix →</div>
      </div>
    `;
  });

  // Tier 2
  const t2List = document.getElementById("cond-tier2-list");
  t2List.innerHTML = "";
  (c.tier2_supplements || []).forEach(s => {
    const suppSlug = findSupplementSlug(s.name);
    t2List.innerHTML += `
      <div class="tier-card clickable-supp" onclick="viewSupplement('${suppSlug}', true, { type: 'condition', slug: '${c.slug}', name: '${escapeHtml(c.name)}' })" title="Click to view full clinical monograph for ${escapeHtml(s.name)}">
        <div class="tier-card-header">
          <span class="tier-card-name">${escapeHtml(s.name)} →</span>
          <span class="grade-badge grade-b">${s.evidence || "B"}</span>
        </div>
        <div class="tier-card-dose">💊 ${escapeHtml(s.dose || "")}</div>
        <p class="tier-card-notes">${escapeHtml(s.notes || "")}</p>
        <div style="margin-top: 6px; font-size: 0.75rem; color: var(--primary-dark); font-weight: 700;">View Clinical Monograph & Matrix →</div>
      </div>
    `;
  });

  // Ineffective
  const t3List = document.getElementById("cond-ineffective-list");
  t3List.innerHTML = "";
  (c.ineffective_supplements || []).forEach(s => {
    t3List.innerHTML += `
      <div class="tier-card" style="border-left: 3px solid #ef4444;">
        <div class="tier-card-header">
          <span class="tier-card-name">${escapeHtml(s.name)}</span>
          <span class="grade-badge grade-d">D</span>
        </div>
        <p class="tier-card-notes">${escapeHtml(s.notes || "")}</p>
      </div>
    `;
  });

  // Lifestyle
  const lifeList = document.getElementById("cond-lifestyle-list");
  lifeList.innerHTML = "";
  (c.lifestyle_factors || []).forEach(f => {
    const li = document.createElement("li");
    li.innerText = f;
    lifeList.appendChild(li);
  });
}

// =======================================================
// 3. CATEGORIES DIRECTORY
// =======================================================
async function loadCategories() {
  try {
    const res = await fetch("/api/categories");
    currentCategories = await res.json();
    renderCategoriesGrid(currentCategories);
  } catch (e) {
    console.error("Failed to load categories:", e);
  }
}

function renderCategoriesGrid(categories) {
  const grid = document.getElementById("categories-grid");
  grid.innerHTML = "";

  categories.forEach(c => {
    const card = document.createElement("div");
    card.className = "category-card";
    card.onclick = () => {
      switchMainTab("supplements");
      filterByCategory(c.name);
    };

    const suppTags = (c.key_supplements || []).map(s => `<span class="synonym-tag">${escapeHtml(s)}</span>`).join("");

    card.innerHTML = `
      <div class="cat-card-icon">${c.icon}</div>
      <h3 class="cat-card-title">${escapeHtml(c.name)}</h3>
      <p class="cat-card-desc">${escapeHtml(c.description)}</p>
      <div class="cat-card-tags">${suppTags}</div>
    `;
    grid.appendChild(card);
  });
}

// =======================================================
// 4. PROTOCOL GUIDES
// =======================================================
async function loadGuides() {
  try {
    const res = await fetch("/api/guides");
    currentGuides = await res.json();
    renderGuidesGrid(currentGuides);
  } catch (e) {
    console.error("Failed to load guides:", e);
  }
}

function renderGuidesGrid(guides) {
  const grid = document.getElementById("guides-grid");
  grid.innerHTML = "";

  guides.forEach(g => {
    const card = document.createElement("div");
    card.className = "guide-card";
    card.onclick = () => viewGuide(g.slug);

    card.innerHTML = `
      <div>
        <span class="hero-tag">${escapeHtml(g.target_goal)}</span>
        <h3 class="guide-card-title">${escapeHtml(g.title)}</h3>
        <p class="guide-card-subtitle">${escapeHtml(g.subtitle)}</p>
        <p class="supp-card-desc">${escapeHtml(g.summary)}</p>
      </div>
      <div class="supp-card-footer">
        <span>⏱️ ${escapeHtml(g.reading_time)}</span>
        <span class="supp-card-link">Read Protocol →</span>
      </div>
    `;
    grid.appendChild(card);
  });
}

async function viewGuide(slug, push = true, record = true) {
  if (record && !isInternalNavigation) {
    if (currentDetailView === "supplement") {
      recordNavigationState({ type: "supplement", slug: currentDetailSlug });
    } else if (currentDetailView === "guide" && currentDetailSlug !== slug) {
      recordNavigationState({ type: "guide", slug: currentDetailSlug });
    } else {
      recordNavigationState({ type: "tab", tab: currentTab });
    }
  }

  currentDetailView = "guide";
  currentDetailSlug = slug;
  updateNavControlStates();

  try {
    const res = await fetch(`/api/guide/${slug}`);
    if (!res.ok) return;
    const guide = await res.json();
    renderGuideDetail(guide);

    document.querySelectorAll(".main-content > div").forEach(el => el.classList.add("hidden"));
    document.getElementById("guide-detail-view").classList.remove("hidden");
    if (push) {
      pushRoute({ type: "guide", slug: slug }, `#/guide/${slug}`);
    }
    updateNavControlStates();
    window.scrollTo({ top: 0, behavior: "smooth" });
  } catch (e) {
    console.error("Error loading guide:", e);
  }
}

function renderGuideDetail(g) {
  document.getElementById("guide-title").innerText = g.title;
  document.getElementById("guide-subtitle").innerText = g.subtitle;
  document.getElementById("guide-goal-tag").innerText = g.target_goal;
  document.getElementById("guide-reading-time").innerText = g.reading_time;
  document.getElementById("guide-summary-text").innerText = g.summary;

  const guideCrumb = document.getElementById("guide-crumb-name");
  if (guideCrumb) guideCrumb.innerText = g.title;

  // Phases
  const phasesCont = document.getElementById("guide-phases-container");
  phasesCont.innerHTML = "";
  (g.protocol_phases || []).forEach(p => {
    phasesCont.innerHTML += `
      <div class="guide-phase-card">
        <h4 class="phase-title">${escapeHtml(p.phase_title)}</h4>
        <div class="phase-action">💊 Protocol Action: ${escapeHtml(p.action)}</div>
        <p class="phase-rationale"><strong>Clinical Rationale:</strong> ${escapeHtml(p.rationale)}</p>
      </div>
    `;
  });

  // Stacks
  const stacksCont = document.getElementById("guide-stacks-container");
  stacksCont.innerHTML = "";
  (g.recommended_stacks || []).forEach(st => {
    const itemsHtml = st.items.map(i => {
      const suppSlug = findSupplementSlug(i);
      return `<li style="cursor: pointer; color: var(--navy); padding: 4px 0; transition: color 0.15s;" onmouseover="this.style.color='var(--primary)'" onmouseout="this.style.color='var(--navy)'" onclick="viewSupplement('${suppSlug}', true, { type: 'guide', slug: '${g.slug}', name: '${escapeHtml(g.title)}' })" title="Click to view monograph for ${escapeHtml(i)}">💊 ${escapeHtml(i)} <span style="font-size:0.75rem; color:var(--primary-dark); font-weight:700;">[View Matrix →]</span></li>`;
    }).join("");

    stacksCont.innerHTML += `
      <div class="info-card">
        <div class="card-header">
          <div class="card-icon">🧪</div>
          <h3>${escapeHtml(st.name)}</h3>
        </div>
        <ul class="effects-list" style="list-style: none; padding-left: 0;">${itemsHtml}</ul>
      </div>
    `;
  });

  // Lifestyle
  const lifeList = document.getElementById("guide-lifestyle-list");
  lifeList.innerHTML = "";
  (g.lifestyle_prerequisites || []).forEach(f => {
    const li = document.createElement("li");
    li.innerText = f;
    lifeList.appendChild(li);
  });
}

// =======================================================
// 5. SYMPTOM-TO-SUPPLEMENT AI CONSULTANT
// =======================================================
function setSymptomPreset(text) {
  const textarea = document.getElementById("symptoms-input-text");
  textarea.value = text;
  textarea.focus();
}

async function submitSymptomConsultation() {
  const textarea = document.getElementById("symptoms-input-text");
  const symptoms = textarea.value.trim();
  const btn = document.getElementById("symptom-submit-btn");
  const resultsCard = document.getElementById("symptom-results-container");

  if (!symptoms) {
    alert("Please describe your symptoms first.");
    return;
  }

  btn.disabled = true;
  btn.innerHTML = `<span class="spinner" style="width:16px; height:16px; margin-right:6px;"></span> Diagnosing Biological Drivers...`;

  try {
    const res = await fetch("/api/consult/symptoms", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symptoms: symptoms })
    });
    const data = await res.json();
    btn.disabled = false;
    btn.innerHTML = `<span>Run Biological Diagnostic & Formulate Stack →</span>`;

    if (!res.ok) {
      alert(data.detail || "Consultation failed.");
      return;
    }

    renderSymptomReport(data);
    resultsCard.classList.remove("hidden");
    resultsCard.scrollIntoView({ behavior: "smooth" });
  } catch (e) {
    btn.disabled = false;
    btn.innerHTML = `<span>Run Biological Diagnostic & Formulate Stack →</span>`;
    alert("Failed to connect to AI consultant.");
  }
}

function renderSymptomReport(data) {
  const bioAnalysis = document.getElementById("symptom-bio-analysis");
  
  // Display spelling correction notice if present
  const existingNotice = document.getElementById("symptom-typo-notice");
  if (existingNotice) existingNotice.remove();

  if (data.corrected_symptoms) {
    const notice = document.createElement("div");
    notice.id = "symptom-typo-notice";
    notice.style.cssText = "background: rgba(14, 165, 233, 0.08); border-left: 3px solid #0284c7; padding: 10px 14px; border-radius: 6px; margin-bottom: 16px; font-size: 0.9rem; color: #0369a1;";
    notice.innerHTML = `💡 <strong>Spelling Corrected:</strong> Analyzed health complaints as: <em>"${escapeHtml(data.corrected_symptoms)}"</em>`;
    bioAnalysis.parentElement.insertBefore(notice, bioAnalysis);
  }

  bioAnalysis.innerText = data.biological_analysis || "";
  
  const driversList = document.getElementById("symptom-drivers-list");
  driversList.innerHTML = "";
  (data.primary_drivers || []).forEach(d => {
    driversList.innerHTML += `<span class="driver-tag">⚡ ${escapeHtml(d)}</span>`;
  });

  // Tier 1
  const t1Cont = document.getElementById("symptom-tier1-cards");
  t1Cont.innerHTML = "";
  (data.tier1_protocol || []).forEach(p => {
    t1Cont.innerHTML += `
      <div class="tier-card" style="border-top: 3px solid var(--primary);">
        <div class="tier-card-header">
          <span class="tier-card-name">${escapeHtml(p.supplement_name)}</span>
          <span class="grade-badge grade-a">${escapeHtml(p.evidence_grade || "A")}</span>
        </div>
        <div class="tier-card-dose">💊 ${escapeHtml(p.exact_dosage)} • ${escapeHtml(p.timing)}</div>
        <div style="font-size: 0.8rem; font-weight:600; color:var(--gray-600); margin-bottom: 4px;">Target: ${escapeHtml(p.target_symptom)}</div>
        <p class="tier-card-notes">${escapeHtml(p.clinical_rationale)}</p>
      </div>
    `;
  });

  // Tier 2
  const t2Cont = document.getElementById("symptom-tier2-cards");
  t2Cont.innerHTML = "";
  (data.tier2_supportive || []).forEach(p => {
    t2Cont.innerHTML += `
      <div class="tier-card" style="border-top: 3px solid var(--grade-b);">
        <div class="tier-card-header">
          <span class="tier-card-name">${escapeHtml(p.supplement_name)}</span>
          <span class="grade-badge grade-b">${escapeHtml(p.evidence_grade || "B")}</span>
        </div>
        <div class="tier-card-dose">💊 ${escapeHtml(p.exact_dosage)} • ${escapeHtml(p.timing)}</div>
        <p class="tier-card-notes">${escapeHtml(p.clinical_rationale)}</p>
      </div>
    `;
  });

  // Avoid
  const avoidList = document.getElementById("symptom-avoid-list");
  avoidList.innerHTML = "";
  (data.what_to_avoid || []).forEach(item => {
    avoidList.innerHTML += `<li>${escapeHtml(item)}</li>`;
  });

  // Safety
  document.getElementById("symptom-safety-text").innerText = data.safety_warnings || "Consult with your physician prior to supplementation.";
}

// =======================================================
// 6. CUSTOM SUPPLEMENT FORMULATOR
// =======================================================
function initFormulator() {
  const container = document.getElementById("ingredient-rows-container");
  if (!container) return;
  container.innerHTML = "";
  addIngredientRow("Magnesium Glycinate", "300mg", "Bisglycinate Chelate");
  addIngredientRow("L-Theanine", "200mg", "Fermented Suntheanine");
  addIngredientRow("Apigenin", "50mg", "Chamomile Extract");
}

function addIngredientRow(name = "", dose = "", form = "Standard") {
  const container = document.getElementById("ingredient-rows-container");
  const row = document.createElement("div");
  row.className = "ingredient-row";
  row.innerHTML = `
    <input type="text" class="ing-name" placeholder="Ingredient (e.g. Creatine)" value="${escapeHtml(name)}" style="flex: 2;">
    <input type="text" class="ing-dose" placeholder="Dose (e.g. 5g)" value="${escapeHtml(dose)}" style="flex: 1;">
    <input type="text" class="ing-form" placeholder="Form (e.g. Monohydrate)" value="${escapeHtml(form)}" style="flex: 1.5;">
    <button class="row-delete-btn" onclick="this.parentElement.remove()" title="Remove Ingredient">×</button>
  `;
  container.appendChild(row);
}

function loadFormulaPreset(type) {
  const container = document.getElementById("ingredient-rows-container");
  container.innerHTML = "";

  if (type === "sleep") {
    document.getElementById("formula-name-input").value = "Deep Sleep PM Matrix";
    document.getElementById("formula-goal-input").value = "Slow-Wave Deep Sleep Architecture";
    addIngredientRow("Magnesium Glycinate", "300mg", "Bisglycinate Chelate");
    addIngredientRow("L-Theanine", "200mg", "Suntheanine");
    addIngredientRow("Apigenin", "50mg", "Standardized Extract");
    addIngredientRow("Melatonin", "0.3mg", "Immediate Release");
  } else if (type === "focus") {
    document.getElementById("formula-name-input").value = "Executive Focus & Memory";
    document.getElementById("formula-goal-input").value = "Working Memory & Neuro-Energy";
    addIngredientRow("Alpha-GPC", "300mg", "50% Powder");
    addIngredientRow("Creatine Monohydrate", "5g", "Micronized");
    addIngredientRow("L-Theanine", "200mg", "Pure");
    addIngredientRow("Caffeine Anhydrous", "100mg", "Standard");
  } else if (type === "joint") {
    document.getElementById("formula-name-input").value = "Joint Cartilage Restoration";
    document.getElementById("formula-goal-input").value = "Synovial Repair & Anti-Inflammatory";
    addIngredientRow("Curcumin Phytosome", "500mg", "Meriva");
    addIngredientRow("Boswellia Serrata", "100mg", "ApresFlex (AKBA)");
    addIngredientRow("Hydrolyzed Collagen", "10g", "Type I & II Peptides");
    addIngredientRow("Vitamin C", "50mg", "Ascorbic Acid");
  }
}

async function validateCustomFormula() {
  const name = document.getElementById("formula-name-input").value.trim() || "Custom Formula";
  const goal = document.getElementById("formula-goal-input").value.trim() || "Health Optimization";
  const target = document.getElementById("formula-target-input").value.trim() || "Adults";

  const rows = document.querySelectorAll(".ingredient-row");
  const ingredients = [];
  rows.forEach(r => {
    const ingName = r.querySelector(".ing-name").value.trim();
    const ingDose = r.querySelector(".ing-dose").value.trim();
    const ingForm = r.querySelector(".ing-form").value.trim();
    if (ingName && ingDose) {
      ingredients.push({ name: ingName, dose: ingDose, form: ingForm });
    }
  });

  if (ingredients.length === 0) {
    alert("Please add at least one ingredient with dosage.");
    return;
  }

  const btn = document.getElementById("validate-formula-btn");
  const sheet = document.getElementById("formula-audit-sheet");

  btn.disabled = true;
  btn.innerHTML = `<span class="spinner" style="width:16px; height:16px; margin-right:6px;"></span> Auditing Pharmacology & Synergy...`;

  try {
    const res = await fetch("/api/formulator/validate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: name,
        goal: goal,
        target_user: target,
        ingredients: ingredients
      })
    });
    const data = await res.json();
    btn.disabled = false;
    btn.innerHTML = `<span>Validate & Audit Formulation with AI →</span>`;

    if (!res.ok) {
      alert(data.detail || "Validation failed.");
      return;
    }

    lastValidatedFormula = {
      name: name,
      goal: goal,
      target_user: target,
      ingredients: ingredients,
      synergy_score: data.synergy_score || 85,
      safety_rating: data.safety_status || "Safe",
      evidence_grade: data.overall_evidence_grade || "Grade A",
      analysis_report: data
    };

    renderFormulaAudit(data);
    sheet.classList.remove("hidden");
    sheet.scrollIntoView({ behavior: "smooth" });
  } catch (e) {
    btn.disabled = false;
    btn.innerHTML = `<span>Validate & Audit Formulation with AI →</span>`;
    alert("Failed to connect to formulation engine.");
  }
}

function renderFormulaAudit(data) {
  document.getElementById("audit-formula-title").innerText = data.formula_name || "Formulation Audit";
  document.getElementById("audit-synergy-score").innerText = data.synergy_score || 85;
  document.getElementById("audit-evidence-grade").innerText = data.overall_evidence_grade || "Grade A";
  document.getElementById("audit-summary-text").innerText = data.executive_summary || "";

  // Synergies
  const synList = document.getElementById("audit-synergies-list");
  synList.innerHTML = "";
  (data.synergy_breakdown || []).forEach(syn => {
    synList.innerHTML += `
      <div class="synergy-item">
        <div class="synergy-compounds">⚡ ${escapeHtml(syn.compounds)}</div>
        <p class="synergy-desc">${escapeHtml(syn.mechanism)}</p>
      </div>
    `;
  });

  // Safety Table
  const tbody = document.getElementById("audit-safety-tbody");
  tbody.innerHTML = "";
  (data.dosage_and_safety_audit || []).forEach(row => {
    const tr = document.createElement("tr");
    let statusClass = "mag-mod";
    if (row.status?.toLowerCase().includes("optimal")) statusClass = "mag-high";
    if (row.status?.toLowerCase().includes("danger") || row.status?.toLowerCase().includes("excess")) statusClass = "mag-none";

    tr.innerHTML = `
      <td><strong>${escapeHtml(row.ingredient)}</strong></td>
      <td>${escapeHtml(row.input_dose)}</td>
      <td>${escapeHtml(row.clinical_standard_range)}</td>
      <td>${escapeHtml(row.tolerable_upper_limit)}</td>
      <td><span class="mag-badge ${statusClass}">${escapeHtml(row.status)}</span></td>
      <td>${escapeHtml(row.comment)}</td>
    `;
    tbody.appendChild(tr);
  });

  // Delivery & Optimizations
  document.getElementById("audit-delivery-text").innerText = data.delivery_and_manufacturing_advice || "";
  const optList = document.getElementById("audit-optimizations-list");
  optList.innerHTML = "";
  (data.optimization_recommendations || []).forEach(opt => {
    optList.innerHTML += `<li>${escapeHtml(opt)}</li>`;
  });
}

async function saveFormulaToLibrary() {
  if (!lastValidatedFormula) {
    alert("Please validate a formula first.");
    return;
  }
  try {
    const res = await fetch("/api/formulator/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(lastValidatedFormula)
    });
    if (res.ok) {
      alert("Formula saved successfully to your local library!");
      loadSavedFormulas();
    }
  } catch (e) {
    alert("Failed to save formula.");
  }
}

async function loadSavedFormulas() {
  try {
    const res = await fetch("/api/formulator/list");
    const formulas = await res.json();
    const grid = document.getElementById("saved-formulas-grid");
    grid.innerHTML = "";

    if (!formulas || formulas.length === 0) {
      grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--gray-500); padding: 1.5rem;">
        No custom formulas saved yet. Build your first stack above!
      </div>`;
      return;
    }

    formulas.forEach(f => {
      const card = document.createElement("div");
      card.className = "supp-card";
      const ingCount = (f.ingredients || []).length;
      card.innerHTML = `
        <div>
          <span class="hero-tag">Synergy Score: ${f.synergy_score}/100</span>
          <h3 class="supp-card-title">${escapeHtml(f.name)}</h3>
          <p class="supp-card-desc"><strong>Goal:</strong> ${escapeHtml(f.goal)}</p>
          <div style="font-size: 0.8rem; color: var(--gray-500); margin-top: 0.5rem;">Contains ${ingCount} ingredients</div>
        </div>
        <div class="supp-card-footer">
          <span>${escapeHtml(f.evidence_grade || "Grade A")}</span>
          <span class="supp-card-link">View Audit →</span>
        </div>
      `;
      card.onclick = () => {
        renderFormulaAudit(f.analysis_report);
        document.getElementById("formula-audit-sheet").classList.remove("hidden");
        document.getElementById("formula-audit-sheet").scrollIntoView({ behavior: "smooth" });
      };
      grid.appendChild(card);
    });
  } catch (e) {
    console.error("Failed to load formulas:", e);
  }
}

// =======================================================
// 7. LIVE RESEARCH FEED
// =======================================================
function filterFeedTopic(topic) {
  currentFeedTopic = topic;
  const pills = document.querySelectorAll(".feed-filter-bar .pill");
  pills.forEach(p => {
    if (p.getAttribute("onclick")?.includes(`'${topic}'`)) p.classList.add("active");
    else p.classList.remove("active");
  });
  loadLatestFeed(false);
}

async function loadLatestFeed(refresh = false) {
  const list = document.getElementById("feed-list");
  const loader = document.getElementById("feed-loading");

  loader.classList.remove("hidden");
  if (refresh) list.innerHTML = "";

  try {
    const res = await fetch(`/api/feed/latest?topic=${encodeURIComponent(currentFeedTopic)}&refresh=${refresh}`);
    const articles = await res.json();
    loader.classList.add("hidden");
    renderFeedArticles(articles);
  } catch (e) {
    loader.classList.add("hidden");
    list.innerHTML = `<div style="color: var(--gray-500); padding: 2rem; text-align: center;">Failed to load live PubMed research feed.</div>`;
  }
}

function renderFeedArticles(articles) {
  const list = document.getElementById("feed-list");
  list.innerHTML = "";

  if (!articles || articles.length === 0) {
    list.innerHTML = `<div style="text-align: center; color: var(--gray-500); padding: 3rem;">
      No studies loaded yet. Click <strong>"Refresh from PubMed"</strong> to fetch the latest trials!
    </div>`;
    return;
  }

  articles.forEach(art => {
    const card = document.createElement("div");
    card.className = "feed-card";

    const takeawayHtml = art.takeaway ? `
      <div class="takeaway-box">
        <div class="takeaway-label">🔬 Clinical Takeaway:</div>
        <div class="takeaway-text">${escapeHtml(art.takeaway)}</div>
      </div>
    ` : "";

    card.innerHTML = `
      <div class="feed-top-row">
        <span class="study-type-tag">${escapeHtml(art.study_type || "Clinical Study")}</span>
        <span class="feed-date">Published ${art.year} • PubMed PMID: ${art.pmid}</span>
      </div>
      <h3 class="feed-title"><a href="${art.url}" target="_blank">${escapeHtml(art.title)}</a></h3>
      <div class="feed-meta">
        <span>📚 ${escapeHtml(art.journal)}</span>
        <span>✍️ ${escapeHtml(art.authors || "")}</span>
      </div>
      ${takeawayHtml}
      <p class="feed-abstract-preview">${escapeHtml(art.abstract.slice(0, 320))}...</p>
      <div class="feed-footer">
        <span style="color: var(--gray-500);">US National Library of Medicine</span>
        <a href="${art.url}" target="_blank" class="chem-link" style="font-weight: 600;">Read Full Study on PubMed ↗</a>
      </div>
    `;
    list.appendChild(card);
  });
}

// =======================================================
// 8. ASK WALPAR-AI
// =======================================================
function setAiPrompt(text) {
  const textarea = document.getElementById("ai-question-input");
  textarea.value = text;
  textarea.focus();
}

async function submitAiQuestion() {
  const textarea = document.getElementById("ai-question-input");
  const question = textarea.value.trim();
  const btn = document.getElementById("ai-ask-btn");
  const container = document.getElementById("ai-response-container");
  const content = document.getElementById("ai-response-content");

  if (!question) {
    alert("Please enter a question.");
    return;
  }

  btn.disabled = true;
  btn.innerText = "Synthesizing Evidence...";
  container.classList.remove("hidden");
  content.innerHTML = `<div style="display:flex; align-items:center; gap:0.75rem; color:var(--gray-600); padding: 1rem 0;">
    <div class="spinner"></div> Consulting clinical trials and synthesizing evidence...
  </div>`;

  try {
    const res = await fetch("/api/ai/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: question })
    });
    const data = await res.json();
    btn.disabled = false;
    btn.innerText = "Ask Question →";

    if (res.ok) {
      let bannerHtml = "";
      if (data.resolved) {
        if (data.resolved.corrected_from) {
          bannerHtml += `<div style="background: rgba(14, 165, 233, 0.08); border-left: 3px solid #0284c7; padding: 8px 12px; border-radius: 6px; margin-bottom: 14px; font-size: 0.88rem; color: #0369a1;">
            💡 <strong>Spelling Corrected:</strong> Interpreted search <em>"${escapeHtml(data.resolved.corrected_from)}"</em> as <strong>${escapeHtml(data.resolved.canonical_name || '')}</strong>
          </div>`;
        }
        if (data.resolved.type === "external_compound") {
          bannerHtml += `<div style="background: rgba(16, 185, 129, 0.08); border-left: 3px solid #059669; padding: 8px 12px; border-radius: 6px; margin-bottom: 14px; font-size: 0.88rem; color: #047857;">
            🔬 <strong>Live Biochemical Registry:</strong> Retrieved real-time chemical & clinical trial data for <strong>${escapeHtml(data.resolved.canonical_name || '')}</strong> from PubChem & PubMed, and indexed it in your local encyclopedia.
          </div>`;
        }
      }

      const formattedAnswer = window.marked ? marked.parse(data.answer) : escapeHtml(data.answer);
      content.innerHTML = bannerHtml + formattedAnswer;
    } else {
      content.innerHTML = `<span style="color: #b91c1c;">${data.detail || "Error querying WalparAI"}</span>`;
    }
  } catch (e) {
    btn.disabled = false;
    btn.innerText = "Ask Question →";
    content.innerHTML = `<span style="color: #b91c1c;">Connection error with local server.</span>`;
  }
}

function copyAiResponse() {
  const content = document.getElementById("ai-response-content").innerText;
  navigator.clipboard.writeText(content).then(() => {
    alert("Answer copied to clipboard!");
  });
}

// =======================================================
// 9. LIVE GLOBAL & HERO SEARCH & AUTOCOMPLETE
// =======================================================
function setupSearch() {
  attachSearchInput("global-search-input", "search-dropdown");
  attachSearchInput("hero-search-input", "hero-search-dropdown", "hero-search-clear-btn");
}

function attachSearchInput(inputId, dropdownId, clearBtnId = null) {
  const input = document.getElementById(inputId);
  const dropdown = document.getElementById(dropdownId);
  const clearBtn = clearBtnId ? document.getElementById(clearBtnId) : null;
  if (!input || !dropdown) return;

  let debounceTimeout = null;
  let currentResults = [];
  let selectedIndex = -1;

  const updateClearBtn = () => {
    if (clearBtn) {
      if (input.value.trim().length > 0) clearBtn.classList.remove("hidden");
      else clearBtn.classList.add("hidden");
    }
  };

  input.addEventListener("input", () => {
    updateClearBtn();
    clearTimeout(debounceTimeout);
    const q = input.value.trim();

    if (q.length < 2) {
      dropdown.classList.add("hidden");
      dropdown.innerHTML = "";
      currentResults = [];
      selectedIndex = -1;
      return;
    }

    debounceTimeout = setTimeout(async () => {
      try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
        currentResults = await res.json();
        selectedIndex = -1;
        renderSearchDropdown(q, currentResults, dropdown);
      } catch (e) {
        console.error("Search error:", e);
      }
    }, 180);
  });

  input.addEventListener("keydown", (e) => {
    const items = dropdown.querySelectorAll(".search-item");
    if (e.key === "ArrowDown") {
      e.preventDefault();
      if (items.length > 0) {
        selectedIndex = (selectedIndex + 1) % items.length;
        items.forEach((it, idx) => {
          if (idx === selectedIndex) {
            it.classList.add("selected");
            it.scrollIntoView({ block: "nearest" });
          } else {
            it.classList.remove("selected");
          }
        });
      }
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      if (items.length > 0) {
        selectedIndex = (selectedIndex - 1 + items.length) % items.length;
        items.forEach((it, idx) => {
          if (idx === selectedIndex) {
            it.classList.add("selected");
            it.scrollIntoView({ block: "nearest" });
          } else {
            it.classList.remove("selected");
          }
        });
      }
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (selectedIndex >= 0 && selectedIndex < items.length) {
        items[selectedIndex].click();
      } else if (currentResults.length > 0) {
        selectSearchResult(currentResults[0], dropdown);
      } else if (input.value.trim().length >= 2) {
        dropdown.classList.add("hidden");
        openNewSupplementModal(input.value.trim());
      }
    } else if (e.key === "Escape") {
      dropdown.classList.add("hidden");
    }
  });

  document.addEventListener("click", (e) => {
    if (!input.contains(e.target) && !dropdown.contains(e.target)) {
      dropdown.classList.add("hidden");
    }
  });
}

function clearHeroSearch() {
  const heroInput = document.getElementById("hero-search-input");
  const heroDropdown = document.getElementById("hero-search-dropdown");
  const clearBtn = document.getElementById("hero-search-clear-btn");
  if (heroInput) {
    heroInput.value = "";
    heroInput.focus();
  }
  if (heroDropdown) heroDropdown.classList.add("hidden");
  if (clearBtn) clearBtn.classList.add("hidden");
}

function triggerHeroSearch() {
  const heroInput = document.getElementById("hero-search-input");
  const heroDropdown = document.getElementById("hero-search-dropdown");
  if (!heroInput) return;
  const q = heroInput.value.trim();
  if (!q) {
    heroInput.focus();
    return;
  }
  fetch(`/api/search?q=${encodeURIComponent(q)}`)
    .then(r => r.json())
    .then(results => {
      if (results && results.length > 0) {
        selectSearchResult(results[0], heroDropdown);
      } else {
        openNewSupplementModal(q);
      }
    })
    .catch(() => openNewSupplementModal(q));
}

function searchBySuggestion(term) {
  const heroInput = document.getElementById("hero-search-input");
  const heroDropdown = document.getElementById("hero-search-dropdown");
  const clearBtn = document.getElementById("hero-search-clear-btn");
  if (!heroInput) return;
  heroInput.value = term;
  if (clearBtn) clearBtn.classList.remove("hidden");
  heroInput.focus();

  fetch(`/api/search?q=${encodeURIComponent(term)}`)
    .then(r => r.json())
    .then(results => {
      renderSearchDropdown(term, results, heroDropdown);
    })
    .catch(e => console.error(e));
}

function selectSearchResult(r, dropdown) {
  if (dropdown) dropdown.classList.add("hidden");
  const heroDropdown = document.getElementById("hero-search-dropdown");
  const searchDropdown = document.getElementById("search-dropdown");
  if (heroDropdown) heroDropdown.classList.add("hidden");
  if (searchDropdown) searchDropdown.classList.add("hidden");

  if (r.type === "condition") {
    viewCondition(r.slug);
  } else if (r.type === "category") {
    switchMainTab("supplements");
    filterByCategory(r.name);
  } else if (r.type === "guide") {
    viewGuide(r.slug);
  } else {
    viewSupplement(r.slug);
  }
}

function renderSearchDropdown(query, results, targetDropdown = null) {
  const dropdown = targetDropdown || document.getElementById("search-dropdown");
  if (!dropdown) return;
  dropdown.innerHTML = "";

  if (!results || results.length === 0) {
    const item = document.createElement("div");
    item.className = "search-item";
    item.innerHTML = `
      <div class="search-item-header">
        <span class="search-item-title">🔍 Analyze "${escapeHtml(query)}" with AI</span>
        <span class="search-type-badge badge-type-supp">AI Discovery</span>
      </div>
      <div class="search-item-desc">Not in local database yet. Click to query PubMed & PubChem in real-time.</div>
    `;
    item.onclick = () => {
      dropdown.classList.add("hidden");
      openNewSupplementModal(query);
    };
    dropdown.appendChild(item);
  } else {
    results.forEach(r => {
      const item = document.createElement("div");
      item.className = "search-item";

      let badgeHtml = "";
      if (r.type === "condition") {
        badgeHtml = `<span class="search-type-badge badge-type-cond">🩺 Condition</span>`;
      } else if (r.type === "category") {
        badgeHtml = `<span class="search-type-badge badge-type-cat">🏷️ Category</span>`;
      } else if (r.type === "guide") {
        badgeHtml = `<span class="search-type-badge badge-type-guide">📖 Guide</span>`;
      } else {
        badgeHtml = `<span class="search-type-badge badge-type-supp">💊 Supplement</span>`;
      }

      item.innerHTML = `
        <div class="search-item-header">
          <span class="search-item-title">${escapeHtml(r.name)}</span>
          ${badgeHtml}
        </div>
        <div class="search-item-desc">${escapeHtml(r.summary ? r.summary.slice(0, 95) + '...' : '')}</div>
      `;
      item.onclick = () => {
        selectSearchResult(r, dropdown);
      };
      dropdown.appendChild(item);
    });
  }

  dropdown.classList.remove("hidden");
}

// =======================================================
// 10. MODALS & API SETTINGS
// =======================================================
function openSettingsModal() {
  document.getElementById("settings-modal").classList.remove("hidden");
  document.getElementById("settings-feedback").classList.add("hidden");
}

function closeSettingsModal() {
  document.getElementById("settings-modal").classList.add("hidden");
}

async function saveApiKey() {
  const geminiInput = document.getElementById("gemini-key-input");
  const ncbiInput = document.getElementById("ncbi-key-input");
  const feedback = document.getElementById("settings-feedback");

  const geminiKey = geminiInput.value.trim();
  const ncbiKey = ncbiInput.value.trim();

  try {
    const res = await fetch("/api/settings/apikey", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ api_key: geminiKey, ncbi_key: ncbiKey })
    });
    const data = await res.json();
    if (res.ok) {
      feedback.className = "feedback-msg success";
      feedback.innerText = "API keys updated successfully!";
      feedback.classList.remove("hidden");
      checkStatus();
      setTimeout(closeSettingsModal, 1200);
    } else {
      feedback.className = "feedback-msg error";
      feedback.innerText = data.detail || "Failed to save API keys.";
      feedback.classList.remove("hidden");
    }
  } catch (e) {
    feedback.className = "feedback-msg error";
    feedback.innerText = "Server error while saving API keys.";
    feedback.classList.remove("hidden");
  }
}

function openNewSupplementModal(defaultName = "") {
  document.getElementById("new-supp-modal").classList.remove("hidden");
  document.getElementById("new-supp-error").classList.add("hidden");
  document.getElementById("analyze-loading").classList.add("hidden");
  document.getElementById("start-analyze-btn").disabled = false;
  const input = document.getElementById("new-supp-input");
  input.value = defaultName;
  input.focus();
}

function closeNewSupplementModal() {
  document.getElementById("new-supp-modal").classList.add("hidden");
}

async function triggerNewAnalysis() {
  const input = document.getElementById("new-supp-input");
  const name = input.value.trim();
  const errDiv = document.getElementById("new-supp-error");
  const loadingDiv = document.getElementById("analyze-loading");
  const startBtn = document.getElementById("start-analyze-btn");

  if (!name) {
    errDiv.innerText = "Please enter a supplement name.";
    errDiv.classList.remove("hidden");
    return;
  }

  errDiv.classList.add("hidden");
  loadingDiv.classList.remove("hidden");
  startBtn.disabled = true;

  const step1 = document.getElementById("step-1");
  const step2 = document.getElementById("step-2");
  const step3 = document.getElementById("step-3");

  step1.className = "step active";
  step2.className = "step";
  step3.className = "step";

  setTimeout(() => {
    step1.className = "step";
    step2.className = "step active";
  }, 1500);

  setTimeout(() => {
    step2.className = "step";
    step3.className = "step active";
  }, 3500);

  try {
    const res = await fetch("/api/supplement/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: name })
    });
    const data = await res.json();

    if (!res.ok) {
      loadingDiv.classList.add("hidden");
      startBtn.disabled = false;
      errDiv.innerText = data.detail || "Analysis failed.";
      errDiv.classList.remove("hidden");
      return;
    }

    closeNewSupplementModal();
    await loadSupplements();
    viewSupplement(data.slug);
  } catch (e) {
    loadingDiv.classList.add("hidden");
    startBtn.disabled = false;
    errDiv.innerText = "Server connection error.";
    errDiv.classList.remove("hidden");
  }
}

// Utility
function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
