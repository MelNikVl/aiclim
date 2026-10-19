"use strict";

(() => {
  const byId = (id) => document.getElementById(id);
  const ui = Object.fromEntries([
    "mode-badge", "data-notice", "data-notice-text", "data-details", "data-details-list", "about-data-button", "discovery-form", "city-select",
    "category-select", "entity-search", "search-status", "search-spinner", "search-results",
    "selected-tastes", "taste-counter", "selection-hint", "discover-button", "discover-button-label",
    "replace-notice", "replace-text", "cancel-replace", "app-error", "app-error-text", "retry-config", "reset-scenario",
    "results-section", "results-title", "results-summary", "results-loading", "zone-cards", "changes-panel",
    "changes-message", "changes-items", "workflow-log", "warnings-list", "usage-summary", "request-id",
    "reset-exclusions", "clear-session", "search-suggestions",
  ].map((id) => [id, byId(id)]));
  const categories = { artist: "Music artist", movie: "Film", book: "Book", place: "Place" };
  const placeholders = {
    artist: "Search for an artist you love…", movie: "Search for a film you love…",
    book: "Search for a book you love…", place: "Search for a place you love…",
  };
  const state = { config: null, tastes: [], replaceIndex: null, results: null, excluded: new Set(), busy: false, resetting: false, searchTimer: null, searchAbort: null, searchVersion: 0, searchItems: [], dirty: false };
  const make = (tag, className, text) => {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (text !== undefined && text !== null) el.textContent = String(text);
    return el;
  };
  const limits = () => state.config?.limits || { min_interests: 3, max_interests: 5 };
  const isDemo = () => state.config?.mode === "demo";
  const safeText = (value, fallback = "") => typeof value === "string" ? value : fallback;
  const isValidSelection = () => state.tastes.length >= limits().min_interests && state.tastes.length <= limits().max_interests;

  async function api(path, options = {}) {
    let response;
    try { response = await fetch(path, { ...options, headers: { "Accept": "application/json", ...(options.body ? { "Content-Type": "application/json" } : {}), ...options.headers } }); }
    catch (error) { if (error.name === "AbortError") throw error; throw new Error("We couldn’t reach the discovery service. Check your connection and try again."); }
    let payload;
    try { payload = await response.json(); }
    catch { throw new Error("The service returned an unreadable response. Please try again."); }
    if (!response.ok) {
      const error = new Error(safeText(payload?.error?.message, "Something interrupted the discovery. Please try again."));
      error.code = safeText(payload?.error?.code);
      throw error;
    }
    return payload;
  }

  function showError(message, configRetry = false, scenarioReset = false) {
    ui["app-error-text"].textContent = message;
    ui["retry-config"].hidden = !configRetry;
    ui["reset-scenario"].hidden = !scenarioReset;
    ui["app-error"].hidden = false;
  }
  function clearError() { ui["app-error"].hidden = true; }

  function updateDataMode(hasLiveResults = false) {
    ui["mode-badge"].textContent = isDemo() ? "Demo data" : hasLiveResults ? "Live Qloo results" : "Qloo live mode configured";
    ui["data-notice-text"].textContent = isDemo()
      ? "Demo data · Real cultural labels, fictional places and synthetic affinities. Explore an illustrative experience, not verified city recommendations."
      : hasLiveResults
        ? "Live Qloo results · This discovery used a successful live Qloo response. Discovery zones are authored groupings, not official neighborhood boundaries. Check each place before visiting."
        : "Qloo live mode is configured. A successful real recommendation request is still needed to verify the integration. Discovery zones are authored groupings, not official neighborhood boundaries.";
  }

  async function loadConfig() {
    clearError();
    try {
      const config = await api("/api/config");
      if (!Array.isArray(config.cities) || !config.cities.length || !["demo", "live"].includes(config.mode)) throw new Error("The discovery service has no supported cities configured.");
      state.config = config;
      ui["city-select"].replaceChildren(...config.cities.map((city) => { const opt = make("option", "", city.name); opt.value = city.id; return opt; }));
      ui["city-select"].disabled = false;
      updateDataMode();
      ui["mode-badge"].classList.remove("is-error");
      ui["data-details-list"].replaceChildren(...(config.warnings || []).filter((warning) => typeof warning === "string").map((warning) => make("li", "", warning)));
      updateSelection();
    } catch (error) {
      state.config = null;
      ui["mode-badge"].textContent = "Service unavailable";
      ui["mode-badge"].classList.add("is-error");
      ui["data-notice-text"].textContent = "The discovery service is unavailable. Please try connecting again.";
      showError(error.message, true);
      updateSelection();
    }
  }

  function updateSelection() {
    const count = state.tastes.length;
    const min = limits().min_interests;
    const max = limits().max_interests;
    ui["taste-counter"].textContent = `${count} / ${max} selected`;
    ui["taste-counter"].classList.toggle("complete", isValidSelection());
    ui["selection-hint"].textContent = state.resetting ? "Starting a new discovery scenario…" : state.busy ? "Finding the places that follow your taste…" : count < min
      ? `Add ${min - count} ${count ? "more " : ""}favorite${min - count === 1 ? "" : "s"} to begin your discovery.`
      : state.results && state.dirty ? "Your taste has changed. Discover what’s different."
      : count === max ? "A full set of favorites. See where they take you." : "You’re ready. Add more favorites, or follow your taste.";
    ui["discover-button"].disabled = state.busy || !state.config || !isValidSelection();
    ui["discover-button-label"].textContent = state.resetting ? "Starting fresh…" : state.busy ? "Finding your places…" : state.results ? "Refresh my discoveries" : "Find my places";
    ui["selected-tastes"].replaceChildren(...state.tastes.map((taste, index) => {
      const chip = make("div", `taste-chip${state.replaceIndex === index ? " is-replacing" : ""}`);
      const replace = make("button", "replace-taste");
      replace.type = "button";
      replace.disabled = state.busy;
      replace.setAttribute("aria-label", `Replace ${taste.name}`);
      replace.title = `Replace this ${categories[taste.category]?.toLowerCase() || "favorite"}`;
      const icon = make("span", "", "↔"); icon.setAttribute("aria-hidden", "true");
      replace.append(make("span", "", taste.name), icon);
      replace.addEventListener("click", () => startReplace(index));
      const remove = make("button", "remove-taste", "×");
      remove.type = "button"; remove.disabled = state.busy;
      remove.setAttribute("aria-label", `Remove ${taste.name}`);
      remove.addEventListener("click", () => {
        state.tastes.splice(index, 1); state.dirty = true; cancelReplace(); updateSelection();
        ui["entity-search"].focus();
      });
      chip.append(replace, remove); return chip;
    }));
    ui["replace-notice"].hidden = state.replaceIndex === null;
    ui["entity-search"].disabled = state.busy;
    ui["category-select"].disabled = state.busy;
    ui["city-select"].disabled = state.busy || !state.config;
    ui["reset-exclusions"].hidden = state.excluded.size === 0;
    ui["reset-exclusions"].disabled = state.busy;
    ui["clear-session"].disabled = state.busy;
    ui["reset-scenario"].disabled = state.busy;
    ui["search-suggestions"].querySelectorAll("button").forEach((button) => { button.disabled = state.busy; });
  }

  function clearSearch() {
    clearTimeout(state.searchTimer);
    state.searchAbort?.abort();
    state.searchVersion += 1;
    state.searchItems = [];
    ui["entity-search"].value = "";
    ui["search-results"].replaceChildren();
    ui["search-results"].hidden = true;
    ui["search-status"].textContent = "";
    ui["search-spinner"].hidden = true;
  }
  function startReplace(index) {
    if (state.busy) return;
    clearSearch();
    state.replaceIndex = index;
    const taste = state.tastes[index];
    ui["category-select"].value = taste.category;
    ui["entity-search"].placeholder = placeholders[taste.category];
    ui["replace-text"].textContent = `Replacing “${taste.name}”. Search for a new favorite.`;
    updateSelection(); ui["entity-search"].focus();
  }
  function cancelReplace() { state.replaceIndex = null; ui["replace-notice"].hidden = true; updateSelection(); }

  function queueSearch() {
    clearTimeout(state.searchTimer);
    state.searchAbort?.abort();
    state.searchVersion += 1;
    ui["search-results"].hidden = true;
    ui["search-spinner"].hidden = true;
    const query = ui["entity-search"].value.trim();
    if (query.length < 2) { ui["search-status"].textContent = query ? "Keep typing—use at least 2 characters." : ""; return; }
    if (state.tastes.length >= limits().max_interests && state.replaceIndex === null) { ui["search-status"].textContent = "Your set is full. Select a favorite above to replace it, or remove one."; return; }
    ui["search-status"].textContent = "Searching favorites…";
    ui["search-spinner"].hidden = false;
    const version = state.searchVersion;
    state.searchTimer = setTimeout(() => performSearch(query, version), 280);
  }

  async function performSearch(query, version) {
    const controller = new AbortController(); state.searchAbort = controller;
    const category = ui["category-select"].value;
    try {
      const payload = await api(`/api/search?${new URLSearchParams({ q: query, category })}`, { signal: controller.signal });
      if (version !== state.searchVersion) return;
      if (!Array.isArray(payload.entities)) throw new Error("The search service returned an unexpected result. Please try another search.");
      state.searchItems = payload.entities.filter((entity) => typeof entity.id === "string" && typeof entity.name === "string" && typeof entity.token === "string");
      ui["search-results"].replaceChildren(...state.searchItems.map((entity) => {
        const row = make("li"); const button = make("button", "search-result-button");
        const alreadySelected = state.tastes.some((taste, i) => taste.id === entity.id && i !== state.replaceIndex);
        button.type = "button"; button.disabled = alreadySelected;
        const copy = make("span", "search-result-copy");
        copy.append(make("span", "search-result-name", entity.name), make("span", "search-result-subtitle", [categories[category], safeText(entity.subtitle), alreadySelected ? "Already selected" : ""].filter(Boolean).join(" · ")));
        const plus = make("span", "result-plus", alreadySelected ? "✓" : "+"); plus.setAttribute("aria-hidden", "true");
        button.append(copy, plus); button.addEventListener("click", () => addTaste(entity, category));
        row.append(button); return row;
      }));
      ui["search-results"].hidden = state.searchItems.length === 0;
      ui["search-status"].textContent = state.searchItems.length
        ? `${state.searchItems.length} match${state.searchItems.length === 1 ? "" : "es"}. Choose the exact favorite you mean.`
        : isDemo() ? "No demo matches. Try one of the example searches, or another category." : "No matches found. Try another title, spelling or category.";
    } catch (error) {
      if (error.name === "AbortError" || version !== state.searchVersion) return;
      ui["search-results"].hidden = true;
      ui["search-status"].textContent = error.message;
      if (error.code === "scenario_budget") showError(error.message, false, true);
    } finally { if (version === state.searchVersion) ui["search-spinner"].hidden = true; }
  }

  function addTaste(entity, category) {
    if (state.busy || state.tastes.some((taste, index) => taste.id === entity.id && index !== state.replaceIndex)) return;
    const taste = { id: entity.id, name: entity.name, token: entity.token, category };
    if (state.replaceIndex !== null) state.tastes[state.replaceIndex] = taste;
    else if (state.tastes.length < limits().max_interests) state.tastes.push(taste);
    else return;
    state.replaceIndex = null; state.dirty = true;
    clearSearch(); clearError(); updateSelection();
    ui["search-status"].textContent = `${entity.name} added to your taste.`;
    ui["entity-search"].focus();
  }

  function resultPlaceNames(result) {
    return new Map((result?.zones || []).flatMap((zone) => (zone.places || []).map((place) => [place.id, place.name])));
  }
  function scoreText(score) {
    return typeof score === "number" && Number.isFinite(score) ? String(Math.round(score)) : "—";
  }
  function coordinateLink(place) {
    const lat = place.latitude, lon = place.longitude;
    if (typeof lat !== "number" || typeof lon !== "number" || !Number.isFinite(lat) || !Number.isFinite(lon) || Math.abs(lat) > 90 || Math.abs(lon) > 180) return null;
    const link = make("a", "coordinate-link", isDemo() ? "View demo coordinate ↗" : "View coordinates ↗");
    link.href = `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lon}#map=16/${lat}/${lon}`;
    link.target = "_blank"; link.rel = "noopener noreferrer";
    link.setAttribute("aria-label", `${isDemo() ? "View demo coordinate" : "View coordinates"} for ${place.name} on OpenStreetMap (opens a new tab)`);
    return link;
  }
  function zoneCard(zone, index) {
    const isCityList = zone.id === "city-wide-picks";
    const card = make("article", `zone-card${isCityList ? " city-place-list" : ""}`);
    const top = make("div", "zone-card-top");
    const topLine = make("div", "zone-card-topline");
    const number = make("div"); number.append(make("div", "zone-number", isCityList ? "◎" : String(index + 1).padStart(2, "0")), make("div", "zone-kind", isCityList ? "CITY PLACE LIST" : "DISCOVERY ZONE"));
    const score = make("div", "app-score"); score.title = "Local app ranking score; not a compatibility probability.";
    score.setAttribute("aria-label", `App score: ${scoreText(zone.score)}. Not a compatibility probability.`);
    score.append(make("span", "score-value", scoreText(zone.score)), make("span", "score-label", "App score"));
    topLine.append(number); if (!isCityList) topLine.append(score);
    top.append(topLine, make("h3", "", safeText(zone.name, isCityList ? "City-wide picks" : "Discovery zone")));
    const body = make("div", "zone-card-body");
    if (zone.description) body.append(make("p", "zone-description", zone.description));
    if (zone.explanation) body.append(make("p", "zone-explanation", zone.explanation));
    const places = Array.isArray(zone.places) ? zone.places : [];
    body.append(make("p", "places-title", `${places.length} ${isDemo() ? "synthetic " : ""}place${places.length === 1 ? "" : "s"} to explore`));
    const list = make("ul", "places-list");
    places.forEach((place) => {
      const item = make("li", "place-item"); const heading = make("div", "place-heading");
      heading.append(make("h4", "place-name", safeText(place.name, "Place")));
      const exclude = make("button", "exclude-place", "×"); exclude.type = "button";
      exclude.setAttribute("aria-label", `Exclude ${place.name} and refresh discoveries`); exclude.title = "Exclude this place and discover again";
      exclude.addEventListener("click", async () => {
        if (state.busy) return;
        state.excluded.add(place.id); updateSelection();
        const success = await discover();
        if (!success) { state.excluded.delete(place.id); updateSelection(); }
      });
      heading.append(exclude); item.append(heading, make("p", "place-category", safeText(place.category, "Place").replaceAll("_", " ")));
      const link = coordinateLink(place); if (link) item.append(link);
      if (Array.isArray(place.evidence) && place.evidence.length) {
        const details = make("details", "place-evidence"); details.append(make("summary", "", "Why this place?"));
        const evidence = make("ul"); place.evidence.forEach((entry) => { if (typeof entry === "string") evidence.append(make("li", "", entry)); });
        details.append(evidence); item.append(details);
      }
      list.append(item);
    });
    body.append(list); card.append(top, body); return card;
  }

  function renderResults(result, previous) {
    updateDataMode(result.mode === "live");
    const zones = result.zones;
    const places = zones.flatMap((zone) => Array.isArray(zone.places) ? zone.places : []);
    const cityName = safeText(result.city?.name, "your city");
    const isCityList = zones.some((zone) => zone.id === "city-wide-picks");
    const zoneCount = Number.isInteger(result.coverage?.zone_count) ? result.coverage.zone_count : zones.length;
    const excludedNote = state.excluded.size ? ` · ${state.excluded.size} excluded` : "";
    ui["results-summary"].textContent = isCityList
      ? `Limited city-wide place list · ${places.length} ${isDemo() ? "synthetic " : ""}place${places.length === 1 ? "" : "s"} in ${cityName} query area${excludedNote}`
      : `${zoneCount} discovery zone${zoneCount === 1 ? "" : "s"} · ${places.length} ${isDemo() ? "synthetic " : ""}place${places.length === 1 ? "" : "s"} in ${cityName}${excludedNote}`;
    ui["zone-cards"].replaceChildren(...zones.slice(0, 3).map(zoneCard));
    if (!zones.length) {
      const empty = make("div", "empty-results"); empty.append(make("h3", "", "A little more curiosity needed."), make("p", "", "No places met the discovery requirements. Try replacing a favorite or restoring excluded places."));
      ui["zone-cards"].append(empty);
    }
    ui["changes-panel"].hidden = !previous;
    ui["changes-items"].replaceChildren();
    if (previous) {
      ui["changes-message"].textContent = safeText(result.changes?.message, "Compare these discoveries with your previous set.");
      const names = new Map([...resultPlaceNames(previous), ...resultPlaceNames(result)]);
      for (const [key, className, prefix] of [["added_places", "added", "+"], ["removed_places", "removed", "−"]]) {
        if (!Array.isArray(result.changes?.[key])) continue;
        result.changes[key].forEach((id) => ui["changes-items"].append(make("span", `change-item ${className}`, `${prefix} ${names.get(id) || id}`)));
      }
    }
    ui["workflow-log"].replaceChildren(...(Array.isArray(result.workflow) ? result.workflow : []).map((entry) => {
      const item = make("li", "workflow-item"); const warning = ["warning", "skipped", "insufficient", "limited"].includes(entry.status);
      const dot = make("span", `workflow-dot${warning ? " is-warning" : ""}`, warning ? "!" : "✓"); dot.title = safeText(entry.status); dot.setAttribute("aria-label", safeText(entry.status, "Complete"));
      const copy = make("div"); copy.append(make("span", "workflow-step", safeText(entry.step).replaceAll("_", " ")), make("p", "workflow-detail", safeText(entry.detail)));
      item.append(dot, copy); return item;
    }));
    const warnings = [...new Set([...(state.config?.warnings || []), ...(result.warnings || [])].filter((item) => typeof item === "string"))];
    if (isDemo()) warnings.unshift("Demo data: real cultural labels, fictional places, synthetic affinities and example scores. They do not establish real city coverage or Qloo performance.");
    ui["warnings-list"].replaceChildren(...warnings.map((warning) => make("li", "", warning)));
    ui["usage-summary"].textContent = `${result.usage?.qloo_requests ?? 0} Qloo requests · ${result.usage?.llm_calls ?? 0} LLM calls`;
    ui["request-id"].textContent = result.request_id ? `Discovery reference: ${result.request_id}` : "";
  }

  async function discover() {
    if (state.busy || !state.config || !isValidSelection()) return false;
    clearError(); clearSearch(); state.replaceIndex = null;
    state.busy = true; updateSelection();
    const previous = state.results;
    ui["results-section"].hidden = false;
    ui["results-section"].setAttribute("aria-busy", "true");
    ui["results-loading"].hidden = false;
    try {
      const result = await api("/api/recommend", { method: "POST", body: JSON.stringify({
        city_id: ui["city-select"].value,
        interest_tokens: state.tastes.map((taste) => taste.token),
        excluded_place_ids: [...state.excluded],
        previous_place_ids: [...resultPlaceNames(previous).keys()],
        previous_zone_ids: (previous?.zones || []).map((zone) => zone.id),
      }) });
      if (!Array.isArray(result.zones)) throw new Error("The service returned unexpected discoveries. Please try again.");
      renderResults(result, previous); state.results = result; state.dirty = false;
      ui["results-title"].focus({ preventScroll: true });
      ui["results-section"].scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth", block: "start" });
      return true;
    } catch (error) {
      showError(error.message, false, error.code === "scenario_budget");
      if (!previous) ui["results-section"].hidden = true;
      return false;
    } finally {
      state.busy = false; ui["results-loading"].hidden = true;
      ui["results-section"].removeAttribute("aria-busy"); updateSelection();
    }
  }

  async function resetSession(keepTastes = false) {
    if (state.busy) return;
    clearError(); clearSearch(); state.busy = true; state.resetting = true; updateSelection();
    try {
      await api("/api/session/reset", { method: "POST" });
      if (!keepTastes) state.tastes = [];
      state.results = null; state.excluded.clear(); state.replaceIndex = null; state.dirty = false;
      updateDataMode();
      ui["results-section"].hidden = true; ui["zone-cards"].replaceChildren();
      ui["search-status"].textContent = keepTastes ? "New scenario started. Your favorites are ready to discover again." : "A fresh start. Find a few things you love.";
      byId("taste-builder").scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (error) { showError(error.message, false, true); }
    finally { state.busy = false; state.resetting = false; updateSelection(); ui["entity-search"].focus(); }
  }

  ui["discovery-form"].addEventListener("submit", (event) => { event.preventDefault(); discover(); });
  ui["entity-search"].addEventListener("input", queueSearch);
  ui["entity-search"].addEventListener("keydown", (event) => {
    if (event.key === "ArrowDown" && !ui["search-results"].hidden) { event.preventDefault(); ui["search-results"].querySelector("button:not(:disabled)")?.focus(); }
    if (event.key === "Escape") { clearSearch(); if (state.replaceIndex !== null) cancelReplace(); }
    if (event.key === "Enter") { event.preventDefault(); if (!ui["search-results"].hidden) ui["search-results"].querySelector("button:not(:disabled)")?.focus(); }
  });
  ui["search-results"].addEventListener("keydown", (event) => {
    const buttons = [...ui["search-results"].querySelectorAll("button:not(:disabled)")];
    const index = buttons.indexOf(document.activeElement);
    if (event.key === "ArrowDown" || event.key === "ArrowUp") { event.preventDefault(); buttons[(index + (event.key === "ArrowDown" ? 1 : -1) + buttons.length) % buttons.length]?.focus(); }
    if (event.key === "Escape") { ui["search-results"].hidden = true; ui["entity-search"].focus(); }
  });
  ui["category-select"].addEventListener("change", () => { ui["entity-search"].placeholder = placeholders[ui["category-select"].value]; queueSearch(); });
  ui["city-select"].addEventListener("change", () => { state.excluded.clear(); state.dirty = true; updateSelection(); });
  ui["cancel-replace"].addEventListener("click", () => { clearSearch(); cancelReplace(); ui["entity-search"].focus(); });
  ui["retry-config"].addEventListener("click", loadConfig);
  ui["about-data-button"].addEventListener("click", () => {
    const opening = ui["data-details"].hidden;
    ui["data-details"].hidden = !opening;
    ui["about-data-button"].setAttribute("aria-expanded", String(opening));
  });
  ui["reset-exclusions"].addEventListener("click", async () => { const excluded = new Set(state.excluded); state.excluded.clear(); updateSelection(); if (!await discover()) { state.excluded = excluded; updateSelection(); } });
  ui["clear-session"].addEventListener("click", () => resetSession(false));
  ui["reset-scenario"].addEventListener("click", () => resetSession(true));
  ui["search-suggestions"].addEventListener("click", (event) => {
    const button = event.target.closest("button[data-query]"); if (!button || state.busy) return;
    ui["category-select"].value = button.dataset.category;
    ui["entity-search"].placeholder = placeholders[button.dataset.category];
    ui["entity-search"].value = button.dataset.query;
    queueSearch(); ui["entity-search"].focus();
  });
  loadConfig();
})();
