"""OpenSatCom CLI entry point."""

import argparse
import sys
import traceback
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="opensatcom",
        description="Professional-grade satellite communications engineering toolkit",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")

    sub = parser.add_subparsers(dest="command")

    # opensatcom run
    run_parser = sub.add_parser("run", help="Snapshot link evaluation")
    run_parser.add_argument("config", help="Path to YAML config file")

    # opensatcom mission
    mission_parser = sub.add_parser("mission", help="Time-series mission simulation")
    mission_parser.add_argument("config", help="Path to YAML config file")

    # opensatcom doe
    doe_parser = sub.add_parser("doe", help="Design of experiments")
    doe_parser.add_argument("config", help="Path to YAML config file")
    doe_parser.add_argument("-n", type=int, default=200, help="Number of cases")
    doe_parser.add_argument("--method", default="lhs", help="Sampling method")

    # opensatcom batch
    batch_parser = sub.add_parser("batch", help="Batch evaluation from parquet")
    batch_parser.add_argument("cases", help="Path to cases parquet file")
    batch_parser.add_argument("--parallel", action="store_true", help="Enable parallel execution")

    # opensatcom report
    report_parser = sub.add_parser("report", help="Generate report from results")
    report_parser.add_argument("results", help="Path to results parquet file")
    report_parser.add_argument("--format", default="html", choices=["html", "pdf"])

    # opensatcom pareto
    pareto_parser = sub.add_parser("pareto", help="Pareto extraction from results")
    pareto_parser.add_argument("results", help="Path to results parquet file")
    pareto_parser.add_argument("--x", required=True, help="X-axis metric")
    pareto_parser.add_argument("--y", required=True, help="Y-axis metric")

    return parser


def cmd_run(args: argparse.Namespace) -> None:
    """Snapshot link evaluation."""
    import pandas as pd

    from opensatcom.cli.builders import build_link_inputs_from_config
    from opensatcom.core.models import PropagationConditions
    from opensatcom.geometry.slant import slant_range_m
    from opensatcom.io.config_loader import load_config
    from opensatcom.io.workspace import RunContext
    from opensatcom.link.engine import DefaultLinkEngine
    from opensatcom.reports.snapshot import render_snapshot_report

    cfg = load_config(args.config)
    link_inputs = build_link_inputs_from_config(cfg)

    # Compute slant range for a default elevation of 30 deg
    elev_deg = 30.0
    range_m = slant_range_m(
        link_inputs.rx_terminal.alt_m,
        link_inputs.tx_terminal.alt_m,
        elev_deg,
    )

    engine = DefaultLinkEngine()
    out = engine.evaluate_snapshot(
        elev_deg=elev_deg, az_deg=0.0, range_m=range_m,
        inputs=link_inputs, cond=PropagationConditions(),
    )

    # Save artifacts
    ctx = RunContext(output_dir=cfg.project.output_dir, run_id=cfg.project.name)
    ctx.save_config_snapshot(cfg.model_dump())

    results_df = pd.DataFrame([{
        "eirp_dbw": out.eirp_dbw,
        "gt_dbk": out.gt_dbk,
        "path_loss_db": out.path_loss_db,
        "cn0_dbhz": out.cn0_dbhz,
        "ebn0_db": out.ebn0_db,
        "margin_db": out.margin_db,
    }])
    ctx.save_results_parquet(results_df)

    if out.breakdown:
        breakdown_df = pd.DataFrame([out.breakdown])
        ctx.save_breakdown_csv(breakdown_df)
        render_snapshot_report(out.breakdown, cfg.model_dump(), ctx.run_dir / "report.html")

    print(f"Snapshot link budget complete. Margin: {out.margin_db:.2f} dB")
    print(f"  EIRP:      {out.eirp_dbw:.2f} dBW")
    print(f"  Path loss:  {out.path_loss_db:.2f} dB")
    print(f"  C/N0:      {out.cn0_dbhz:.2f} dB-Hz")
    print(f"  Eb/N0:     {out.ebn0_db:.2f} dB")
    print(f"  Margin:    {out.margin_db:.2f} dB")
    print(f"Artifacts saved to: {ctx.run_dir}")


