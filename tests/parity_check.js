'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const PROJECT_ROOT = path.join(__dirname, '..');
const modelDir = path.join(PROJECT_ROOT, 'model');
const docsDir = path.join(PROJECT_ROOT, 'docs');
const webTemplatePath = path.join(PROJECT_ROOT, 'web', 'main.js.template');

const archetypes = JSON.parse(fs.readFileSync(path.join(modelDir, 'archetypes.json'), 'utf8'));
const scenarios = JSON.parse(fs.readFileSync(path.join(modelDir, 'scenarios.json'), 'utf8'));
const clusters = JSON.parse(fs.readFileSync(path.join(modelDir, 'clusters.json'), 'utf8'));
const pathways = JSON.parse(fs.readFileSync(path.join(modelDir, 'pathways.json'), 'utf8'));
const occupations = JSON.parse(fs.readFileSync(path.join(docsDir, 'occupations.json'), 'utf8')).occupations;

function loadRuntime() {
  const source = fs.readFileSync(webTemplatePath, 'utf8');
  const sandbox = {
    console,
    module: { exports: {} },
    exports: {},
    setTimeout,
    clearTimeout,
  };
  sandbox.globalThis = sandbox;
  vm.runInNewContext(source, sandbox, { filename: webTemplatePath });
  return sandbox.module.exports || sandbox.H2AtlasRuntime;
}

const runtime = loadRuntime();

function findScenario(scenarioId) {
  const scenario = scenarios.find(item => item.id === scenarioId);
  if (!scenario) {
    throw new Error(`Unknown scenario: ${scenarioId}`);
  }
  return scenario;
}

function getScenarioPipeline(scenarioId, targetMtOverride) {
  const scenario = findScenario(scenarioId);
  const targetMt = targetMtOverride == null ? Number(scenario.target_mt || 0) : Number(targetMtOverride);
  const demandRecords = runtime.computeScenarioDemandRecords(
    scenario,
    targetMt,
    archetypes,
    occupations
  );
  const clusterRecords = runtime.distributeDemandByCluster(demandRecords, clusters);
  const timeline = runtime.computeTimeline(
    clusterRecords,
    Number(scenario.start_year || scenario.target_year || 0),
    Number(scenario.target_year || scenario.start_year || 0),
    archetypes,
    Number(scenario.target_year || scenario.start_year || 0) + 5
  );
  return { scenario, targetMt, demandRecords, clusterRecords, timeline };
}

function sortObjectEntries(input) {
  const output = {};
  for (const key of Object.keys(input).sort()) {
    output[key] = input[key];
  }
  return output;
}

function normaliseDemand(records) {
  return sortObjectEntries(runtime.aggregateDemandByOccupation(records));
}

function normaliseSingleArchetypeDemand(targetMt) {
  const records = runtime.computeDemandRecords(Number(targetMt), archetypes[0], occupations);
  const aggregated = normaliseDemand(records);
  const output = {};
  for (const occupationId of Object.keys(aggregated)) {
    const record = aggregated[occupationId];
    if (occupationId === '__unallocated__') {
      continue;
    }
    output[occupationId] = {
      demand: Number(record.demand || 0),
      phases: sortObjectEntries(record.phases || {}),
    };
  }
  return output;
}

function normaliseClusterRecords(records) {
  return records
    .map(record => ({
      occupation_id: record.occupation_id,
      archetype_id: record.archetype_id,
      nco_group: record.nco_group,
      phase: record.phase,
      demand: Number(record.demand || 0),
      allocation_weight: Number(record.allocation_weight || 0),
      source: record.source || '',
      source_type: record.source_type || '',
      cluster_id: record.cluster_id,
      cluster_name: record.cluster_name,
      state: record.state || '',
    }))
    .sort((left, right) => {
      const leftKey = [
        left.cluster_id,
        left.occupation_id || '',
        left.archetype_id || '',
        left.nco_group || '',
        left.phase || '',
      ].join('|');
      const rightKey = [
        right.cluster_id,
        right.occupation_id || '',
        right.archetype_id || '',
        right.nco_group || '',
        right.phase || '',
      ].join('|');
      return leftKey.localeCompare(rightKey);
    });
}

function countFullSnapshotRows(scenarioId, targetMtOverride) {
  const pipeline = getScenarioPipeline(scenarioId, targetMtOverride);
  const rows = runtime.buildFullSnapshotRows(
    runtime.buildOccupationIndex(occupations),
    pipeline.timeline,
    clusters,
    pathways,
    runtime.buildSupplyLookup(occupations)
  );
  return {
    count: rows.length,
    headers: runtime.EXPORT_HEADERS,
  };
}

function parseJsonArg(raw) {
  return raw ? JSON.parse(raw) : {};
}

function run() {
  const command = process.argv[2] || 'demand';
  let output;

  if (command === 'demand') {
    output = normaliseSingleArchetypeDemand(process.argv[3] || '5');
  } else if (command === 'cluster') {
    output = normaliseClusterRecords(getScenarioPipeline(process.argv[3], process.argv[4]).clusterRecords);
  } else if (command === 'timeline') {
    output = getScenarioPipeline(process.argv[3], process.argv[4]).timeline;
  } else if (command === 'dominant-phase') {
    output = runtime.dominantPhase(parseJsonArg(process.argv[3]));
  } else if (command === 'suggested-cluster') {
    output = runtime.getSuggestedClusterId(
      process.argv[3] || '',
      process.argv[4] ? parseJsonArg(process.argv[4]) : clusters
    );
  } else if (command === 'full-snapshot-row-count') {
    output = countFullSnapshotRows(process.argv[3], process.argv[4]);
  } else {
    throw new Error(`Unknown command: ${command}`);
  }

  process.stdout.write(JSON.stringify(output, null, 2));
}

run();
