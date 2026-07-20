"use strict";

const DATA = window.ABIA_APP_DATA;
const GROUP_LABELS = { PW: "Pregnant women", U5: "Children under 5", A5: "Age 5+" };
const INTERVENTION_NAMES = {
  CM: "Case management",
  IPTp: "IPTp",
  "Dual AI": "Dual-active-ingredient nets",
  Pyr: "Pyrethroid nets",
  PMC: "Perennial malaria chemoprevention",
  Vac: "Malaria vaccination",
  LSM: "Larval source management"
};

const state = {
  lga: Object.keys(DATA.metadata)[0],
  coverage: {},
  effectLevel: "base",
  costLevel: "base",
  exchangeRate: DATA.settings.usdToNgn,
  gradual: true,
  latestResult: null
};

const el = id => document.getElementById(id);
const formatNumber = value => Math.round(value).toLocaleString("en-NG");
const formatPercent = value => `${value.toFixed(1)}%`;
const formatNaira = value => {
  if (!Number.isFinite(value)) return "—";
  const abs = Math.abs(value);
  if (abs >= 1e9) return `₦${(value / 1e9).toFixed(2)}bn`;
  if (abs >= 1e6) return `₦${(value / 1e6).toFixed(2)}m`;
  if (abs >= 1e3) return `₦${(value / 1e3).toFixed(1)}k`;
  return `₦${Math.round(value).toLocaleString("en-NG")}`;
};

function initialize() {
  const select = el("lgaSelect");
  Object.keys(DATA.metadata).forEach(lga => {
    const option = document.createElement("option");
    option.value = lga;
    option.textContent = lga;
    select.appendChild(option);
  });
  select.value = state.lga;

  select.addEventListener("change", event => {
    state.lga = event.target.value;
    resetCoverage();
    renderLGA();
  });
  el("effectLevel").addEventListener("change", event => { state.effectLevel = event.target.value; recalculate(); });
  el("costLevel").addEventListener("change", event => { state.costLevel = event.target.value; recalculate(); });
  el("exchangeRate").addEventListener("input", event => {
    const value = Number(event.target.value);
    state.exchangeRate = Number.isFinite(value) && value > 0 ? value : DATA.settings.usdToNgn;
    recalculate();
  });
  el("gradualScaleUp").addEventListener("change", event => { state.gradual = event.target.checked; recalculate(); });
  el("resetButton").addEventListener("click", () => { resetCoverage(); renderSliders(); recalculate(); });
  document.querySelectorAll(".preset-button").forEach(button => {
    button.addEventListener("click", () => {
      const value = Number(button.dataset.value);
      DATA.metadata[state.lga].mix.forEach(i => state.coverage[i] = value);
      renderSliders();
      recalculate();
    });
  });
  el("downloadButton").addEventListener("click", downloadScenario);
  el("printButton").addEventListener("click", () => window.print());

  resetCoverage();
  renderLGA();
}

function resetCoverage() {
  state.coverage = {};
  DATA.metadata[state.lga].mix.forEach(i => state.coverage[i] = 0);
}

function renderLGA() {
  const meta = DATA.metadata[state.lga];
  el("lgaName").textContent = state.lga;
  el("prevalenceBadge").textContent = `Prevalence: ${meta.prevalence.toFixed(2)}%`;
  el("burdenBadge").textContent = `Burden: ${meta.burden}`;
  el("populationBadge").textContent = `Projected 2026 population: ${formatNumber(meta.population2026)}`;
  el("populationSource").textContent = `Population source: ${meta.populationSource}`;

  const badges = el("mixBadges");
  badges.innerHTML = "";
  meta.mix.forEach(intervention => {
    const badge = document.createElement("span");
    badge.className = "mix-badge";
    badge.textContent = `${intervention}: ${INTERVENTION_NAMES[intervention]}`;
    badges.appendChild(badge);
  });
  renderSliders();
  renderEvidence();
  recalculate();
}

function renderSliders() {
  const container = el("slidersContainer");
  container.innerHTML = "";
  DATA.metadata[state.lga].mix.forEach(intervention => {
    const item = document.createElement("div");
    item.className = "slider-item";
    const effectiveness = DATA.effectiveness[intervention][state.effectLevel] * 100;
    item.innerHTML = `
      <div class="slider-head">
        <span class="slider-title">${intervention} — ${INTERVENTION_NAMES[intervention]}</span>
        <span class="slider-value" id="value-${slug(intervention)}">${state.coverage[intervention]}%</span>
      </div>
      <input id="slider-${slug(intervention)}" type="range" min="0" max="100" step="1" value="${state.coverage[intervention]}" aria-label="${intervention} coverage" />
      <p class="slider-note">Modelled ${state.effectLevel} effectiveness: ${effectiveness.toFixed(0)}%; targets ${DATA.effectiveness[intervention].targets.map(g => GROUP_LABELS[g]).join(", ")}.</p>
    `;
    container.appendChild(item);
    const slider = item.querySelector("input");
    slider.addEventListener("input", event => {
      state.coverage[intervention] = Number(event.target.value);
      el(`value-${slug(intervention)}`).textContent = `${event.target.value}%`;
      recalculate();
    });
  });
}

