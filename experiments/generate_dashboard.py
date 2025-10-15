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
    
    # Research question one-liners (scientific framing)
    rq_descriptions = {
        "RQ1": "Do LLMs exhibit representation-invariant logical reasoning, or is performance fundamentally bound to surface encodings?",
        "RQ2": "When representations mismatch problem structure, do models exhibit systematic failures or degrade randomly?",
        "RQ3": "How does reasoning accuracy scale with problem complexity, and can we predict breakdown thresholds?",
        "RQ4": "Does extended thinking enable qualitatively different problem-solving or merely reduce errors on solvable problems?",
        "RQ5": "Do models exhibit sharp phase transitions or gradual degradation at complexity thresholds?",
        "RQ6": "Do models transfer reasoning capability across representations or exhibit task-specific specialization?",
    }
    
    html = []
    
    # HTML header
    html.append("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LLM Logic Reasoning Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
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
    </style>
</head>
<body>
    <div class="container">
""")
    
    # Header
    run_id = metadata.get("run_id", "unknown")
    html.append(f"""
        <header>
            <h1>🧠 LLM Logic Reasoning Dashboard</h1>
            <div class="subtitle">Systematic evaluation across representations, tasks, and models</div>
            <div class="subtitle">Run: {run_id}</div>
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
                <div class="stat-label">Overall Accuracy</div>
                <div class="stat-value">{overall_acc:.0f}%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total Evaluations</div>
                <div class="stat-value">{all_total}</div>
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
                    <input type="checkbox" id="filterTier1" checked onchange="filterModels()"> Tier 1 (Flagship)
                </label>
                <label>
                    <input type="checkbox" id="filterTier2" checked onchange="filterModels()"> Tier 2 (Medium)
                </label>
                <label>
                    <input type="checkbox" id="filterTier3" checked onchange="filterModels()"> Tier 3 (Budget)
                </label>
                <label style="margin-left: 30px;">
                    Show: 
                    <select id="metricSelect" onchange="updateMetric()">
                        <option value="accuracy">Accuracy</option>
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
    
    html.append("""
            <div class="rq-section">
                <div class="rq-title">RQ1: Does Representation Matter?</div>
                <div class="rq-description">{rq_descriptions.get('RQ1', '')}</div>
                <div class="finding">
""")
    
    if horn_exps and cnf_exps:
        horn_acc = sum(experiments[e]["summary"]["avg_accuracy"] for e in horn_exps) / len(horn_exps) * 100 if horn_exps else 0
        cnf_acc = sum(experiments[e]["summary"]["avg_accuracy"] for e in cnf_exps) / len(cnf_exps) * 100 if cnf_exps else 0
        html.append(f"""
                    <strong>Preliminary Evidence:</strong> 
                    <ul style="margin-top: 10px; margin-left: 20px;">
                        <li>Horn representation (goal-directed): ~{horn_acc:.0f}% average accuracy</li>
                        <li>CNF representations (satisfiability): ~{cnf_acc:.0f}% average accuracy</li>
                        <li>Δ = {abs(cnf_acc - horn_acc):.1f}% ({'CNF favored' if cnf_acc > horn_acc else 'Horn favored' if horn_acc > cnf_acc else 'representation-invariant'})</li>
                        <li><strong>Interpretation:</strong> {'Models show representation sensitivity, indicating encoding-dependent rather than abstract reasoning.' if abs(cnf_acc - horn_acc) > 10 else 'Weak representation dependence suggests partial abstraction capability.'}</li>
                    </ul>
""")
    
    html.append("""
                </div>
            </div>
            
            <div class="rq-section">
                <div class="rq-title">RQ2: Can Models Handle Representation Mismatch?</div>
                <div class="rq-description">{rq_descriptions.get('RQ2', '')}</div>
""")
    
    if 'horn_yn_hornonly' in experiments and 'horn_yn_mixed' in experiments:
        matched_acc = experiments['horn_yn_hornonly']['summary']['avg_accuracy'] * 100
        mixed_acc = experiments['horn_yn_mixed']['summary']['avg_accuracy'] * 100
        penalty = matched_acc - mixed_acc
        
        html.append(f"""
                <div class="finding">
                    <strong>Mismatch Penalty Analysis:</strong>
                    <ul style="margin-top: 10px; margin-left: 20px;">
                        <li>Matched condition (Horn on Horn): {matched_acc:.0f}%</li>
                        <li>Mismatch condition (Horn on mixed): {mixed_acc:.0f}%</li>
                        <li>Penalty: {penalty:.1f}% accuracy loss</li>
                        <li><strong>Error characterization:</strong> {'Systematic failure mode detected (>10% penalty) - models cannot gracefully handle incompatible representations.' if penalty > 10 else 'Mild degradation suggests partial robustness to representation mismatch.'}</li>
                        <li><strong>Implication:</strong> Representation compatibility is critical for deployment reliability.</li>
                    </ul>
                </div>
""")
    
    html.append("""
            </div>
            
            <div class="rq-section">
                <div class="rq-title">RQ3: Scaling Laws for Logical Complexity</div>
                <div class="rq-description">{rq_descriptions.get('RQ3', '')}</div>
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
    
    html.append("""                        </tbody>
                    </table>
                    <div class="note" style="margin-top: 15px;">
                        <strong>Interpretation:</strong> Degradation curves (below) visualize the scaling relationship Acc(n) where n = complexity. 
                        Full validation will enable fitting power-law models: Acc(n) ≈ A - B·n^α to predict breakdown thresholds.
                    </div>
                </div>
            </div>
            
            <div class="rq-section">
                <div class="rq-title">RQ4: Is Extended Thinking Worth It?</div>
                <div class="rq-description">{rq_descriptions.get('RQ4', '')}</div>
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
    
    html.append("""                        </tbody>
                    </table>
                    <div class="note" style="margin-top: 15px;">
                        <strong>Limited data:</strong> Full validation will show thinking benefits by complexity level.
                    </div>
                </div>
            </div>
            
            <div class="rq-section">
                <div class="rq-title">RQ5: Phase Transitions in Reasoning Capability</div>
                <div class="rq-description">{rq_descriptions.get('RQ5', '')}</div>
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
    
    html.append("""                        </tbody>
                    </table>
                    <div class="note" style="margin-top: 15px;">
                        <strong>Hypothesis:</strong> Sharp transitions indicate discrete capacity limits; gradual decay suggests continuous scaling. 
                        Full dataset will reveal exact transition points and enable phase diagram construction.
                    </div>
                </div>
            </div>
            
            <div class="rq-section">
                <div class="rq-title">RQ6: Cross-Task Transfer and Specialization</div>
                <div class="rq-description">{rq_descriptions.get('RQ6', '')}</div>
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
    
    html.append("""                        </tbody>
                    </table>
                    <div class="note" style="margin-top: 15px;">
                        <strong>Transfer Analysis:</strong> Rank correlation across task types will reveal generalists (high transfer) vs. specialists (task-specific). 
                        Full validation enables statistical significance testing.
                    </div>
                </div>
            </div>
        </div>
""")
    
    # Section 3: Degradation Curves (Interactive Charts)
    html.append("""
        <div class="section">
            <h2>📉 Quality Degradation by Complexity</h2>
            <p style="margin-bottom: 15px;">How accuracy changes as problem complexity increases. Each line represents one model.</p>
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
    
    # Section 4: Model Performance Table
    html.append("""
        <div class="section">
            <h2>📈 Model Performance Across Experiments</h2>
            <div style="overflow-x: auto;">
                <table>
                    <thead>
                        <tr>
                            <th style="text-align: left;">Model</th>
""")
    
    for exp_name in exp_names:
        html.append(f'                            <th>{exp_name}</th>\n')
    
    html.append("""                            <th>Average</th>
                        </tr>
                    </thead>
                    <tbody>
""")
    
    for model_key in model_keys:
        model_data = models[model_key]
        html.append(f'                        <tr>\n')
        html.append(f'                            <td style="text-align: left;">{model_key}</td>\n')
        
        accs = []
        for exp_name in exp_names:
            if exp_name in model_data["experiments"]:
                acc = model_data["experiments"][exp_name]["accuracy"] * 100
                accs.append(acc)
                
                css_class = (
                    "acc-100" if acc >= 95 else
                    "acc-90" if acc >= 85 else
                    "acc-75" if acc >= 70 else
                    "acc-50" if acc >= 50 else
                    "acc-low"
                )
                html.append(f'                            <td class="{css_class}">{acc:.0f}%</td>\n')
            else:
                html.append(f'                            <td>—</td>\n')
        
        avg_acc = sum(accs) / len(accs) if accs else 0
        avg_class = (
            "acc-100" if avg_acc >= 95 else
            "acc-90" if avg_acc >= 85 else
            "acc-75" if avg_acc >= 70 else
            "acc-50" if avg_acc >= 50 else
            "acc-low"
        )
        html.append(f'                            <td class="{avg_class}"><strong>{avg_acc:.0f}%</strong></td>\n')
        html.append(f'                        </tr>\n')
    
    html.append("""                    </tbody>
                </table>
            </div>
        </div>
""")
    
    # Add JavaScript for interactivity
    html.append("""
        <script>
        // Store full data for interactivity
        const fullData = """ + json.dumps(aggregated_data) + """;
        
        function filterModels() {
            // Model filtering logic (placeholder for now)
            console.log('Filtering models...');
        }
        
        function updateMetric() {
            // Metric switching logic (placeholder for now)
            console.log('Updating metric...');
        }
        
        function showDetails(exp, model) {
            // Show detailed modal or expand section
            alert(`Details for ${exp} - ${model}\\n\\nClick on degradation chart legends to toggle models on/off.`);
        }
        
        // Add chart legend interactivity hint
        document.addEventListener('DOMContentLoaded', function() {
            const note = document.createElement('div');
            note.className = 'note';
            note.innerHTML = '<strong>💡 Tip:</strong> Click on chart legends to show/hide individual models. Hover over lines to see exact values.';
            document.querySelector('.section:has(canvas)').prepend(note);
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

