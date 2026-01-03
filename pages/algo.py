import streamlit as st
import requests
import pandas as pd
from config import Config
from typing import Dict, Optional

st.set_page_config(
    page_title="algo",
    page_icon="./favicon/android-chrome-192x192.png",
    layout="wide"
)

EXPERIMENT_ID = "1"  # reel_driver experiment


def fetch_latest_run(config: Config) -> Optional[Dict]:
    """Fetch the latest finished run from MLflow experiment"""
    if not config.mlflow_base_url:
        return None

    try:
        response = requests.post(
            f"{config.mlflow_base_url}/api/2.0/mlflow/runs/search",
            json={
                "experiment_ids": [EXPERIMENT_ID],
                "max_results": 1,
                "order_by": ["start_time DESC"],
                "filter": "status = 'FINISHED'"
            },
            auth=config.mlflow_auth,
            timeout=config.api_timeout
        )
        response.raise_for_status()
        data = response.json()
        runs = data.get("runs", [])
        return runs[0] if runs else None
    except Exception as e:
        st.error(f"Failed to fetch latest run: {str(e)}")
        return None


def fetch_artifact(config: Config, run_id: str, artifact_path: str) -> Optional[Dict]:
    """Fetch an artifact from MLflow"""
    if not config.mlflow_base_url:
        return None

    try:
        response = requests.get(
            f"{config.mlflow_base_url}/get-artifact",
            params={"run_id": run_id, "path": artifact_path},
            auth=config.mlflow_auth,
            timeout=config.api_timeout
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to fetch artifact {artifact_path}: {str(e)}")
        return None


def main():
    """Main application function"""
    try:
        config = Config()
    except ValueError as e:
        st.error(f"Configuration Error: {str(e)}")
        return

    st.title("algo")

    if not config.mlflow_base_url:
        st.error("MLflow not configured. Set CENTER_CONSOLE_MLFLOW_HOST and CENTER_CONSOLE_MLFLOW_PORT.")
        return

    # Fetch latest run
    with st.spinner("Loading latest model run..."):
        run = fetch_latest_run(config)

    if not run:
        st.warning("No runs found in experiment")
        return

    run_info = run.get("info", {})
    run_data = run.get("data", {})
    run_id = run_info.get("run_id")

    # Display run metadata
    st.subheader("Latest Model Run")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Run Name", run_info.get("run_name", "N/A"))
    with col2:
        st.metric("Status", run_info.get("status", "N/A"))
    with col3:
        import datetime
        start_time = run_info.get("start_time")
        if start_time:
            dt = datetime.datetime.fromtimestamp(start_time / 1000)
            st.metric("Started", dt.strftime("%Y-%m-%d %H:%M"))
        else:
            st.metric("Started", "N/A")

    st.code(f"Run ID: {run_id}")

    # Display key metrics from the run
    metrics = {m["key"]: m["value"] for m in run_data.get("metrics", [])}
    if metrics:
        st.subheader("Model Metrics")

        col_left, col_right = st.columns(2)

        with col_left:
            # Confusion Matrix visualization
            tp = int(metrics.get("true_positives", 0))
            fp = int(metrics.get("false_positives", 0))
            tn = int(metrics.get("true_negatives", 0))
            fn = int(metrics.get("false_negatives", 0))

            st.markdown("**Confusion Matrix**")
            # Create confusion matrix as styled HTML table
            cm_html = f"""
            <table style="border-collapse: collapse; text-align: center; width: 100%;">
                <tr>
                    <td style="width:25%;"></td>
                    <td style="width:37.5%; font-weight: bold; padding: 8px;">Pred: Watch</td>
                    <td style="width:37.5%; font-weight: bold; padding: 8px;">Pred: Not</td>
                </tr>
                <tr>
                    <td style="font-weight: bold; padding: 8px;">Actual: Watch</td>
                    <td style="background: #35B779; color: white; padding: 20px; font-size: 1.5em; border-radius: 4px;">{tp}<br><small>TP</small></td>
                    <td style="background: #440154; color: white; padding: 20px; font-size: 1.5em; border-radius: 4px;">{fn}<br><small>FN</small></td>
                </tr>
                <tr>
                    <td style="font-weight: bold; padding: 8px;">Actual: Not</td>
                    <td style="background: #31688E; color: white; padding: 20px; font-size: 1.5em; border-radius: 4px;">{fp}<br><small>FP</small></td>
                    <td style="background: #90D743; color: black; padding: 20px; font-size: 1.5em; border-radius: 4px;">{tn}<br><small>TN</small></td>
                </tr>
            </table>
            """
            st.markdown(cm_html, unsafe_allow_html=True)

        with col_right:
            # Radar chart for metrics
            import plotly.graph_objects as go

            radar_metrics = ["AUC", "Accuracy", "Precision", "Recall", "F1"]
            radar_values = [
                metrics.get("auc", 0),
                metrics.get("accuracy", 0),
                metrics.get("precision", 0),
                metrics.get("recall", 0),
                metrics.get("f1", 0)
            ]
            # Close the polygon
            radar_metrics_closed = radar_metrics + [radar_metrics[0]]
            radar_values_closed = radar_values + [radar_values[0]]

            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=radar_values_closed,
                theta=radar_metrics_closed,
                fill='toself',
                fillcolor='rgba(33, 145, 140, 0.3)',
                line=dict(color='#21918C', width=2),
                name='Model Performance'
            ))
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 1], tickvals=[0, 0.25, 0.5, 0.75, 1], ticktext=['0', '', '', '', '1'], tickfont=dict(color='white')),
                    angularaxis=dict(tickfont=dict(color='white', size=12)),
                    bgcolor='rgba(0,0,0,0)'
                ),
                showlegend=False,
                margin=dict(l=80, r=80, t=60, b=60),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=450
            )
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Fetch xgboost_trees.json artifact
    with st.spinner("Loading XGBoost trees artifact..."):
        trees_data = fetch_artifact(config, run_id, "xgboost_trees.json")

    if not trees_data:
        st.warning("Could not load xgboost_trees.json artifact")
        return

    # Display metadata
    metadata = trees_data.get("metadata", {})
    st.subheader("Model Structure")
    meta_cols = st.columns(3)
    with meta_cols[0]:
        st.metric("Total Trees", metadata.get("total_trees", "N/A"))
    with meta_cols[1]:
        st.metric("Exported Trees", metadata.get("exported_trees", "N/A"))
    with meta_cols[2]:
        st.metric("Feature Count", metadata.get("feature_count", "N/A"))

    st.divider()

    # Feature importance chart
    feature_importance = trees_data.get("feature_importance", {})
    if feature_importance:
        st.subheader("Feature Importance")

        # Filter to non-zero importance and sort
        nonzero_features = {k: v for k, v in feature_importance.items() if v > 0}
        sorted_features = sorted(nonzero_features.items(), key=lambda x: x[1], reverse=True)

        if sorted_features:
            df = pd.DataFrame(sorted_features, columns=["Feature", "Importance"])
            df["Importance %"] = df["Importance"] * 100

            # Conditionally formatted table with viridis gradient
            max_importance = df["Importance"].max()

            def importance_to_viridis(val):
                """Map importance to viridis color."""
                normalized = val / max_importance if max_importance > 0 else 0
                # Viridis gradient steps
                if normalized < 0.15:
                    return "#440154"
                elif normalized < 0.30:
                    return "#443983"
                elif normalized < 0.45:
                    return "#31688E"
                elif normalized < 0.60:
                    return "#21918C"
                elif normalized < 0.75:
                    return "#35B779"
                elif normalized < 0.90:
                    return "#90D743"
                else:
                    return "#FDE725"

            # Build styled dataframe with inline bar charts
            styled_df = df.style.bar(
                subset=["Importance %"],
                color="#21918C",
                vmin=0,
                vmax=df["Importance %"].max()
            ).format({"Importance": "{:.4f}", "Importance %": "{:.2f}%"})

            st.dataframe(styled_df, use_container_width=True, hide_index=True, height=400)

    st.divider()

    # Tree visualizations
    trees = trees_data.get("trees", [])
    if trees:
        st.subheader("Sample Decision Trees")

        # Tree selector
        tree_idx = st.selectbox(
            "Select tree to visualize:",
            options=range(len(trees)),
            format_func=lambda x: f"Tree {x}"
        )

        # Enhance DOT with better styling
        def style_dot(dot_string: str) -> str:
            """Add styling to DOT graph for better readability"""
            import re

            def condense_category_set(match: re.Match) -> str:
                """Condense category sets like {0,1,2,3,5,7,8,9} to {0-3,5,7-9}"""
                feature_name = match.group(1)
                values_str = match.group(2)
                rest = match.group(3) if match.lastindex >= 3 else ""

                # Parse the comma-separated values
                try:
                    values = sorted(int(v.strip()) for v in values_str.split(','))
                except ValueError:
                    return match.group(0)  # Return unchanged if parsing fails

                if not values:
                    return match.group(0)

                # Build ranges from consecutive values
                ranges = []
                range_start = values[0]
                range_end = values[0]

                for v in values[1:]:
                    if v == range_end + 1:
                        range_end = v
                    else:
                        # Close current range
                        if range_start == range_end:
                            ranges.append(str(range_start))
                        else:
                            ranges.append(f"{range_start}-{range_end}")
                        range_start = range_end = v

                # Close final range
                if range_start == range_end:
                    ranges.append(str(range_start))
                else:
                    ranges.append(f"{range_start}-{range_end}")

                condensed = ','.join(ranges)
                return f"{feature_name}:{{{condensed}}}{rest}"

            def condense_category_sets(dot: str) -> str:
                """Find and condense all category set labels."""
                # Match patterns like: feature_name:{0,1,2,3,4}
                # Capture: feature_name, the values inside {}, and any trailing content
                pattern = r'(\w+):\{([\d,\s]+)\}([^"]*)'
                return re.sub(pattern, condense_category_set, dot)

            def value_to_color(value: float) -> str:
                """Map leaf value to stepped red-purple-blue gradient."""
                # Clamp and normalize to -1 to 1 range
                normalized = max(-1, min(1, value / 0.025))

                # 7-step gradient: red (would not) -> purple (neutral) -> blue (would watch)
                steps = [
                    (-1.0, "#D94A4A"),   # Strong red
                    (-0.66, "#C45499"),  # Red-purple
                    (-0.33, "#B05EB0"),  # Light red-purple
                    (0.0, "#9B59B6"),    # Purple (neutral)
                    (0.33, "#7A6DC3"),   # Light blue-purple
                    (0.66, "#5A80CF"),   # Blue-purple
                    (1.0, "#4A90D9"),    # Strong blue
                ]

                # Find the closest step
                closest = min(steps, key=lambda s: abs(s[0] - normalized))
                return closest[1]

            def color_leaves(dot: str) -> str:
                """Find leaf nodes and color them based on their value."""
                def replace_leaf(match):
                    node_id = match.group(1)
                    value_str = match.group(2)
                    try:
                        value = float(value_str)
                        color = value_to_color(value)
                        # Display as scientific notation locked at E-3
                        display_val = f"{value * 1000:.1f}E-3"
                        return f'{node_id} [ label="{display_val}" fillcolor="{color}" ]'
                    except ValueError:
                        return match.group(0)

                # Match leaf node definitions like: 7 [ label="leaf=-0.0243379008" ]
                return re.sub(
                    r'(\d+) \[ label="leaf=([^"]+)" \]',
                    replace_leaf,
                    dot
                )

            style_block = """
    graph [rankdir=TB, bgcolor="transparent", nodesep=0.5, ranksep=0.8]
    node [shape=box, style="rounded,filled", fillcolor="#2d2d2d", fontcolor="white", fontname="Helvetica", fontsize=11, color="white"]
    edge [fontname="Helvetica", fontsize=10, fontcolor="white", color="#666666"]
"""
            # Replace the existing graph directive with our styled version
            styled = re.sub(r'graph \[.*?\]', '', dot_string)
            # Style edges based on label: solid for yes, dashed for no
            def style_edge(match: re.Match) -> str:
                """Style edge based on its label (yes* or no*)."""
                edge_def = match.group(0)
                # Replace "missing" with "null" in labels
                edge_def = edge_def.replace('missing', 'null')
                if 'label="yes' in edge_def:
                    # Yes edge (yes, yes null, etc): solid gray
                    edge_def = re.sub(r'color="[^"]*"', 'color="#AAAAAA" style="solid"', edge_def)
                elif 'label="no' in edge_def:
                    # No edge (no, no null, etc): dashed gray
                    edge_def = re.sub(r'color="[^"]*"', 'color="#AAAAAA" style="dashed"', edge_def)
                return edge_def

            styled = re.sub(r'\d+ -> \d+ \[[^\]]+\]', style_edge, styled)

            def flip_edges(dot: str) -> str:
                """Swap yes/no edge order to flip them horizontally."""
                # Find pairs of edges from same parent and swap their order
                lines = dot.split('\n')
                result = []
                i = 0
                while i < len(lines):
                    # Look for yes edge followed by no edge
                    if i + 1 < len(lines) and 'label="yes"' in lines[i] and 'label="no' in lines[i + 1]:
                        # Swap them
                        result.append(lines[i + 1])
                        result.append(lines[i])
                        i += 2
                    else:
                        result.append(lines[i])
                        i += 1
                return '\n'.join(result)

            styled = flip_edges(styled)
            # Condense category sets like {0,1,2,3} to {0-3}
            styled = condense_category_sets(styled)
            # Color leaf nodes based on their value
            styled = color_leaves(styled)
            # Insert style block after digraph {
            styled = styled.replace('digraph {', 'digraph {\n' + style_block, 1)
            return styled

        styled_dot = style_dot(trees[tree_idx])

        # Legend
        with st.expander("How to read the tree", expanded=False):
            st.markdown("""
**What are the different trees?**
- **Tree 0** = First tree, learns the biggest patterns in the data
- **Tree 1** = Trained on Tree 0's *errors*, corrects its mistakes
- **Tree 2, 3, ...** = Each corrects the remaining errors from previous trees
- Earlier trees → major patterns; later trees → fine-tuning edge cases

**How to follow a tree:**
- Start at the **left** (root node) and follow arrows right to a leaf
- Each box is a **decision**: e.g., `tmdb_votes < 0.00003` means "is tmdb_votes less than 0.00003?"
- **Solid gray arrow (yes)** → condition is TRUE
- **Dashed gray arrow (no, null)** → condition is FALSE or value is null
- **Leaf nodes** show a score: positive = leans "would watch", negative = leans "would not watch"
- **Leaf values** are displayed as `raw_value × 100` with a % sign for readability (not a true probability)
- **Final prediction** = sum of leaf scores from ALL 125 trees

**Leaf colors:** (would not) <span style="display:inline-block;width:18px;height:14px;background:#D94A4A;vertical-align:middle;"></span><span style="display:inline-block;width:18px;height:14px;background:#C45499;vertical-align:middle;"></span><span style="display:inline-block;width:18px;height:14px;background:#B05EB0;vertical-align:middle;"></span><span style="display:inline-block;width:18px;height:14px;background:#9B59B6;vertical-align:middle;"></span><span style="display:inline-block;width:18px;height:14px;background:#7A6DC3;vertical-align:middle;"></span><span style="display:inline-block;width:18px;height:14px;background:#5A80CF;vertical-align:middle;"></span><span style="display:inline-block;width:18px;height:14px;background:#4A90D9;vertical-align:middle;"></span> (would watch)
""", unsafe_allow_html=True)

        # Render selected tree in a bordered container
        with st.container(border=True):
            st.graphviz_chart(styled_dot, use_container_width=True)

        # Show raw DOT in expander
        with st.expander("View DOT source"):
            st.code(trees[tree_idx], language="dot")


if __name__ == "__main__":
    main()