function renderEvidence() {
  const container = el("evidenceList");
  container.innerHTML = "";
  DATA.metadata[state.lga].mix.forEach(intervention => {
    const e = DATA.effectiveness[intervention];
    const c = DATA.costs[intervention];
    const item = document.createElement("article");
    item.className = "evidence-item";
    item.innerHTML = `
      <h4>${intervention} — ${INTERVENTION_NAMES[intervention]}</h4>
      <p><strong>Effectiveness:</strong> low ${(e.low*100).toFixed(0)}%, base ${(e.base*100).toFixed(0)}%, high ${(e.high*100).toFixed(0)}%. ${e.note}</p>
      <p><strong>Cost unit:</strong> ${c.unit}. Base 2024 USD: $${c.base.toFixed(2)}.</p>
      <a href="${e.url}" target="_blank" rel="noopener">Effectiveness source</a> ·
      <a href="${c.url}" target="_blank" rel="noopener">Cost source</a>
    `;
    container.appendChild(item);
  });
}

function slug(value) { return value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, ""); }

function coverageAtMonth(intervention, monthIndex) {
  const target = (state.coverage[intervention] || 0) / 100;
  if (!state.gradual) return target;
  return target * Math.min((monthIndex + 1) / 12, 1);
}

function residualRisk(mix, group, monthIndex) {
  return mix.reduce((risk, intervention) => {
    const e = DATA.effectiveness[intervention];
    if (!e.targets.includes(group)) return risk;
    const coverage = coverageAtMonth(intervention, monthIndex);
    return risk * (1 - coverage * e[state.effectLevel]);
  }, 1);
}

function monthlyInterventionCost(intervention, coverage, meta, bauCases) {
  const unit = DATA.costs[intervention][state.costLevel];
  if (coverage <= 0) return 0;
  if (intervention === "CM") return coverage * bauCases * unit;
  if (intervention === "IPTp") return coverage * (meta.annualBirths2026 / 12) * unit;
  if (intervention === "PMC") return coverage * meta.under2Population2026 * unit / 12;
  if (intervention === "Vac") return coverage * (meta.annualBirths2026 / 12) * unit;
  if (intervention === "Pyr" || intervention === "Dual AI") return coverage * meta.population2026 * unit / 12;
  if (intervention === "LSM") return coverage * meta.population2026 * DATA.settings.lsmTargetableShare * unit / 12;
  return 0;
}

function calculateScenario() {
  const meta = DATA.metadata[state.lga];
  const forecast = DATA.forecasts[state.lga];
  const monthly = [];
  const groupAverted = { PW: 0, U5: 0, A5: 0 };
  let bauTotal = 0, scenarioTotal = 0, lowerTotal = 0, upperTotal = 0, programmeCostUsd = 0;

  forecast.forEach((row, monthIndex) => {
    let scenarioMonth = 0;
    let bauMonth = 0;
    ["PW", "U5", "A5"].forEach(group => {
      const bau = row[group];
      const risk = residualRisk(meta.mix, group, monthIndex);
      const scenario = bau * risk;
      bauMonth += bau;
      scenarioMonth += scenario;
      groupAverted[group] += Math.max(bau - scenario, 0);
    });
    meta.mix.forEach(intervention => {
      programmeCostUsd += monthlyInterventionCost(intervention, coverageAtMonth(intervention, monthIndex), meta, bauMonth);
    });
    bauTotal += bauMonth;
    scenarioTotal += scenarioMonth;
    lowerTotal += row.lower95;
    upperTotal += row.upper95;
    monthly.push({ date: row.date, bau: bauMonth, scenario: scenarioMonth, averted: bauMonth - scenarioMonth });
  });

  const casesAverted = Math.max(bauTotal - scenarioTotal, 0);
  const treatmentSavingsUsd = casesAverted * DATA.settings.treatmentCostSavedUsd2024;
  const netCostUsd = programmeCostUsd - treatmentSavingsUsd;
  const programmeCostNgn = programmeCostUsd * state.exchangeRate;
  const netCostNgn = netCostUsd * state.exchangeRate;
  const costPerCase = casesAverted > 0 ? netCostNgn / casesAverted : NaN;
  return {
    meta, monthly, groupAverted, bauTotal, scenarioTotal, lowerTotal, upperTotal,
    casesAverted, percentAverted: bauTotal > 0 ? casesAverted / bauTotal * 100 : 0,
    programmeCostUsd, programmeCostNgn, treatmentSavingsUsd, netCostUsd, netCostNgn, costPerCase
  };
}

