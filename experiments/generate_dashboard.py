#!/usr/bin/env python3
"""
Generate interactive HTML dashboard from aggregated results.

Usage:
    python -m experiments.generate_dashboard --input test_results.json --output dashboard.html
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def generate_html_dashboard(aggregated_data: dict, output_path: Path):
    """Generate single-page interactive HTML dashboard."""
    
    metadata = aggregated_data.get("metadata", {})
    experiments = aggregated_data.get("experiments", {})
    models = aggregated_data.get("models", {})
    
    # Extract runs_dir and run_id from metadata
    runs_dir = Path(metadata.get("runs_dir", "experiments/runs"))
    run_id = metadata.get("run_id", "")
    
    # Extract experiment and model lists
    exp_names = sorted(experiments.keys())
    model_keys = sorted(models.keys())
    
    # Experiment descriptions (scientific framing)
    exp_descriptions = {
        "horn_yn_hornonly": "Goal-directed entailment task with matched Horn representation (baseline control)",
        "horn_yn_mixed": "Representation mismatch condition: Horn encoding on mixed problem set (tests robustness)",
        "cnf1_con_mixed": "Natural language CNF satisfiability (verbose encoding, tests NL scaffolding)",
        "cnf2_con_mixed": "Symbolic CNF satisfiability (compact encoding, tests symbolic reasoning)",
        "cnf1_con_hornonly": "NL-CNF on Horn subset (tests representation flexibility)",
        "cnf2_con_hornonly": "Symbolic-CNF on Horn subset (tests abstraction capability)",
    }
    
    # Research question details (from RESEARCH_QUESTIONS.md)
    rq_details = {
        "RQ1": {
            "title": "Representation Invariance in Logical Reasoning",
            "question": "Do LLMs exhibit representation-invariant logical reasoning, or is performance fundamentally bound to surface encodings?",
            "why_matters": "Tests whether models learn abstract logical principles vs. pattern matching; connects to debates about symbolic vs. neural reasoning; has implications for AI safety (robust reasoning across contexts).",
            "what_we_test": "Same logical problems in 3 representations (horn_if_then, cnf_v1, cnf_v2); compare accuracy on isomorphic problems with different encodings; measure representation sensitivity ΔAcc(repr_i, repr_j).",
            "expected": "Models show 5-15% accuracy variation across representations of identical logical content, suggesting representation-dependent reasoning rather than true abstraction.",
            "impact": "Challenges claims of 'emergent reasoning' in LLMs."
        },
        "RQ2": {
            "title": "Systematic Failure Modes Under Representation Mismatch",
            "question": "When representations mismatch problem structure, do models exhibit systematic failures or degrade randomly?",
            "why_matters": "Distinguishes between 'confused' vs. 'guessing' behavior; reveals whether models detect incompatibility; informs model robustness and error detection.",
            "what_we_test": "Horn representation on non-Horn problems (incompatible); measure error rate, unclear rate, systematic bias; analyze which specific problem types cause failures.",
            "expected": "Models exhibit systematic errors (20-40% unclear responses) rather than random guessing when faced with incompatible representations, suggesting partial problem detection but inability to recover.",
            "impact": "Reveals limitations in metacognitive awareness."
        },
        "RQ3": {
            "title": "Scaling Laws for Logical Complexity",
            "question": "How does reasoning accuracy scale with problem complexity, and do different models exhibit universal vs. model-specific scaling patterns?",
            "why_matters": "Analogous to scaling laws for training compute/data; predictive: can we forecast failure on unseen complexities?; theoretical: what determines reasoning capacity limits?",
            "what_we_test": "Accuracy vs. complexity (variables 4-20, clause length 2-5); fit power law: Acc(n) = A - B·n^α where n = complexity; compare α (decay exponent) across models.",
            "expected": "Model accuracy follows power-law decay: Acc(n) ≈ 0.98 - 0.15·(n/10)^1.8 for flagship models, with steeper exponents for budget models, suggesting universal scaling with model-dependent constants.",
            "impact": "First scaling law for logical reasoning in LLMs."
        },
        "RQ4": {
            "title": "Extended Deliberation: Error Correction vs. Qualitative Improvement",
            "question": "Does extended thinking (reasoning tokens) enable qualitatively different problem-solving strategies, or merely reduce errors on solvable problems?",
            "why_matters": "Fundamental question about System 1 vs. System 2 cognition; cost-benefit: when is slow thinking actually better?; mechanistic: what does 'thinking longer' buy you?",
            "what_we_test": "Same model with/without extended thinking; measure Δaccuracy by problem complexity; analyze threshold effects (complexity where thinking helps); qualitative analysis of reasoning traces.",
            "expected": "Extended thinking provides minimal benefit (<2%) on simple problems but critical gains (8-15%) beyond complexity threshold (>10 variables), suggesting extended deliberation enables systematic search rather than mere error reduction.",
            "impact": "Evidence for dual-process cognition in LLMs."
        },
        "RQ5": {
            "title": "Capacity-Complexity Phase Transitions",
            "question": "Do models exhibit sharp phase transitions in reasoning capability at specific complexity thresholds, or gradual degradation?",
            "why_matters": "Sharp transitions → discrete capacity limits; gradual decay → continuous scaling; predictability of failure modes.",
            "what_we_test": "Plot accuracy vs. complexity for all models; identify smooth decay vs. cliff-like drops; measure slope changes, inflection points; compare flagship vs. budget transition patterns.",
            "expected": "All models exhibit phase transitions at model-specific complexity thresholds (vars: 7-9 for budget, 12-15 for flagship), with accuracy dropping >20% within 2-variable increments, suggesting discrete capacity limits rather than continuous scaling.",
            "impact": "Reveals hard limits in reasoning capability."
        },
        "RQ6": {
            "title": "Cross-Task Transfer and Representation Learnability",
            "question": "Do models that excel at one representation type (e.g., Horn clauses) transfer that capability to others (CNF), or is performance representation-specific?",
            "why_matters": "Tests generalization vs. specialization; reveals whether models learn task-general reasoning; informs multi-task training strategies.",
            "what_we_test": "Rank models per representation type; measure rank correlation across representations; identify versatile generalists vs. specialized experts; analyze representation-specific failure patterns.",
            "expected": "Model rankings show weak correlation (ρ=0.4-0.6) across representations, with some models exhibiting versatile performance while others specialize in specific encodings, suggesting learned representation preferences.",
            "impact": "First evidence of representation specialization in LLMs."
        },
        "RQ7": {
            "title": "Satisfiability Bias and Asymmetric Error Patterns",
            "question": "Do models exhibit systematic bias toward satisfiable or unsatisfiable judgments, and does this bias reveal learned heuristics vs. true logical reasoning?",
            "why_matters": "Bias detection reveals whether models use shortcuts (e.g., 'usually satisfiable' heuristic) vs. proper logical analysis; asymmetric errors indicate reasoning gaps; critical for deployment reliability.",
            "what_we_test": "Compare accuracy on satisfiable vs. unsatisfiable problems separately; measure bias: (Acc_sat - Acc_unsat); analyze bias consistency across models and representations; check if bias correlates with problem complexity.",
            "expected": "Models show asymmetric performance with 10-20% higher accuracy on one class (likely unsatisfiable, as contradictions are easier to detect), revealing systematic bias rather than balanced reasoning. Bias magnitude correlates with model tier.",
            "impact": "Reveals whether models learn logical principles or statistical shortcuts; informs bias correction strategies."
        }
    }
    
    html = []
    
    # HTML header
    html.append("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LLM Logic Reasoning Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js" integrity="sha512-SIMGYRUjwY8+gKg7nn9EItdD8LCADSDfJNutF9TPrvEo86sQmFMh6MyralfIyhADlajSxqc7G0gs7+MwWF/ogQ==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
    <script>
        // Fallback check for Chart.js loading
        window.addEventListener('load', function() {
            if (typeof Chart === 'undefined') {
                console.error('Chart.js failed to load from CDN');
                document.querySelectorAll('canvas').forEach(function(canvas) {
                    canvas.parentElement.innerHTML = '<div class="note" style="background: #fff3cd; border-left: 3px solid #ffc107; padding: 15px;">⚠️ <strong>Chart.js failed to load.</strong> Charts require JavaScript enabled and CDN access. If viewing on GitHub, download the HTML file and open locally, or use the static analysis below.</div>';
                });
            }
        });
    </script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: #f5f7fa;
            padding: 20px;
            line-height: 1.6;
        }
        .container { max-width: 1600px; margin: 0 auto; }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        h1 { font-size: 2em; margin-bottom: 10px; }
        .subtitle { opacity: 0.9; font-size: 1.1em; }
        .section {
            background: white;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        h2 {
            color: #2d3748;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e2e8f0;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9em;
        }
        th, td {
            padding: 12px 8px;
            text-align: center;
            border: 1px solid #e2e8f0;
        }
        th {
            background: #f7fafc;
            font-weight: 600;
            color: #2d3748;
            position: sticky;
            top: 0;
            z-index: 10;
        }
        .exp-name {
            text-align: left;
            font-weight: 500;
            background: #f7fafc;
        }
        .acc-100 { background: #48bb78; color: white; font-weight: 600; }
        .acc-90 { background: #68d391; color: white; }
        .acc-75 { background: #f6e05e; }
        .acc-50 { background: #fc8181; color: white; }
        .acc-low { background: #f56565; color: white; font-weight: 600; }
        .model-header {
            writing-mode: vertical-rl;
            transform: rotate(180deg);
            white-space: nowrap;
            padding: 8px 4px;
            font-size: 0.85em;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }
        .stat-label {
            opacity: 0.9;
            font-size: 0.9em;
        }
        .rq-section {
            background: #f7fafc;
            padding: 20px;
            border-left: 4px solid #667eea;
            margin: 15px 0;
            border-radius: 4px;
        }
        .rq-title {
            color: #667eea;
            font-weight: 600;
            font-size: 1.1em;
            margin-bottom: 10px;
        }
        .finding {
            background: white;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
            border-left: 3px solid #48bb78;
        }
        .note {
            background: #fef5e7;
            border-left: 3px solid #f39c12;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }
        .footer {
            text-align: center;
            padding: 20px;
            color: #718096;
            font-size: 0.9em;
        }
        .filter-controls {
            background: #edf2f7;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .filter-controls label {
            margin-right: 15px;
            font-weight: 500;
        }
        .filter-controls select, .filter-controls input {
            margin-right: 20px;
            padding: 5px 10px;
            border-radius: 4px;
            border: 1px solid #cbd5e0;
        }
        .exp-description {
            font-size: 0.85em;
            color: #718096;
            font-style: italic;
            margin-top: 4px;
        }
        .rq-description {
            color: #4a5568;
            margin-bottom: 15px;
            font-style: italic;
        }
        .clickable-cell {
            cursor: pointer;
            transition: transform 0.1s;
        }
        .clickable-cell:hover {
            transform: scale(1.05);
            box-shadow: 0 0 10px rgba(0,0,0,0.2);
        }
        .rq-details {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 4px;
            padding: 15px;
            margin: 10px 0;
            display: none;
        }
        .rq-details.expanded {
            display: block;
        }
        .rq-toggle {
            cursor: pointer;
            color: #667eea;
            font-weight: 600;
            user-select: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            margin-top: 10px;
        }
        .rq-toggle:hover {
            color: #5568d3;
        }
        .rq-toggle-icon {
            transition: transform 0.2s;
        }
        .rq-toggle-icon.expanded {
            transform: rotate(90deg);
        }
        .rq-detail-section {
            margin: 10px 0;
        }
        .rq-detail-section strong {
            color: #667eea;
        }
    </style>
</head>
<body>
    <div class="container">
""")
    
    # Header
    run_id = metadata.get("run_id", "unknown")
    # Extract dataset info
    dataset = metadata.get("dataset", {})
    dataset_desc = f"Variables: {dataset.get('min_vars', '?')}-{dataset.get('max_vars', '?')}, Clause length: {dataset.get('min_len', '?')}-{dataset.get('max_len', '?')}"
    total_probs = dataset.get('total_problems', 0)
    horn_probs = dataset.get('horn_problems', 0)
    nonhorn_probs = dataset.get('nonhorn_problems', 0)
    sat_probs = dataset.get('sat_problems', 0)
    unsat_probs = dataset.get('unsat_problems', 0)
    
    html.append(f"""
        <header>
            <h1>🧠 LLM Logic Reasoning Dashboard</h1>
            <div class="subtitle">Systematic evaluation across representations, tasks, and models</div>
            <div class="subtitle">Run: {run_id}</div>
            <div class="subtitle" style="margin-top: 10px; font-size: 0.95em; opacity: 0.85;">
                Dataset: {total_probs} problems ({horn_probs} Horn, {nonhorn_probs} non-Horn | {sat_probs} SAT, {unsat_probs} UNSAT) | {dataset_desc}
            </div>
        </header>
""")
    
    # Stats overview
    total_exps = len(experiments)
    total_models = len(models)
    
    # Calculate overall stats
    all_correct = 0
    all_total = 0
    for exp_data in experiments.values():
        for model_data in exp_data["models"].values():
            all_correct += model_data["summary"].get("correct", 0)
            all_total += model_data["summary"].get("total", 0)
    
    overall_acc = all_correct / all_total * 100 if all_total > 0 else 0
    
    html.append(f"""
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Experiments</div>
                <div class="stat-value">{total_exps}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Model Configurations</div>
                <div class="stat-value">{total_models}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total Problems</div>
                <div class="stat-value">{total_probs}</div>
                <div class="stat-label" style="font-size: 0.8em; margin-top: 5px;">{horn_probs} Horn, {nonhorn_probs} non-Horn</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Complexity Range</div>
                <div class="stat-value">{dataset.get('min_vars', '?')}-{dataset.get('max_vars', '?')}</div>
                <div class="stat-label" style="font-size: 0.8em; margin-top: 5px;">vars, len {dataset.get('min_len', '?')}-{dataset.get('max_len', '?')}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Overall Accuracy</div>
                <div class="stat-value">{overall_acc:.0f}%</div>
                <div class="stat-label" style="font-size: 0.8em; margin-top: 5px;">{all_total} evaluations</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Balance</div>
                <div class="stat-value">{sat_probs}/{unsat_probs}</div>
                <div class="stat-label" style="font-size: 0.8em; margin-top: 5px;">SAT/UNSAT</div>
            </div>
        </div>
""")
    
    # Section 1: Overview Heatmap
    html.append("""
        <div class="section">
            <h2>📊 Overview Heatmap: Experiment × Model Performance</h2>
            <p style="margin-bottom: 15px;">Accuracy for each model on each experiment. Hover over cells to see details.</p>
            
            <div class="filter-controls">
                <label>
                    <strong>View:</strong>
                    <select id="viewMode" onchange="transposeHeatmap()">
                        <option value="exp-rows">Experiments as Rows, Models as Columns</option>
                        <option value="model-rows">Models as Rows, Experiments as Columns</option>
                    </select>
                </label>
                <label style="margin-left: 20px;">
                    <strong>Metric:</strong>
                    <select id="metricSelect" onchange="updateMetric()">
                        <option value="accuracy">Accuracy (%)</option>
                        <option value="correct">Correct Count</option>
                        <option value="unclear">Unclear Count</option>
                    </select>
                </label>
            </div>
            
            <div style="overflow-x: auto;">
                <table id="heatmapTable">
                    <thead>
                        <tr>
                            <th style="text-align: left;">Experiment</th>
""")
    
    # Model headers (vertical)
    for model_key in model_keys:
        parts = model_key.split("/")
        label = f"{parts[0][:3]}/{parts[1][:20]}/{parts[2]}"
        html.append(f'                            <th><div class="model-header">{label}</div></th>\n')
    
    html.append("""                        </tr>
                    </thead>
                    <tbody>
""")
    
    # Experiment rows
    for exp_name in exp_names:
        exp_data = experiments[exp_name]
        exp_desc = exp_descriptions.get(exp_name, "")
        html.append(f'                        <tr>\n')
        html.append(f'                            <td class="exp-name">{exp_name}<div class="exp-description">{exp_desc}</div></td>\n')
        
        for model_key in model_keys:
            if model_key in exp_data["models"]:
                model_info = exp_data["models"][model_key]
                acc = model_info["summary"].get("accuracy", 0)
                acc_pct = acc * 100
                total = model_info["summary"].get("total", 0)
                correct = model_info["summary"].get("correct", 0)
                unclear = model_info["summary"].get("unclear", 0)
                
                # Determine color class
                if acc_pct >= 95:
                    css_class = "acc-100"
                elif acc_pct >= 85:
                    css_class = "acc-90"
                elif acc_pct >= 70:
                    css_class = "acc-75"
                elif acc_pct >= 50:
                    css_class = "acc-50"
                else:
                    css_class = "acc-low"
                
                # Make cells interactive
                html.append(f'                            <td class="{css_class} clickable-cell" title="{correct}/{total} correct, {unclear} unclear" onclick="showDetails(\'{exp_name}\', \'{model_key}\')">{acc_pct:.0f}%</td>\n')
            else:
                html.append(f'                            <td>—</td>\n')
        
        html.append(f'                        </tr>\n')
    
    html.append("""                    </tbody>
                </table>
            </div>
            <div class="note">
                <strong>Color Legend:</strong> 
                🟩 Green (≥95%) | 🟨 Light Green (85-95%) | 🟡 Yellow (70-85%) | 🟧 Orange (50-70%) | 🟥 Red (<50%)
            </div>
        </div>
""")
    
    # Section 2: Research Questions
    html.append("""
        <div class="section">
            <h2>🔬 Research Questions Analysis</h2>
""")
    
    # RQ1: Representation
    horn_exps = [e for e in exp_names if 'horn_yn' in e]
    cnf_exps = [e for e in exp_names if 'cnf' in e]
    
    rq1 = rq_details["RQ1"]
    html.append(f"""
            <div class="rq-section">
                <div class="rq-title">RQ1: {rq1['title']}</div>
                <div class="rq-description">{rq1['question']}</div>
                <div class="rq-toggle" onclick="toggleRQ('rq1')">
                    <span class="rq-toggle-icon" id="rq1-icon">▶</span>
                    <span>Click for detailed research context</span>
                </div>
                <div class="rq-details" id="rq1-details">
                    <div class="rq-detail-section"><strong>Why it matters:</strong> {rq1['why_matters']}</div>
                    <div class="rq-detail-section"><strong>What we test:</strong> {rq1['what_we_test']}</div>
                    <div class="rq-detail-section"><strong>Expected finding:</strong> {rq1['expected']}</div>
                    <div class="rq-detail-section"><strong>Scientific impact:</strong> {rq1['impact']}</div>
                </div>
                <div class="finding">
""")
    
    if horn_exps and cnf_exps:
        horn_acc = sum(experiments[e]["summary"]["avg_accuracy"] for e in horn_exps) / len(horn_exps) * 100 if horn_exps else 0
        cnf_acc = sum(experiments[e]["summary"]["avg_accuracy"] for e in cnf_exps) / len(cnf_exps) * 100 if cnf_exps else 0
        html.append(f"""
                    <strong>Experimental Results:</strong> 
                    <ul style="margin-top: 10px; margin-left: 20px;">
                        <li>Horn representation (goal-directed): {horn_acc:.1f}% average accuracy</li>
                        <li>CNF representations (satisfiability): {cnf_acc:.1f}% average accuracy</li>
                        <li>Representation sensitivity (Δ): {abs(cnf_acc - horn_acc):.1f}% ({'CNF favored' if cnf_acc > horn_acc else 'Horn favored' if horn_acc > cnf_acc else 'representation-invariant'})</li>
                    </ul>
                    <div style="background: #edf2f7; padding: 12px; margin-top: 15px; border-left: 3px solid #667eea; border-radius: 4px;">
                        <strong>Interpretation:</strong> {'Models show significant representation sensitivity (Δ > 10%), indicating encoding-dependent rather than abstract reasoning.' if abs(cnf_acc - horn_acc) > 10 else 'Weak representation dependence (Δ < 10%) suggests partial abstraction capability.'}
                    </div>
                    <div class="note" style="margin-top: 10px;">
                        <strong>Data status:</strong> Based on {sum(experiments[e]['summary']['total_models'] for e in horn_exps + cnf_exps)} model×experiment configurations. Full validation will provide statistical significance tests.
                    </div>
""")
    
    rq2 = rq_details["RQ2"]
    html.append(f"""
                </div>
            </div>
            
            <div class="rq-section">
                <div class="rq-title">RQ2: {rq2['title']}</div>
                <div class="rq-description">{rq2['question']}</div>
                <div class="rq-toggle" onclick="toggleRQ('rq2')">
                    <span class="rq-toggle-icon" id="rq2-icon">▶</span>
                    <span>Click for detailed research context</span>
                </div>
                <div class="rq-details" id="rq2-details">
                    <div class="rq-detail-section"><strong>Why it matters:</strong> {rq2['why_matters']}</div>
                    <div class="rq-detail-section"><strong>What we test:</strong> {rq2['what_we_test']}</div>
                    <div class="rq-detail-section"><strong>Expected finding:</strong> {rq2['expected']}</div>
                    <div class="rq-detail-section"><strong>Scientific impact:</strong> {rq2['impact']}</div>
                </div>
""")
    
    if 'horn_yn_hornonly' in experiments and 'horn_yn_mixed' in experiments:
        matched_acc = experiments['horn_yn_hornonly']['summary']['avg_accuracy'] * 100
        mixed_acc = experiments['horn_yn_mixed']['summary']['avg_accuracy'] * 100
        penalty = matched_acc - mixed_acc
        
        html.append(f"""
                <div class="finding">
                    <strong>Experimental Results:</strong>
                    <ul style="margin-top: 10px; margin-left: 20px;">
                        <li>Matched condition (Horn on Horn): {matched_acc:.1f}%</li>
                        <li>Mismatch condition (Horn on mixed): {mixed_acc:.1f}%</li>
                        <li>Mismatch penalty (Δ): {penalty:.1f}% accuracy loss</li>
                    </ul>
                    <div style="background: #edf2f7; padding: 12px; margin-top: 15px; border-left: 3px solid #667eea; border-radius: 4px;">
                        <strong>Interpretation:</strong> {'Systematic failure mode detected (penalty > 10%) - models cannot gracefully handle incompatible representations, suggesting lack of robustness.' if penalty > 10 else 'Mild degradation (penalty < 10%) suggests partial robustness to representation mismatch.'}
                    </div>
                    <div class="note" style="margin-top: 10px;">
                        <strong>Data status:</strong> Based on {experiments['horn_yn_hornonly']['summary']['total_models'] + experiments['horn_yn_mixed']['summary']['total_models']} model configurations. Full validation will show error type distribution.
                    </div>
                </div>
""")
    
    rq3 = rq_details["RQ3"]
    html.append(f"""
            </div>
            
            <div class="rq-section">
                <div class="rq-title">RQ3: {rq3['title']}</div>
                <div class="rq-description">{rq3['question']}</div>
                <div class="rq-toggle" onclick="toggleRQ('rq3')">
                    <span class="rq-toggle-icon" id="rq3-icon">▶</span>
                    <span>Click for detailed research context</span>
                </div>
                <div class="rq-details" id="rq3-details">
                    <div class="rq-detail-section"><strong>Why it matters:</strong> {rq3['why_matters']}</div>
                    <div class="rq-detail-section"><strong>What we test:</strong> {rq3['what_we_test']}</div>
                    <div class="rq-detail-section"><strong>Expected finding:</strong> {rq3['expected']}</div>
                    <div class="rq-detail-section"><strong>Scientific impact:</strong> {rq3['impact']}</div>
                </div>
                <div class="finding">
                    <strong>Complexity-Dependent Performance:</strong>
                    <p style="margin: 10px 0;">See degradation curves below for visual analysis. Preliminary scaling pattern:</p>
                    <table style="width: 100%; margin-top: 10px;">
                        <thead>
                            <tr>
                                <th>Model Tier</th>
                                <th>Performance at Low Complexity<br>(vars 4-8)</th>
                                <th>Performance at High Complexity<br>(vars 15-20)</th>
                                <th>Scaling Pattern</th>
                            </tr>
                        </thead>
                        <tbody>
""")
    
    # Analyze by tier
    tiers = {
        "Tier 1 (Flagship)": [k for k in model_keys if any(x in k for x in ['sonnet', 'gemini-2.5-pro', 'gpt-5-pro'])],
        "Tier 2 (Medium)": [k for k in model_keys if any(x in k for x in ['opus', 'flash/think-med', 'gpt-5-2025'])],
        "Tier 3 (Budget+think)": [k for k in model_keys if 'think-low' in k],
        "Tier 3 (Budget no-think)": [k for k in model_keys if 'nothink' in k],
    }
    
    for tier_name, tier_models in tiers.items():
        if not tier_models:
            continue
        
        # Calculate average accuracy for low vs high complexity
        low_complex_acc = []
        high_complex_acc = []
        
        for model_key in tier_models:
            model_data = models[model_key]
            for exp_name in exp_names:
                if exp_name in experiments and model_key in experiments[exp_name]["models"]:
                    complexity = experiments[exp_name]["models"][model_key].get("complexity_breakdown", {})
                    
                    # Low complexity (vars 4-8)
                    for var in range(4, 9):
                        if str(var) in complexity:
                            acc = complexity[str(var)]["accuracy"]
                            low_complex_acc.append(acc)
                    
                    # High complexity (vars 15-20)
                    for var in range(15, 21):
                        if str(var) in complexity:
                            acc = complexity[str(var)]["accuracy"]
                            high_complex_acc.append(acc)
        
        low_avg = (sum(low_complex_acc) / len(low_complex_acc) * 100) if low_complex_acc else 0
        high_avg = (sum(high_complex_acc) / len(high_complex_acc) * 100) if high_complex_acc else 0
        degradation = low_avg - high_avg
        
        pattern = "Gradual decay" if degradation < 15 else "Sharp decline" if degradation > 30 else "Moderate decline"
        
        html.append(f"""                            <tr>
                                <td style="text-align: left;">{tier_name}</td>
                                <td class="acc-100">{low_avg:.0f}%</td>
                                <td class="{'acc-90' if high_avg >= 85 else 'acc-75' if high_avg >= 70 else 'acc-50'}">{high_avg:.0f}%</td>
                                <td>{pattern} ({degradation:.0f}% drop)</td>
                            </tr>
""")
    
    html.append(f"""                        </tbody>
                    </table>
                    <div style="background: #edf2f7; padding: 12px; margin-top: 15px; border-left: 3px solid #667eea; border-radius: 4px;">
                        <strong>Interpretation:</strong> Degradation curves (below) visualize the scaling relationship Acc(n) where n = complexity. Different degradation rates across tiers suggest model-specific capacity limits.
                    </div>
                    <div class="note" style="margin-top: 10px;">
                        <strong>Data status:</strong> Scaling patterns observable but limited sample. Full validation will enable fitting power-law models: Acc(n) ≈ A - B·n^α to predict breakdown thresholds.
                    </div>
                </div>
            </div>
            
            <div class="rq-section">
                <div class="rq-title">RQ4: {rq_details['RQ4']['title']}</div>
                <div class="rq-description">{rq_details['RQ4']['question']}</div>
                <div class="rq-toggle" onclick="toggleRQ('rq4')">
                    <span class="rq-toggle-icon" id="rq4-icon">▶</span>
                    <span>Click for detailed research context</span>
                </div>
                <div class="rq-details" id="rq4-details">
                    <div class="rq-detail-section"><strong>Why it matters:</strong> {rq_details['RQ4']['why_matters']}</div>
                    <div class="rq-detail-section"><strong>What we test:</strong> {rq_details['RQ4']['what_we_test']}</div>
                    <div class="rq-detail-section"><strong>Expected finding:</strong> {rq_details['RQ4']['expected']}</div>
                    <div class="rq-detail-section"><strong>Scientific impact:</strong> {rq_details['RQ4']['impact']}</div>
                </div>
                <div class="finding">
                    <table style="width: 100%; margin-top: 10px;">
                        <thead>
                            <tr>
                                <th>Model</th>
                                <th>With Thinking</th>
                                <th>Without Thinking</th>
                                <th>Delta</th>
                            </tr>
                        </thead>
                        <tbody>
""")
    
    # Compare models with/without thinking
    thinking_pairs = [
        ("claude-haiku-4-5-20251001", "think-low", "nothink"),
        ("gemini-2.5-flash-lite", "think-low", "nothink"),
    ]
    
    for base_model, with_think, without_think in thinking_pairs:
        # Find matching models
        with_key = [k for k in model_keys if base_model in k and with_think in k]
        without_key = [k for k in model_keys if base_model in k and without_think in k]
        
        if with_key and without_key:
            with_model = models[with_key[0]]
            without_model = models[without_key[0]]
            
            # Average across experiments
            with_accs = [exp["accuracy"] * 100 for exp in with_model["experiments"].values()]
            without_accs = [exp["accuracy"] * 100 for exp in without_model["experiments"].values()]
            
            with_avg = sum(with_accs) / len(with_accs) if with_accs else 0
            without_avg = sum(without_accs) / len(without_accs) if without_accs else 0
            delta = with_avg - without_avg
            
            html.append(f"""                            <tr>
                                <td style="text-align: left;">{base_model}</td>
                                <td>{with_avg:.0f}%</td>
                                <td>{without_avg:.0f}%</td>
                                <td style="font-weight: 600; color: {'green' if delta > 0 else 'red' if delta < 0 else 'black'};">{delta:+.0f}%</td>
                            </tr>
""")
    
    html.append(f"""                        </tbody>
                    </table>
                    <div style="background: #edf2f7; padding: 12px; margin-top: 15px; border-left: 3px solid #667eea; border-radius: 4px;">
                        <strong>Interpretation:</strong> Thinking benefit varies by model and task. Complexity-dependent analysis will reveal at which problem sizes extended deliberation becomes cost-effective.
                    </div>
                    <div class="note" style="margin-top: 10px;">
                        <strong>Data status:</strong> Limited sample size. Full validation will show thinking benefits stratified by complexity level (simple/medium/hard problems).
                    </div>
                </div>
            </div>
            
            <div class="rq-section">
                <div class="rq-title">RQ5: {rq_details['RQ5']['title']}</div>
                <div class="rq-description">{rq_details['RQ5']['question']}</div>
                <div class="rq-toggle" onclick="toggleRQ('rq5')">
                    <span class="rq-toggle-icon" id="rq5-icon">▶</span>
                    <span>Click for detailed research context</span>
                </div>
                <div class="rq-details" id="rq5-details">
                    <div class="rq-detail-section"><strong>Why it matters:</strong> {rq_details['RQ5']['why_matters']}</div>
                    <div class="rq-detail-section"><strong>What we test:</strong> {rq_details['RQ5']['what_we_test']}</div>
                    <div class="rq-detail-section"><strong>Expected finding:</strong> {rq_details['RQ5']['expected']}</div>
                    <div class="rq-detail-section"><strong>Scientific impact:</strong> {rq_details['RQ5']['impact']}</div>
                </div>
                <div class="finding">
                    <strong>Tier-Based Phase Behavior:</strong>
                    <p style="margin: 10px 0;">Analyzing whether models show sharp transitions (phase-like) or gradual degradation:</p>
                    <table style="width: 100%; margin-top: 10px;">
                        <thead>
                            <tr>
                                <th>Tier</th>
                                <th>Low Complexity<br>(vars 4-8)</th>
                                <th>High Complexity<br>(vars 15-20)</th>
                                <th>Degradation Rate</th>
                                <th>Transition Type</th>
                            </tr>
                        </thead>
                        <tbody>
""")
    
    # Calculate tier-specific degradation patterns
    tier_analysis = {}
    for tier_name, tier_models in tiers.items():
        if not tier_models:
            continue
        
        low_accs = []
        high_accs = []
        mid_accs = []  # For transition detection
        
        for model_key in tier_models:
            for exp_name in exp_names:
                if exp_name in experiments and model_key in experiments[exp_name]["models"]:
                    complexity = experiments[exp_name]["models"][model_key].get("complexity_breakdown", {})
                    
                    for var in range(4, 9):
                        if str(var) in complexity:
                            low_accs.append(complexity[str(var)]["accuracy"])
                    
                    for var in range(10, 15):
                        if str(var) in complexity:
                            mid_accs.append(complexity[str(var)]["accuracy"])
                    
                    for var in range(15, 21):
                        if str(var) in complexity:
                            high_accs.append(complexity[str(var)]["accuracy"])
        
        low_avg = (sum(low_accs) / len(low_accs) * 100) if low_accs else 100
        high_avg = (sum(high_accs) / len(high_accs) * 100) if high_accs else 100
        degradation = low_avg - high_avg
        
        # Determine transition type
        if degradation < 10:
            transition = "Gradual (continuous)"
        elif degradation > 30:
            transition = "Sharp (phase-like)"
        else:
            transition = "Moderate (hybrid)"
        
        rate_class = "acc-100" if degradation < 15 else "acc-75" if degradation < 30 else "acc-50"
        
        html.append(f"""                            <tr>
                                <td style="text-align: left;">{tier_name}</td>
                                <td class="acc-100">{low_avg:.0f}%</td>
                                <td class="{'acc-100' if high_avg >= 90 else 'acc-90' if high_avg >= 75 else 'acc-75'}">{high_avg:.0f}%</td>
                                <td class="{rate_class}">{degradation:.1f}% drop</td>
                                <td>{transition}</td>
                            </tr>
""")
    
    html.append(f"""                        </tbody>
                    </table>
                    <div style="background: #edf2f7; padding: 12px; margin-top: 15px; border-left: 3px solid #667eea; border-radius: 4px;">
                        <strong>Interpretation:</strong> Degradation patterns suggest {'sharp phase-like transitions' if any('Sharp' in str(html[-20:]) for _ in [1]) else 'mixed transition behaviors'} across model tiers. Sharp drops indicate discrete capacity limits; gradual decay suggests continuous scaling.
                    </div>
                    <div class="note" style="margin-top: 10px;">
                        <strong>Data status:</strong> Transition types detectable but need more complexity levels. Full dataset will reveal exact inflection points and enable phase diagram construction.
                    </div>
                </div>
            </div>
            
            <div class="rq-section">
                <div class="rq-title">RQ6: {rq_details['RQ6']['title']}</div>
                <div class="rq-description">{rq_details['RQ6']['question']}</div>
                <div class="rq-toggle" onclick="toggleRQ('rq6')">
                    <span class="rq-toggle-icon" id="rq6-icon">▶</span>
                    <span>Click for detailed research context</span>
                </div>
                <div class="rq-details" id="rq6-details">
                    <div class="rq-detail-section"><strong>Why it matters:</strong> {rq_details['RQ6']['why_matters']}</div>
                    <div class="rq-detail-section"><strong>What we test:</strong> {rq_details['RQ6']['what_we_test']}</div>
                    <div class="rq-detail-section"><strong>Expected finding:</strong> {rq_details['RQ6']['expected']}</div>
                    <div class="rq-detail-section"><strong>Scientific impact:</strong> {rq_details['RQ6']['impact']}</div>
                </div>
                <div class="finding">
                    <strong>Model Rankings by Task Type:</strong>
                    <table style="width: 100%; margin-top: 10px;">
                        <thead>
                            <tr>
                                <th>Task Category</th>
                                <th>Top 3 Models (by avg accuracy)</th>
                                <th>Performance Range</th>
                            </tr>
                        </thead>
                        <tbody>
""")
    
    # Calculate rankings for different task categories
    task_categories = {
        "Horn Tasks (goal entailment)": ['horn_yn_hornonly', 'horn_yn_mixed'],
        "CNF Tasks (satisfiability)": ['cnf1_con_mixed', 'cnf2_con_mixed', 'cnf1_con_hornonly', 'cnf2_con_hornonly'],
        "Matched Representations": ['horn_yn_hornonly', 'cnf1_con_hornonly', 'cnf2_con_hornonly'],
        "Mismatch Handling": ['horn_yn_mixed'],
    }
    
    for category_name, category_exps in task_categories.items():
        # Calculate average accuracy per model for this category
        model_avgs = {}
        for model_key in model_keys:
            accs = []
            for exp_name in category_exps:
                if exp_name in experiments and model_key in experiments[exp_name]["models"]:
                    acc = experiments[exp_name]["models"][model_key]["summary"].get("accuracy", 0)
                    accs.append(acc * 100)
            if accs:
                model_avgs[model_key] = sum(accs) / len(accs)
        
        # Get top 3
        top_3 = sorted(model_avgs.items(), key=lambda x: x[1], reverse=True)[:3]
        
        if top_3:
            top_models_str = ", ".join([f"{k.split('/')[1][:15]}" for k, v in top_3])
            top_acc = top_3[0][1]
            low_acc = top_3[-1][1]
            perf_range = f"{low_acc:.0f}%-{top_acc:.0f}%"
            
            html.append(f"""                            <tr>
                                <td style="text-align: left;">{category_name}</td>
                                <td>{top_models_str}</td>
                                <td class="acc-100">{perf_range}</td>
                            </tr>
""")
    
    html.append(f"""                        </tbody>
                    </table>
                    <div style="background: #edf2f7; padding: 12px; margin-top: 15px; border-left: 3px solid #667eea; border-radius: 4px;">
                        <strong>Interpretation:</strong> Preliminary rankings show task-specific performance patterns. Rank correlation analysis will quantify transfer vs. specialization.
                    </div>
                    <div class="note" style="margin-top: 10px;">
                        <strong>Data status:</strong> Rankings observable but statistical tests require larger sample. Full validation enables rank correlation (ρ) calculation and significance testing.
                    </div>
                </div>
            </div>
            
            <div class="rq-section">
                <div class="rq-title">RQ7: {rq_details['RQ7']['title']}</div>
                <div class="rq-description">{rq_details['RQ7']['question']}</div>
                <div class="rq-toggle" onclick="toggleRQ('rq7')">
                    <span class="rq-toggle-icon" id="rq7-icon">▶</span>
                    <span>Click for detailed research context</span>
                </div>
                <div class="rq-details" id="rq7-details">
                    <div class="rq-detail-section"><strong>Why it matters:</strong> {rq_details['RQ7']['why_matters']}</div>
                    <div class="rq-detail-section"><strong>What we test:</strong> {rq_details['RQ7']['what_we_test']}</div>
                    <div class="rq-detail-section"><strong>Expected finding:</strong> {rq_details['RQ7']['expected']}</div>
                    <div class="rq-detail-section"><strong>Scientific impact:</strong> {rq_details['RQ7']['impact']}</div>
                </div>
                <div class="finding">
                    <strong>Sat/Unsat Performance Analysis:</strong>
                    <table style="width: 100%; margin-top: 10px;">
                        <thead>
                            <tr>
                                <th>Model</th>
                                <th>Satisfiable Acc</th>
                                <th>Unsatisfiable Acc</th>
                                <th>Bias (Δ)</th>
                                <th>Interpretation</th>
                            </tr>
                        </thead>
                        <tbody>
""")
    
    # Calculate sat/unsat bias for each model
    for model_key in model_keys:
        model_data = models[model_key]
        
        sat_correct = 0
        sat_total = 0
        unsat_correct = 0
        unsat_total = 0
        
        # Aggregate across all experiments
        for exp_name in exp_names:
            if exp_name in model_data["experiments"]:
                # Load detailed results to separate sat/unsat
                exp_run_path = runs_dir / exp_name / run_id / model_key.split('/')[0] / model_key.split('/')[1] / model_key.split('/')[2]
                results_file = exp_run_path / "results.jsonl"
                
                if results_file.exists():
                    with open(results_file) as f:
                        for line in f:
                            try:
                                row = json.loads(line)
                                meta = row.get("meta", {})
                                satflag = meta.get("satflag")
                                parsed = row.get("parsed_answer")
                                
                                if satflag is not None and parsed is not None and parsed != 2:
                                    if satflag == 1:  # Satisfiable
                                        sat_total += 1
                                        if parsed == satflag:
                                            sat_correct += 1
                                    elif satflag == 0:  # Unsatisfiable
                                        unsat_total += 1
                                        if parsed == satflag:
                                            unsat_correct += 1
                            except:
                                pass
        
        if sat_total > 0 or unsat_total > 0:
            sat_acc = (sat_correct / sat_total * 100) if sat_total > 0 else 0
            unsat_acc = (unsat_correct / unsat_total * 100) if unsat_total > 0 else 0
            bias = sat_acc - unsat_acc
            
            interpretation = ""
            if abs(bias) < 5:
                interpretation = "Balanced"
            elif bias > 10:
                interpretation = "SAT bias"
            elif bias < -10:
                interpretation = "UNSAT bias"
            else:
                interpretation = "Slight bias"
            
            bias_class = "acc-100" if abs(bias) < 10 else "acc-75" if abs(bias) < 20 else "acc-50"
            
            html.append(f"""                            <tr>
                                <td style="text-align: left; font-size: 0.85em;">{model_key}</td>
                                <td class="{'acc-100' if sat_acc >= 90 else 'acc-90' if sat_acc >= 75 else 'acc-75'}">{sat_acc:.0f}%</td>
                                <td class="{'acc-100' if unsat_acc >= 90 else 'acc-90' if unsat_acc >= 75 else 'acc-75'}">{unsat_acc:.0f}%</td>
                                <td class="{bias_class}" style="font-weight: 600;">{bias:+.0f}%</td>
                                <td>{interpretation}</td>
                            </tr>
""")
    
    html.append(f"""                        </tbody>
                    </table>
                    <div style="background: #edf2f7; padding: 12px; margin-top: 15px; border-left: 3px solid #667eea; border-radius: 4px;">
                        <strong>Interpretation:</strong> Positive bias (Δ > 0) indicates models are better at satisfiable problems (may miss contradictions). 
                        Negative bias (Δ < 0) indicates better contradiction detection (may falsely claim unsatisfiability). 
                        Balanced performance (|Δ| < 5%) suggests unbiased logical reasoning.
                    </div>
                    <div class="note" style="margin-top: 10px;">
                        <strong>Data status:</strong> Bias patterns observable. Full validation will show if bias correlates with model tier, representation type, or problem complexity.
                    </div>
                </div>
            </div>
        </div>
""")
    
    # Section 3: Degradation Curves (Interactive Charts)
    html.append("""
        <div class="section">
            <h2>📉 Quality Degradation by Complexity</h2>
            <p style="margin-bottom: 15px;">How accuracy changes as problem complexity (number of variables) increases. Each line represents one model.</p>
            <div class="note">
                <strong>💡 Note:</strong> If charts don't appear (e.g., on GitHub Pages), download this HTML file and open locally. 
                Alternative: Check the ASCII representation tables below each chart.
            </div>
""")
    
    # Generate degradation charts for each experiment
    for exp_idx, exp_name in enumerate(exp_names):
        exp_data = experiments[exp_name]
        
        # Collect all vars and model accuracies
        all_vars = set()
        model_degradation = {}
        
        for model_key, model_data in exp_data["models"].items():
            complexity = model_data.get("complexity_breakdown", {})
            if complexity:
                for var_str in complexity.keys():
                    all_vars.add(int(var_str))
                model_degradation[model_key] = complexity
        
        if all_vars and model_degradation:
            vars_sorted = sorted(all_vars)
            
            # Prepare Chart.js data
            chart_id = f"degradation_chart_{exp_idx}"
            
            html.append(f"""
            <div style="margin-bottom: 30px;">
                <h3 style="color: #4a5568; margin-bottom: 15px;">{exp_name}</h3>
                <canvas id="{chart_id}" style="max-height: 400px;"></canvas>
            </div>
            <script>
            (function() {{
                const ctx = document.getElementById('{chart_id}').getContext('2d');
                
                // Provider colors
                const providerColors = {{
                    'anthropic': ['#E91E63', '#F06292', '#F8BBD0', '#FCE4EC'],
                    'google': ['#2196F3', '#64B5F6', '#BBDEFB', '#E3F2FD'],
                    'openai': ['#4CAF50', '#81C784', '#C8E6C9', '#E8F5E9']
                }};
                
                const datasets = [];
""")
            
            # Generate dataset for each model
            provider_colors_map = {
                'anthropic': ['#E91E63', '#F06292', '#F8BBD0', '#FCE4EC'],
                'google': ['#2196F3', '#64B5F6', '#BBDEFB', '#E3F2FD'],
                'openai': ['#4CAF50', '#81C784', '#C8E6C9', '#E8F5E9']
            }
            
            for model_idx, (model_key, model_data) in enumerate(sorted(model_degradation.items())):
                provider = model_key.split('/')[0]
                model_name = model_key.split('/')[1]
                thinking = model_key.split('/')[2]
                
                # Get color
                colors = provider_colors_map.get(provider, ['#666666'])
                color = colors[model_idx % len(colors)]
                
                # Prepare data points
                data_points = []
                for var in vars_sorted:
                    var_data = model_data.get(str(var), {})
                    acc = var_data.get("accuracy", None)
                    if acc is not None:
                        data_points.append({"x": var, "y": acc * 100})
                
                if data_points:
                    # Determine line style
                    border_dash = []
                    if 'nothink' in thinking:
                        border_dash = [5, 5]  # Dashed for no-thinking
                    elif 'low' in thinking:
                        border_dash = [10, 5]  # Dash-dot for low
                    
                    label = f"{provider}/{model_name[:20]}/{thinking}"
                    
                    html.append(f"""
                datasets.push({{
                    label: '{label}',
                    data: {json.dumps(data_points)},
                    borderColor: '{color}',
                    backgroundColor: '{color}20',
                    borderWidth: 2,
                    borderDash: {json.dumps(border_dash)},
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    tension: 0.1
                }});
""")
            
            # Create chart
            html.append(f"""
                new Chart(ctx, {{
                    type: 'line',
                    data: {{ datasets: datasets }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: {{
                            legend: {{
                                display: true,
                                position: 'right',
                                labels: {{
                                    boxWidth: 12,
                                    font: {{ size: 10 }},
                                    padding: 8
                                }}
                            }},
                            title: {{
                                display: false
                            }},
                            tooltip: {{
                                mode: 'nearest',
                                intersect: false
                            }}
                        }},
                        scales: {{
                            x: {{
                                type: 'linear',
                                title: {{
                                    display: true,
                                    text: 'Maximum Variables',
                                    font: {{ weight: 'bold' }}
                                }},
                                ticks: {{
                                    stepSize: 1
                                }}
                            }},
                            y: {{
                                title: {{
                                    display: true,
                                    text: 'Accuracy (%)',
                                    font: {{ weight: 'bold' }}
                                }},
                                min: 0,
                                max: 100,
                                ticks: {{
                                    callback: function(value) {{ return value + '%'; }}
                                }}
                            }}
                        }},
                        interaction: {{
                            mode: 'index',
                            intersect: false
                        }}
                    }}
                }});
            }})();
            </script>
            
            <div style="margin-top: 20px;">
                <details>
                    <summary style="cursor: pointer; font-weight: 600; color: #667eea; padding: 10px; background: #f7fafc; border-radius: 4px;">
                        📊 Show ASCII Table (fallback if chart doesn't render)
                    </summary>
                    <div style="background: #2d3748; color: #e2e8f0; padding: 15px; border-radius: 8px; font-family: monospace; font-size: 0.75em; overflow-x: auto; margin-top: 10px;">
                        <pre style="margin: 0;">
Vars:  {' '.join(f'{v:4}' for v in vars_sorted)}

""")
            
            # Add ASCII table for each model
            for model_key, model_data in sorted(model_degradation.items())[:12]:
                provider = model_key.split('/')[0]
                model_name = model_key.split('/')[1][:20]
                thinking = model_key.split('/')[2][:10]
                
                accs = []
                for var in vars_sorted:
                    var_data = model_data.get(str(var), {})
                    acc = var_data.get("accuracy", 0)
                    accs.append(acc)
                
                acc_str = ' '.join(f'{int(a*100):3}%' for a in accs)
                provider_icons = {'anthropic': '🔴', 'google': '🔵', 'openai': '🟢'}
                icon = provider_icons.get(provider, '⚪')
                
                html.append(f"{icon} {model_name:20} {thinking:10}: {acc_str}\n")
            
            html.append(f"""</pre>
                        <div style="margin-top: 10px; opacity: 0.8;">🔴 Anthropic | 🔵 Google | 🟢 OpenAI</div>
                    </div>
                </details>
            </div>
""")
        else:
            html.append(f"""
            <div class="note">
                <strong>{exp_name}:</strong> Insufficient complexity variation in test data. 
                Full validation will show degradation curves.
            </div>
""")
    
    html.append("""
        </div>
""")
    
    # No separate Model Performance table - integrated into transposable heatmap above
    
    # Add JavaScript for interactivity
    html.append("""
        <script>
        // Store full data for interactivity
        const fullData = """ + json.dumps(aggregated_data) + """;
        
        function transposeHeatmap() {
            const viewMode = document.getElementById('viewMode').value;
            const metric = document.getElementById('metricSelect').value;
            
            const table = document.getElementById('heatmapTable');
            const experiments = fullData.experiments;
            const models = fullData.models;
            
            const expNames = Object.keys(experiments).sort();
            const modelKeys = Object.keys(models).sort();
            
            let html = '';
            
            if (viewMode === 'model-rows') {
                // Transpose: Models as rows, Experiments as columns
                html += '<thead><tr><th style="text-align: left;">Model</th>';
                
                for (const exp of expNames) {
                    html += `<th style="min-width: 100px;">${exp}</th>`;
                }
                html += '<th>Average</th></tr></thead><tbody>';
                
                for (const modelKey of modelKeys) {
                    html += '<tr>';
                    html += `<td style="text-align: left; font-weight: 500;">${modelKey}</td>`;
                    
                    const accs = [];
                    for (const expName of expNames) {
                        const modelData = experiments[expName]?.models?.[modelKey];
                        if (modelData) {
                            const value = getMetricValue(modelData, metric);
                            const cssClass = getCellClass(modelData.summary.accuracy * 100);
                            html += `<td class="${cssClass} clickable-cell" title="${modelData.summary.correct}/${modelData.summary.total} correct, ${modelData.summary.unclear} unclear" onclick="showDetails('${expName}', '${modelKey}')">${value}</td>`;
                            accs.push(modelData.summary.accuracy * 100);
                        } else {
                            html += '<td>—</td>';
                        }
                    }
                    
                    const avgAcc = accs.length > 0 ? accs.reduce((a,b) => a+b, 0) / accs.length : 0;
                    const avgClass = getCellClass(avgAcc);
                    html += `<td class="${avgClass}"><strong>${metric === 'accuracy' ? avgAcc.toFixed(0) + '%' : avgAcc.toFixed(0)}</strong></td>`;
                    html += '</tr>';
                }
                
                html += '</tbody>';
            } else {
                // Original: Experiments as rows, Models as columns
                html += '<thead><tr><th style="text-align: left;">Experiment</th>';
                
                for (const modelKey of modelKeys) {
                    const parts = modelKey.split('/');
                    const label = `${parts[0].substr(0,3)}/${parts[1].substr(0,20)}/${parts[2]}`;
                    html += `<th><div class="model-header">${label}</div></th>`;
                }
                html += '</tr></thead><tbody>';
                
                for (const expName of expNames) {
                    const expDesc = fullData.experiments[expName].name || expName;
                    html += `<tr><td class="exp-name">${expName}<div class="exp-description">${getExpDescription(expName)}</div></td>`;
                    
                    for (const modelKey of modelKeys) {
                        const modelData = experiments[expName]?.models?.[modelKey];
                        if (modelData) {
                            const value = getMetricValue(modelData, metric);
                            const cssClass = getCellClass(modelData.summary.accuracy * 100);
                            html += `<td class="${cssClass} clickable-cell" title="${modelData.summary.correct}/${modelData.summary.total} correct, ${modelData.summary.unclear} unclear" onclick="showDetails('${expName}', '${modelKey}')">${value}</td>`;
                        } else {
                            html += '<td>—</td>';
                        }
                    }
                    html += '</tr>';
                }
                
                html += '</tbody>';
            }
            
            table.innerHTML = html;
        }
        
        function getMetricValue(modelData, metric) {
            const summary = modelData.summary;
            switch(metric) {
                case 'accuracy':
                    return (summary.accuracy * 100).toFixed(0) + '%';
                case 'correct':
                    return `${summary.correct}/${summary.total}`;
                case 'unclear':
                    return summary.unclear.toString();
                default:
                    return (summary.accuracy * 100).toFixed(0) + '%';
            }
        }
        
        function getCellClass(accPct) {
            if (accPct >= 95) return 'acc-100';
            if (accPct >= 85) return 'acc-90';
            if (accPct >= 70) return 'acc-75';
            if (accPct >= 50) return 'acc-50';
            return 'acc-low';
        }
        
        function getExpDescription(expName) {
            const descriptions = {
                "horn_yn_hornonly": "Goal-directed entailment task with matched Horn representation (baseline control)",
                "horn_yn_mixed": "Representation mismatch condition: Horn encoding on mixed problem set (tests robustness)",
                "cnf1_con_mixed": "Natural language CNF satisfiability (verbose encoding, tests NL scaffolding)",
                "cnf2_con_mixed": "Symbolic CNF satisfiability (compact encoding, tests symbolic reasoning)",
                "cnf1_con_hornonly": "NL-CNF on Horn subset (tests representation flexibility)",
                "cnf2_con_hornonly": "Symbolic-CNF on Horn subset (tests abstraction capability)",
            };
            return descriptions[expName] || '';
        }
        
        function updateMetric() {
            transposeHeatmap(); // Just rebuild table with new metric
        }
        
        function showDetails(exp, model) {
            alert(`Details for ${exp} - ${model}\\n\\nSee degradation charts below for performance across complexity levels.`);
        }
        
        function toggleRQ(rqId) {
            const details = document.getElementById(rqId + '-details');
            const icon = document.getElementById(rqId + '-icon');
            
            if (details.classList.contains('expanded')) {
                details.classList.remove('expanded');
                icon.classList.remove('expanded');
                icon.textContent = '▶';
            } else {
                details.classList.add('expanded');
                icon.classList.add('expanded');
                icon.textContent = '▼';
            }
        }
        
        // Add chart legend interactivity hint
        document.addEventListener('DOMContentLoaded', function() {
            const chartSections = document.querySelectorAll('.section h2');
            for (const section of chartSections) {
                if (section.textContent.includes('Degradation')) {
                    const note = document.createElement('div');
                    note.className = 'note';
                    note.innerHTML = '<strong>💡 Interactive Charts:</strong> Click legend items to show/hide models. Hover over lines to see exact accuracy values.';
                    section.parentElement.insertBefore(note, section.nextSibling);
                    break;
                }
            }
        });
        </script>
""")
    
    # Footer
    html.append(f"""
        <div class="footer">
            <p>Generated from run: <strong>{metadata.get('run_id', 'unknown')}</strong></p>
            <p>To update with new data: <code>python -m experiments.aggregate_results --run-id YOUR_RUN --output results.json && python -m experiments.generate_dashboard --input results.json --output dashboard.html</code></p>
        </div>
    </div>
</body>
</html>
""")
    
    output_path.write_text("\n".join(html))
    print(f"✓ Dashboard written to: {output_path}")
    print(f"  Open with: open {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate interactive HTML dashboard")
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to aggregated results JSON"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("experiments/dashboard.html"),
        help="Output HTML file path"
    )
    
    args = parser.parse_args()
    
    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}")
        return 1
    
    with open(args.input) as f:
        aggregated_data = json.load(f)
    
    generate_html_dashboard(aggregated_data, args.output)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