def cmd_mission(args: argparse.Namespace) -> None:
    """Time-series mission simulation."""
    import numpy as np
    import pandas as pd

    from opensatcom.cli.builders import build_link_inputs_from_config
    from opensatcom.core.models import OpsPolicy, PropagationConditions
    from opensatcom.geometry.slant import slant_range_m
    from opensatcom.io.config_loader import load_config
    from opensatcom.io.workspace import RunContext
    from opensatcom.reports.mission import render_mission_report
    from opensatcom.world.providers import PrecomputedTrajectory, StaticEnvironmentProvider
    from opensatcom.world.sim import SimpleWorldSim

    cfg = load_config(args.config)
    link_inputs = build_link_inputs_from_config(cfg)

    world_cfg = cfg.world
    if world_cfg is None:
        print("Error: 'world' section required for mission command", file=sys.stderr)
        sys.exit(2)

    # Generate synthetic pass data (elevation sweep)
    t0 = world_cfg.t0_s
    t1 = world_cfg.t1_s
    dt = world_cfg.dt_s
    n_steps = int((t1 - t0) / dt)
    times = np.linspace(t0, t1, n_steps)
    elev = np.concatenate([
        np.linspace(5.0, 80.0, n_steps // 2),
        np.linspace(80.0, 5.0, n_steps - n_steps // 2),
    ])
    az = np.zeros(n_steps)
    range_arr = np.array([
        slant_range_m(link_inputs.rx_terminal.alt_m, link_inputs.tx_terminal.alt_m, e)
        for e in elev
    ])

    traj = PrecomputedTrajectory.from_arrays(times, elev, az, range_arr)
    ops = OpsPolicy(
        min_elevation_deg=world_cfg.ops_policy.min_elevation_deg,
        max_scan_deg=world_cfg.ops_policy.max_scan_deg,
    )
    env = StaticEnvironmentProvider(PropagationConditions())

    sim = SimpleWorldSim()
    out = sim.run(link_inputs, traj, ops, env)

    # Save artifacts
    ctx = RunContext(output_dir=cfg.project.output_dir, run_id=cfg.project.name)
    ctx.save_config_snapshot(cfg.model_dump())

    results_df = pd.DataFrame({
        "time_s": out.times_s,
        "elev_deg": out.elev_deg,
        "range_m": out.range_m,
        "margin_db": out.margin_db,
        "outage": out.outages_mask,
    })
    ctx.save_results_parquet(results_df)

    render_mission_report(
        summary=out.summary,
        times_s=out.times_s,
        margin_db=out.margin_db,
        elev_deg=out.elev_deg,
        outages_mask=out.outages_mask,
        config=cfg.model_dump(),
        output_path=ctx.run_dir / "report.html",
        plots_dir=ctx.plots_dir,
    )

    print("Mission simulation complete.")
    for key, val in out.summary.items():
        print(f"  {key}: {val:.4f}")
    print(f"Artifacts saved to: {ctx.run_dir}")


def cmd_report(args: argparse.Namespace) -> None:
    """Generate report from results parquet."""
    import pandas as pd

    results_path = Path(args.results)
    if not results_path.exists():
        print(f"Error: results file not found: {results_path}", file=sys.stderr)
        sys.exit(2)

    df = pd.read_parquet(results_path)

    # Detect type based on columns
    if "time_s" in df.columns:
        # Mission results
        import numpy as np

        from opensatcom.reports.mission import render_mission_report

        out_path = results_path.with_suffix(".html")
        summary = {
            "margin_db_mean": float(df["margin_db"].mean()),
            "margin_db_min": float(df["margin_db"].min()),
        }
        render_mission_report(
            summary=summary,
            times_s=df["time_s"].to_numpy(),
            margin_db=df["margin_db"].to_numpy(),
            elev_deg=(
                df["elev_deg"].to_numpy() if "elev_deg" in df.columns
                else np.zeros(len(df))
            ),
            outages_mask=(
                df["outage"].to_numpy() if "outage" in df.columns
                else np.zeros(len(df), dtype=bool)
            ),
            config={},
            output_path=out_path,
        )
        print(f"Report generated: {out_path}")
    else:
        # Snapshot results
        from opensatcom.reports.snapshot import render_snapshot_report

        out_path = results_path.with_suffix(".html")
        breakdown: dict[str, float] = {str(k): float(v) for k, v in df.iloc[0].to_dict().items()}
        render_snapshot_report(breakdown, {}, out_path)
        print(f"Report generated: {out_path}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    dispatch = {
        "run": cmd_run,
        "mission": cmd_mission,
        "report": cmd_report,
    }

    handler = dispatch.get(args.command)
    if handler is None:
        print(f"opensatcom {args.command}: not yet implemented")
        sys.exit(1)

    try:
        handler(args)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Runtime error: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(3)