function recalculate() {
  const result = calculateScenario();
  state.latestResult = result;
  el("bauCases").textContent = formatNumber(result.bauTotal);
  el("scenarioCases").textContent = formatNumber(result.scenarioTotal);
  el("casesAverted").textContent = formatNumber(result.casesAverted);
  el("percentAverted").textContent = `${formatPercent(result.percentAverted)} of forecast cases`;
  el("programmeCost").textContent = formatNaira(result.programmeCostNgn);
  el("costPerCase").textContent = result.casesAverted > 0 ? formatNaira(result.costPerCase) : "—";
  el("forecastRange").textContent = `${formatNumber(result.lowerTotal)}–${formatNumber(result.upperTotal)}`;
  updateDecision(result);
  drawLineChart(el("forecastChart"), result.monthly);
  drawBarChart(el("groupChart"), result.groupAverted);
}

function updateDecision(result) {
  const active = Object.entries(state.coverage).filter(([,v]) => v > 0);
  if (!active.length) {
    el("decisionTitle").textContent = "No additional scale-up selected";
    el("decisionText").textContent = `The ${state.lga} SARIMA business-as-usual forecast is ${formatNumber(result.bauTotal)} reported cases over 24 months. Move one or more recommended-intervention sliders to test a policy scenario.`;
    return;
  }
  const highest = [...active].sort((a,b) => b[1]-a[1])[0];
  const costText = result.costPerCase < 0 ? "cost-saving after treatment savings" : `${formatNaira(result.costPerCase)} net cost per case averted`;
  el("decisionTitle").textContent = `${formatNumber(result.casesAverted)} potential cases averted`;
  el("decisionText").textContent = `Under the selected additional coverage, the model projects a ${formatPercent(result.percentAverted)} reduction relative to BAU. The highest selected coverage is ${highest[0]} at ${highest[1]}%. Estimated programme cost is ${formatNaira(result.programmeCostNgn)}, with ${costText}.`;
}

function drawLineChart(canvas, rows) {
  const ctx = prepareCanvas(canvas);
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  const pad = { left: 64, right: 22, top: 24, bottom: 48 };
  const values = rows.flatMap(r => [r.bau, r.scenario]);
  const maxY = Math.max(...values, 1) * 1.1;
  drawAxes(ctx, width, height, pad, maxY, rows.length);
  plotSeries(ctx, rows.map(r=>r.bau), width, height, pad, maxY, "#1769aa", 3);
  plotSeries(ctx, rows.map(r=>r.scenario), width, height, pad, maxY, "#1f8a5b", 3);
  ctx.fillStyle = "#667789";
  ctx.font = "12px sans-serif";
  [0,5,11,17,23].forEach(i => {
    if (!rows[i]) return;
    const x = pad.left + i * (width-pad.left-pad.right)/(rows.length-1);
    ctx.textAlign = "center";
    ctx.fillText(formatMonth(rows[i].date), x, height-18);
  });
}

function drawBarChart(canvas, groupAverted) {
  const ctx = prepareCanvas(canvas);
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  const pad = { left: 54, right: 18, top: 24, bottom: 55 };
  const keys = ["PW","U5","A5"];
  const values = keys.map(k=>groupAverted[k]);
  const maxY = Math.max(...values,1) * 1.18;
  drawAxes(ctx, width, height, pad, maxY, keys.length);
  const areaW = width-pad.left-pad.right;
  const barW = Math.min(74, areaW/(keys.length*1.8));
  const colors = ["#e38b2c","#0b7d77","#1769aa"];
  keys.forEach((k,i)=>{
    const x = pad.left + areaW*(i+0.5)/keys.length - barW/2;
    const barH = values[i]/maxY*(height-pad.top-pad.bottom);
    const y = height-pad.bottom-barH;
    ctx.fillStyle = colors[i];
    roundedRect(ctx,x,y,barW,barH,6,true,false);
    ctx.fillStyle = "#172332";
    ctx.textAlign = "center";
    ctx.font = "bold 12px sans-serif";
    ctx.fillText(formatNumber(values[i]), x+barW/2, Math.max(y-8,14));
    ctx.font = "11px sans-serif";
    ctx.fillStyle = "#667789";
    wrapText(ctx,GROUP_LABELS[k],x+barW/2,height-32,100,13);
  });
}

function prepareCanvas(canvas) {
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = Math.max(300, Math.round(rect.width*dpr));
  canvas.height = Math.max(220, Math.round(rect.height*dpr));
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr,0,0,dpr,0,0);
  ctx.clearRect(0,0,rect.width,rect.height);
  return ctx;
}

