// Parity check script: extracts the JS scenario engine logic for Node.js comparison.
// Loads the same data files used by Python (model/archetypes.json, docs/occupations.json)
// and outputs JSON results to stdout for comparison with the Python engine.

'use strict';

const fs = require('fs');
const path = require('path');

// Load data
const archetypes = JSON.parse(
  fs.readFileSync(path.join(__dirname, '..', 'model', 'archetypes.json'), 'utf8')
);
const occData = JSON.parse(
  fs.readFileSync(path.join(__dirname, '..', 'docs', 'occupations.json'), 'utf8')
);
const occupations = occData.occupations;

// Copy the exact computeScenarioDemand logic from main.js.template
// adapted for Node.js (no DOM, no global `data`)
function computeScenarioDemand(targetMt) {
  if (!archetypes || archetypes.length === 0) return null;
  const archetype = archetypes[0]; // alkaline_1gw
  const units = targetMt / archetype.h2_output_mt_per_year;

  const results = {}; // occupation_id -> { demand, phases: { construction: N, ... } }

  for (const coeff of archetype.coefficients) {
    const rawDemand = units * coeff.headcount_per_unit;

    // Find matching occupations
    const matching = occupations.filter(
      occ => occ.nco_code && occ.nco_code.substring(0, 4) === coeff.nco_group
    );

    if (matching.length === 0) continue; // unallocated

    // Compute allocation weights
    const weights = matching.map(occ => {
      const scores = occ.scores || {};
      return (scores.h2_adjacency || 0) + (scores.transition_demand || 0);
    });
    const totalWeight = weights.reduce((a, b) => a + b, 0);

    matching.forEach((occ, i) => {
      const normWeight = totalWeight > 0 ? weights[i] / totalWeight : 1 / matching.length;
      const occDemand = Math.round(rawDemand * normWeight);

      if (!results[occ.id]) {
        results[occ.id] = { demand: 0, phases: {} };
      }
      results[occ.id].demand += occDemand;
      results[occ.id].phases[coeff.phase] =
        (results[occ.id].phases[coeff.phase] || 0) + occDemand;
    });
  }

  return results;
}

// Run for target MT from command line arg (default 5)
const targetMt = parseFloat(process.argv[2] || '5');
const result = computeScenarioDemand(targetMt);

// Output as JSON (sorted keys for stable comparison)
const output = {};
for (const [id, data] of Object.entries(result).sort()) {
  output[id] = { demand: data.demand, phases: data.phases };
}
console.log(JSON.stringify(output, null, 2));