function drawAxes(ctx,width,height,pad,maxY,count) {
  ctx.strokeStyle = "#dce5ed";
  ctx.lineWidth = 1;
  ctx.fillStyle = "#667789";
  ctx.font = "11px sans-serif";
  ctx.textAlign = "right";
  for (let i=0;i<=4;i++) {
    const y = pad.top + (height-pad.top-pad.bottom)*i/4;
    ctx.beginPath(); ctx.moveTo(pad.left,y); ctx.lineTo(width-pad.right,y); ctx.stroke();
    ctx.fillText(formatNumber(maxY*(1-i/4)),pad.left-8,y+4);
  }
  ctx.strokeStyle="#9fb0be";
  ctx.beginPath(); ctx.moveTo(pad.left,pad.top); ctx.lineTo(pad.left,height-pad.bottom); ctx.lineTo(width-pad.right,height-pad.bottom); ctx.stroke();
}

function plotSeries(ctx,values,width,height,pad,maxY,color,lineWidth) {
  ctx.strokeStyle=color; ctx.lineWidth=lineWidth; ctx.lineJoin="round"; ctx.lineCap="round";
  ctx.beginPath();
  values.forEach((v,i)=>{
    const x=pad.left+i*(width-pad.left-pad.right)/(values.length-1);
    const y=height-pad.bottom-v/maxY*(height-pad.top-pad.bottom);
    if(i===0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
  });
  ctx.stroke();
}

function roundedRect(ctx,x,y,w,h,r,fill,stroke){
  if(h<0){y+=h;h=Math.abs(h);} r=Math.min(r,w/2,h/2);
  ctx.beginPath(); ctx.moveTo(x+r,y); ctx.arcTo(x+w,y,x+w,y+h,r); ctx.arcTo(x+w,y+h,x,y+h,r); ctx.arcTo(x,y+h,x,y,r); ctx.arcTo(x,y,x+w,y,r); ctx.closePath();
  if(fill) ctx.fill(); if(stroke) ctx.stroke();
}
function wrapText(ctx,text,x,y,maxWidth,lineHeight){
  const words=text.split(" "); let line=""; let lines=[];
  words.forEach(word=>{const test=line+word+" "; if(ctx.measureText(test).width>maxWidth&&line){lines.push(line.trim());line=word+" ";}else line=test;});
  lines.push(line.trim()); lines.forEach((l,i)=>ctx.fillText(l,x,y+i*lineHeight));
}
function formatMonth(dateString){return new Date(`${dateString}T00:00:00`).toLocaleDateString("en-GB",{month:"short",year:"2-digit"});}

function downloadScenario() {
  const r = state.latestResult;
  if (!r) return;
  const coverages = Object.entries(state.coverage).map(([k,v])=>`${k}=${v}%`).join("; ");
  const header = ["LGA","Prevalence_percent","Burden","Recommended_mix","Coverage_settings","Effectiveness_level","Cost_level","Gradual_scale_up","Forecast_month","BAU_cases","Scenario_cases","Cases_averted"];
  const rows = r.monthly.map(m => [state.lga,r.meta.prevalence,r.meta.burden,`"${r.meta.mixText}"`,`"${coverages}"`,state.effectLevel,state.costLevel,state.gradual,m.date,m.bau.toFixed(4),m.scenario.toFixed(4),m.averted.toFixed(4)]);
  rows.push([]);
  rows.push(["SUMMARY"]);
  rows.push(["BAU_24m",r.bauTotal.toFixed(4)]);
  rows.push(["Scenario_cases_24m",r.scenarioTotal.toFixed(4)]);
  rows.push(["Cases_averted_24m",r.casesAverted.toFixed(4)]);
  rows.push(["Percent_averted",r.percentAverted.toFixed(4)]);
  rows.push(["Programme_cost_NGN",r.programmeCostNgn.toFixed(2)]);
  rows.push(["Net_cost_NGN",r.netCostNgn.toFixed(2)]);
  rows.push(["Net_cost_per_case_averted_NGN",Number.isFinite(r.costPerCase)?r.costPerCase.toFixed(2):""]);
  const csv = [header,...rows].map(row=>row.join(",")).join("\n");
  const blob = new Blob([csv],{type:"text/csv;charset=utf-8"});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a"); a.href=url; a.download=`${slug(state.lga)}_intervention_scenario.csv`; a.click(); URL.revokeObjectURL(url);
}

window.addEventListener("resize", () => { if(state.latestResult){ drawLineChart(el("forecastChart"),state.latestResult.monthly); drawBarChart(el("groupChart"),state.latestResult.groupAverted); } });
window.addEventListener("DOMContentLoaded", initialize);
